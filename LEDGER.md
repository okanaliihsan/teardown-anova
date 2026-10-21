# LEDGER.md — Kanıt defteri

**Hedef:** G*Power 3.1.9.7 (Windows), `GPowerNT.exe`
**SHA-256:** `C63E6A133EB6372932F810C08CC33DC35A06D1DDB658F897BD6C34A754EFC812` (bkz. `docs/BINARY.md`)
**Kapsam:** yalnızca *F tests → ANOVA: Fixed effects, omnibus, one-way*, a priori ve post hoc modları.
**Araç:** REA 6.7.0 MCP, sağlayıcı **Ghidra 12.1.4** (`analyzer_preset: ghidra-default`, profil digest `3de5374f…bbc896`).
**Not:** Bu çalışma eğitim amaçlıdır (YZM301 Teardown Sprint); G*Power yazarları Faul, Erdfelder, Lang ve Buchner'e saygıyla, yalnızca algoritmayı ve davranışı anlamak için incelenmiştir.

Etiketler: `[REA]` binary'den kanıtlandı · `[DOK]` kılavuz/makalede yazıyor · `[AJAN]` ajan çıkarımı, kanıtı yok.
Adresler sanal adrestir (image base `0x400000`). Fonksiyon adları Ghidra'nın otomatik verdiği adlardır.

---

## 1. Kimlik, mimari, kütüphaneler

| ID | Etiket | İddia | Kanıt (adres / dize / REA aracı) | Güven | Bilinmeyen / Nasıl sınanır |
|---|---|---|---|---|---|
| L01 | [REA] | Hedef 32-bit PE32 (x86) MSVC C++ uygulaması; image base `0x400000`; 4 bölüm (`.text` `0x401000`, `.rdata` `0x5be000`, `.data` `0x608000`, `.rsrc` `0x68a000`); 9116 fonksiyon, 2570 dize | `open_binary` (provider ghidra) + `binary_overview` | Yüksek | — |
| L02 | [REA] | Sınıf hiyerarşisi MSVC RTTI'den kurtarıldı: `Distribution` → `FDistribution`; `PowerAnalysis` → `PowerF` → `PowerFAnovaGlobal`. Ayrıca `GPowerError` istisna sınıfı var | `search_strings` (regex), 346 tip tanımlayıcı; ör. `0x60c7a0` `.?AVFDistribution@@`, `0x60cb78` `.?AVPowerFAnovaGlobal@@`, `0x60b8c4` `.?AVGPowerError@@` | Yüksek | — |
| L03 | [REA] | Kapsamdaki test sınıfı **`PowerFAnovaGlobal`**; vtable tabanı `0x5c8538`. Zincir: dize `0x5c9ae4` "ANOVA: Fixed effects, omnibus, one-way" → `xrefs` → `0x4ba58a` (`FUN_004ba550`) → bu fonksiyon yalnızca vtable yuvası `0x5c85b0`'de geçiyor → vtable[-1] `0x5c8534` = `0x5eeeac` (RTTI locator) → tip tanımlayıcı `0x60cb70` → ad `0x60cb78` | `search_strings`, `xrefs`, `resolve_containing_procedure`, `read_bytes` | Yüksek | — |
| L04 | [REA] | Dağılım motoru **DCDFLIB**'dir. `FDistribution::cdf` = `FUN_00459e70`, `FDistribution::quantile` = `FUN_0045ac00`; ikisi de `FUN_0044e7a0`'yı DCDFLIB imzasıyla `(which, p, q, f, dfn, dfd, pnonc, status, bound)` çağırır | `procedure_pseudo_code`; DCDFLIB durum metinleri: "FDist-Cdf: answer below lower search bound", "… above upper search bound", "FDist-Cdf: p + q != 1.0", "FDist-Cdf: input parameter out of range" | Yüksek | `cumfnc` serisinin iç kesme sabitleri çözülmedi → Açık soru 1 |
| L05 | [REA] | **Cephes** kütüphanesi bağlı: `mtherr` hata tablosu ve kayıtlı fonksiyon adları | `search_strings`; `0x5e4b10` "domain", `0x5e4b18` "singularity", `0x5e4b24` "overflow", `0x5e4b3c` "total loss of precision", `0x5e4b78` "%s error"; adlar `0x5e49c4` "gamma", `0x5e49cc` "lgam", `0x5e4ae0` "hyperg", `0x5e4af0` "incbet" | Yüksek | Cephes'in ANOVA yolunda mı yoksa yalnızca formül ayrıştırıcısında mı kullanıldığı izlenmedi |
| L06 | [REA] | **GSL** yalnızca sayısal integrasyon (CQUAD) için derlenmiş | `0x5ec3b0` `G:\GPower\GPower30_3.1.7_22\Prog\gsl\integration\cquad.c`, `0x5ec6d7` "gsl: %s:%d: %s: %s" | Yüksek | — |
| L07 | [REA] | **CLAPACK/libf2c** bağlı (DGEEV, DGESDD, DLAMC2 …); çok değişkenli testler için | `0x5e4300`–`0x5e46c8` rutin adları; libf2c G/Ç hata dizeleri `0x5e46fc`+ | Orta | one-way ANOVA yolunda kullanılmadığı doğrudan izlenmedi |
| L08 | [REA] | Arayüz ve hesap katmanları kodlamayla ayrışıyor: hesap/protokol metinleri ASCII, GUI metinleri UTF-16LE | `search_strings`; ASCII etiket tablosu `0x5c54b0`–`0x5c57f4`; UTF-16 `0x5ce434` "Protocol of power analyses" | Orta | — |

## 2. Girdi alanları ve etiketler

| ID | Etiket | İddia | Kanıt | Güven | Bilinmeyen / Nasıl sınanır |
|---|---|---|---|---|---|
| L09 | [REA] | Çıktı etiketleri `.rdata`'da LaTeX işaretlemeli sabit tablo: `0x5c55fc` "Noncentrality parameter $\lambda$", `0x5c5640` "Critical F", `0x5c556c` "Numerator df", `0x5c557c` "Denominator df", `0x5c54e0` "Total sample size", `0x5c5658` "Actual power", `0x5c55dc` "Effect size f", `0x5c558c` "Number of groups" | `search_strings`; λ ve Critical F etiketleri `.data` içindeki etiket işaretçi tablosundan referanslanıyor (`xrefs` → `0x609414`, `0x609420`) | Yüksek | — |
| L10 | [REA] | Parametreler indeksli alan okuyucularıyla alınıyor: **k = alan `0xc`**, **f = alan `0x13`**, **N = alan `2`** | `procedure_pseudo_code` `FUN_004ba6b0`: `FUN_0048ab70(…,0xc)`, `FUN_0048aac0(…,0x13)`, `FUN_0048ab70(…,2)` | Yüksek | — |
| L11 | [DOK] | Cohen eşikleri f = .10 küçük / .25 orta / .40 büyük; binary'de de yazılı | Faul vd. (2007); `search_strings` `0x5c99b8` "f = .10 - small", `0x5c99c8` "f = .25 - medium", `0x5c99d9` "f = .40 - large" | Yüksek | — |

## 3. Hesap kuralları (λ, df, kritik F, güç)

| ID | Etiket | İddia | Kanıt | Güven | Bilinmeyen / Nasıl sınanır |
|---|---|---|---|---|---|
| L12 | [REA] | **df₁ = k − 1** ve **df₂ = N − k**. `FUN_004b9e40` (vtable+0x120) bunları hesaplayıp hem test nesnesine hem dağılım nesnesine yazıyor | `procedure_pseudo_code` `FUN_004b9e40`; nesne alanları `+0xf0`=k, `+0xe8`=N, `+0x88`=df₁, `+0x90`=df₂ | Yüksek | — |
| L13 | [REA] | **λ = f² · N**. `FUN_004ba340` (vtable+0x50) `FUN_00572840`'ı çağırıp sonucu N ile çarpıyor; `FUN_00572840(x)` tam olarak `x*x` | `procedure_pseudo_code` `FUN_004ba340`, `FUN_00572840` | Yüksek | — |
| L14 | [DOK] | λ = f²N, df₁ = k−1, df₂ = N−k kılavuzda ve Faul vd. (2007)'de yazılı | G*Power 3.1 kılavuzu, "F test: ANOVA: Fixed effects, omnibus, one-way" | Yüksek | L12/L13 ile binary'de de doğrulandı |
| L15 | [REA] | **Kritik F, merkezi F dağılımının tersidir.** `FUN_004b8d50` önce dağılımın noncentrality'sini **0**'a set eder, sonra `quantile(1 − α)` çağırır | `procedure_pseudo_code` `FUN_004b8d50`: `dist->(vtable+0x2c)(0)` ardından `dist->(vtable+0x8)(1.0 − α)` | Yüksek | — |
| L16 | [REA] | **Güç = 1 − noncentral F CDF(kritik F).** Aynı fonksiyon λ'yı set edip `1 − cdf(F_crit)` döndürür | `procedure_pseudo_code` `FUN_004b8d50` son satırları; λ `vtable+0x50` ile üretiliyor (L13) | Yüksek | — |
| L17 | [REA] | Ters fonksiyon DCDFLIB'de **`which = 2`** (p ve q'dan f), CDF **`which = 1`** ile çağrılıyor; terste `p = 1−α`, `q = α` | `procedure_pseudo_code` `FUN_0045ac00`, `FUN_00459e70` | Yüksek | — |
| L18 | [REA] | **Merkezi/noncentral dalı iki ayrı eşikle seçiliyor:** CDF'de `|λ| ≥ 1e-40`, ters fonksiyonda `|λ| ≥ 1e-100`. Eşik altında merkezi rutin (`FUN_0044bdd0`) çağrılıyor | `procedure_pseudo_code` `FUN_00459e70` (1e-40), `FUN_0045ac00` (1e-100) | Yüksek | İki eşiğin farkının gözlemlenebilir sonucu: P07 (post hoc, f=0) ile sınanır |
| L19 | [REA] | Dağılıma giren x bir ölçek katsayısıyla çarpılıyor, terste sonuç aynı katsayıya bölünüyor | `procedure_pseudo_code` `FUN_00459e70` / `FUN_0045ac00`; parametre yapısının 4. alanı | Orta | Katsayının one-way ANOVA'da 1.0 olduğu doğrulanmadı; A01 ile sınanır |
| L20 | [AJAN] | Bu zincir *Noncentrality parameter λ*, *Critical F*, *Numerator df*, *Denominator df* ve *Power* çıktılarının tamamını üretir | L12, L13, L15, L16 birleşimi; çıktı alanlarına yazma noktaları tek tek izlenmedi | Orta | Diferansiyel testle sınanacak: oracle A01 / P09 |

## 4. A priori çözücü (N arama, durma koşulu, yuvarlama)

| ID | Etiket | İddia | Kanıt | Güven | Bilinmeyen / Nasıl sınanır |
|---|---|---|---|---|---|
| L21 | [REA] | A priori hesabı jenerik taban sınıfta (`PowerAnalysis`) **`FUN_00496aa0`** (vtable+0x48); sıra: sınır kur → kök bul → yuvarla → alt sınıra kırp → **gerçek gücü yeniden hesapla** | `procedure_pseudo_code` `FUN_00496aa0`; `vtable+0x64` sınır, `vtable+0x74` yuvarlama, `vtable+0x30` güç | Yüksek | — |
| L22 | [REA] | **Hedef fonksiyon `g(N) = güç(f, α, N) − hedef_güç`.** `FUN_004968d0` (vtable+0x11c) gücü `vtable+0x30` ile hesaplayıp hedef güçten çıkarır; `FUN_00496830` mod bayrağına (`[0xab]`, a priori'de 0) göre bu hedefi seçer | `procedure_pseudo_code` `FUN_004968d0`, `FUN_00496830`, `FUN_00496aa0` | Yüksek | — |
| L23 | [REA] | **Kök bulucu Brent yöntemidir** (`FUN_004f9bb0`, 993 bayt, 29 blok): ters kuadratik interpolasyon + ikiye bölme geri dönüşü, yakınsama testi `|(c−b)/2| ≤ |b|·2⁻⁵³`. İşaret değişimi yoksa durum=1 ile 0 döner; iterasyon tükenirse durum=2 | `procedure_pseudo_code` `FUN_004f9bb0`; sabit `1.1102230246251565e-16` = 2⁻⁵³ | Yüksek | — |
| L24 | [REA] | **Maksimum iterasyon 300**, çağrıda sabit geçiliyor | `procedure_pseudo_code` `FUN_00496aa0`: `FUN_004f9bb0(…, 300)` | Yüksek | — |
| L25 | [REA] | Çağrıda **1e-10** toleransı geçiliyor ve çözücü nesnesine saklanıyor | `FUN_00496aa0` içindeki sabit `0x3ddb7cdfd9d7bdbb` = 1e-10 | Yüksek | — |
| L26 | [AJAN] | Saklanan 1e-10 toleransı `FUN_004f9bb0`'nun **görünür yakınsama testinde kullanılmıyor**; test yalnızca göreli makine-epsilon terimini içeriyor | `FUN_004f9bb0` gövdesinde saklama var, okuma yok | Orta | Dekompilasyon terimi düşürmüş olabilir; `procedure_assembly` ile sınanmalı |
| L27 | [REA] | **Başlangıç arama aralığı [k+1, k+100]** | `procedure_pseudo_code` `FUN_004bae20` (vtable+0x64): `FUN_004962d0(k + 1.0, k + 100.0)` | Yüksek | — |
| L28 | [REA] | Aralık `FUN_004962d0` ile ayarlanıyor: üst uçta kök yoksa **1.6 çarpanıyla geometrik genişletme** (işaret değişene kadar); kök aralıktaysa aşağı daraltma; son olarak alt sınır `k+1`'e kırpılıyor | `procedure_pseudo_code` `FUN_004962d0` | Yüksek | Genişletme döngüsünde görünür iterasyon tavanı yok → A13/A14 ile sınanacak |
| L29 | [REA] | **Yuvarlama kuralı: `N = ceil(N_sürekli / k) · k`.** Yani grup başına n yukarı yuvarlanıp k ile çarpılıyor; toplam N her zaman **k'nın katı** | `procedure_pseudo_code` `FUN_004badb0` (vtable+0x74) | Yüksek | — |
| L30 | [REA] | A priori çağrısında yuvarlama bayrağı **açık** geçiliyor | `procedure_pseudo_code` `FUN_004ba6b0` case 0: `vtable+0x48(…, 1)` | Yüksek | — |
| L31 | [REA] | Yuvarlanan N çözücünün alt sınırının altındaysa alt sınıra çekilip **yeniden yuvarlanıyor**; alt sınır `k+1` olduğunda sonuç `ceil((k+1)/k)·k = 2k` olur → **grup başına minimum n = 2** | `procedure_pseudo_code` `FUN_00496aa0` kırpma dalı + L27, L29 | Orta | Alt sınır her zaman `k+1` değil (genişletme dalında büyüyor); uçtan uca sonuç A16/A17 ile sınanacak |
| L32 | [REA] | **Gerçek güç, yuvarlanmış N ile post hoc güç fonksiyonu çağrılarak yeniden hesaplanıyor** ve ayrı alana yazılıyor | `procedure_pseudo_code` `FUN_00496aa0`: `vtable+0x30(f, α, N)` → alan `+0x108` | Yüksek | — |
| L33 | [AJAN] | Durma koşulu "güç ≥ hedef" biçiminde bir **tam sayı döngüsü değildir**. Sürekli kök `güç(N) = hedef` olarak bulunup yukarı yuvarlandığı ve güç N'de monoton arttığı için sonuç, **gücü hedefe ulaştıran en küçük k katıdır**; gerçek güç bu yüzden hedeften büyük (dejenere durumda eşit) çıkar | L22, L23, L29, L32 birleşimi; monotonluk varsayımı binary'den kanıtlanmadı | Orta | A02/A03/A04/A08/A09: "en küçük tam sayı N" ile "en küçük k katı N" ayrışıyor; ayrıca actual power > hedef mi bakılacak |
| L34 | [REA] | **A priori'de `N mod k` uyarısı hiç çalışmaz**: `FUN_004ba6b0` case 0 hesaptan sonra doğrudan `-1` döndürür, ortak kuyruğa düşmez | `procedure_pseudo_code` `FUN_004ba6b0` case 0 akışı | Yüksek | — |

## 5. Post hoc

| ID | Etiket | İddia | Kanıt | Güven | Bilinmeyen / Nasıl sınanır |
|---|---|---|---|---|---|
| L35 | [REA] | Post hoc hesabı `vtable+0x30` = **`FUN_004b8d50`** (`PowerF` katmanı); girdi (f, α, N), çıktı güç | `read_bytes` vtable `0x5c8538+0x30` = `0x4b8d50`; `procedure_pseudo_code` `FUN_004ba6b0` case 2 | Yüksek | — |
| L36 | [REA] | **N, k'ya bölünmüyorsa hesap yine yapılır ve sonuç üretilir; uyarı sonradan eklenir.** Güç `vtable+0x30` ile *önce* hesaplanıyor; `FUN_00488970(N, k)` kontrolü ortak kuyrukta *sonra* çalışıyor ve dönüş kodu `-1` yerine **`-2`** oluyor | `procedure_pseudo_code` `FUN_004ba6b0` case 2 + kuyruk; `FUN_00488970` gövdesi | Yüksek | `-2` kodunun arayüzde yalnızca uyarı mı olduğu izlenmedi → P02/P11 |
| L37 | [REA] | Uyarı metni parçalı: "The total sample size (" + ") is not a multiple of" + "the number of groups (" + "). The analysis was " + "based on the average group size." (`0x5c6448`, `0x5c6430`, `0x5c6418`, `0x5c6400`, `0x5c63dc`) | `search_strings` + `xrefs` `0x5c6448` → `0x4889ae` (`FUN_00488970`) | Yüksek | — |
| L38 | [REA] | `FUN_00488970` bölünebilirlik sağlandığında başarı bayrağıyla birlikte **`N / k`** (tam sayı bölme) değerini de döndürüyor | `procedure_pseudo_code` `FUN_00488970` | Yüksek | — |

## 6. Geçersiz girdi davranışı

| ID | Etiket | İddia | Kanıt | Güven | Bilinmeyen / Nasıl sınanır |
|---|---|---|---|---|---|
| L39 | [REA] | **k ≥ 2 zorunlu** (`k > 1` testi). Mesaj: "There must be at least 2 groups." | `procedure_pseudo_code` `FUN_00487cb0`; dize `0x5c6594`; `xrefs` → `0x487cc2` | Yüksek | — |
| L40 | [REA] | **α ∈ [1e-07, 0.9999999]**; dışındaysa "Alpha is outside the admissible range (" | `procedure_pseudo_code` `FUN_00487530` (sabitler 1e-07 ve 0.9999999); dize `0x5c6100` | Yüksek | — |
| L41 | [REA] | **Güç ∈ [1e-07, 0.9999999]**; dışındaysa "Power is outside the admissible range (" → güç = 1 reddedilir | `procedure_pseudo_code` `FUN_00488110`; dize `0x5c60d8` | Yüksek | — |
| L42 | [REA] | **α ≤ güç zorunlu, eşitlik kabul.** Test `α <= güç` biçiminde; mesaj "Power must be greater than or equal to alpha." | `procedure_pseudo_code` `FUN_004880e0`; dizeler `0x5c6220`, `0x5ca258` | Yüksek | Eşitlik durumunun (A21) gerçekten hesaplandığı oracle ile sınanacak |
| L43 | [REA] | **f aralığı moda göre değişiyor:** a priori'de `[1e-06, 50]`, post hoc / criterion / compromise'de `[0, 50]`. Genel kontrol `FUN_00487b70`; a priori'de alt sınır sabiti `0x3eb0c6f7a0b5ed8d` = 1e-06, diğerlerinde 0; üst sınır `0x4049000000000000` = 50.0 | `procedure_pseudo_code` `FUN_004ba6b0` case 0 vs case 2/3/4; `FUN_00487b70` gövdesi | Yüksek | — |
| L44 | [REA] | A priori'de f = 0 için ayrı metin var: "In a priori calculations the effect size must not be zero." | `search_strings` `0x5c67d0`; `xrefs` → `0x487d87` (`FUN_00487d20`) | Yüksek | Bu metnin one-way a priori yolunda mı yoksa etki büyüklüğü diyaloğunda mı kullanıldığı izlenmedi (X01) |
| L45 | [REA] | **Post hoc'ta N > k zorunlu** (yani df₂ ≥ 1). Mesaj: "Sample size must be greater than" + "the number of groups (" | `procedure_pseudo_code` `FUN_00488800` (`k < N` testi); dizeler `0x5c6280`, `0x5c62a1` | Yüksek | — |
| L46 | [REA] | ANOVA için ayrıca bir "hesaplanamıyor" istisnası var: "Cannot compute result! … leading to a violating of the relation: (groups + covariates) < sample size."; `GPowerError` olarak atılıyor | `search_strings` `0x5c99f0`; `xrefs` → `0x4b9829`; `resolve_containing_procedure` → `Catch_All@004b9821`; L02 | Orta | Hangi girdi bileşiminde bu yolun seçildiği izlenmedi (P04/P08) |
| L47 | [REA] | f negatif verildiğinde L43'teki aralık kontrolüne düşer (alt sınır ihlali); ayrı bir "negatif" mesajı yok | `FUN_00487b70` yalnızca `x < lo || hi < x` testi yapıyor | Orta | X02 ile sınanacak |
| L48 | [AJAN] | k tam sayı olmayan veya k = 0 girildiğinde alan okuyucusu tam sayıya dönüştürür ve ardından L39 devreye girer | L10, L39; dönüştürme kodu incelenmedi | Düşük | X07/X08 ile sınanacak |

## 7. Ekran biçimi

| ID | Etiket | İddia | Kanıt | Güven | Bilinmeyen / Nasıl sınanır |
|---|---|---|---|---|---|
| L49 | [REA] | Sayılar **sabit ondalık basamakla değil, `%g` ile anlamlı basamak** olarak yazdırılıyor. Arayüz katmanında `%.7g` (`0x5cee00`, ~50+ çağrı yeri) ve `%.6g` (`0x5cf138`, 8 çağrı yeri); protokol satırı " = %.6g" (`0x5ca290`) | `search_strings` + `xrefs` (`0x5cee00`, `0x5cf138`); çağrı yerleri `0x506xxx`–`0x52xxxx` GUI katmanı | Orta | Hangi çıktı alanının hangi biçimi kullandığı izlenmedi; oracle ekran görüntülerinden basamak sayılarak sınanacak |
| L50 | [REA] | Protokol metninde her alan "&lt;etiket&gt; = &lt;değer&gt;" kalıbıyla yazılıyor | `0x5ca290` " = %.6g"; L09 etiket tablosu | Orta | — |

---

## Açık sorular

1. **`cumfnc` serisinin kesme koşulu ve iterasyon limiti.** DCDFLIB kimliği kesin (L04) ama noncentral F CDF'inin iç seri açılımı, yakınsama toleransı ve terim üst sınırı çözülmedi: `FUN_0044e7a0` 10 892 bayt / 356 blok olduğu için tek dekompilasyonla okunamadı. Sınama: `procedure_assembly` ile sabit taraması veya P12 (N=30000) gibi uç vektörlerde hassasiyet kaybı aranması.
2. **Tolerans 1e-10'un rolü** (L25, L26): çözücüye geçiliyor ve saklanıyor ama yakınsama testinde görünmüyor. Assembly düzeyinde doğrulanmalı.
3. **Aralık genişletme döngüsünün üst sınırı yok** (L28). Çok küçük f'de (A13: f=0.02, A14: f=0.01) N binlere çıkar; 1.6 çarpanlı genişletme ile 300 iterasyon sınırının birlikte davranışı bilinmiyor — sonuç mu, hata mı, donma mı?
4. **Dağılım ölçek katsayısı** (L19) one-way ANOVA'da 1.0 mı? Değilse kritik F beklenenden farklı çıkar.
5. **Post hoc `-2` dönüş kodunun arayüzdeki etkisi** (L36): sonuç alanları yine doluyor mu, yalnızca uyarı mı gösteriliyor? P02/P11 ekran görüntüleri belirleyici.
6. **İki farklı noncentrality eşiği** (L18: CDF 1e-40, ters 1e-100) gözlemlenebilir fark yaratıyor mu? P07 kritik: güç tam α'ya eşit mi?
7. **k tam sayı değilse / k = 0** davranışı kanıtsız (L48), yalnızca çıkarım.
8. **Çıktı biçimi eşlemesi** (L49): λ, kritik F, df ve güç alanları `%.7g` mi `%.6g` mi kullanıyor?
9. **A priori'de N üst sınırı var mı?** `FUN_00496aa0`'da yalnızca alt kırpma görüldü, üst kırpma yok. A17 (f=10) ve A14 (f=0.01) uçları sınayacak.
10. **f = 0 mesajının (L44) one-way a priori yolunda tetiklendiği** doğrulanmadı; L43 aralık kontrolü de f=0'ı aynı anda reddeder, bu yüzden X01'de hangi metnin çıkacağı belirsiz.
11. **Sensitivity / criterion / compromise modları** kapsam dışı bırakıldı; `FUN_004ba6b0` case 1/3/4 olarak tespit edildi ama incelenmedi.
