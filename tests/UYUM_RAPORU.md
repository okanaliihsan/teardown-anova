# Diferansiyel Test — Uyum Raporu

Aynı girdiler G*Power 3.1.9.7 arayüzüne (kâhin) ve yeniden yazımın CLI'sine (hocanın sözleşmesi, CONTRACT.md v1.0.0) verildi.
Bu dosya `python tests/differential.py` ile üretilir; elle düzenlenmez. Tolerans: tam sayılar tam; ondalıklar mutlak/bağıl ≤ 1e-6 **ve** G*Power'ın gösterdiği basamağa kadar.

## Özet

| Ölçü | Değer |
|---|---|
| Kâhin vektörü (ölçülen) | 50 |
| Tam uyum (tüm alanlar / beklenen hata) | 45 / 50 |
| Sözleşme gereği bilinçli fark (CLI sözleşme hata kodu verir, **motor G*Power ile aynı**) | 5 |
| Uyuşmayan | **0** |
| **N tam eşleşme** (a priori sayısal vektörler — kapı ölçütü) | **26 / 26 (100.0%)** |
| Hata vektörlerinde sözleşme kodu (`code`) eşleşmesi | 10 / 10 |
| Sözleşme referans vektörleri (anova a-priori + post-hoc) | 2 / 2 (en büyük mutlak fark 2.7e-08) |
| Kütüphane a priori (statsmodels, kural: ceil(N/k)·k) | 450 / 450 (100.0%) |
| Kütüphane post hoc (güç, sözleşme toleransı 1e-6) | 69 / 120 (57.5%) |
| ↳ farklı çıkan ama bağımsız Poisson serisi hakemi yeniden yazımı doğrulayan | 51 (en büyük fark 1.15e-05) |
| ↳ açıklanamayan | 0 |
| Kütüphanenin naif `ceil(N)` değerinden farklı çıkan N | 328 / 450 |

Not: kütüphane satırları ayrıca `tests/library_results.csv` dosyasında.

### Kütüphane kâhini hakkında (açıklanmış uyuşmazlıklar)

1. **Kesirli N (a priori).** statsmodels toplam N'yi kesirli döndürür; G*Power (ve yeniden yazım) grup başına n'yi yukarı yuvarlayıp k ile çarpar (SPEC R23, LEDGER L29). Beklenen: N_yeniden_yazım = ceil(N_kütüphane / k) · k

2. **Post hoc güçte ~1e-6 mertebesinde farklar.** Kütüphane vektörleri öğrencinin Windows/Anaconda ortamında (statsmodels 0.14.0 ve onunla gelen scipy) üretildi; yeniden yazım daha yeni bir scipy ile çalışıyor. Farklı çıkan her vektör, `scipy.stats.ncf`'den bağımsız bir yolla (Poisson karışımı + düzenlenmiş tamamlayıcı beta) hakemlendi: hakem yeniden yazımla 1e-9 içinde aynı, kütüphane değeri ise farklı. Yani fark kütüphane kâhininin kendi sayısal hassasiyetinden geliyor. Yeniden yazım G*Power kâhininde de tutuyor (ör. P05: f=0.10, N=1000, k=5 → 0.7136330). Bu, "kâhin de yanılabilir" bulgusudur: iki katmanlı kâhinde ana kâhin G*Power'dır, kütüphane yalnızca ölçek içindir.

### Sözleşme ↔ G*Power ayrılıkları

Hocanın sözleşmesi (§2.4, §5) kesirli tam sayı alanlarını `INVALID_VALUE`, f ≤ 0'ı `OUT_OF_RANGE` sayar. G*Power ise kesirli k ve N'yi en yakın tam sayıya yuvarlar (SPEC R35; X07, X09, P13, P14) ve post hoc'ta f = 0'ı kabul eder (P07). Puanlama sözleşmeye göre yapıldığı için CLI/MCP sözleşmeye uyar; motor (`engine.py`) G*Power davranışını korur ve bu vektörlerde motorun G*Power ile birebir aynı sonucu verdiği ayrıca doğrulanır (aşağıda "SÖZLEŞME" satırları).

## Sözleşme referans vektörleri (CONTRACT.md §9, anova-oneway)

| ID | Mod | Sonuç | Ayrıntı |
|---|---|---|---|
| C-apriori | a-priori | ✅ UYUŞTU | tüm alanlar |
| C-posthoc | post-hoc | ✅ UYUŞTU | tüm alanlar |
| C-compromise | compromise | ➖ DESTEKLENMİYOR | bonus mod; CLI `UNSUPPORTED` |
| C-criterion | criterion | ➖ DESTEKLENMİYOR | bonus mod; CLI `UNSUPPORTED` |
| C-sensitivity | sensitivity | ➖ DESTEKLENMİYOR | bonus mod; CLI `UNSUPPORTED` |

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
| A22 | a-priori | 0.25 | 0.05 | 0.04 | 3 | ✅ UYUŞTU | G*Power: Input error: Power must be greater than or equal to alpha. | yeniden yazım: INCONSISTENT — Power must be greater than or equal to alpha. |
| A23 | a-priori | 0.25 | 0.05 | 0.06 | 3 | ✅ UYUŞTU | tüm alanlar |
| A24 | a-priori | 0.25 | 0.05 | 0.8 | 20 | ✅ UYUŞTU | tüm alanlar |
| A25 | a-priori | 0.25 | 0.05 | 0.8 | 100 | ✅ UYUŞTU | tüm alanlar |
| A26 | a-priori | 0.3 | 0.001 | 0.95 | 4 | ✅ UYUŞTU | tüm alanlar |
| A27 | a-priori | 0.30 | 0.5 | 0.8 | 3 | ✅ UYUŞTU | tüm alanlar |
| X01 | a-priori | 0 | 0.05 | 0.8 | 3 | ✅ UYUŞTU | G*Power: Input error: Effect size f is outside the admissible range (1e-06, 50). | yeniden yazım: OUT_OF_RANGE — Effect size f is outside the admissible range (1e-06, 50). |
| X02 | a-priori | -0.25 | 0.05 | 0.8 | 3 | ✅ UYUŞTU | G*Power: Input error: Effect size f is outside the admissible range (1e-06, 50). | yeniden yazım: OUT_OF_RANGE — Effect size f is outside the admissible range (1e-06, 50). |
| X03 | a-priori | 0.25 | 0 | 0.8 | 3 | ✅ UYUŞTU | G*Power: Input error: Alpha is outside the admissible range (1e-07, 1). | yeniden yazım: OUT_OF_RANGE — Alpha is outside the admissible range (1e-07, 1). |
| X04 | a-priori | 0.25 | 1 | 0.8 | 3 | ✅ UYUŞTU | G*Power: Input error: Alpha is outside the admissible range (1e-07, 1). | yeniden yazım: OUT_OF_RANGE — Alpha is outside the admissible range (1e-07, 1). |
| X05 | a-priori | 0.25 | 0.05 | 1 | 3 | ✅ UYUŞTU | G*Power: Input error: Power is outside the admissible range (1e-07, 1). | yeniden yazım: OUT_OF_RANGE — Power is outside the admissible range (1e-07, 1). |
| X06 | a-priori | 0.25 | 0.05 | 0.8 | 1 | ✅ UYUŞTU | G*Power: Input error: There must be at least 2 groups. | yeniden yazım: OUT_OF_RANGE — There must be at least 2 groups. |
| X07 | a-priori | 0.25 | 0.05 | 0.8 | 2.5 | 🔀 SÖZLEŞME | G*Power sonuç veriyor; sözleşme gereği CLI `INVALID_VALUE` döndü (beklenen INVALID_VALUE). motor: N=159, df=(2,156), λ=9.9375000, F=3.0540042, güç=0.8048873 → G*Power ile aynı |
| X08 | a-priori | 0.25 | 0.05 | 0.8 | 0 | ✅ UYUŞTU | G*Power: Input error: There must be at least 2 groups. | yeniden yazım: OUT_OF_RANGE — There must be at least 2 groups. |
| X09 | a-priori | 0.25 | 0.05 | 0.8 | 2.4 | 🔀 SÖZLEŞME | G*Power sonuç veriyor; sözleşme gereği CLI `INVALID_VALUE` döndü (beklenen INVALID_VALUE). motor: N=128, df=(1,126), λ=8.0000000, F=3.9163246, güç=0.8014596 → G*Power ile aynı |
| P01 | post-hoc | 0.25 | 0.05 | 159 | 3 | ✅ UYUŞTU | tüm alanlar |
| P02 | post-hoc | 0.25 | 0.05 | 100 | 3 | ✅ UYUŞTU | tüm alanlar + uyarı |
| P03 | post-hoc | 0.25 | 0.05 | 4 | 3 | ✅ UYUŞTU | tüm alanlar + uyarı |
| P04 | post-hoc | 0.25 | 0.05 | 3 | 3 | ✅ UYUŞTU | G*Power: Input error: Sample size must be greater than the number of groups (3). | yeniden yazım: INCONSISTENT — Sample size must be greater than the number of groups (3). |
| P05 | post-hoc | 0.1 | 0.05 | 1000 | 5 | ✅ UYUŞTU | tüm alanlar |
| P06 | post-hoc | 0.4 | 0.01 | 60 | 4 | ✅ UYUŞTU | tüm alanlar |
| P07 | post-hoc | 0 | 0.05 | 100 | 3 | 🔀 SÖZLEŞME | G*Power sonuç veriyor; sözleşme gereği CLI `OUT_OF_RANGE` döndü (beklenen OUT_OF_RANGE). motor: N=100, df=(2,97), λ=0.0000000, F=3.0901867, güç=0.0500000 → G*Power ile aynı |
| P08 | post-hoc | 0.25 | 0.05 | 2 | 3 | ✅ UYUŞTU | G*Power: Input error: Sample size must be greater than the number of groups (3). | yeniden yazım: INCONSISTENT — Sample size must be greater than the number of groups (3). |
| P09 | post-hoc | 0.25 | 0.05 | 390 | 10 | ✅ UYUŞTU | tüm alanlar |
| P10 | post-hoc | 1.0 | 0.05 | 6 | 3 | ✅ UYUŞTU | tüm alanlar |
| P11 | post-hoc | 0.25 | 0.05 | 101 | 2 | ✅ UYUŞTU | tüm alanlar + uyarı |
| P12 | post-hoc | 0.05 | 0.05 | 30000 | 3 | ✅ UYUŞTU | tüm alanlar |
| P13 | post-hoc | 0.25 | 0.05 | 159.4 | 3 | 🔀 SÖZLEŞME | G*Power sonuç veriyor; sözleşme gereği CLI `INVALID_VALUE` döndü (beklenen INVALID_VALUE). motor: N=159, df=(2,156), λ=9.9375000, F=3.0540042, güç=0.8048873 → G*Power ile aynı |
| P14 | post-hoc | 0.25 | 0.05 | 159.6 | 3 | 🔀 SÖZLEŞME | G*Power sonuç veriyor; sözleşme gereği CLI `INVALID_VALUE` döndü (beklenen INVALID_VALUE). motor: N=160, df=(2,157), λ=10.0000000, F=3.0536283, güç=0.8075443 → G*Power ile aynı |
