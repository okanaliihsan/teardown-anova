"""Oracle CSV yükleyici ve karşılaştırma yardımcıları (yalnızca testler için)."""
from __future__ import annotations

import csv
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

CSV_PATH = os.path.join(ROOT, "oracle", "gpower_vectors.csv")

OUTPUT_COLUMNS = ("lambda", "critical_F", "df1", "df2", "n_total",
                  "actual_power", "gpower_message")
NUMERIC_OUTPUTS = ("lambda", "critical_F", "df1", "df2", "n_total", "actual_power")
EXACT_COLUMNS = ("df1", "df2", "n_total")


def load_vectors() -> dict[str, dict[str, str]]:
    with open(CSV_PATH, newline="", encoding="utf-8") as fh:
        return {row["id"]: row for row in csv.DictReader(fh)}


VECTORS = load_vectors()


def vector(vid: str) -> dict[str, str]:
    return VECTORS[vid]


def has_oracle_output(row: dict[str, str]) -> bool:
    """Çıkış sütunlarından en az biri doluysa oracle değeri toplanmıştır."""
    return any(row.get(c, "").strip() for c in OUTPUT_COLUMNS)


def decimals_of(text: str) -> int:
    text = text.strip()
    if "e" in text.lower():
        raise ValueError(f"bilimsel gösterim beklenmiyor: {text!r}")
    return len(text.split(".", 1)[1]) if "." in text else 0


def matches_display(actual: float, expected_text: str) -> bool:
    """Gerçek değeri CSV'deki ondalık hane sayısına yuvarlayıp karşılaştırır."""
    d = decimals_of(expected_text)
    return math.isclose(round(actual, d), float(expected_text),
                        rel_tol=0.0, abs_tol=10.0 ** (-d) * 1e-6)


def inputs(row: dict[str, str]) -> dict:
    """Satırdaki girdileri ham (ayrıştırılmış ama dönüştürülmemiş) olarak döndürür."""
    def num(s):
        s = s.strip()
        return float(s) if s else None
    return {
        "mode": row["mode"],
        "f": num(row["f"]),
        "alpha": num(row["alpha"]),
        "power": num(row["power_in"]),
        "n": num(row["n_in"]),
        "k": num(row["k"]),
    }
