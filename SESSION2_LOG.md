# SESSION2_LOG.md

## Süreç

1. **Okuma:** PROMPT.md, SPEC.md, oracle/gpower_vectors.csv. Klasörde başka dosya
   yoktu (yalnızca `find` ile klasör içi listelendi; klasör dışına bakılmadı).
2. **Tur 1 — testler (kırmızı):** `tests/oracle.py` (CSV yükleyici, ondalık haneye
   göre karşılaştırma) ve `tests/test_spec.py` yazıldı. Motor yokken çalıştırıldı:
   tüm modül `ImportError: cannot import name 'engine'` ile kırmızıydı (1 hata).
   Bu, "kırmızı" aşamasının yalnızca içe aktarma düzeyinde olduğu anlamına gelir;
   testlerin tek tek bir sayısal uyuşmazlık nedeniyle kırmızı olduğu görülmedi.
3. **Tur 2 — motor:** `errors.py`, `engine.py`, `cli.py`, `__init__.py` tek seferde
   yazıldı. İlk çalıştırmada 32 test: 25 geçti, 7 atlandı, 0 başarısız.
4. **Doğrulama:** Testlerin gerçekten karşılaştırdığından emin olmak için 26 a priori
   vektörün motor çıktısı ile oracle değeri yan yana basıldı; λ, kritik F, df₁, df₂,
   N ve gerçek güç 7 ondalığa birebir aynı. Sürekli kökler de basıldı (ör. A02:
   157.19 → 159; A09: 110.38 → 114); yuvarlama ayırt edici vektörlerde doğru.
5. **Tur 3 — CLI:** `tests/test_cli.py`, `gpower-clone`, `gpower-clone.cmd`,
   `pyproject.toml`. İlk çalıştırmada 39 test: 32 geçti, 7 atlandı, 0 başarısız.
6. **Yoklama (U03):** f = 1e-3, 1e-4, 1e-6 ile a priori çalıştırıldı; hepsi hatasız
   sonuç verdi (N ≈ 9.6e6, 9.6e8, 9.6e12).

Toplam: 3 kod turu, oracle'a uydurma amaçlı düzeltme gerekmedi.

## İlk denemede kırmızı olan testler

- Motor yazılmadan önce: tümü (içe aktarma hatası) — beklenen TDD kırmızısı.
- Motor yazıldıktan sonra: hiçbiri. Dürüstçe not: bu nedenle "sayısal hatayı SPEC
  kurallarıyla araştırma" döngüsü hiç çalışmadı.

## Takıldığım / dikkat çeken yerler

- **scipy `ncf.sf` ncp = 0'da yanlış:** `stats.ncf.sf(3.0, 2, 97, 0.0)` = −0.9456
  (doğrusu 0.0544). R19'daki merkezi dağılıma geçiş olmasaydı P07 (f = 0) ve ayrıca
  çok küçük λ'lar yanlış güç verirdi. Eşik 1e-12 seçildi (gerçek G*Power sabiti
  bilinmiyor).
- **X07 (k = 2.5) ile R32 çelişkisi:** bkz. aşağıda.
- **Atlanan testler:** Tüm P vektörlerinin çıkış sütunları boş; bu yüzden post hoc
  sayısal karşılaştırmaları atlanıyor (7 test/alt test). Bunların yerine oracle
  gerektirmeyen SPEC iddiaları ayrı testlerde koşturuluyor (df₂ = N − k, uyarı,
  güç = α, P01/P09'un A02/A01 gerçek gücüyle tutarlılığı).

## SPEC'te eksik / yanlış olduğunu düşündüğüm yerler

1. **R32 ↔ X07 çelişkisi.** R32 "tam sayı olmayan k dönüştürüldükten sonra R04'e
   tabi olur" diyor; kesme ile 2.5 → 2 geçerli olur. §9 ise X07 için "en az iki grup"
   hatası bekliyor. Ya dönüştürme kesme değil (ör. reddetme), ya da senaryo yanlış.
   R32 zaten `[AJAN]` düzeyinde işaretli; X07'nin oracle çıktısı (mesaj) boş.
2. **R12 ↔ oracle gösterimi.** R12 "sabit ondalık değil, anlamlı basamak" diyor; oracle
   değerleri ise sabit 7 ondalıkla kaydedilmiş (24.3750000, 9.6360000, 1.0000000;
   ör. 24087 df'li vektörde de 7 ondalık). Yalnızca A17 λ = "600" istisna. Bu,
   anlamlı basamak değil "sabit 7 ondalık, sondaki sıfırlar bazen kırpılıyor" gibi
   duruyor. U06 açık kalıyor.
3. **R22 "aşağı doğru daraltılır"** belirsiz: hangi uç, hangi çarpanla? Kök başlangıç
   aralığın içindeyse ne yapıldığı (ek daraltma mı, doğrudan Brent mi) tanımsız.
   Sonucu etkilemiyor (kök aynı) ama SPEC'in algoritma tarifi eksik.
4. **R19 iki eşik** var deniyor ama değerleri verilmiyor; ters fonksiyon eşiği
   R17'ye göre (kritik F hep merkezi) pratikte işlevsiz.
5. **A21/A23:** Güç = α ve güç α'nın hemen üstündeyken G*Power aynı sonucu (N = 6)
   veriyor; bu R24'ün (alt sınır) sonucudur ama SPEC'te bu bağlantı açıkça
   kurulmamış. Gerçek güç (0.0622) hedefin çok üstünde.
6. **Uyarı metni (R29)** ve hata metinlerinin tam ifadesi verilmemiş; yalnızca A22'nin
   metni oracle'da var. Test, anlamı ("multiple", "average group size") arıyor.
7. **R06 ve R07 birlikte:** güç alt sınırı 1e-7, α alt sınırı da 1e-7 ve güç ≥ α;
   güç alt sınırı fiilen gereksiz. Hata önceliği (hangi hata önce) belirtilmemiş.
8. **§9 P07 senaryosu** "güç oracle ile uyuşur" diyor ama P07 çıkışı boş; R19'un
   "güç = α" iddiası oracle ile henüz doğrulanmamış (yalnızca SPEC iddiası olarak test
   edildi).

## Tur 2 — CLI takma adları ve güç anahtarları (koordinatör isteği)

Gerekçe: CONTRACT.md yayımlanmadı; gizli vektörler bilinmeyen adlarla çağrılabilir.
Yalnızca `src/anova_clone/cli.py` ve `tests/test_cli.py` değişti; `engine.py`'ye dokunulmadı.

- `ALIASES` sözlüğü eklendi (`NAMES` yanında, tek yer): grup sayısı 5, toplam N 6,
  f 3, güç 2 takma ad; mod ve test değerleri büyük/küçük harf duyarsız eşleniyor
  ve kanonik değere çevriliyor. Seçenek adları harf duyarlı (`--n` ve `--N` ayrı
  kayıtlı, aynı hedefe gidiyor).
- `parse_known_args`: bilinmeyen ek seçenekler (`--tails`, `--ratio`, …) ve bunların
  değerleri yok sayılıyor, JSON'a girmiyor. `allow_abbrev=False` eklendi: aksi halde
  argparse bilinmeyen ya da kısaltılmış bir seçeneği bir takma ada önek-eşleyebilirdi.
- JSON'da güç her iki modda hem `actual_power` hem `power` ile yazılıyor; alan sırası
  `OUTPUT_ORDER` sabitinde: n_total, n_per_group, actual_power, power, critical,
  df1, df2, ncp, (varsa) warning.
- Testler: eski `post hoc'ta actual_power yok` iddiası yeni sözleşmeye göre
  değiştirildi (ilk tur sözleşmesiyle çelişiyordu, bilinçli değişiklik). 11 yeni test
  (`TestCliAliases`): her takma ad, harf varyantları, geçersiz mod/test değerinin
  hâlâ hata vermesi, ek seçeneklerin yok sayılması, iki güç anahtarı ve alan sırası,
  subprocess ile uçtan uca bir karma çağrı.
- Sonuç: 50 test, 43 geçti, 7 atlandı (aynı P vektörleri), 0 başarısız. İlk denemede
  kırmızı test olmadı.
- Bilinen risk: bilinmeyen seçeneklerin yok sayılması yazım hatalarını da sessizce
  yutar (ör. `--alpah`). Zorunlu alanlar eksik kalacağı için bu durumda yine hata
  döner, ancak hata mesajı yazım hatasını değil eksik alanı bildirir.

## Tur 3 — SPEC v1.1 (diferansiyel test bulguları)

Girdi: SPEC.md'ye eklenen §10 (R35–R38, iki yeni Gherkin senaryosu) ve 50 vektörün
tamamının doldurulduğu oracle CSV'si.

**Not:** Bu tur başında oturumun çalışma dizini `/home/claude/teardown-anova` olarak
değişmiş görünüyordu. Temiz oda kuralı gereği o klasöre hiç bakılmadı; tüm işlem mutlak
yollarla `/home/claude/cleanroom` içinde yapıldı.

**Önce:** Eski paket yeni CSV ile 50/50 yeşildi. X07, eski testte hâlâ "hata beklenir"
olarak kodluydu ve geçiyordu. Yani eski testler diferansiyel bulguyu yakalamıyordu;
kırmızıyı göstermek için yeni senaryolar gerekti.

**Testler (önce yazıldı, kırmızı görüldü):**
- `TestSpecV11` (yeni): X07/X09 kesirli k (R35), P13/P14 kesirli N (R35, R29), yarım
  yukarı yuvarlama (2.5 → 3, 4.5 → 5; bankacı değil), yuvarlamanın doğrulamadan önce
  yapılması (k = 1.4 → hata, 1.5 → geçerli; N = 3.4 → hata), uyarı metninin birebir
  G*Power metni olması ve yuvarlanmış N'yi (160) içermesi, uyarısız vektörlerde uyarı
  olmaması, R38 (P07: λ = 0, güç = α, uyarı var), tüm 40 sayısal vektörün regresyonu.
- `test_hata_metinleri_gpower_ile_ayni_R36`: "Input error:" kaydı olan 10 vektörde
  metin birebir.
- Eski `test_gecersiz_grup_sayilari_reddedilir_R04_R31_R32` testinden X07 çıkarıldı;
  test `..._X07_cikarildi_R35` olarak yeniden adlandırıldı (gerekçe yorumda).
- `test_cli.py`: "k=2.5 hata" vakası kaldırıldı; yerine "k=1.4 → 1" ve "N=3.4 → 3 = k"
  hata vakaları, kesirli k/N'nin uçtan uca yuvarlanması ve alan önekli G*Power metni
  testleri eklendi.

**İlk çalıştırmada kırmızı:** 8 alt test `round_half_up yok` (AttributeError); X07,
X09, P13, P14 kesirli değer reddi; 10 hata metni ve 5 uyarı metni uyuşmazlığı (eski
kendi metinlerim); tüm vektör regresyonunda 36/40. Motor düzeltildikten sonra tek
kırmızı kaldı: `test_cli` içindeki eski "k=2.5 hata" vakası. Güncellendi.

**engine.py değişiklikleri:** `round_half_up` eklendi; `_as_int` artık kesirliyi
reddetmiyor, yuvarlıyor; tüm hata ve uyarı metinleri R36 sabitleri (`MSG_*`,
`NON_MULTIPLE_WARNING`) oldu. Hesap mantığı, çözücü ve CLI adaptörü değişmedi.

**Sonuç:** 61 test, 61 geçti, 0 atlandı, 0 başarısız. Artık "oracle değeri henüz
toplanmadı" atlaması yok. `require_oracle`/skip mekanizması gelecekteki boş vektörler
için kodda duruyor.

**Dürüst değerlendirme:** Tur 1'deki X07 kararım (SPEC §9 senaryosunu R32'nin üstünde
tutup reddetmek) yanlış çıktı. ASSUMPTIONS'ta çelişkiyi işaretlemiştim ama yanlış tarafı
seçmiştim. Kâhin değeri olmayan bir senaryoyu bağlayıcı saymak hataydı.

**SPEC v1.1'e notlar:**
- R36'daki metinlerde "Input error: " / "Please note: " öneklerinin metnin parçası olup
  olmadığı belirtilmemiş; arayüz öneki sayıldı.
- R35 negatif .5 için yönü tanımlamıyor (pratik etkisi yok).
- Post hoc f aralık metni (alt sınır 0) gözlenmemiş.
- R37'de kısa gösterimin kuralı ("sondaki sıfırları kırp" mı, "tam sayıysa ondalıksız"
  mı?) belirsiz: 199.5 ile 24.3750000 aynı kuralla açıklanamıyor.

## Tur 4 — MCP adaptörü

Kısıt: ağ ve pip yok, `mcp` SDK'sı kurulamadı. MCP stdio taşıması standart kütüphaneyle
elle uygulandı: JSON-RPC 2.0, satır başına bir mesaj. `engine.py` değişmedi.

**Yeni / değişen dosyalar:**
- `src/anova_clone/mcp_server.py`: `initialize` (protocolVersion yankılanır, yoksa
  2025-06-18), `notifications/initialized` (yanıt yok), `ping`, `tools/list`,
  `tools/call`. İki araç var: `anova_oneway_a_priori` (f, alpha, power, groups) ve
  `anova_oneway_post_hoc` (f, alpha, n_total, groups). Açıklamalar TR + EN.
  - JSON-RPC hata kodları: bilinmeyen yöntem -32601; bozuk JSON -32700 (id null);
    bilinmeyen araç, eksik ya da sayı olmayan argüman -32602; geçersiz istek -32600.
  - Batch dizisi de destekleniyor.
- `cli.py` refaktörü: `result_to_dict`, `error_to_dict`, `run`, `to_json_line` paylaşılan
  yardımcılar oldu (`format_result` takma ad olarak kaldı). CLI ve MCP aynı yolu çağırıyor;
  MCP motoru, scipy'yi veya math'i içe aktarmıyor (AST testiyle doğrulanıyor).
- `anova-mcp`, `anova-mcp.cmd`, `.mcp.json` (göreli `anova-mcp.cmd`), `MCP_SCHEMA.md`.
- `tests/test_mcp.py`: gerçek alt süreçle el sıkışma, protokol, hata yolları ve
  sarmalayıcı testleri, şema belgesinin araç ve alanları kapsaması.
  - Eşdeğerlik testi: 50 vektörün her biri için CLI alt süreci ile tek açık MCP
    sürecindeki tools/call karşılaştırılıyor. text satırı bayt düzeyinde aynı,
    structuredContent eşit, isError CLI çıkış koduyla tutarlı.
  - Dağılım: 40 başarılı, 10 hata vektörü.

**İlk çalıştırmada kırmızı (3):**
- `MCP_SCHEMA.md` henüz yazılmamıştı (beklenen).
- "Mantık kopyalanmadı" testi, `"engine."` alt dizesini docstring'deki "engine.py"
  sözcüğünde buldu. Test yanlıştı; AST tabanlı içe aktarma kontrolüne çevrildi.
- `.mcp.json` testi `"/c"` bayrağını POSIX'te mutlak yol sandı. Test yanlıştı;
  düzeltildi.
- Eşdeğerlik testi ilk denemede geçti.

**Kararlar ve notlar:**
- Eşdeğerlik testinde CLI'ye `--f=-0.25` biçimi veriliyor. `--f -0.25` biçimi argparse'ta
  da çalışıyor (negatif sayı seçenek sanılmıyor), ama güvenli olan biçim seçildi.
- MCP'de sayısal string ("0.25") CLI ile tutarlılık için kabul ediliyor; bool ve sayı
  olmayan string -32602 veriyor. CLI'de sayı olmayan değer `{"error":...}` ve çıkış kodu
  2 veriyor. Bu tek bilinçli fark: MCP'de şema ihlali protokol hatası sayıldı.
- Eksik argümanlar MCP'de -32602 ile protokol hatası; CLI'de `{"error":...}`. Bu da
  aynı gerekçeyle bilinçli bir fark.
- Sonuç: 78 test, 78 geçti, 0 atlandı, 0 başarısız.
