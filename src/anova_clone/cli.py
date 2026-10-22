"""CLI adaptörü — hocanın CLI sözleşmesi (CONTRACT.md v1.0.0, CONTRACT_NOTES.md).

Katmanlar:
  argv -> parse_argv() -> params (dict, ham değerler)
  params -> run() -> (payload, exit_code, stderr_text)      <- CLI ve MCP ortak yolu
  run(): sözleşme doğrulaması (test/mod, alan kümesi, değer tipi, §5 aralıkları)
         -> engine.a_priori / engine.post_hoc (G*Power kuralları, formüller)
         -> sözleşme çıktı sözlüğü (sayılar YUVARLANMADAN)

Formül ve G*Power'a özgü doğrulama yalnızca engine.py'dedir. Bu modül yalnızca
sözleşmenin dış kabuğunu uygular: adlar, tipler, §5 aralıkları, hata kodları.
"""
from __future__ import annotations

import json
import math
import platform
import re
import sys

from . import engine
from .errors import InvalidInputError, SolverError

# ---------------------------------------------------------------------------
# Sözleşme sabitleri (tek yer)
# ---------------------------------------------------------------------------
CONTRACT_VERSION = "1.0.0"
TEAM_NAME = "teardown-anova"

TEST_ANOVA = "anova-oneway"
MODE_A_PRIORI = "a-priori"
MODE_POST_HOC = "post-hoc"

# Moda göre izinli (= gerekli) alanlar, sözleşmedeki sırayla
MODE_FIELDS = {
    MODE_A_PRIORI: ("f", "alpha", "power", "groups"),
    MODE_POST_HOC: ("f", "alpha", "n_total", "groups"),
}
INTEGER_FIELDS = frozenset({"groups", "n_total"})
CONTROL_FIELDS = ("test", "mode")

# Sözleşmede tanımlı ama bu motorun desteklemediği kimlikler (mesaj için)
OTHER_TESTS = ("t2-indep", "t-paired", "chi2-contingency", "multireg-r2")
BONUS_MODES = ("compromise", "criterion", "sensitivity")

EXIT_OK = 0
EXIT_NO_SOLUTION = 1
EXIT_INVALID = 2

# Motorun alan adı -> sözleşme alan adı
ENGINE_FIELD = {"f": "f", "alpha": "alpha", "power": "power",
                "k": "groups", "n_total": "n_total"}

# Sözleşme §5 aralıkları. Mesajlar G*Power metinleriyle aynı (R36) olabildiği
# yerde aynı; G*Power'ın kabul edip sözleşmenin reddettiği post hoc f = 0 için
# ayrı metin kullanılır.
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


class ContractError(Exception):
    def __init__(self, code: str, field, message: str, exit_code: int = EXIT_INVALID):
        super().__init__(message)
        self.code, self.field, self.message, self.exit_code = code, field, message, exit_code


# ---------------------------------------------------------------------------
# Çıktı yardımcıları
# ---------------------------------------------------------------------------
def to_json_line(obj: dict) -> str:
    """Tek satır JSON; float'lar json'un varsayılan repr'i ile (tam double)."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def error_to_dict(code: str, field, message: str) -> dict:
    return {"error": message, "code": code, "field": field}


def result_to_dict(result: engine.Result, mode: str) -> dict:
    out = {
        "ncp": float(result.ncp),
        "critical_f": float(result.critical_f),
        "df1": int(result.df1),
        "df2": int(result.df2),
    }
    if mode == MODE_A_PRIORI:
        out["n_total"] = int(result.n_total)
        out["actual_power"] = float(result.power)
        out["n_per_group"] = result.n_per_group
    else:
        out["power"] = float(result.power)
        out["n_total"] = int(result.n_total)
        out["n_per_group"] = result.n_per_group
        if result.warning is not None:
            out["warning"] = result.warning
    return out


def version_dict() -> dict:
    import scipy
    return {"contract_version": CONTRACT_VERSION, "name": TEAM_NAME,
            "engine": f"Python {platform.python_version()} + scipy {scipy.__version__}"}


# ---------------------------------------------------------------------------
# Sözleşme doğrulaması
# ---------------------------------------------------------------------------
def _check_test_mode(params: dict) -> str:
    for name in CONTROL_FIELDS:
        if params.get(name) is None:
            raise ContractError("MISSING_PARAM", name, f"Missing required parameter: {name}.")
    test, mode = params["test"], params["mode"]
    if not isinstance(test, str) or test != TEST_ANOVA:
        raise ContractError("UNSUPPORTED", "test",
                            f"Unsupported test: {test!s}. Supported: {TEST_ANOVA}.")
    if not isinstance(mode, str) or mode not in MODE_FIELDS:
        raise ContractError("UNSUPPORTED", "mode",
                            f"Unsupported mode: {mode!s}. Supported: "
                            f"{MODE_A_PRIORI}, {MODE_POST_HOC}.")
    return mode


def _check_field_set(params: dict, mode: str) -> None:
    allowed = MODE_FIELDS[mode]
    for name in params:
        if name in CONTROL_FIELDS or params[name] is None:
            continue
        if name not in allowed:
            raise ContractError("UNKNOWN_PARAM", name,
                                f"Unknown or irrelevant parameter for {mode}: {name}.")
    for name in allowed:
        if params.get(name) is None:
            raise ContractError("MISSING_PARAM", name,
                                f"Missing required parameter for {mode}: {name}.")


def _parse_value(name: str, raw):
    """Ham değeri (CLI: str, MCP: number/str) sayıya çevirir. Tamsayı alanlarda
    tam sayı değerli ondalık (3.0) kabul edilir, kesirli (2.5) INVALID_VALUE."""
    if isinstance(raw, bool):
        x = None
    elif isinstance(raw, (int, float)):
        x = float(raw)
    elif isinstance(raw, str) and _NUMBER_RE.match(raw.strip()):
        x = float(raw.strip())
    else:
        x = None
    if x is None or not math.isfinite(x):
        raise ContractError("INVALID_VALUE", name, f"Value of {name} is not a valid number.")
    if name in INTEGER_FIELDS:
        if x != math.floor(x):
            raise ContractError("INVALID_VALUE", name, f"Value of {name} must be an integer.")
        return int(x)
    return x


# G*Power'ın da reddettiği durumlarda motorun G*Power metni (R36) kullanılır;
# yalnızca sözleşmenin reddettiği post hoc f = 0 için ayrı metin vardır.
MSG_F_ZERO_CONTRACT = "Effect size f must be greater than 0."


def _check_range(name: str, value, values: dict, mode: str) -> None:
    """Sözleşme §5. alpha, power (0,1) açık; f > 0; groups, n_total ≥ 2."""
    if name == "alpha" and not 0.0 < value < 1.0:
        raise ContractError("OUT_OF_RANGE", name, engine.MSG_ALPHA_RANGE)
    if name == "power" and not 0.0 < value < 1.0:
        raise ContractError("OUT_OF_RANGE", name, engine.MSG_POWER_RANGE)
    if name == "f" and not value > 0.0:
        if mode == MODE_POST_HOC and value == 0.0:
            message = MSG_F_ZERO_CONTRACT
        else:
            lo = engine.F_MIN_A_PRIORI if mode == MODE_A_PRIORI else engine.F_MIN_POST_HOC
            message = engine.MSG_F_RANGE.format(lo=lo, hi=engine.F_MAX)
        raise ContractError("OUT_OF_RANGE", name, message)
    if name == "groups" and value < 2:
        raise ContractError("OUT_OF_RANGE", name, engine.MSG_GROUPS)
    if name == "n_total" and value < 2:
        raise ContractError("OUT_OF_RANGE", name,
                            engine.MSG_SAMPLE_SIZE.format(k=values["groups"]))


def run(params: dict) -> tuple[dict, int, str | None]:
    """Sözleşme girişi: params (alan adı -> ham değer). Dönüş: (stdout sözlüğü,
    çıkış kodu, stderr metni ya da None). CLI ve MCP bu fonksiyonu kullanır."""
    try:
        mode = _check_test_mode(params)
        _check_field_set(params, mode)
        values = {n: _parse_value(n, params[n]) for n in MODE_FIELDS[mode]}
        for n in MODE_FIELDS[mode]:
            _check_range(n, values[n], values, mode)
        try:
            if mode == MODE_A_PRIORI:
                result = engine.a_priori(f=values["f"], alpha=values["alpha"],
                                         power=values["power"], k=values["groups"])
            else:
                result = engine.post_hoc(f=values["f"], alpha=values["alpha"],
                                         n_total=values["n_total"], k=values["groups"])
        except InvalidInputError as exc:
            raise ContractError(exc.code, ENGINE_FIELD.get(exc.field, exc.field), exc.message)
        except SolverError as exc:
            raise ContractError(SolverError.code, None, str(exc), EXIT_NO_SOLUTION)
    except ContractError as exc:
        return error_to_dict(exc.code, exc.field, exc.message), exc.exit_code, None
    except Exception as exc:  # pragma: no cover - beklenmeyen iç hata
        return (error_to_dict("NO_SOLUTION", None, f"Internal error: {exc}"),
                EXIT_NO_SOLUTION, None)
    payload = result_to_dict(result, mode)
    return payload, EXIT_OK, payload.get("warning")


# ---------------------------------------------------------------------------
# argv -> params
# ---------------------------------------------------------------------------
def parse_argv(argv: list[str]) -> dict:
    """`--ad değer` ya da `--ad=değer`. Negatif sayılar değer olarak kabul edilir
    (`--f -0.25`). argparse kullanılmaz: stdout'a kendi metnini yazmasın diye."""
    params: dict = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if not tok.startswith("--") or len(tok) == 2:
            raise ContractError("UNKNOWN_PARAM", None, f"Unexpected argument: {tok}.")
        name, eq, value = tok[2:].partition("=")
        if not eq:
            nxt = argv[i + 1] if i + 1 < len(argv) else None
            if nxt is None or (nxt.startswith("--") and not _NUMBER_RE.match(nxt)):
                raise ContractError("INVALID_VALUE", name, f"Missing value for --{name}.")
            value = nxt
            i += 1
        if name in params:
            raise ContractError("INVALID_VALUE", name, f"Parameter given more than once: {name}.")
        params[name] = value
        i += 1
    return params


def main(argv=None, stdout=None, stderr=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    if "--version" in argv:
        stdout.write(to_json_line(version_dict()) + "\n")
        return EXIT_OK
    try:
        params = parse_argv(argv)
    except ContractError as exc:
        stdout.write(to_json_line(error_to_dict(exc.code, exc.field, exc.message)) + "\n")
        return exc.exit_code
    payload, code, stderr_text = run(params)
    stdout.write(to_json_line(payload) + "\n")
    if stderr_text:
        stderr.write(stderr_text + "\n")
    return code


def console_main() -> None:
    sys.exit(main())


if __name__ == "__main__":
    console_main()
