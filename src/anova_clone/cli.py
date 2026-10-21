"""İnce CLI adaptörü: argüman ayrıştır -> engine çağır -> tek satır JSON yaz.

Hiçbir formül, aralık kontrolü veya hesap mantığı burada yoktur. Tüm dış adlar
(CLI seçenekleri ve takma adları, test/mod değerleri, JSON alanları) aşağıdaki
NAMES ve ALIASES sözlüklerindedir; CONTRACT.md gelince yalnızca orası değişmelidir.
"""
from __future__ import annotations

import argparse
import json
import sys

from . import engine
from .errors import InvalidInputError, SolverError

# ---------------------------------------------------------------------------
# Tek ad sözlüğü (geçici sözleşme)
# ---------------------------------------------------------------------------
NAMES = {
    # komut adı
    "prog": "gpower-clone",
    # seçeneklerin kanonik (mesajlarda gösterilen) adları
    "opt_test": "--test",
    "opt_mode": "--mode",
    "opt_f": "--f",
    "opt_alpha": "--alpha",
    "opt_power": "--power",
    "opt_n": "--n",
    "opt_groups": "--groups",
    # seçenek değerlerinin kanonik adları
    "test_anova_oneway": "anova-oneway",
    "mode_a_priori": "a-priori",
    "mode_post_hoc": "post-hoc",
    # JSON çıktı alanları
    "out_n_total": "n_total",
    "out_n_per_group": "n_per_group",
    "out_power_a_priori": "actual_power",
    "out_power_post_hoc": "power",
    "out_critical": "critical",
    "out_df1": "df1",
    "out_df2": "df2",
    "out_ncp": "ncp",
    "out_warning": "warning",
    "out_error": "error",
}

# Takma adlar. Seçenekler büyük/küçük harf DUYARLI (--n ve --N ayrı yazımlar,
# ikisi de aynı hedefe gider); değerler büyük/küçük harf DUYARSIZ eşlenir.
ALIASES = {
    "opt_test": ["--test"],
    "opt_mode": ["--mode"],
    "opt_f": ["--f", "--effect-size", "--es"],
    "opt_alpha": ["--alpha"],
    "opt_power": ["--power", "--target-power"],
    "opt_n": ["--n", "--n-total", "--n_total", "--total-n", "--sample-size", "--N"],
    "opt_groups": ["--groups", "--k", "--k-groups", "--num-groups", "--number-of-groups"],
    "test_anova_oneway": ["anova-oneway", "anova_oneway", "anova"],
    "mode_a_priori": ["a-priori", "apriori", "a_priori"],
    "mode_post_hoc": ["post-hoc", "posthoc", "post_hoc"],
}

# JSON'daki alan sırası (güç her iki modda iki anahtarla yazılır)
OUTPUT_ORDER = ["out_n_total", "out_n_per_group", "out_power_a_priori",
                "out_power_post_hoc", "out_critical", "out_df1", "out_df2",
                "out_ncp", "out_warning"]

# Motor alan adı -> dışarıya gösterilecek seçenek adı (hata mesajları için)
FIELD_TO_OPTION = {
    "f": "opt_f",
    "alpha": "opt_alpha",
    "power": "opt_power",
    "n_total": "opt_n",
    "k": "opt_groups",
}

# JSON'daki sayıların ondalık basamak sayısı
JSON_DECIMALS = 7

EXIT_OK = 0
EXIT_INPUT_ERROR = 2
EXIT_COMPUTE_ERROR = 3


class _ArgError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):  # argparse'ın stderr'e yazıp çıkmasını engelle
        raise _ArgError(message)


def _number(text: str) -> float:
    try:
        return float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a number: {text!r}")


def _value_map(*keys: str) -> dict[str, str]:
    """Küçük harfli takma ad -> kanonik değer."""
    return {alias.lower(): NAMES[key] for key in keys for alias in ALIASES[key]}


def _choice(keys, option_key):
    mapping = _value_map(*keys)

    def convert(text: str) -> str:
        try:
            return mapping[text.strip().lower()]
        except KeyError:
            allowed = ", ".join(a for k in keys for a in ALIASES[k])
            raise argparse.ArgumentTypeError(
                f"invalid value {text!r} for {NAMES[option_key]} (allowed: {allowed})")
    return convert


def build_parser() -> argparse.ArgumentParser:
    # allow_abbrev=False: --e gibi kısaltmalar takma adlar arasında belirsizlik yaratmasın,
    # bilinmeyen seçenekler de yanlışlıkla bir takma ada önek-eşlenmesin.
    p = _Parser(prog=NAMES["prog"], add_help=True, allow_abbrev=False)
    p.add_argument(*ALIASES["opt_test"], dest="test", required=True,
                   type=_choice(["test_anova_oneway"], "opt_test"))
    p.add_argument(*ALIASES["opt_mode"], dest="mode", required=True,
                   type=_choice(["mode_a_priori", "mode_post_hoc"], "opt_mode"))
    p.add_argument(*ALIASES["opt_f"], dest="f", type=_number, required=True)
    p.add_argument(*ALIASES["opt_alpha"], dest="alpha", type=_number, required=True)
    p.add_argument(*ALIASES["opt_power"], dest="power", type=_number)
    p.add_argument(*ALIASES["opt_n"], dest="n", type=_number)
    p.add_argument(*ALIASES["opt_groups"], dest="groups", type=_number, required=True)
    return p


def _num(x):
    if x is None:
        return None
    if isinstance(x, int):
        return x
    return round(float(x), JSON_DECIMALS)


def result_to_dict(result: engine.Result, mode: str | None = None) -> dict:
    """Paylaşılan çıktı biçimleyici (CLI ve MCP). Alan adları NAMES, sıra OUTPUT_ORDER,
    sayılar JSON_DECIMALS ondalık. `mode` geriye uyumluluk için kabul edilir; güç her
    iki modda iki anahtarla yazıldığından çıktıyı etkilemez."""
    power = _num(result.power)
    values = {
        "out_n_total": result.n_total,
        "out_n_per_group": result.n_per_group,
        "out_power_a_priori": power,
        "out_power_post_hoc": power,
        "out_critical": _num(result.critical_f),
        "out_df1": result.df1,
        "out_df2": result.df2,
        "out_ncp": _num(result.ncp),
        "out_warning": result.warning,
    }
    out = {}
    for key in OUTPUT_ORDER:
        if key == "out_warning" and values[key] is None:
            continue
        out[NAMES[key]] = values[key]
    return out


format_result = result_to_dict   # eski ad (Tur 1-3 testleri)


def error_to_dict(exc_or_message) -> dict:
    """Paylaşılan hata biçimleyici. InvalidInputError'da mesajın önüne sorunlu
    alanın kanonik CLI seçenek adı eklenir (R34): "--alpha: Alpha is outside ..."."""
    if isinstance(exc_or_message, InvalidInputError):
        exc = exc_or_message
        opt = NAMES[FIELD_TO_OPTION[exc.field]] if exc.field in FIELD_TO_OPTION else exc.field
        message = f"{opt}: {exc.message}"
    else:
        message = str(exc_or_message)
    return {NAMES["out_error"]: message}


def run(mode: str, f, alpha, groups, power=None, n=None) -> tuple[dict, int]:
    """Kanonik mod değeriyle motoru çağırır; (JSON sözlüğü, çıkış kodu) döndürür.
    CLI ve MCP aynı yolu kullanır; hesap/doğrulama yalnızca engine'de."""
    try:
        if mode == NAMES["mode_a_priori"]:
            if power is None:
                return error_to_dict(f"{NAMES['opt_power']} is required in "
                                     f"{NAMES['mode_a_priori']} mode"), EXIT_INPUT_ERROR
            result = engine.a_priori(f=f, alpha=alpha, power=power, k=groups)
        elif mode == NAMES["mode_post_hoc"]:
            if n is None:
                return error_to_dict(f"{NAMES['opt_n']} is required in "
                                     f"{NAMES['mode_post_hoc']} mode"), EXIT_INPUT_ERROR
            result = engine.post_hoc(f=f, alpha=alpha, n_total=n, k=groups)
        else:
            return error_to_dict(f"invalid value {mode!r} for {NAMES['opt_mode']}"), EXIT_INPUT_ERROR
    except InvalidInputError as exc:
        return error_to_dict(exc), EXIT_INPUT_ERROR
    except SolverError as exc:
        return error_to_dict(exc), EXIT_COMPUTE_ERROR
    return result_to_dict(result, mode), EXIT_OK


def to_json_line(obj: dict) -> str:
    """Tek satır JSON (CLI stdout'u ve MCP text içeriği birebir aynı olsun diye)."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _emit(obj: dict, stream) -> None:
    stream.write(to_json_line(obj) + "\n")


def _error(message: str, code: int, stream) -> int:
    _emit(error_to_dict(message), stream)
    return code


def main(argv=None, stdout=None) -> int:
    stdout = stdout or sys.stdout
    try:
        # Bilinmeyen ek seçenekler (ör. --tails, --ratio) yok sayılır; JSON'a girmez.
        args, _ignored = build_parser().parse_known_args(argv)
    except _ArgError as exc:
        return _error(str(exc), EXIT_INPUT_ERROR, stdout)
    except SystemExit as exc:          # --help
        return int(exc.code or 0)

    payload, code = run(args.mode, f=args.f, alpha=args.alpha, groups=args.groups,
                        power=args.power, n=args.n)
    _emit(payload, stdout)
    return code


def console_main() -> None:
    sys.exit(main())


if __name__ == "__main__":
    console_main()
