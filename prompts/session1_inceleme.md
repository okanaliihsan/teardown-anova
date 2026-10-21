# Oturum 1 — İnceleme (Kirli Oda) · İlk Prompt

> Bu dosya ödevin `prompts/` isterini karşılar. Aşağıdaki çizginin altındaki metin, inceleme oturumunun **ilk mesajı** olarak Claude Code'a (REA + Ghidra bağlı) aynen yapıştırılır.
> Oturum sonunda üretilecek dosyalar: `LEDGER.md` ve `SPEC.md`. Başka hiçbir şey repoya girmez.

---

Sen bir tersine mühendislik oturumundasın. Hedef: **G*Power 3.1.9.7 (Windows)**, dosya `C:\Users\90553\Desktop\re\gpower\GPower_3.1.9.7_143\GPowerNT.exe` (SHA-256: C63E6A13...EFC812, bkz. docs/BINARY.md). Bu bir eğitim çalışmasıdır (YZM301 Teardown Sprint); G*Power yazarları Faul, Erdfelder, Lang ve Buchner'e saygıyla, yalnızca algoritmayı ve davranışı anlamak için inceliyoruz.

## Kapsam

Yalnızca şu hesap: **F tests → ANOVA: Fixed effects, omnibus, one-way**, iki mod:
- **A priori:** girdi f (etki büyüklüğü), α, güç (1−β), grup sayısı k → çıktı λ, kritik F, pay df, payda df, toplam N, gerçek güç
- **Post hoc:** girdi f, α, toplam N, k → çıktı λ, kritik F, pay df, payda df, güç

Başka test ailelerine, lisans/kopya koruma koduna, ağ koduna veya arayüz çizimine girme.

## Araçlar

REA MCP araçlarını Ghidra sağlayıcısıyla kullan (`provider: ghidra`). Önce şunu doğrula ve bana söyle: "REA araçları ve Ghidra sağlayıcısı bu oturumda kullanılabilir mi?" Sonra binary'yi aç, genel bilgiyi çıkar (mimari, derleyici/dil izleri, 32/64-bit).

## Yöntem (sırayla)

1. **Dizeden giriş:** `search_strings` ile arayüz/protokol metinlerini bul: "Noncentrality parameter", "Critical F", "Numerator df", "Denominator df", "Total sample size", "Actual power", "Effect size f", "Number of groups", "ANOVA", hata/uyarı metinleri. Her dizenin adresini ve ona referans veren fonksiyonları (`xrefs`) kaydet.
2. **Hesap motoruna in:** Bu dizelerden çağrı grafiği boyunca (`procedure_callers`, `procedure_callees`, `get_call_graph`) ANOVA hesabını yapan fonksiyonları bul. Arayüz kodu ile hesap kodunu ayır.
3. **Şu soruların her biri için kanıt ara** (puanı bunlar getiriyor; kılavuzda YAZMAYAN davranışlar):
   - **λ formülü:** λ, f ve N'den nasıl hesaplanıyor?
   - **df:** pay df ve payda df nasıl hesaplanıyor?
   - **Kritik F:** Merkezi F dağılımının tersi hangi yöntemle bulunuyor (kök bulma, seri, hazır rutin)? Hassasiyet/tolerans sabiti var mı?
   - **Güç:** Noncentral F dağılımı nasıl hesaplanıyor (hangi algoritma, seri açılımı, kesme koşulu, iterasyon limiti)?
   - **N arama (a priori çözücü):** N hangi değerden başlıyor, nasıl artırılıyor (adım, ikiye bölme, doğrusal tarama)? **Durma koşulu** tam olarak ne (güç ≥ hedef mi, > mi)? Maksimum iterasyon / üst sınır var mı?
   - **Yuvarlama:** Toplam N tam sayıya nasıl yuvarlanıyor? **k'nın katına** yuvarlanıyor mu (eşit grup büyüklüğü)? Grup başına n'den mi toplam N'ye mi gidiyor?
   - **Post hoc'ta k'ya bölünmeyen N** (ör. N=100, k=3) nasıl işleniyor?
   - **Geçersiz girdi:** f ≤ 0, α ≤ 0 veya ≥ 1, güç ≤ α, güç ≥ 1, k < 2, N ≤ k gibi durumlarda ne oluyor? Hata metni var mı, sessizce mi kırpılıyor?
   - **Ekran biçimi:** Sonuçlar kaç ondalık basamakla yazdırılıyor (biçim dizeleri)?
4. **Her iddia için kendine sor:** "Bunun kanıtı hangi fonksiyonda / hangi adreste?" Gösteremiyorsan iddia `[AJAN]` etiketi alır ve "diferansiyel testle sınanacak" notu düşülür. Tahmini kanıt gibi yazma.

## Etiketler (zorunlu)

- `[REA]` Binary'den kanıtlandı → fonksiyon adresi ve/veya dize adresi + REA aracının adı yazılır
- `[DOK]` G*Power kılavuzunda veya Faul vd. (2007, 2009) makalesinde yazıyor
- `[AJAN]` Senin çıkarımın, kanıtı yok

## Çıktı 1 — `LEDGER.md` (kanıt defteri)

Tablo sütunları: `ID | Etiket | İddia | Kanıt (adres / dize / REA aracı) | Güven (Yüksek/Orta/Düşük) | Bilinmeyen / Nasıl sınanır`
- ID'ler `L01, L02, ...`
- "Kanıt" sütununda **en fazla 1–2 satırlık kısa alıntı** ve fonksiyon adresi olabilir. Decompile edilmiş fonksiyon gövdesi KOPYALANMAZ.
- Sonuna "Açık sorular" bölümü ekle.

## Çıktı 2 — `SPEC.md` (yazım oturumu yalnızca bunu görecek)

Kurallar:
- **Kod yok, sözde kod yok, adres yok, decompile alıntısı yok.** Yalnızca davranış ve algoritmanın fikri (soyutlama düzeyi). Matematiksel formül yazılabilir.
- Her kural `R01, R02, ...` diye numaralanır ve hangi LEDGER satırına dayandığını belirtir (ör. "Kaynak: L03, L07").
- Bölümler: Kapsam · Girdiler ve geçerli aralıkları · Çıktılar ve gösterim hassasiyeti · Hesap kuralları (λ, df, kritik F, güç) · A priori çözücü (başlangıç, adım, durma koşulu, yuvarlama) · Post hoc · Geçersiz girdi davranışı · Bilinmeyenler
- **Kabul kriterleri Gherkin formatında** (`Feature / Scenario / Given / When / Then`). En az şu senaryolar: kılavuzdaki örnek, k=2, k=3 tipik, çok küçük f, çok büyük f, güç ≤ α, geçersiz girdiler, post hoc'ta k'ya bölünmeyen N.
- SPEC'e beklenen sayısal değerleri **sen uydurma**; sayısal beklenen değerler G*Power arayüzünden toplanan `oracle/` vektörlerinden gelecek. Gherkin'de sayı gerekiyorsa "oracle vektörü V07'ye göre" diye referans ver.

## Süreç kaydı

Oturum sonunda şunu raporla (AGENT_COST.md için): kaç tur konuştuk, hangi REA araçlarını kaç kez çağırdın, takıldığın / yanlış yola girdiğin noktalar, emin olmadığın iddialar.

Hazırsan 1. adımla başla.
