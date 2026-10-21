# SPEC.md — Tek yönlü sabit etkili ANOVA omnibus güç analizi motoru

Bu belge bir davranış spesifikasyonudur. Kod, sözde kod, adres veya dekompilasyon alıntısı içermez; yalnızca gözlenen davranışı ve algoritmanın fikrini tanımlar. Her kural, dayandığı kanıt defteri satırlarına atıfla verilir.

Sayısal **beklenen değerler bu belgede yer almaz.** Kabul kriterlerinde geçen sayısal sonuçlar, G*Power arayüzünden toplanan `oracle/gpower_vectors.csv` vektörlerine kimlikle atıfla belirtilir.

---

## 1. Kapsam

**R01** Motor tek bir istatistiksel testi gerçekleştirir: tek yönlü, sabit etkili ANOVA omnibus F testi. (Kaynak: L03)

**R02** İki hesap modu desteklenir:
- **A priori:** girdi f, α, hedef güç, k → çıktı λ, kritik F, df₁, df₂, toplam N, gerçek güç
- **Post hoc:** girdi f, α, toplam N, k → çıktı λ, kritik F, df₁, df₂, güç
(Kaynak: L10, L21, L35)

**R03** Kapsam dışı: diğer test aileleri, duyarlılık (sensitivity), kriter (criterion) ve uzlaşma (compromise) modları, grafik çizimi, protokol yönetimi. (Kaynak: L11 açık soru)

---

## 2. Girdiler ve geçerli aralıkları

**R04** Grup sayısı **k** bir tam sayıdır ve **k ≥ 2** olmalıdır. Aksi halde geçersiz girdi hatası verilir. (Kaynak: L39)

**R05** Anlamlılık düzeyi **α**, kapalı aralık **[1e-07, 0.9999999]** içinde olmalıdır. Bu aralık α = 0 ve α = 1 değerlerini dışlar. (Kaynak: L40)

**R06** Hedef güç (a priori modunda) aynı kapalı aralık **[1e-07, 0.9999999]** içinde olmalıdır. Bu, güç = 1 değerini dışlar. (Kaynak: L41)

**R07** **α ≤ hedef güç** olmalıdır. Eşitlik **geçerlidir**: güç tam olarak α'ya eşit verildiğinde hesap yapılır, hata verilmez. (Kaynak: L42)

**R08** Etki büyüklüğü **f**'nin geçerli aralığı moda göre değişir:
- A priori modunda **f ∈ [1e-06, 50]** — yani f = 0 kabul edilmez.
- Post hoc modunda **f ∈ [0, 50]** — yani **f = 0 kabul edilir**.
(Kaynak: L43, L44)

**R09** Post hoc modunda toplam örneklem **N > k** olmalıdır. Bu koşul payda serbestlik derecesinin en az 1 olmasını güvence altına alır. (Kaynak: L45, R12)

**R10** Post hoc modunda N'in k'ya tam bölünmesi **gerekli değildir**. Bölünmeme bir hata değil, uyarı durumudur (bkz. R24). (Kaynak: L36, L37)

---

## 3. Çıktılar ve gösterim hassasiyeti

**R11** Motor her başarılı hesapta şu alanları üretir: noncentrality parametresi λ, kritik F, pay serbestlik derecesi df₁, payda serbestlik derecesi df₂, toplam örneklem N, ve güç (a priori modunda "gerçek güç" olarak adlandırılır). (Kaynak: L09, L20)

**R12** Sayısal çıktılar sabit ondalık basamak sayısıyla değil, **anlamlı basamak** esasına göre gösterilir; gözlenen hassasiyet 6–7 anlamlı basamaktır. Protokol metni 6 anlamlı basamak kullanır. Motorun kendisi tam duyarlıklı kayan nokta değer döndürmeli; basamak kısaltma yalnızca gösterim katmanının işidir. (Kaynak: L49, L50)

**R13** Protokol/özet metninde her alan "etiket = değer" kalıbıyla yazılır. (Kaynak: L50)

---

## 4. Hesap kuralları

**R14** Pay serbestlik derecesi: **df₁ = k − 1**. (Kaynak: L12, L14)

**R15** Payda serbestlik derecesi: **df₂ = N − k**. (Kaynak: L12, L14)

**R16** Noncentrality parametresi: **λ = f² · N**, burada N toplam örneklem büyüklüğüdür (grup başına örneklem değil). (Kaynak: L13, L14)

**R17** Kritik F, **merkezi** F dağılımının ters birikimli dağılım fonksiyonudur:
**F_krit = F⁻¹(1 − α; df₁, df₂)**, noncentrality sıfır alınarak.
Hesap, ters birikimli dağılım fonksiyonunu doğrudan veren hazır bir dağılım rutiniyle yapılır; motor kendi kök bulma döngüsünü kurmaz. (Kaynak: L15, L17, L18)

**R18** Güç, **merkezi olmayan** (noncentral) F dağılımının sağ kuyruğudur:
**güç = 1 − F_nc(F_krit; df₁, df₂, λ)**.
Aynı dağılım nesnesi kritik F için noncentrality sıfırla, güç için λ ile kullanılır. (Kaynak: L15, L16)

**R19** Dağılım motoru, noncentrality değeri ihmal edilebilir küçüklükte olduğunda merkezi dağılım rutinine geçer. Gözlenen eşikler birikimli dağılım için ve ters fonksiyon için farklıdır (sırasıyla çok küçük iki sabit). Pratik sonucu: **f = 0 verildiğinde λ = 0 olur ve güç α'ya eşit çıkar.** (Kaynak: L18; doğrulama: oracle P07)

---

## 5. A priori çözücü

**R20** A priori hesabı, aşağıdaki fikirle çalışır: güç fonksiyonu N'in sürekli bir fonksiyonu olarak ele alınır ve
**g(N) = güç(f, α, N) − hedef_güç**
denkleminin **kökü** bulunur. Hedef fonksiyon, post hoc güç hesabının ta kendisidir. (Kaynak: L21, L22)

**R21** Kök bulma, **parantezlemeli bir tek boyutlu kök bulucu** ile yapılır (gözlenen yöntem: ters kuadratik interpolasyon ile ikiye bölme geri dönüşünü birleştiren Brent yöntemi). Yakınsama ölçütü bağıl makine duyarlığı mertebesindedir; **maksimum iterasyon sayısı 300**'dür. Çözücü, verilen parantezin uçlarında işaret değişimi bulamazsa başarısız döner. (Kaynak: L23, L24, L25, L26)

**R22** Başlangıç arama parantezi **[k + 1, k + 100]**'dür. Üst uçta hâlâ hedef güce ulaşılamıyorsa parantez **1.6 çarpanıyla geometrik olarak genişletilir** ve işaret değişimi bulunana kadar bu sürdürülür. Kök parantezin içindeyse parantez aşağı doğru daraltılır. Parantezin alt ucu hiçbir zaman **k + 1**'in altına inmez. (Kaynak: L27, L28)

**R23** **Yuvarlama kuralı (zorunlu davranış):** sürekli kök bulunduktan sonra toplam N, **k'nın bir üst katına yukarı yuvarlanır**:
**n_grup = ⌈N_sürekli / k⌉**, **N = n_grup · k**.
Dolayısıyla bildirilen toplam N **her zaman k'nın tam katıdır**; motor grup başına n üzerinden yukarı yuvarlayıp toplam N'e geçer. Sonuç, en küçük tam sayı N değil, **gücü hedefe ulaştıran en küçük k katıdır**. (Kaynak: L29, L30, L33)

**R24** Yuvarlanmış N, çözücünün alt sınırının altına düşerse alt sınır değeri kullanılır ve yeniden yuvarlanır. Alt sınır k + 1 olduğunda bu, toplam N = 2k (grup başına n = 2) anlamına gelir; yani **grup başına en az 2 gözlem** bildirilir. (Kaynak: L31; doğrulama: oracle A16, A17)

**R25** **Gerçek güç, yuvarlanmış nihai N ile güç fonksiyonu yeniden çağrılarak hesaplanır.** Hedef güç doğrudan kopyalanmaz. Yuvarlama yukarı yönlü olduğu ve güç N'de artan olduğu için gerçek güç hedef güce eşit ya da ondan büyüktür; tipik olarak kesin olarak büyüktür. (Kaynak: L32, L33)

**R26** A priori modunda N'in k'ya bölünebilirliğiyle ilgili **hiçbir uyarı üretilmez**; R23 gereği N zaten k'nın katıdır. (Kaynak: L34)

**R27** A priori modunda N için bir üst sınır gözlenmemiştir; çok küçük f değerleri çok büyük N'lere yol açar. (Kaynak: L28, açık soru 3 ve 9)

---

## 6. Post hoc

**R28** Post hoc modunda N girdi olarak alınır; df₁, df₂ ve λ R14–R16 ile, kritik F R17 ile, güç R18 ile hesaplanır. Ek bir arama veya iterasyon yoktur. (Kaynak: L35)

**R29** **N, k'ya tam bölünmediğinde hesap durdurulmaz.** Güç, verilen N ile (dolayısıyla df₂ = N − k ile) normal biçimde hesaplanır ve sonuç üretilir; ardından bir **uyarı** eklenir. Uyarı, toplam örneklemin grup sayısının katı olmadığını ve çözümlemenin **ortalama grup büyüklüğü** temel alınarak yapıldığını bildirir. Çağrı, başarıdan ayırt edilebilen bir "uyarılı başarı" durumu döndürür. (Kaynak: L36, L37, L38; doğrulama: oracle P02, P11)

**R30** Motor, bölünebilirlik sağlandığında grup başına örneklem büyüklüğünü (N / k, tam sayı bölme) de türetir. (Kaynak: L38)

---

## 7. Geçersiz girdi davranışı

**R31** Geçersiz girdilerde hesap yapılmaz; açıklayıcı bir hata üretilir. Gözlenen hata sınıfları ve tetikleyicileri:

| Durum | Davranış | Kaynak |
|---|---|---|
| k < 2 (k = 0, 1 dahil) | Hata: en az 2 grup gerekir | L39 |
| α aralık dışı (α = 0, α = 1) | Hata: α izinli aralığın dışında | L40 |
| Hedef güç aralık dışı (güç = 1) | Hata: güç izinli aralığın dışında | L41 |
| Hedef güç < α | Hata: güç α'dan küçük olamaz | L42 |
| A priori'de f = 0 veya f < alt sınır | Hata: etki büyüklüğü izinli aralığın dışında / a priori'de sıfır olamaz | L43, L44 |
| f negatif | Hata: aralık alt sınırı ihlali (ayrı bir "negatif" mesajı yoktur) | L47 |
| f > 50 | Hata: aralık üst sınırı ihlali | L43 |
| Post hoc'ta N ≤ k | Hata: örneklem grup sayısından büyük olmalı | L45 |

**R32** Grup sayısı ve örneklem alanları tam sayıya dönüştürülerek okunur; tam sayı olmayan k değerleri dönüştürüldükten sonra R04'e tabi olur. (Kaynak: L48 — bu kural `[AJAN]` düzeyinde kanıta dayanır, oracle X07/X08 ile doğrulanmalıdır.)

**R33** Grup ve kovaryans sayısının örneklem büyüklüğüne göre fazla olduğu durumlar için ayrıca bir "sonuç hesaplanamıyor" istisnası vardır; bildirdiği bağıntı (grup sayısı + kovaryans sayısı) < örneklem büyüklüğü biçimindedir. Tek yönlü ANOVA'da kovaryans sayısı sıfır olduğundan bu, R09 ile aynı koşula indirgenir. (Kaynak: L46)

**R34** Hata durumları, hangi girdi alanının sorunlu olduğunu ayırt edebilecek biçimde bildirilmelidir. (Kaynak: L39–L45 mesaj metinlerinin alan adını içermesi)

---

## 8. Bilinmeyenler

Aşağıdaki noktalar binary'den kanıtlanamadı; uygulama bunları makul ve belgelenmiş bir varsayımla ele almalı, farklılık çıkarsa oracle vektörleri belirleyici kabul edilmelidir.

**U01** Noncentral F birikimli dağılım fonksiyonunun iç seri açılımı, kesme koşulu ve terim sayısı üst sınırı bilinmiyor. Hazır bir dağılım kütüphanesi kullanıldığı kesin, iç sabitleri çözülmedi. (LEDGER açık soru 1)

**U02** Kök bulucuya geçirilen mutlak tolerans sabitinin yakınsama ölçütündeki rolü belirsiz; görünür ölçüt yalnızca bağıl makine duyarlığı terimini içeriyor. (LEDGER açık soru 2)

**U03** Çok küçük f değerlerinde (çok büyük N) parantez genişletmesinin ve 300 iterasyon sınırının birlikte davranışı bilinmiyor: sonuç mu, hata mı üretilir? (LEDGER açık soru 3, 9)

**U04** Dağılım nesnesine uygulanan ölçek katsayısının tek yönlü ANOVA'da birim olduğu doğrulanmadı. (LEDGER açık soru 4)

**U05** Post hoc "uyarılı başarı" durumunun sunum katmanındaki etkisi (sonuç alanlarının yine doldurulup doldurulmadığı) izlenmedi. (LEDGER açık soru 5)

**U06** Her bir çıktı alanının tam gösterim hassasiyeti (6 mı 7 anlamlı basamak mı) alan bazında belirlenmedi. (LEDGER açık soru 8)

**U07** f = 0 ile a priori çağrıldığında iki ayrı hata yolundan hangisinin metninin gösterildiği belirsiz. (LEDGER açık soru 10)

---

## 9. Kabul kriterleri

Sayısal beklenen değerler `oracle/gpower_vectors.csv` dosyasındaki vektörlerden alınır. Aşağıda vektör kimliği verilir; testler beklenen değeri o satırdan okur.

```gherkin
Feature: Tek yönlü sabit etkili ANOVA omnibus güç analizi

  Background:
    Given tek yönlü sabit etkili ANOVA omnibus motoru

  # --- A priori: kılavuz örneği ---
  Scenario: Kilavuz ornegi a priori sonucu (R14-R18, R20-R25)
    Given a priori modu
    When oracle vektoru A01 girdileri verilir
    Then lambda, kritik F, df1, df2, toplam N ve gercek guc oracle vektoru A01 ile uyusur
    And toplam N grup sayisinin tam kati olur
    And gercek guc hedef gucten kucuk olmaz

  # --- A priori: k sinir ve tipik degerler ---
  Scenario: En kucuk gecerli grup sayisi k=2 (R04, R14, R15, R23)
    Given a priori modu
    When oracle vektoru A11 girdileri verilir
    Then sonuc oracle vektoru A11 ile uyusur
    And df1 bir olur
    And toplam N ikinin tam kati olur

  Scenario: Tipik uc grup durumu k=3 (R23)
    Given a priori modu
    When oracle vektoru A02 girdileri verilir
    Then sonuc oracle vektoru A02 ile uyusur
    And toplam N ucun tam kati olur

  # --- A priori: yuvarlama kuralinin ayirt edici vektorleri ---
  Scenario Outline: N, k'nin katina yukari yuvarlanir, en kucuk tam sayiya degil (R23)
    Given a priori modu
    When oracle vektoru <id> girdileri verilir
    Then toplam N oracle vektoru <id> ile uyusur
    And toplam N grup sayisinin tam kati olur
    And toplam N, surekli cozumun k'nin katina yukari yuvarlanmasiyla elde edilen deger olur

    Examples:
      | id  |
      | A02 |
      | A03 |
      | A04 |
      | A08 |
      | A09 |

  Scenario: Gercek guc yuvarlanmis N ile yeniden hesaplanir (R25)
    Given a priori modu
    When oracle vektoru A03 girdileri verilir
    Then gercek guc oracle vektoru A03 ile uyusur
    And gercek guc hedef guce esit ya da ondan buyuk olur

  # --- A priori: etki buyuklugu uclari ---
  Scenario: Cok kucuk etki buyuklugu buyuk orneklem uretir (R22, R27)
    Given a priori modu
    When oracle vektoru A13 girdileri verilir
    Then sonuc oracle vektoru A13 ile uyusur
    And hesap hata vermeden tamamlanir

  Scenario: Asiri kucuk etki buyuklugu cozucu sinirlarini yoklar (R22, R27, U03)
    Given a priori modu
    When oracle vektoru A14 girdileri verilir
    Then davranis oracle vektoru A14 ile uyusur

  Scenario: Cok buyuk etki buyuklugu grup basina alt sinira dayanir (R24)
    Given a priori modu
    When oracle vektoru A16 girdileri verilir
    Then sonuc oracle vektoru A16 ile uyusur
    And grup basina orneklem ikiden kucuk olmaz

  Scenario: Asiri buyuk etki buyuklugu (R08 ust sinir, R24)
    Given a priori modu
    When oracle vektoru A17 girdileri verilir
    Then davranis oracle vektoru A17 ile uyusur

  # --- A priori: guc ve alpha iliskisi ---
  Scenario: Guc alpha'ya tam esit oldugunda hesap yapilir (R07)
    Given a priori modu
    When oracle vektoru A21 girdileri verilir
    Then hesap gecersiz girdi hatasi vermez
    And sonuc oracle vektoru A21 ile uyusur

  Scenario: Guc alpha'dan kucuk oldugunda gecersiz girdi hatasi verilir (R07)
    Given a priori modu
    When oracle vektoru A22 girdileri verilir
    Then gucun alpha'dan kucuk olamayacagini bildiren bir hata verilir
    And hicbir sonuc alani uretilmez

  Scenario: Guc alpha'nin hemen ustunde kabul edilir (R07)
    Given a priori modu
    When oracle vektoru A23 girdileri verilir
    Then sonuc oracle vektoru A23 ile uyusur

  # --- Gecersiz girdiler ---
  Scenario: A priori'de sifir etki buyuklugu reddedilir (R08, R31, U07)
    Given a priori modu
    When oracle vektoru X01 girdileri verilir
    Then etki buyuklugunun gecersiz oldugunu bildiren bir hata verilir

  Scenario: Negatif etki buyuklugu reddedilir (R08, R31)
    Given a priori modu
    When oracle vektoru X02 girdileri verilir
    Then etki buyuklugunun izinli aralik disinda oldugunu bildiren bir hata verilir

  Scenario Outline: Alpha sinir disi degerleri reddedilir (R05, R31)
    Given a priori modu
    When oracle vektoru <id> girdileri verilir
    Then alpha'nin izinli aralik disinda oldugunu bildiren bir hata verilir

    Examples:
      | id  |
      | X03 |
      | X04 |

  Scenario: Guc birim degeri reddedilir (R06, R31)
    Given a priori modu
    When oracle vektoru X05 girdileri verilir
    Then gucun izinli aralik disinda oldugunu bildiren bir hata verilir

  Scenario Outline: Gecersiz grup sayilari reddedilir (R04, R31, R32)
    Given a priori modu
    When oracle vektoru <id> girdileri verilir
    Then en az iki grup gerektigini bildiren bir hata verilir

    Examples:
      | id  |
      | X06 |
      | X07 |
      | X08 |

  # --- Post hoc ---
  Scenario: Post hoc a priori sonucuyla tutarlidir (R28)
    Given post hoc modu
    When oracle vektoru P01 girdileri verilir
    Then sonuc oracle vektoru P01 ile uyusur
    And elde edilen guc, ayni girdilerle yapilan A02 a priori hesabinin gercek gucuyle tutarli olur

  Scenario: Kilavuz ornegiyle post hoc tutarliligi (R28)
    Given post hoc modu
    When oracle vektoru P09 girdileri verilir
    Then sonuc oracle vektoru P09 ile uyusur
    And elde edilen guc, A01 a priori hesabinin gercek gucuyle tutarli olur

  Scenario Outline: Post hoc'ta k'ya bolunmeyen toplam orneklem (R10, R29)
    Given post hoc modu
    When oracle vektoru <id> girdileri verilir
    Then hesap gecersiz girdi hatasi vermez
    And lambda, kritik F, df1, df2 ve guc oracle vektoru <id> ile uyusur
    And payda df, toplam orneklem ile grup sayisinin farki olur
    And toplam orneklemin grup sayisinin kati olmadigini ve cozumlemenin ortalama grup buyuklugu temel alinarak yapildigini bildiren bir uyari dondurulur
    And durum, uyarisiz basari durumundan ayirt edilebilir olur

    Examples:
      | id  |
      | P02 |
      | P11 |

  Scenario: Post hoc'ta sifir etki buyuklugu kabul edilir ve guc alpha'ya esit cikar (R08, R19)
    Given post hoc modu
    When oracle vektoru P07 girdileri verilir
    Then hesap gecersiz girdi hatasi vermez
    And guc oracle vektoru P07 ile uyusur
    And lambda sifir olur

  Scenario: Payda df birime indiginde hesap yapilir (R09)
    Given post hoc modu
    When oracle vektoru P03 girdileri verilir
    Then sonuc oracle vektoru P03 ile uyusur
    And payda df bir olur

  Scenario: Payda df sifira indiginde gecersiz girdi hatasi verilir (R09, R31)
    Given post hoc modu
    When oracle vektoru P04 girdileri verilir
    Then orneklemin grup sayisindan buyuk olmasi gerektigini bildiren bir hata verilir

  Scenario: Toplam orneklem grup sayisindan kucuk oldugunda hata verilir (R09, R31)
    Given post hoc modu
    When oracle vektoru P08 girdileri verilir
    Then orneklemin grup sayisindan buyuk olmasi gerektigini bildiren bir hata verilir

  Scenario: Cok buyuk toplam orneklemde hassasiyet korunur (R18, U01)
    Given post hoc modu
    When oracle vektoru P12 girdileri verilir
    Then sonuc oracle vektoru P12 ile uyusur

  # --- Cikti bicimi ---
  Scenario: Cikti alanlari tam duyarlikla uretilir, kisaltma sunum katmanindadir (R12)
    Given post hoc modu
    When oracle vektoru P01 girdileri verilir
    Then motor kayan nokta degerleri kisaltmadan dondurur
    And sunum katmani degerleri anlamli basamak esasina gore bicimlendirir
```
