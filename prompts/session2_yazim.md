# Oturum 2 — Yazım (Temiz Oda) · İlk Prompt

> Bu oturum **yeni** bir ajan oturumunda başlar ve **yalnızca `SPEC.md`** dosyasını görür.
> Ghidra/REA çıktısı, `LEDGER.md`, decompile parçaları ve inceleme oturumunun konuşması bu oturuma VERİLMEZ.
> Aşağıdaki çizginin altındaki metin oturumun ilk mesajıdır; `SPEC.md` içeriği sonuna eklenir.

---

Bir istatistiksel güç analizi motorunu, ekteki `SPEC.md` spesifikasyonuna göre **sıfırdan** yazacaksın. Spesifikasyon dışında bir kaynağa (başka bir programın kodu, decompile çıktısı) bakma; spesifikasyonda açık kalan bir nokta olursa tahmin etme, soruyu bana yaz ve varsayımını `ASSUMPTIONS` başlığı altında belgele.

## Dil ve kütüphane

- Python 3.11+.
- Dağılım fonksiyonları için yalnızca `scipy.stats` (merkezi F'nin tersi, noncentral F'nin sağ kuyruğu). Çözücü (N arama), yuvarlama ve df hesabı senin kodun olmalı.

## Mimari (zorunlu)

```
src/anova_clone/
  engine.py      # TEK hesap motoru: saf fonksiyonlar, G/Ç yok
  cli.py         # İnce adaptör: argüman ayrıştır → engine çağır → tek satır JSON yaz
  errors.py      # Geçersiz girdi istisnaları
```

- **Hesap mantığı yalnızca `engine.py` içinde.** CLI (ve sonradan eklenecek MCP) sadece motoru çağırır; hiçbir formül adaptöre sızmaz.
- Motorun genel arayüzü: `a_priori(f, alpha, power, k) -> Result` ve `post_hoc(f, alpha, n_total, k) -> Result`.

## CLI sözleşmesi (değiştirilemez)

[CONTRACT.md'deki anova-oneway parametre adları ve JSON alanları buraya aynen eklenecek]

- Başarılı çağrı: stdout'a **tek satır JSON**, çıkış kodu 0.
- Geçersiz girdi: `{"error":"<açıklama>"}` ve sıfırdan farklı çıkış kodu.

## Test güdümlü yaz

1. Önce SPEC.md'deki her Gherkin senaryosunu bir pytest testine çevir (`tests/test_spec.py`). Test adları senaryo ve kural numarasını içersin.
2. Testleri çalıştır, kırmızı olduklarını gör.
3. Motoru yaz, testleri yeşile çevir.

## Teslim

- Kod, testler, `ASSUMPTIONS` listesi ve bu oturumun süreç özeti (kaç tur, hangi noktada takıldın).

---

`SPEC.md`:

[SPEC.md içeriği buraya yapıştırılır]
