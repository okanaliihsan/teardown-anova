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
"hesaplanamıyor"; Tur 5'ten beri CLI'de `NO_SOLUTION`, çıkış kodu 1). Pratikte izinli en küçük f = 1e-6 ile bile
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
`JSON_DECIMALS = 7` ondalığa yuvarlanıyordu (Tur 1–4). **Tur 5 (sözleşme):** yuvarlama
kaldırıldı; JSON tam double yazar (json'un varsayılan repr'i). Oracle testleri hâlâ CSV'deki
ondalık sayısına göre karşılaştırır.

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
- **CLI hata kodları.** Tur 5'ten beri sözleşmeye göre: geçersiz girdi 2, `NO_SOLUTION` 1.
  Hata JSON'u `{"error","code","field"}`; `field` sözleşme alan adıdır (motorun `k` alanı
  `groups` olur).
- **Hata metinleri (R36).** Motor G*Power metinlerini birebir üretir; oracle'daki
  "Input error: " öneki arayüze ait sayıldı ve eklenmedi. CLI bunun önüne alan
  öneki koyar (`--alpha: Alpha is outside ...`). Sayı olmayan/NaN/sonsuz girdi de
  ilgili alanın aralık metniyle reddedilir; G*Power'da gözlenmedi, bir varsayım.
- **R37 (gösterim).** Tur 5'te JSON yuvarlaması kaldırıldı (bkz. U06). G*Power'ın 7 ondalık
  gösterimi yalnızca testlerdeki karşılaştırma toleransını belirler.

## Sözleşme ↔ G*Power ayrılıkları (Tur 5, CONTRACT.md v1.0.0)

Motor (`engine.py`) G*Power'a sadık kalır. Sözleşmenin dış kabuğu (`cli.run`; CLI ve MCP
ortak yolu) bazı girdileri motordan önce reddeder. Bu ayrılıklar bilinçlidir:

| Durum | G*Power / motor | Sözleşme / CLI-MCP | Gerekçe |
|---|---|---|---|
| Kesirli k (X07 2.5, X09 2.4) | En yakın tam sayıya yuvarlar (R35) | `INVALID_VALUE` (field `groups`) | Sözleşme: "tam sayı gereken yerde ondalık → INVALID_VALUE" |
| Kesirli N (P13 159.4, P14 159.6) | En yakın tam sayıya yuvarlar (R35) | `INVALID_VALUE` (field `n_total`) | Aynı kural |
| Post hoc f = 0 (P07) | Kabul eder, güç = α (R19, R38) | `OUT_OF_RANGE` (field `f`), mesaj "Effect size f must be greater than 0." | Sözleşme §5: f > 0 |
| Güç = α (A21) | Kabul eder (R07) | Kabul edilir (sözleşme yalnızca güç < α'yı INCONSISTENT sayar) | G*Power davranışı korundu; sözleşme notundaki "büyük olmalı" ifadesi katı eşitsizlik gibi okunabilir, ama motor sonucu G*Power'a sadık |
| Tam sayı değerli ondalık ("3.0", "100.0") | — | Kabul edilir (= 3, 100) | **Varsayım:** değer tam sayıdır; "ondalık" sözleşmede kesirli değer anlamında okundu |
| Çözücü başarısızlığı (SolverError) | — | `NO_SOLUTION`, çıkış 1, field `null` | Sözleşme: 1 = iç hata / hesap başarısız |

Bu 5 vektörde (X07, X09, P13, P14, P07) G*Power davranışı motor düzeyinde
`tests/test_spec.py` ile doğrulanmaya devam ediyor. CLI düzeyinde ise sözleşme hatası
bekleniyor (`tests/test_cli.py`).

Diğer Tur 5 varsayımları:
- **Mesajlar.** Bir durumu hem G*Power hem sözleşme reddediyorsa G*Power metni kullanılır
  (alpha 0/1, power 1, groups 1, f < 0, a priori'de f = 0, n_total 1). n_total = 1 için
  G*Power metni "Sample size must be greater than the number of groups (k)." seçildi.
  Kod ise sözleşmeye göre `OUT_OF_RANGE`'dir (N < 2), `INCONSISTENT` değildir.
- **Sözleşme aralığında olup G*Power aralığı dışında kalan değerler** (ör. alpha = 1e-8,
  f = 60) motorda reddedilir ve `OUT_OF_RANGE` olur.
- **Sayı biçimi.** Yalnızca `[+-]rakamlar[.rakamlar][e±üs]` kabul edilir. "0,05",
  "1_000", "nan" ve "inf" → `INVALID_VALUE` (Python `float()`'unun gevşekliği
  kullanılmadı). MCP'de JSON number ya da aynı biçimde string kabul edilir; bool →
  `INVALID_VALUE`.
- **Argv ayrıştırma.** argparse kullanılmıyor, çünkü stdout'a kendi metnini yazabiliyor.
  `--ad değer` ve `--ad=değer` biçimleri destekleniyor; `--f -0.25` biçimindeki negatif
  sayı değer olarak alınıyor. Hatalı biçimler:
  - Konumsal argüman → `UNKNOWN_PARAM` (field `null`).
  - Değeri eksik seçenek → `INVALID_VALUE`.
  - Aynı alanın tekrarı → `INVALID_VALUE`.
  - `--help` tanınmayan bir alandır (değersiz olduğu için `INVALID_VALUE`).
  - `--version` diğer argümanlardan bağımsız olarak önceliklidir.
- **Harf duyarlılığı.** `test` ve `mode` kimlikleri birebir küçük harfle eşlenir
  (`ANOVA-ONEWAY` → `UNSUPPORTED`). Tur 2'deki takma adlar kaldırıldı.
- **Doğrulama sırası.** test → mode → bilinmeyen alan → eksik alan → değer tipi (sözleşme
  alan sırasıyla) → §5 aralığı → motor.
- **`--version` "name".** Takım adı olarak `teardown-anova` yazıldı (koordinatörün
  verdiği değer).
- **MCP uyarısı.** MCP'de uyarı yalnızca JSON'daki `warning` alanında yer alır; MCP
  sunucusu stderr'e yazmaz.
