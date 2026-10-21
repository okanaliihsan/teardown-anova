# ASSUMPTIONS.md

SPEC.md'de açık kalan noktalar ve uygulamada yapılan varsayımlar. Oracle vektörleri
(`oracle/gpower_vectors.csv`) belirleyici kabul edildi; aşağıdaki varsayımların
hiçbiri oracle sayılarına göre özel durum içermez.

## SPEC'in bilinmeyenleri (U01–U07)

**U01 — Noncentral F CDF iç serisi.** G*Power'ın iç sabitleri bilinmiyor; `scipy.stats.ncf.sf`
kullanıldı (Boost tabanlı). Oracle'daki 26 a priori vektörün tümünde (N = 96 351'e kadar)
λ, kritik F ve güç 7 ondalığa birebir tuttu; seri farkı gösterim düzeyinde gözlenmedi.
Tur 3'te P vektörleri de dolduruldu; P12 (N = 30 000) dahil 40 sayısal vektörün
tümü tutuyor.

**U01/R19 — Merkezi dağılıma geçiş eşiği.** Gerçek iki sabit bilinmiyor. Tek eşik
`NCP_CENTRAL_THRESHOLD = 1e-12` seçildi: λ < 1e-12 ise güç `stats.f.sf` ile hesaplanır.
Kritik F zaten her zaman merkezi F'den (`stats.f.isf`) alındığı için ters fonksiyon
eşiğine gerek kalmadı. **Not:** Bu ortamdaki scipy'de `ncf.sf(x, d1, d2, 0)` yanlış
(negatif) değer döndürüyor (ör. −0.9456); dolayısıyla bu geçiş yalnızca G*Power'ı
taklit etmek için değil, doğruluk için de zorunlu.

**U02 — Kök bulucu mutlak toleransı.** `brentq(xtol=1e-10, rtol=4·eps, maxiter=300)`.
N ölçeğinde 1e-10 mutlak tolerans, yuvarlamayı (⌈N/k⌉) hiçbir vektörde etkilemiyor;
sürekli kökler k katlarına en yakın 0.11 uzaklıkta (A17 hariç, o alt sınıra dayanıyor).

**U03 — Çok küçük f.** Parantez genişletmesine en fazla 200 adım (1.6^200 ≈ 1e40 kat)
izin verildi; aşılırsa veya üst uç sonsuza giderse `SolverError` (girdi hatası değil,
"hesaplanamıyor"; CLI çıkış kodu 3). Pratikte izinli en küçük f = 1e-6 ile bile
(N ≈ 9.6e12) sonuç üretiliyor ve hata çıkmıyor. Bu kadar büyük N'de değerlerin
G*Power ile aynı olacağı doğrulanmadı. 300 iterasyon sınırı yalnızca Brent
döngüsüne uygulanır, genişletme adımlarına değil.

**U04 — Ölçek katsayısı.** Tek yönlü ANOVA'da 1 kabul edildi (λ = f²·N, ek çarpan yok).
Tüm oracle λ değerleri bunu doğruluyor.

**U05 — Uyarılı başarının sunumu.** Post hoc'ta N, k'ya bölünmezse tüm sonuç alanları
yine doldurulur, `n_per_group = None`, `warning` alanı İngilizce bir metin içerir.
"Uyarılı başarı" ile "uyarısız başarı" `warning is None` ile ayırt edilir. CLI'da çıkış
kodu yine 0'dır ve JSON'a `warning` alanı eklenir. SPEC v1.1 R36'dan sonra uyarı
metni G*Power'ınkiyle birebir aynı ("The total sample size (<N>) is not a multiple of
the number of groups (<k>). The analysis was based on the average group size.").
Oracle'daki "Please note: " öneki G*Power arayüzünün bir parçası sayıldı ve motor
metnine eklenmedi. <N> yuvarlanmış değerdir (P14: 160).

**U06 — Gösterim hassasiyeti.** Motor tam duyarlıklı float döndürür. CLI JSON'da sayılar
`JSON_DECIMALS = 7` ondalığa yuvarlanır (PROMPT'un istediği sabit). Testlerde
karşılaştırma CSV'deki değerin ondalık hanesi kadardır (A17'de λ = "600" → 0 hane).

**U07 — A priori'de f = 0 (SPEC v1.1 R36 ile çözüldü).** Tek hata yolu var:
`EffectSizeRangeError(field="f")`, metin "Effect size f is outside the admissible range
(1e-06, 50)." (X01). f < 0 için de aynı metin çıkıyor (X02). Post hoc'ta alt sınır 0
olduğu için metin "(0, 50)" olarak biçimlenir. Bu G*Power'da gözlenmedi, bir varsayım.

## Diğer varsayımlar

- **R32 → R35 (SPEC v1.1).** Tur 1'de R32 ile X07 senaryosu çelişiyordu ve kesirli
  k reddediliyordu. Diferansiyel test bunun yanlış olduğunu gösterdi; R35 ile
  değiştirildi: k ve post hoc N, doğrulamadan **önce** en yakın tam sayıya yuvarlanır,
  tam .5 yukarı gider (`engine.round_half_up`). Python'un `round()` fonksiyonu
  kullanılmaz (bankacı yuvarlaması 2.5 → 2 yapar).
  - Uygulama `lo = floor(x); lo + 1 if x − lo ≥ 0.5 else lo` biçiminde. `floor(x + 0.5)`
    kullanılmadı, çünkü 0.49999999999999994 gibi değerlerde yanlış sonuç veriyor.
  - **Varsayım:** Negatif .5 değerlerde de "yukarı" (+∞ yönüne) gidilir; ör. −1.5 → −1.
    Bu durumda k < 2 olduğu için sonuç her durumda aynı hatadır.
  - **Varsayım:** Ondalık yazımın ikili gösterimi tam .5'in altına düşerse (ör.
    2.4999999999999999 ifadesi zaten 2.5 olarak ayrıştırılır) ayrıştırılmış float esas
    alınır.
  - Yuvarlanmış değer tüm kurallarda kullanılır: R04 (k = 1.4 → 1 hata, 1.5 → 2
    geçerli), R09 (N = 3.4, k = 3 → hata), R29 uyarısı, df, λ.
- **Doğrulama sırası.** A priori: k → α → güç → güç ≥ α → f. Post hoc: k → α → f → N.
  Birden fazla alan hatalıysa ilk ihlal bildirilir. G*Power'ın sırası bilinmiyor.
- **Kritik F.** `stats.f.isf(α)` kullanıldı (`ppf(1−α)` ile matematiksel olarak aynı,
  küçük α'da sayısal olarak daha doğru).
- **Parantez daraltma (R22).** "Kök parantezin içindeyse aşağı doğru daraltılır"
  şöyle yorumlandı: genişletme sırasında her adımda alt uç önceki üst uca kayar
  (lo ← hi, hi ← 1.6·hi), böylece Brent'e verilen aralık dar kalır. Başlangıçta
  g(k+1) ≥ 0 ise (hedef güç alt sınırda zaten sağlanıyor; ör. A21, A17) kök aranmaz,
  N_sürekli = k+1 alınır ve R24 gereği 2k'ya yuvarlanır.
- **Sürekli N'de df₂.** Çözücü sırasında df₂ = N − k sürekli (kesirli) değer olarak
  dağılım fonksiyonlarına verilir.
- **Güç = α (A21).** Hedef güç α'ya eşitken g(k+1) > 0 olduğundan sonuç alt sınırdan
  gelir; oracle ile uyumlu.
- **CLI hata kodları.** Girdi/argüman hatası 2, çözücü hatası 3. Hata JSON'u yalnızca
  `error` alanını içerir; mesaj sorunlu seçeneğin adıyla başlar (R34), ör. `--alpha: ...`.
- **Hata metinleri (R36).** Motor G*Power metinlerini birebir üretir; oracle'daki
  "Input error: " öneki arayüze ait sayıldı ve eklenmedi. CLI bunun önüne alan
  öneki koyar (`--alpha: Alpha is outside ...`). Sayı olmayan/NaN/sonsuz girdi de
  ilgili alanın aralık metniyle reddedilir; G*Power'da gözlenmedi, bir varsayım.
- **R37 (gösterim).** JSON hâlâ 7 ondalığa yuvarlar; `json` modülü sondaki sıfırları
  yazmadığı için 600.0 / 0.0 / 199.5 kısa görünür. Bu, G*Power'ın kısa gösterimiyle
  sayıca uyumludur ama biçim (ör. "24.375" ↔ "24.3750000") birebir değildir.
