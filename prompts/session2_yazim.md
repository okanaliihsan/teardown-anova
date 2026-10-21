# Oturum 2 — Yazım (Temiz Oda) · İlk Prompt

> Bu oturum, inceleme oturumunu hiç görmemiş **yeni ve ayrı bir ajan oturumunda** başlatıldı.
> Oturuma verilen girdiler yalnızca şunlardır:
> 1. `SPEC.md` (inceleme oturumunun ürettiği davranış spesifikasyonu)
> 2. `oracle/gpower_vectors.csv` (G*Power **arayüzünden** elle toplanan kâhin değerleri; SPEC'teki Gherkin senaryoları sayısal beklentiler için bu dosyaya atıf yapar)
>
> Ghidra/REA çıktısı, `LEDGER.md`, decompile parçaları ve inceleme oturumunun konuşması bu oturuma **verilmedi**. Ajan, yalnızca kendisine ayrılan boş bir çalışma klasöründe (`cleanroom/`) çalıştı.
> Aşağıdaki çizginin altındaki metin oturumun ilk mesajıdır.

---

Bir istatistiksel güç analizi motorunu, çalışma klasöründeki `SPEC.md` spesifikasyonuna göre **sıfırdan** yazacaksın.

## Kurallar (temiz oda)

- Yalnızca çalışma klasöründeki dosyaları oku: `SPEC.md` ve `oracle/gpower_vectors.csv`. Bu klasörün dışındaki hiçbir dosyayı açma, arama, listeleme. Başka bir programın kaynak koduna veya decompile çıktısına bakma.
- `oracle/gpower_vectors.csv` bir **kara kutu gözlemidir**: G*Power arayüzüne girilen değerler ve ekranda okunan sonuçlar. Kodu bu sayılara "uydurmak" için sabit tablo, özel durum veya `if id == ...` gibi kısayollar YAZMA; sayılar yalnızca testlerde beklenen değer olarak kullanılır. Bir test tutmazsa nedenini SPEC'teki kurallar üzerinden araştır.
- SPEC'te açık kalan bir nokta olursa tahmin ettiğini açıkça belgele (`ASSUMPTIONS.md`).

## Dil ve kütüphane

- Python 3.11+, yalnızca `scipy`, `numpy` ve standart kütüphane. Ortamda paket kurulamıyor; testler için **`unittest`** (standart kütüphane) kullan, `pytest` yok.
- `scipy.stats.f` (merkezi F'nin tersi) ve `scipy.stats.ncf` (noncentral F'nin sağ kuyruğu) serbest. Kök bulucu için `scipy.optimize.brentq` serbest. **Parantezleme, genişletme, yuvarlama ve df hesabı senin kodun olmalı** (ödev: "Puan çözücüden, yuvarlamadan ve df hesabından gelir").

## Mimari (zorunlu)

```
src/anova_clone/
  __init__.py
  engine.py      # TEK hesap motoru: saf fonksiyonlar, G/Ç yok, tam duyarlıklı float döndürür
  errors.py      # Geçersiz girdi istisnaları (hangi alanın sorunlu olduğunu taşır)
  cli.py         # İnce adaptör: argüman ayrıştır → engine çağır → tek satır JSON yaz
```

- **Hesap mantığı yalnızca `engine.py` içinde.** CLI (ve sonradan eklenecek MCP sunucusu) sadece motoru çağırır; hiçbir formül, aralık kontrolü veya yuvarlama adaptöre sızmaz.
- Motorun genel arayüzü:
  - `a_priori(f: float, alpha: float, power: float, k: int) -> Result`
  - `post_hoc(f: float, alpha: float, n_total: int, k: int) -> Result`
  - `Result` (dataclass): `ncp`, `critical_f`, `df1`, `df2`, `n_total`, `n_per_group` (bölünebiliyorsa, değilse None), `power` (a priori'de gerçek güç), `warning` (yoksa None)

## CLI (geçici sözleşme)

Komut: `python -m anova_clone.cli`. Ayrıca `gpower-clone` adıyla çağrılabilmesi için `pyproject.toml` içinde konsol betiği tanımla ve repo kökünde `gpower-clone` (Unix) ile `gpower-clone.cmd` (Windows) adlı, paket kurulmadan da çalışan ince sarmalayıcılar koy.

```
gpower-clone --test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --power 0.95 --groups 10
gpower-clone --test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --n 390 --groups 10
```

- Başarı: stdout'a **tek satır JSON**, çıkış kodu 0. Alanlar: `n_total`, `n_per_group`, `actual_power` (post hoc'ta `power`), `critical`, `df1`, `df2`, `ncp`; uyarı varsa `warning`.
- Geçersiz girdi: `{"error":"<açıklama>"}` ve sıfırdan farklı çıkış kodu.
- Parametre adları ve JSON alan adları henüz kesinleşmedi (hocanın CONTRACT.md'si bekleniyor). Bu yüzden **tüm adları `cli.py` başındaki tek bir sözlükte** topla; değişince yalnızca orası değişsin. Sayıların JSON'daki ondalık sayısı da tek bir sabitte olsun (varsayılan 7).

## Test güdümlü yaz

1. Önce SPEC.md'nin 9. bölümündeki her Gherkin senaryosunu bir `unittest` testine çevir (`tests/test_spec.py`). Test adı senaryoyu ve kural numaralarını içersin. Beklenen sayılar `oracle/gpower_vectors.csv`'den okunur. Çıkış sütunları boş olan vektörlerin testleri `self.skipTest("oracle değeri henüz toplanmadı")` ile atlanır.
2. Karşılaştırma toleransı (SPEC + ödev): `n_total`, `df1`, `df2` **tam** eşleşir; diğer değerler G*Power'ın ekranda gösterdiği ondalık basamak sayısına kadar eşleşir (CSV'deki değerin ondalık hanesi kadar yuvarlayıp karşılaştır).
3. Testleri çalıştır, kırmızı olduklarını gör, motoru yaz, yeşile çevir.
4. Ayrıca CLI için uçtan uca testler yaz (`tests/test_cli.py`, subprocess ile): JSON tek satır mı, hata durumunda çıkış kodu sıfırdan farklı mı.

## Teslim

- Kod ve testler.
- `ASSUMPTIONS.md`: SPEC'te açık kalan her nokta (özellikle U01–U07) için ne varsaydığın.
- `SESSION2_LOG.md`: kaç tur/iterasyon, hangi testler ilk denemede kırmızıydı ve neden, takıldığın yerler, SPEC'te eksik/yanlış olduğunu düşündüğün yerler. Bu kayıt ödevdeki AGENT_COST.md ve HALLUCINATIONS.md'ye girdi olacak; dürüst ol.

---

## Sonraki turlar (aynı yazım oturumuna gönderilen mesajların özeti)

Yönerge yalnızca ilk prompt'u istiyor; şeffaflık için sonraki turlar da kaydedildi. Hiçbirinde Ghidra/REA çıktısı veya LEDGER içeriği verilmedi.

- **Tur 2 — CLI takma adları.** CONTRACT.md yayımlanmadığı için: grup/N/f/güç seçeneklerinin birden çok yazımı, harf duyarsız mod/test değerleri, bilinmeyen ek seçenekleri (`--tails`, `--ratio`) yok sayma, güç değerini hem `actual_power` hem `power` anahtarıyla yazma. Yalnızca `cli.py` ve `test_cli.py`; `engine.py`'ye dokunulmadı.
- **Tur 3 — SPEC v1.1.** "SPEC.md'nin sonuna §10 eklendi (R35–R38) ve oracle CSV'si 50 vektörle tamamlandı. Diferansiyel test X07, X09, P13, P14'te uyuşmazlık buldu; SPEC v1.1'i uygula." Kaynak: G*Power arayüzü (`[KÂHİN]`), binary değil.
- **Tur 4 — MCP adaptörü.** Ödevin MCP isteri aynen verildi. Standart kütüphaneyle stdio JSON-RPC 2.0 sunucusu; iki araç; JSON üretimi CLI ile paylaşılan fonksiyonda; 50 vektörün her birinde CLI ≡ MCP eşdeğerlik testi; `MCP_SCHEMA.md`.
