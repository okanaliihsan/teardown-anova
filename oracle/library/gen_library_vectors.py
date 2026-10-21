"""Kütüphane kâhini: statsmodels ile 500+ referans vektörü üretir.

Ödev, "c) KÂHİN" maddesi: "Ölçek için R'daki pwr ya da Python'daki statsmodels ile 500'den fazla vektör".

Bu kâhin G*Power'dan BAĞIMSIZ ikinci bir kaynaktır:
  - G*Power kâhini (oracle/gpower_vectors.csv): az sayıda ama "doğru cevap"ın kendisi.
  - Kütüphane kâhini (bu dosya): çok sayıda, ama N'yi KESİRLİ verir.

Bilinen fark (bulgu): statsmodels toplam N'yi kesirli döndürür (ör. 157.19),
G*Power ise tam sayıya yuvarlar. Diferansiyel testte bu fark "açıklanmış uyuşmazlık"
olarak raporlanır, hata sayılmaz.

Çalıştırma:
    python oracle/library/gen_library_vectors.py
Çıktı:
    oracle/library/statsmodels_vectors.csv
"""

from __future__ import annotations

import csv
import itertools
import sys
from pathlib import Path

import statsmodels
from statsmodels.stats.power import FTestAnovaPower

OUT = Path(__file__).with_name("statsmodels_vectors.csv")

# A priori ızgarası: 10 x 3 x 3 x 5 = 450 vektör
F_GRID = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.00]
ALPHA_GRID = [0.01, 0.05, 0.10]
POWER_GRID = [0.80, 0.90, 0.95]
K_GRID = [2, 3, 4, 5, 6]

# Post hoc ızgarası: 5 x 6 x 4 = 120 vektör
PH_F_GRID = [0.10, 0.20, 0.25, 0.40, 0.60]
PH_N_GRID = [24, 36, 60, 120, 240, 600]
PH_K_GRID = [2, 3, 4, 6]
PH_ALPHA = 0.05

FIELDS = [
    "id", "mode", "f", "alpha", "power_in", "n_in", "k",
    "lib", "lib_version", "lib_n_fractional", "lib_power",
]


def main() -> int:
    solver = FTestAnovaPower()
    rows = []
    version = f"statsmodels {statsmodels.__version__}"

    for i, (f, a, p, k) in enumerate(
        itertools.product(F_GRID, ALPHA_GRID, POWER_GRID, K_GRID), start=1
    ):
        n_frac = solver.solve_power(
            effect_size=f, nobs=None, alpha=a, power=p, k_groups=k
        )
        rows.append({
            "id": f"LA{i:03d}", "mode": "a-priori", "f": f, "alpha": a,
            "power_in": p, "n_in": "", "k": k, "lib": "statsmodels.FTestAnovaPower",
            "lib_version": version, "lib_n_fractional": f"{float(n_frac):.6f}",
            "lib_power": "",
        })

    for j, (f, n, k) in enumerate(
        itertools.product(PH_F_GRID, PH_N_GRID, PH_K_GRID), start=1
    ):
        pw = solver.power(effect_size=f, nobs=n, alpha=PH_ALPHA, k_groups=k)
        rows.append({
            "id": f"LP{j:03d}", "mode": "post-hoc", "f": f, "alpha": PH_ALPHA,
            "power_in": "", "n_in": n, "k": k, "lib": "statsmodels.FTestAnovaPower",
            "lib_version": version, "lib_n_fractional": "",
            "lib_power": f"{float(pw):.10f}",
        })

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print(f"{len(rows)} vektör yazıldı → {OUT} ({version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
