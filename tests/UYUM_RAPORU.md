# Diferansiyel Test — Uyum Raporu

Aynı girdiler G*Power 3.1.9.7 arayüzüne (kâhin) ve yeniden yazımın CLI'sine verildi.
Bu dosya `python tests/differential.py` ile üretilir; elle düzenlenmez.

## Özet

| Ölçü | Değer |
|---|---|
| Kâhin vektörü (ölçülen) | 50 |
| Tam uyum (tüm alanlar / beklenen hata) | 46 / 50 (92.0%) |
| **N tam eşleşme** (sayısal vektörler) | **36 / 40 (90.0%)** |
| Henüz toplanmamış vektör | 0 |

Kütüphane kâhini (`oracle/library/statsmodels_vectors.csv`) henüz üretilmedi.

## Vektör bazında sonuç (G*Power kâhini)

| ID | Mod | f | α | güç / N | k | Sonuç | Ayrıntı |
|---|---|---|---|---|---|---|---|
| A01 | a-priori | 0.25 | 0.05 | 0.95 | 10 | ✅ UYUŞTU | tüm alanlar |
| A02 | a-priori | 0.25 | 0.05 | 0.8 | 3 | ✅ UYUŞTU | tüm alanlar |
| A03 | a-priori | 0.1 | 0.05 | 0.8 | 3 | ✅ UYUŞTU | tüm alanlar |
| A04 | a-priori | 0.4 | 0.05 | 0.8 | 3 | ✅ UYUŞTU | tüm alanlar |
| A05 | a-priori | 0.25 | 0.05 | 0.95 | 3 | ✅ UYUŞTU | tüm alanlar |
| A06 | a-priori | 0.25 | 0.01 | 0.8 | 3 | ✅ UYUŞTU | tüm alanlar |
| A07 | a-priori | 0.25 | 0.05 | 0.8 | 4 | ✅ UYUŞTU | tüm alanlar |
| A08 | a-priori | 0.25 | 0.05 | 0.8 | 5 | ✅ UYUŞTU | tüm alanlar |
| A09 | a-priori | 0.35 | 0.05 | 0.8 | 6 | ✅ UYUŞTU | tüm alanlar |
| A10 | a-priori | 0.2 | 0.05 | 0.9 | 4 | ✅ UYUŞTU | tüm alanlar |
| A11 | a-priori | 0.25 | 0.05 | 0.8 | 2 | ✅ UYUŞTU | tüm alanlar |
| A12 | a-priori | 0.5 | 0.05 | 0.9 | 3 | ✅ UYUŞTU | tüm alanlar |
| A13 | a-priori | 0.02 | 0.05 | 0.8 | 3 | ✅ UYUŞTU | tüm alanlar |
| A14 | a-priori | 0.01 | 0.05 | 0.8 | 3 | ✅ UYUŞTU | tüm alanlar |
| A15 | a-priori | 1.5 | 0.05 | 0.8 | 3 | ✅ UYUŞTU | tüm alanlar |
| A16 | a-priori | 3.0 | 0.05 | 0.8 | 3 | ✅ UYUŞTU | tüm alanlar |
| A17 | a-priori | 10.0 | 0.05 | 0.95 | 3 | ✅ UYUŞTU | tüm alanlar |
| A18 | a-priori | 0.25 | 0.05 | 0.99 | 3 | ✅ UYUŞTU | tüm alanlar |
| A19 | a-priori | 0.25 | 0.05 | 0.999 | 3 | ✅ UYUŞTU | tüm alanlar |
| A20 | a-priori | 0.25 | 0.1 | 0.8 | 3 | ✅ UYUŞTU | tüm alanlar |
| A21 | a-priori | 0.25 | 0.05 | 0.05 | 3 | ✅ UYUŞTU | tüm alanlar |
| A22 | a-priori | 0.25 | 0.05 | 0.04 | 3 | ✅ UYUŞTU | G*Power: Input error: Power must be greater than or equal to alpha. | yeniden yazım: --power: Power must be greater than or equal to alpha. |
| A23 | a-priori | 0.25 | 0.05 | 0.06 | 3 | ✅ UYUŞTU | tüm alanlar |
| A24 | a-priori | 0.25 | 0.05 | 0.8 | 20 | ✅ UYUŞTU | tüm alanlar |
| A25 | a-priori | 0.25 | 0.05 | 0.8 | 100 | ✅ UYUŞTU | tüm alanlar |
| A26 | a-priori | 0.3 | 0.001 | 0.95 | 4 | ✅ UYUŞTU | tüm alanlar |
| A27 | a-priori | 0.30 | 0.5 | 0.8 | 3 | ✅ UYUŞTU | tüm alanlar |
| X01 | a-priori | 0 | 0.05 | 0.8 | 3 | ✅ UYUŞTU | G*Power: Input error: Effect size f is outside the admissible range (1e-06, 50). | yeniden yazım: --f: Effect size f is out of the allowed range [1e-06, 50] (got 0.0). |
| X02 | a-priori | -0.25 | 0.05 | 0.8 | 3 | ✅ UYUŞTU | G*Power: Input error: Effect size f is outside the admissible range (1e-06, 50). | yeniden yazım: --f: Effect size f is out of the allowed range [1e-06, 50] (got -0.25). |
| X03 | a-priori | 0.25 | 0 | 0.8 | 3 | ✅ UYUŞTU | G*Power: Input error: Alpha is outside the admissible range (1e-07, 1). | yeniden yazım: --alpha: Alpha is out of the allowed range [1e-07, 0.9999999] (got 0.0). |
| X04 | a-priori | 0.25 | 1 | 0.8 | 3 | ✅ UYUŞTU | G*Power: Input error: Alpha is outside the admissible range (1e-07, 1). | yeniden yazım: --alpha: Alpha is out of the allowed range [1e-07, 0.9999999] (got 1.0). |
| X05 | a-priori | 0.25 | 0.05 | 1 | 3 | ✅ UYUŞTU | G*Power: Input error: Power is outside the admissible range (1e-07, 1). | yeniden yazım: --power: Power is out of the allowed range [1e-07, 0.9999999] (got 1.0). |
| X06 | a-priori | 0.25 | 0.05 | 0.8 | 1 | ✅ UYUŞTU | G*Power: Input error: There must be at least 2 groups. | yeniden yazım: --groups: Number of groups must be at least 2 (got 1). |
| X07 | a-priori | 0.25 | 0.05 | 0.8 | 2.5 | ❌ UYUŞMADI | G*Power sonuç verdi, yeniden yazım hata: {'error': '--groups: Number of groups (at least 2 groups required) must be an integer (got 2.5).'} |
| X08 | a-priori | 0.25 | 0.05 | 0.8 | 0 | ✅ UYUŞTU | G*Power: Input error: There must be at least 2 groups. | yeniden yazım: --groups: Number of groups must be at least 2 (got 0). |
| X09 | a-priori | 0.25 | 0.05 | 0.8 | 2.4 | ❌ UYUŞMADI | G*Power sonuç verdi, yeniden yazım hata: {'error': '--groups: Number of groups (at least 2 groups required) must be an integer (got 2.4).'} |
| P01 | post-hoc | 0.25 | 0.05 | 159 | 3 | ✅ UYUŞTU | tüm alanlar |
| P02 | post-hoc | 0.25 | 0.05 | 100 | 3 | ✅ UYUŞTU | tüm alanlar |
| P03 | post-hoc | 0.25 | 0.05 | 4 | 3 | ✅ UYUŞTU | tüm alanlar |
| P04 | post-hoc | 0.25 | 0.05 | 3 | 3 | ✅ UYUŞTU | G*Power: Input error: Sample size must be greater than the number of groups (3). | yeniden yazım: --n: Total sample size must be greater than the number of groups (N = 3, k = 3). |
| P05 | post-hoc | 0.1 | 0.05 | 1000 | 5 | ✅ UYUŞTU | tüm alanlar |
| P06 | post-hoc | 0.4 | 0.01 | 60 | 4 | ✅ UYUŞTU | tüm alanlar |
| P07 | post-hoc | 0 | 0.05 | 100 | 3 | ✅ UYUŞTU | tüm alanlar |
| P08 | post-hoc | 0.25 | 0.05 | 2 | 3 | ✅ UYUŞTU | G*Power: Input error: Sample size must be greater than the number of groups (3). | yeniden yazım: --n: Total sample size must be greater than the number of groups (N = 2, k = 3). |
| P09 | post-hoc | 0.25 | 0.05 | 390 | 10 | ✅ UYUŞTU | tüm alanlar |
| P10 | post-hoc | 1.0 | 0.05 | 6 | 3 | ✅ UYUŞTU | tüm alanlar |
| P11 | post-hoc | 0.25 | 0.05 | 101 | 2 | ✅ UYUŞTU | tüm alanlar |
| P12 | post-hoc | 0.05 | 0.05 | 30000 | 3 | ✅ UYUŞTU | tüm alanlar |
| P13 | post-hoc | 0.25 | 0.05 | 159.4 | 3 | ❌ UYUŞMADI | G*Power sonuç verdi, yeniden yazım hata: {'error': '--n: Total sample size must be an integer (got 159.4).'} |
| P14 | post-hoc | 0.25 | 0.05 | 159.6 | 3 | ❌ UYUŞMADI | G*Power sonuç verdi, yeniden yazım hata: {'error': '--n: Total sample size must be an integer (got 159.6).'} |
