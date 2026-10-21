# Kâhin Vektörlerini Toplama Rehberi (G*Power arayüzü)

Bu klasör ödevin **kâhin** isterini karşılar: "G*Power arayüzünden en az 30 vektör, her biri ekran görüntüsüyle". Listede **47 vektör** var (27 a priori, 8 geçersiz girdi, 12 post hoc). Hepsini toplamak puanı en çok getiren iş; yarısında kalırsan bile ilk 30'u mutlaka bitir.

Vektörler `gpower_vectors.csv` içinde; giriş sütunları dolu, çıkış sütunları boş.

## Neden bu vektörler?

Rastgele seçilmedi. Sommerville Bölüm 8.1.2'deki **bölüm (eşdeğerlik) testi** ve **sınır değer** mantığıyla seçildi:

| Grup | Ne arıyor? |
|---|---|
| A01–A12 (tipik) | Cohen eşikleri (f = 0,10 / 0,25 / 0,40), farklı α, güç, k. Kılavuz örneği A01. |
| A02, A03, A04, A08, A09, A01 | **Yuvarlama kuralı.** Bu girdilerde "en küçük tam sayı N" ile "k'nın katı olan en küçük N" farklı çıkıyor. G*Power'ın hangisini verdiği gizli bir davranış. |
| A13–A19 | Uç değerler: çok küçük / çok büyük f, çok yüksek güç. Çözücünün sınırları ve durma koşulu. |
| A21–A23 | Güç ≤ α (tutarsız giriş). Hata mı, anlamsız sonuç mu? |
| A24–A27 | Çok grup, çok küçük / büyük α. |
| X01–X08 | Geçersiz girdiler. G*Power ne mesaj veriyor? |
| P01–P12 | Post hoc. P01 ve P09 a priori sonuçlarıyla tutarlılık kontrolü. P02, P11: k'ya bölünmeyen N. |

## G*Power'da bir vektörü girme

1. G*Power'ı aç.
2. **Test family:** `F tests`
3. **Statistical test:** `ANOVA: Fixed effects, omnibus, one-way`
4. **Type of power analysis:**
   - `mode = a-priori` → `A priori: Compute required sample size – given α, power, and effect size`
   - `mode = post-hoc` → `Post hoc: Compute achieved power – given α, sample size, and effect size`
5. **Input parameters** alanlarına CSV'deki değerleri gir:
   - `Effect size f` ← `f`
   - `α err prob` ← `alpha`
   - `Power (1-β err prob)` ← `power_in` (a priori)
   - `Total sample size` ← `n_in` (post hoc)
   - `Number of groups` ← `k`
6. **Calculate**'e bas.
7. **Ekran görüntüsü al** (giriş ve çıkış alanları görünecek şekilde, tüm pencere). `screenshots/<ID>.png` olarak kaydet. Windows'ta `Win + Shift + S` → pencere seç.
8. Çıkışları CSV'ye **ekranda görünen tüm basamaklarla** yaz:
   - `Noncentrality parameter λ` → `lambda`
   - `Critical F` → `critical_F`
   - `Numerator df` → `df1`
   - `Denominator df` → `df2`
   - `Total sample size` → `n_total`
   - `Actual power` (a priori) veya `Power (1-β err prob)` (post hoc) → `actual_power`
9. Hata, uyarı, kırmızı alan, açılır pencere ya da hiç tepki vermeme gibi bir durum olursa **ekran görüntüsünü yine al**. Mesajı aynen `gpower_message` sütununa yaz. Hiçbir şey olmadıysa "tepki yok" yaz. **Geçersiz girdi davranışı puan getiren bir bulgu.**

## Daha az hata için: Protokol sekmesi

G*Power her hesabı **Protocol of power analyses** sekmesine metin olarak yazar. Tüm vektörleri bitirince bu sekmenin içeriğinin tamamını kopyalayıp `protocol_raw.txt` dosyasına yapıştır. Elle yazarken yaptığın yazım hatalarını bu metinden otomatik kontrol edeceğim. Bu yüzden CSV'ye yazmaya vaktin yoksa sadece ekran görüntüleri ve `protocol_raw.txt` de yeterli; ayrıştırmayı ben yaparım.

## Dikkat

- **Ondalık ayırıcı:** Windows'un bölge ayarı Türkçeyse G*Power virgül (`0,25`) isteyebilir. Hangisini kabul ettiğini not et (bu da bir bulgu). CSV'de her zaman **nokta** kullan.
- **Sıra önemli değil**, ama her hesaptan sonra ekran görüntüsünü almadan bir sonrakine geçme.
- Bir alanda G*Power değeri kendiliğinden değiştirirse (ör. kırpma, yuvarlama) bunu `gpower_message`'a yaz.
- Ekran görüntülerinde kişisel bilgi (masaüstü, sekmeler) görünmesin; yalnızca G*Power penceresi.
