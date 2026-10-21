"""MCP sunucusu: stdio üzerinden JSON-RPC 2.0 (satır başına bir mesaj).

İnce adaptör: argümanları alır, `cli.run` üzerinden motoru çağırır, CLI ile birebir
aynı JSON'u döndürür. Hesap ve doğrulama mantığı yalnızca engine.py'dedir; bu modül
yalnızca protokolü ve araç şemasını tanımlar. stdout yalnızca protokol mesajları
içindir; tanılama gerekiyorsa stderr kullanılır.
"""
from __future__ import annotations

import json
import sys

from . import cli

SERVER_NAME = "anova-power-clone"
SERVER_VERSION = "1.1.0"
DEFAULT_PROTOCOL_VERSION = "2025-06-18"

# JSON-RPC hata kodları
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# ---------------------------------------------------------------------------
# Araç şeması (tek kaynak; MCP_SCHEMA.md bununla eşleşir, testte doğrulanır)
# ---------------------------------------------------------------------------
_F = {"type": "number",
      "description": "Cohen's f etki büyüklüğü / effect size "
                     "(küçük/small .10, orta/medium .25, büyük/large .40)"}
_ALPHA = {"type": "number",
          "description": "Anlamlılık düzeyi α / significance level, örn./e.g. 0.05"}
_GROUPS = {"type": "number",
           "description": "Grup sayısı k (≥2) / number of groups; kesirliyse en yakına yuvarlanır"}
_POWER = {"type": "number",
          "description": "Hedef güç 1−β / target power, örn./e.g. 0.80"}
_N = {"type": "number",
      "description": "Toplam örneklem N (tüm gruplar) / total sample size, > groups"}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "n_total": {"type": "integer"},
        "n_per_group": {"type": ["integer", "null"]},
        "actual_power": {"type": "number"},
        "power": {"type": "number"},
        "critical": {"type": "number"},
        "df1": {"type": "integer"},
        "df2": {"type": "integer"},
        "ncp": {"type": "number"},
        "warning": {"type": "string"},
        "error": {"type": "string"},
    },
}

TOOLS = [
    {
        "name": "anova_oneway_a_priori",
        "description": ("Tek yönlü ANOVA (sabit etkili, omnibus F): hedef güç için gereken "
                        "örneklem büyüklüğü N. / One-way ANOVA a priori: required sample size."),
        "inputSchema": {
            "type": "object",
            "properties": {"f": _F, "alpha": _ALPHA, "power": _POWER, "groups": _GROUPS},
            "required": ["f", "alpha", "power", "groups"],
        },
        "outputSchema": OUTPUT_SCHEMA,
        "_mode": cli.NAMES["mode_a_priori"],
    },
    {
        "name": "anova_oneway_post_hoc",
        "description": ("Tek yönlü ANOVA (sabit etkili, omnibus F): verilen N ile ulaşılan "
                        "istatistiksel güç. / One-way ANOVA post hoc: achieved power."),
        "inputSchema": {
            "type": "object",
            "properties": {"f": _F, "alpha": _ALPHA, "n_total": _N, "groups": _GROUPS},
            "required": ["f", "alpha", "n_total", "groups"],
        },
        "outputSchema": OUTPUT_SCHEMA,
        "_mode": cli.NAMES["mode_post_hoc"],
    },
]
_TOOLS_BY_NAME = {t["name"]: t for t in TOOLS}


def _public(tool: dict) -> dict:
    return {k: v for k, v in tool.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# Araç çağrısı
# ---------------------------------------------------------------------------
class _ParamsError(Exception):
    pass


def _number_arg(args: dict, name: str):
    """Argümanı sayıya çevirir. Sayı olmayan değerlerin anlamsal kontrolü
    engine'de yapılır; burada yalnızca JSON tipinden Python float'a geçiş var.
    Sayısal string ("0.25") CLI ile aynı davranış için kabul edilir."""
    if name not in args or args[name] is None:
        raise _ParamsError(f"missing required argument: {name}")
    v = args[name]
    if isinstance(v, bool):
        raise _ParamsError(f"argument {name} must be a number")
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            pass
    raise _ParamsError(f"argument {name} must be a number")


def call_tool(name: str, arguments: dict | None) -> dict:
    """tools/call sonucunu (MCP CallToolResult) döndürür. Bilinmeyen araç/eksik
    argüman -> _ParamsError (JSON-RPC -32602)."""
    tool = _TOOLS_BY_NAME.get(name)
    if tool is None:
        raise _ParamsError(f"unknown tool: {name}")
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise _ParamsError("arguments must be an object")
    for req in tool["inputSchema"]["required"]:
        if req not in arguments or arguments[req] is None:
            raise _ParamsError(f"missing required argument: {req}")

    mode = tool["_mode"]
    f = _number_arg(arguments, "f")
    alpha = _number_arg(arguments, "alpha")
    groups = _number_arg(arguments, "groups")
    if mode == cli.NAMES["mode_a_priori"]:
        payload, code = cli.run(mode, f=f, alpha=alpha, groups=groups,
                                power=_number_arg(arguments, "power"))
    else:
        payload, code = cli.run(mode, f=f, alpha=alpha, groups=groups,
                                n=_number_arg(arguments, "n_total"))
    return {
        "content": [{"type": "text", "text": cli.to_json_line(payload)}],
        "structuredContent": payload,
        "isError": code != cli.EXIT_OK,
    }


# ---------------------------------------------------------------------------
# JSON-RPC dağıtımı
# ---------------------------------------------------------------------------
def _ok(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _err(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def handle_message(msg) -> dict | None:
    """Tek bir JSON-RPC mesajını işler; yanıt (ya da bildirimse None) döndürür."""
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or "method" not in msg:
        return _err(msg.get("id") if isinstance(msg, dict) else None,
                    INVALID_REQUEST, "Invalid Request")
    method = msg["method"]
    is_notification = "id" not in msg
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    if is_notification:
        return None                     # notifications/initialized, cancelled, ...

    try:
        if method == "initialize":
            requested = params.get("protocolVersion") if isinstance(params, dict) else None
            return _ok(msg_id, {
                "protocolVersion": requested or DEFAULT_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            })
        if method == "ping":
            return _ok(msg_id, {})
        if method == "tools/list":
            return _ok(msg_id, {"tools": [_public(t) for t in TOOLS]})
        if method == "tools/call":
            if not isinstance(params, dict) or not isinstance(params.get("name"), str):
                return _err(msg_id, INVALID_PARAMS, "tools/call requires a tool name")
            return _ok(msg_id, call_tool(params["name"], params.get("arguments")))
        return _err(msg_id, METHOD_NOT_FOUND, f"Method not found: {method}")
    except _ParamsError as exc:
        return _err(msg_id, INVALID_PARAMS, str(exc))
    except Exception as exc:            # pragma: no cover - güvenlik ağı
        print(f"[{SERVER_NAME}] internal error: {exc!r}", file=sys.stderr)
        return _err(msg_id, INTERNAL_ERROR, "Internal error")


def handle_line(line: str) -> list[dict]:
    """Bir stdin satırını işler; yazılacak yanıtları döndürür (batch desteklenir)."""
    line = line.strip()
    if not line:
        return []
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return [_err(None, PARSE_ERROR, "Parse error")]
    if isinstance(msg, list):
        if not msg:
            return [_err(None, INVALID_REQUEST, "Invalid Request")]
        return [r for r in (handle_message(m) for m in msg) if r is not None]
    r = handle_message(msg)
    return [] if r is None else [r]


def serve(stdin=None, stdout=None) -> None:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for line in stdin:
        responses = handle_line(line)
        if not responses:
            continue
        out = responses if len(responses) > 1 or line.lstrip().startswith("[") else responses[0]
        stdout.write(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n")
        stdout.flush()


def main() -> None:
    # Satır tamponlu, UTF-8 stdio (Windows konsol kodlamasından bağımsız)
    try:
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    except (AttributeError, ValueError):  # pragma: no cover
        pass
    try:
        serve()
    except KeyboardInterrupt:  # pragma: no cover
        pass


if __name__ == "__main__":
    main()
