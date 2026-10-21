# Diferansiyel Test — Uyum Raporu

Aynı girdiler G*Power 3.1.9.7 arayüzüne (kâhin) ve yeniden yazımın CLI'sine verildi.
Bu dosya `python tests/differential.py` ile üretilir; elle düzenlenmez.

## Özet

| Ölçü | Değer |
|---|---|
| Kâhin vektörü (ölçülen) | 27 |
| Tam uyum (tüm alanlar / beklenen hata) | 27 / 27 (100.0%) |
| **N tam eşleşme** (sayısal vektörler) | **26 / 26 (100.0%)** |
| Henüz toplanmamış vektör | 20 |

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
| X01 | | | | | | ⏳ toplanmadı | |
| X02 | | | | | | ⏳ toplanmadı | |
| X03 | | | | | | ⏳ toplanmadı | |
| X04 | | | | | | ⏳ toplanmadı | |
| X05 | | | | | | ⏳ toplanmadı | |
| X06 | | | | | | ⏳ toplanmadı | |
| X07 | | | | | | ⏳ toplanmadı | |
| X08 | | | | | | ⏳ toplanmadı | |
| P01 | | | | | | ⏳ toplanmadı | |
| P02 | | | | | | ⏳ toplanmadı | |
| P03 | | | | | | ⏳ toplanmadı | |
| P04 | | | | | | ⏳ toplanmadı | |
| P05 | | | | | | ⏳ toplanmadı | |
| P06 | | | | | | ⏳ toplanmadı | |
| P07 | | | | | | ⏳ toplanmadı | |
| P08 | | | | | | ⏳ toplanmadı | |
| P09 | | | | | | ⏳ toplanmadı | |
| P10 | | | | | | ⏳ toplanmadı | |
| P11 | | | | | | ⏳ toplanmadı | |
| P12 | | | | | | ⏳ toplanmadı | |
