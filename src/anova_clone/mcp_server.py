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
# Araç şeması (sözleşme: tek araç `power_analysis`, CLI ile aynı alan adları)
# ---------------------------------------------------------------------------
TOOL_NAME = "power_analysis"

TOOL = {
    "name": TOOL_NAME,
    "description": (
        "G*Power uyumlu güç analizi / power analysis. test='anova-oneway' (tek yönlü ANOVA, "
        "sabit etkili, omnibus F). mode='a-priori': gerekli N (f, alpha, power, groups); "
        "mode='post-hoc': ulaşılan güç (f, alpha, n_total, groups). Moda ilgisiz alan "
        "verilmemeli. Hatalar {error, code, field} JSON'u döner."),
    "inputSchema": {
        "type": "object",
        "properties": {
            "test": {"type": "string",
                     "description": "Test ailesi / test family; desteklenen: anova-oneway"},
            "mode": {"type": "string",
                     "description": "Hesap modu / analysis mode: a-priori | post-hoc"},
            "f": {"type": "number",
                  "description": "Cohen's f etki büyüklüğü / effect size (küçük .10, orta .25, "
                                 "büyük .40); > 0; her iki mod"},
            "alpha": {"type": "number",
                      "description": "Anlamlılık düzeyi / significance level, (0,1); her iki mod"},
            "power": {"type": "number",
                      "description": "Hedef güç 1−β / target power, (0,1); yalnızca a-priori"},
            "groups": {"type": "number",
                       "description": "Grup sayısı / number of groups, tam sayı ≥ 2; her iki mod"},
            "n_total": {"type": "number",
                        "description": "Toplam örneklem / total sample size, tam sayı > groups; "
                                       "yalnızca post-hoc"},
        },
        "required": ["test", "mode"],
    },
}


class _ParamsError(Exception):
    pass


def call_tool(name: str, arguments) -> dict:
    """tools/call sonucu. Bilinmeyen araç / nesne olmayan arguments -> -32602.
    Alan hataları (eksik, bilinmeyen, geçersiz değer...) sözleşme hata JSON'u olarak
    `isError: true` ile döner (CLI ile aynı)."""
    if name != TOOL_NAME:
        raise _ParamsError(f"unknown tool: {name}")
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise _ParamsError("arguments must be an object")
    payload, code, _stderr = cli.run(dict(arguments))
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
            return _ok(msg_id, {"tools": [TOOL]})
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
