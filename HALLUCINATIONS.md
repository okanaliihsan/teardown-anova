# HALLUCINATIONS.md — Ajanın yanlış çıkardığı şeyler

Ödev isteri: *"Ajanın yanlış çıkardığı en az 2 şey, nasıl fark edildiği, hangi testin yakaladığı."*

Aşağıdaki her madde için: ajan **ne iddia etti**, **gerçek ne çıktı**, **nasıl fark edildi**, **hangi test yakaladı**, **ne düzeltildi**. "Oturum 1" inceleme ajanı (Claude Code + REA + Ghidra), "Oturum 2" temiz odadaki yazım ajanıdır.

Özet:

| # | Kim | İddia | Gerçek | Yakalayan |
|---|---|---|---|---|
| H1 | Oturum 1 | Kesirli grup sayısı tam sayıya **çevrilir** (2.5 → 2) | **En yakına yuvarlanır**, .5 yukarı (2.5 → 3, 2.4 → 2) | Diferansiyel test: X07 ❌, sonra X09 |
| H2 | Oturum 1 | Kabul kriteri: k = 2.5 → "en az 2 grup" **hatası** | G*Power hata vermez, k = 3 ile hesaplar | Diferansiyel test: X07 ❌ |
| H3 | Oturum 1 | Sonuçlar `%g` ile **anlamlı basamak** olarak gösterilir | Arayüz **sabit 7 ondalık** gösterir (24.3750000) | Kâhin ekran görüntüleri + Oturum 2 testleri |
| H4 | Oturum 2 | H1/H2 çelişkisinde kesirli k'yı **reddetmek** doğru | Yanlış (H1) | Diferansiyel test: X07, X09, P13, P14 ❌ |
| H5 | Oturum 1 | f alt sınırı sabiti **1e-5** | **1e-06** | Ajanın kendi yeniden okuması; kâhin X01 metni doğruladı |
| H6 | Oturum 1 | `FUN_004bed00` tek yönlü ANOVA'dır | MANOVA'ya aitti | Ajanın kendi kontrolü (RTTI/vtable) |

---

## H1 — Kesirli grup sayısı "tam sayıya çevrilir" (yanlış)

- **İddia:** `LEDGER.md` L48 — *"k tam sayı olmayan veya k = 0 girildiğinde alan okuyucusu tam sayıya dönüştürür ve ardından L39 devreye girer."* Etiket **`[AJAN]`**, güven **Düşük**; dönüştürme kodu incelenmemiş. SPEC'e R32 olarak geçti.
- **Gerçek:** G*Power 2.5'i **3**'e, 2.4'ü **2**'ye yuvarlıyor (en yakın tam sayı, tam .5 yukarı). Aynı kural post hoc'taki toplam örneklem için de geçerli: 159.4 → 159, 159.6 → 160 (uyarı metninde "160" yazıyor).
- **Nasıl fark edildi:** X07 (k = 2.5) için G*Power hata yerine **sonuç** verdi ve sonuç A02 (k = 3) ile birebir aynıydı. Ardından yuvarlama yönünü ayırt etmek için **X09 (k = 2.4)** vektörü özel olarak eklendi: sonuç A11 (k = 2) ile aynı çıktı → "kesme" değil, "en yakına yuvarlama". Aynı mantıkla P13/P14 eklendi.
- **Yakalayan test:** `tests/differential.py` → `tests/UYUM_RAPORU.md`: X07 ❌ "G*Power sonuç verdi, yeniden yazım hata". Kanıt: `oracle/screenshots/X07.png`, `X09.png`, `P13.png`, `P14.png`.
- **Düzeltme:** `SPEC.md` §10 **R35** (R32'nin yerine geçer). Oturum 2 tur 3'te uygulandı; diferansiyel test 46/50 → **50/50**.
- **Ders:** `[AJAN]` etiketi tam olarak bu yüzden var. İddia binary'den kanıtlanmamıştı; diferansiyel testle sınanması gerekiyordu ve sınandığında yanlış çıktı.

## H2 — Kabul kriterinde yanlış beklenen davranış

- **İddia:** `SPEC.md` §9, *"Gecersiz grup sayilari reddedilir"* senaryosu: X07 (k = 2.5) için *"en az iki grup gerektigini bildiren bir hata verilir"*.
- **Gerçek:** Hata yok; G*Power k = 3 ile hesaplıyor (H1).
- **Not:** Bu iddia SPEC'in kendi R32 kuralıyla da çelişiyordu (R32'ye göre 2.5 → 2 geçerli olurdu). Ajan aynı belgede iki uyumsuz davranış yazmıştı; ikisi de yanlıştı.
- **Yakalayan:** Diferansiyel test X07 ❌. Oturum 2 bu çelişkiyi `ASSUMPTIONS.md`'de ilk turda işaretlemişti, ama doğru cevabı ancak kâhin verebildi.

## H3 — Gösterim biçimi "%g, anlamlı basamak" (yanlış)

- **İddia:** `LEDGER.md` L49 — *"Sayılar sabit ondalık basamakla değil, `%g` ile anlamlı basamak olarak yazdırılıyor."* `[REA]`, güven **Orta**. Binary'de `%.7g` ve `%.6g` dizeleri gerçekten var (kanıt doğru), ama **hangi alanın hangi biçimi kullandığı izlenmedi** (LEDGER açık soru 8). SPEC'e R12 olarak geçti.
- **Gerçek:** G*Power çıktı alanlarını **sabit 7 ondalıkla** gösteriyor: `24.3750000`, `1.0000000`, `9.6360000`. `%g` biçimi sondaki sıfırları atardı. Yalnızca birkaç uç durumda kısa gösterim var (λ = `0`, λ = `600`, kritik F = `199.5`).
- **Nasıl fark edildi:** İlk 26 a priori ekran görüntüsü okunurken. Oturum 2 de bağımsız olarak *"R12 oracle'la uyuşmuyor"* diye raporladı.
- **Yakalayan:** Kâhin (`oracle/gpower_vectors.csv`, `oracle/screenshots/A01.png`, `A17.png`, `P03.png`, `P07.png`); Oturum 2'nin `tests/test_spec.py` karşılaştırması basamak sayısını CSV'den aldığı için çelişki görünür oldu.
- **Düzeltme:** `SPEC.md` §10 **R37**. Motor tam duyarlıkla döndürür; JSON 7 ondalık yazar.
- **Ders:** Bir dizenin binary'de **var olması** (`[REA]` kanıtı) ile **o alanda kullanılması** aynı şey değil. Kanıt doğru, çıkarım yanlış.

## H4 — Yazım ajanının yanlış tarafı seçmesi

- **İddia:** Oturum 2, tur 1: R32 ile §9 çelişkisinde senaryoyu esas alıp kesirli k'yı **reddetti** (`SESSION2_LOG.md`, "Dürüst değerlendirme").
- **Gerçek:** H1.
- **Önemli:** Oturum 2'nin kendi testleri bu hatayı **yakalamadı**. Yeni CSV ile eski test paketi 50/50 yeşil kaldı, çünkü testler ajanın kendi varsayımını ("2.5 → hata") kodluyordu. Hatayı yalnızca **G*Power'a karşı diferansiyel test** gösterdi (X07, X09, P13, P14 ❌).
- **Ders:** *"Ajan 'çalışıyor' dedi → bu bir test değil, bir iddia."* (ders slaytı 13). Testin beklenen değerini ajan değil kara kutu belirlemeli.

## H5 — Sabitin yanlış okunması (1e-5 ↔ 1e-06)

- **İddia:** Oturum 1, a priori f alt sınırı sabiti `0x3eb0c6f7a0b5ed8d` önce **1e-5** olarak okundu.
- **Gerçek:** **1e-06** (LEDGER L43).
- **Nasıl fark edildi:** Ajan sabiti IEEE-754 olarak yeniden çözünce kendi hatasını düzeltti (`docs/session1_process_log.png`, madde 3).
- **Kâhin doğrulaması:** X01 ve X02 ekran görüntüleri: *"Effect size f is outside the admissible range (1e-06, 50)."*

## H6 — Yanlış fonksiyonu hedef sanmak (MANOVA)

- **İddia:** Oturum 1, `N % k` yardımcısını çağıran tek fonksiyon olduğu için `FUN_004bed00` tek yönlü ANOVA sanıldı.
- **Gerçek:** Fonksiyon MANOVA'ya aitti. "response variable" kontrolü görülünce ajan vtable/RTTI üzerinden doğru sınıfa (`PowerFAnovaGlobal`, `FUN_004ba6b0`) geçti (`docs/session1_process_log.png`, madde 4).
- **Yakalayan:** Ajanın kendi tutarlılık kontrolü. Doğru sınıf, LEDGER L03'te dize → xref → vtable → RTTI zinciriyle kanıtlandı.

---

## Ayrıca: "kâhin de yanılabilir"

Kütüphane kâhini (statsmodels 0.14.0, öğrencinin Anaconda ortamı) post hoc güçte 51/120 vektörde yeniden yazımdan sözleşme toleransını (1e-6) aşan, en fazla 1.2e-5 fark verdi. Bağımsız bir hakem (Poisson karışımı + düzenlenmiş tamamlayıcı beta, `tests/differential.py: poisson_series_power`) her durumda **yeniden yazımla** aynı çıktı; G*Power kâhini de yeniden yazımla 7 ondalık uyumlu. Bu bir ajan halüsinasyonu değil, ama aynı dersi veriyor: tek bir kaynağa körü körüne güvenme, uyuşmazlığı açıkla.
