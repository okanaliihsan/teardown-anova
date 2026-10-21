# YZM301 Teardown Sprint — Tek yönlü ANOVA güç analizi

G*Power 3.1.9.7'nin **"F tests → ANOVA: Fixed effects, omnibus, one-way"** hesabı REA + Ghidra ile söküldü, kanıtlandı, temiz odada yeniden yazıldı ve G*Power ile ölçüldü. Ardından hesap motoru az token harcayan bir CLI'nin, bir MCP sunucusunun ve Türkçe soru anlayan bir ajanın arkasına konuldu.

> Bu yazılım **G*Power değildir** ve onun yerine geçmez. G*Power'ın yazarlarına atıf: aşağıda, [Atıf](#atıf-ve-etik).
> Test ailesi: **3 · F testi, tek yönlü ANOVA (üç tedavi kolu)**. Bireysel çalışma.

## Tamamlanan katmanlar

| Katman | Durum | Kanıt |
|---|---|---|
| **Temel: motor + CLI + diferansiyel test** (85) | ✅ | [`tests/UYUM_RAPORU.md`](tests/UYUM_RAPORU.md) |
| **Bonus kapısı:** G*Power vektörlerinde N tam eşleşme ≥ %90 | ✅ **40/40 = %100** | aynı rapor |
| **+15 MCP sunucusu** | ✅ | [`MCP_SCHEMA.md`](MCP_SCHEMA.md), `tests/test_mcp.py` (50 vektörde CLI ≡ MCP) |
| **+10 AI ajanı** (MCP üzerinden, Türkçe) | ✅ ajan + 10 soruluk set + ölçüm betiği hazır · ⏳ ölçüm sonuçları | [`agent/`](agent/), [`agent/EVAL_REPORT.md`](agent/EVAL_REPORT.md) |
| İsteğe bağlı: Sistem 1 modeli (Jev) | ➖ Jev erişimi yok. Yönergenin izin verdiği gibi aynı etiket setine kısıtlanmış bir LLM kullanıldı (etiket + güven, eşik 0.75). | [`agent/AGENT_PROMPT.md`](agent/AGENT_PROMPT.md) |

## Sonuç özeti

| Ölçü | Değer |
|---|---|
| G*Power kâhini (arayüzden elle, ekran görüntülü) | **50 vektör**: 27 a priori, 9 geçersiz/sınır girdi, 14 post hoc |
| Tam uyum (λ, kritik F, df₁, df₂, N, güç, uyarı/hata) | **50 / 50** |
| N tam eşleşme | **40 / 40** |
| Kütüphane kâhini (statsmodels 0.14.0) | 570 vektör. A priori 450/450 (yuvarlama kuralıyla). Post hoc 68 vektörde 1e-6 mertebesinde farklı: bağımsız hakem her birinde yeniden yazımı doğruladı, açıklanamayan fark **0**. |
| Birim + bileşen + sistem testleri | 78 test (`python -m unittest discover -s tests`) |
| `[REA]` etiketli kanıt satırı | **44 / 50** ([`LEDGER.md`](LEDGER.md)) |
| Diferansiyel testin bulduğu gizli kural | Kesirli k ve N **en yakın tam sayıya** yuvarlanır (2.4 → 2, 2.5 → 3, 159.6 → 160). Ajanın tahmini yanlıştı, bkz. [`HALLUCINATIONS.md`](HALLUCINATIONS.md) H1. |

**Kılavuzda yazmayan, binary'den kanıtlanan davranışlar** (ayrıntı `LEDGER.md`, kural `SPEC.md`):
- A priori çözücü: sürekli güç fonksiyonunda **Brent kök bulucu** (en fazla 300 iterasyon). Başlangıç aralığı **[k+1, k+100]**, kök bulunamazsa **×1.6** ile genişletilir (L21–L28).
- Yuvarlama: **N = ⌈N_sürekli / k⌉ · k**. Toplam N her zaman k'nın katıdır; en küçük tam sayı değil (A02: 158 değil **159**) (L29).
- Alt sınır: grup başına **en az 2** (f = 3, f = 10 ve güç = α için N = 6) (L31).
- Gerçek güç, yuvarlanmış N ile **yeniden hesaplanır** (L32).
- Post hoc: N, k'nın katı değilse hata vermez; **uyarı** verir ve hesabı yine yapar (L36–L37).
- Aralıklar: α ve güç **[1e-07, 0.9999999]**; f a priori'de **[1e-06, 50]**, post hoc'ta **[0, 50]**; güç ≥ α ve **eşitlik kabul** (L40–L43).

---

## Kurulum

Gerekenler: Python 3.10+, `numpy`, `scipy`. Windows'ta en kolayı **Anaconda Prompt**'tur. Paket kurmak gerekmez; repo kökündeki sarmalayıcılar `PYTHONPATH`'i kendisi ayarlar.

```bat
git clone <bu repo>
cd <repo>
python -m unittest discover -s tests        :: 78 test
```

İsteğe bağlı kurulum: `pip install -e .` → `gpower-clone` komutu PATH'e girer.

## Çalıştırma — CLI

```bat
gpower-clone --test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --power 0.95 --groups 10
{"n_total":390,"n_per_group":39,"actual_power":0.9523634,"power":0.9523634,"critical":1.9045377,"df1":9,"df2":380,"ncp":24.375}

gpower-clone --test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --n 100 --groups 3
{"n_total":100,"n_per_group":null,"actual_power":0.5885389,"power":0.5885389,"critical":3.0901867,"df1":2,"df2":97,"ncp":6.25,"warning":"The total sample size (100) is not a multiple of the number of groups (3). The analysis was based on the average group size."}

gpower-clone --test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --power 0.04 --groups 3
{"error":"--power: Power must be greater than or equal to alpha."}      (çıkış kodu 2)
```

Unix'te `./gpower-clone`, Windows'ta `gpower-clone` (`gpower-clone.cmd`). Doğrudan çağrı: `python -m anova_clone.cli` (`PYTHONPATH=src`).

### CLI sözleşmesi

Yönergedeki t2-indep örneğinin biçimi izlendi: tek satır JSON; geçersiz girdide `{"error": ...}` ve sıfırdan farklı çıkış kodu. ANOVA için `CONTRACT.md` yayımlanmadığından (yönergedeki link boştu) CLI birden çok yazımı kabul eder:

| Anlam | Kabul edilen seçenekler |
|---|---|
| test | `--test anova-oneway` (`anova_oneway`, `anova` da olur; büyük/küçük harf duyarsız) |
| mod | `--mode a-priori` / `post-hoc` (`apriori`, `a_priori`, `posthoc`, `post_hoc`) |
| etki büyüklüğü f | `--f`, `--effect-size`, `--es` |
| α | `--alpha` |
| hedef güç | `--power`, `--target-power` |
| grup sayısı k | `--groups`, `--k`, `--k-groups`, `--num-groups`, `--number-of-groups` |
| toplam N (post hoc) | `--n`, `--N`, `--n-total`, `--n_total`, `--total-n`, `--sample-size` |

Tanınmayan ek seçenekler (ör. `--tails`, `--ratio`) yok sayılır. Çıktı alanları: `n_total`, `n_per_group`, `actual_power`, `power` (aynı değer, iki anahtar), `critical`, `df1`, `df2`, `ncp`, varsa `warning`. Sayılar 7 ondalık, yani G*Power'ın ekranda gösterdiği hassasiyet. Çıkış kodları: 0 başarı, 2 geçersiz girdi, 3 hesaplanamıyor. Tüm adlar `src/anova_clone/cli.py` başındaki `NAMES`/`ALIASES` sözlüklerindedir; sözleşme gelince yalnızca orası değişir.

## MCP sunucusu (+15)

```bat
claude mcp add anova-power --scope project -- cmd /c anova-mcp.cmd
```

Repo kökündeki `.mcp.json` aynı kaydı içerir. Araçlar `anova_oneway_a_priori` (f, alpha, power, groups) ve `anova_oneway_post_hoc` (f, alpha, n_total, groups). **Araç şeması, girdi/çıktı alanları ve örnek istek/yanıt: [`MCP_SCHEMA.md`](MCP_SCHEMA.md).**

MCP ince bir adaptördür: `mcp_server.py` → `cli.run()` → `engine`. Formül, aralık kontrolü ve yuvarlama yalnızca `engine.py`'dedir. Bunu bir AST testi denetler: MCP katmanı `engine`, `scipy` veya `math` içe aktarmaz. `tests/test_mcp.py`, 50 kâhin vektörünün **her birinde** CLI çıktısıyla MCP çıktısının bayt bayt aynı olduğunu doğrular.

## AI ajanı (+10)

Ajan = **Claude Code** (headless `claude -p`) + bu reponun MCP sunucusu + [`agent/AGENT_PROMPT.md`](agent/AGENT_PROMPT.md). Ayrı bir API anahtarı gerekmez.
- Ajan önce soruyu etiketler (`t2-indep, t-paired, anova-oneway, chi2-contingency, multireg-r2, ambiguous, unsupported`) ve bir güven değeri verir. Etiket `anova-oneway` değilse **ya da güven < 0.75 ise** aracı çağırmaz, araştırmacıya sorar.
- **Hesap yapmaz:** sayı yalnızca MCP aracından gelir. `Bash` dahil hesap yapabilecek tüm araçlar kapalıdır (`--disallowedTools`).
- 10 soruluk set: [`agent/eval_questions.json`](agent/eval_questions.json). 8 desteklenen soru var ve beklenen N/güç değerleri **G*Power kâhininden** alınmıştır. Bir soru t testidir (desteklenmez), bir soru da eksik bilgilidir (sorması gerekir). Her sorunun İngilizce çevirisi de var.
- Ölçüm: `python agent/run_eval.py`. Aynı soruları **MCP yolu** ve **GUI yolu** (MCP yok, G*Power ekran görüntülerini okuyarak) ile çözer; token, süre, doğruluk, araç çağrı kayıtları ve güven kalibrasyonunu raporlar. `--langs tr en` ile Türkçe/İngilizce karşılaştırması da yapılır.
- Çıktılar: `agent/EVAL_REPORT.md`, `agent/EVAL_RESULTS.json`, araç çağrı kayıtları `agent/logs/*.jsonl`.

## Diferansiyel test

```bat
python tests\differential.py
```

Kâhin vektörlerini **CLI üzerinden** (gizli vektörlerin çalıştırılacağı yolun ta kendisi) koşturur ve [`tests/UYUM_RAPORU.md`](tests/UYUM_RAPORU.md), `tests/differential_results.csv`, `tests/library_results.csv` dosyalarını üretir. Tolerans yönergedeki gibidir: N, df₁ ve df₂ tam eşleşir; diğer değerler G*Power'ın gösterdiği basamak sayısına kadar eşleşir. Uyarı ve hata davranışı da karşılaştırılır.

**İki katmanlı kâhin:**
1. `oracle/gpower_vectors.csv`: G*Power arayüzünden 50 vektör, her biri `oracle/screenshots/<ID>.png` ile. Sınır değerler bilinçli seçildi: çok küçük/büyük f, güç = α ve güç < α, k = 2 ve k = 100, k'ya bölünmeyen N, kesirli k/N, geçersiz girdiler. Neden bu vektörlerin seçildiği: [`oracle/TOPLAMA_REHBERI.md`](oracle/TOPLAMA_REHBERI.md).
2. `oracle/library/statsmodels_vectors.csv`: statsmodels ile 570 vektör (`oracle/library/gen_library_vectors.py`). Kütüphane N'yi kesirli verir, G*Power yukarı yuvarlar; bu fark raporda açıklanır.

---

## Nasıl yapıldı: koddan kanıta, kanıttan spec'e

| Adım | Ne yapıldı | Çıktı |
|---|---|---|
| 1 · Sök | REA 6.7.0 + Ghidra 12.1.4, Claude Code oturumu | `prompts/session1_inceleme.md` (ilk prompt) |
| 2 · Kanıtla | Her iddia `[REA]`/`[DOK]`/`[AJAN]` etiketiyle, fonksiyon/dize adresiyle | [`LEDGER.md`](LEDGER.md) |
| 3 · Spec çıkar | Kabul kriterleri Gherkin; v1.1 diferansiyel test bulgularıyla güncellendi | [`SPEC.md`](SPEC.md) |
| 4 · Yeniden yaz | Temiz oda: ayrı ajan oturumu, yalnızca SPEC.md + kâhin değerleri | `src/`, `prompts/session2_yazim.md`, [`ASSUMPTIONS.md`](ASSUMPTIONS.md), [`SESSION2_LOG.md`](SESSION2_LOG.md) |
| 5 · Diferansiyel test | G*Power + kütüphane kâhini, CLI üzerinden | [`tests/UYUM_RAPORU.md`](tests/UYUM_RAPORU.md) |
| 6 · Ajan çağına taşı | CLI → MCP → ajan | [`MCP_SCHEMA.md`](MCP_SCHEMA.md), [`agent/`](agent/) |

**Temiz oda nasıl sağlandı:** İnceleme oturumu (Claude Code, kullanıcının Windows makinesi) yalnızca `LEDGER.md` ve `SPEC.md` üretti. Yazım oturumu ise ayrı bir ajandı ve boş bir klasörde başlatıldı. Ona yalnızca `SPEC.md` ve `oracle/gpower_vectors.csv` (G*Power **arayüzünden** okunan sayılar, decompile değil) verildi; klasör dışına bakmaması talimatıyla çalıştı (`SESSION2_LOG.md`). SPEC v1.1'deki düzeltmelerin kaynağı da binary değil, kâhindir (`[KÂHİN]`). Teslim edilen kodda decompile çıktısı yoktur. `GPowerNT.exe` repoda yoktur (`.gitignore`).

**"Ajanın söktüğü şeyin doğru olduğunu nasıl kanıtlarsın?"** Ajanın iddiası tek başına kanıt sayılmadı:
- **Statik doğrulama:** her kural bir `[REA]` adresine bağlandı.
- **Dinamik doğrulama:** her kural G*Power'ın kendisine karşı ölçüldü (diferansiyel test).
- İki yol ayrıştığında **kara kutu kazandı**. Örnek: L48 `[AJAN]` iddiası X07/X09'da çürüdü ve SPEC buna göre düzeltildi.

Ayrıntılar: [`HALLUCINATIONS.md`](HALLUCINATIONS.md), [`AGENT_COST.md`](AGENT_COST.md).

## Sürüm bilgisi (konfigürasyon yönetimi)

| | |
|---|---|
| İncelenen binary | G*Power **3.1.9.7** (Windows), `GPowerNT.exe`, resmi sayfadan (psychologie.hhu.de) |
| **GPowerNT.exe SHA-256** | `C63E6A133EB6372932F810C08CC33DC35A06D1DDB658F897BD6C34A754EFC812` |
| Sürüm kanıtı | [`docs/gpower_about.png`](docs/gpower_about.png), [`docs/BINARY.md`](docs/BINARY.md) |
| Not | Yönerge dosyayı `GPower.exe` diye anıyor; 3.1.9.7 zip'inde çalıştırılabilir dosyanın adı `GPowerNT.exe` |
| Araçlar | REA (npm `rea-agents`) 6.7.0, Ghidra 12.1.4, Temurin JDK 21.0.12, Node 24.21, Claude Code 2.1.299 |
| REA/Ghidra kontrolü | *"REA araçları ve Ghidra sağlayıcısı bu oturumda kullanılabilir mi?"* → ![rea check](docs/rea_check.png) ([`docs/rea_doctor_ghidra.json`](docs/rea_doctor_ghidra.json)) |
| Host ↔ target | İnceleme: Windows x64 host, 32-bit x86 PE hedef. Yeniden yazım: platformdan bağımsız Python. Ayrıntı: [`SETUP.md`](SETUP.md) |
| Yeniden yazım sürümü | `anova-clone` 1.1 (SPEC v1.1) |

## Demo

**60 saniyelik CLI videosu:** _DEMO_LINK_  
Senaryo ve komutlar: [`docs/DEMO.md`](docs/DEMO.md)

## Repo haritası (yönergedeki teslim listesi)

| Yönerge | Bu repoda |
|---|---|
| SPEC.md (Gherkin) | [`SPEC.md`](SPEC.md) |
| LEDGER.md ([DOK]/[REA]/[AJAN]) | [`LEDGER.md`](LEDGER.md) |
| HALLUCINATIONS.md | [`HALLUCINATIONS.md`](HALLUCINATIONS.md) (6 madde) |
| AGENT_COST.md | [`AGENT_COST.md`](AGENT_COST.md) |
| prompts/ | [`prompts/session1_inceleme.md`](prompts/session1_inceleme.md), [`prompts/session2_yazim.md`](prompts/session2_yazim.md) |
| oracle/ (CSV + ekran görüntüleri) | [`oracle/gpower_vectors.csv`](oracle/gpower_vectors.csv), `oracle/screenshots/`, `oracle/library/` |
| src/ (motor + CLI; MCP ve ajan) | `src/anova_clone/engine.py` (tek motor), `cli.py`, `mcp_server.py`; `agent/` |
| tests/ (diferansiyel test + uyum raporu) | `tests/differential.py`, [`tests/UYUM_RAPORU.md`](tests/UYUM_RAPORU.md), `tests/test_*.py` |
| README (kurulum, çalıştırma, sürüm, hash, demo, atıf) | bu dosya |

## Sommerville bağlantısı (kısa)

- **Doğrulama:** "ürünü doğru mu yapıyoruz?" → yeniden yazım SPEC'e uyuyor mu (`tests/test_spec.py`).
- **Geçerleme:** "doğru ürünü mü yapıyoruz?" → SPEC kara kutunun gerçek davranışı mı (`tests/differential.py`). İkisi ayrı başarısızlıklar yakaladı: H1/H2 yalnızca geçerlemede görüldü.
- **Test seviyeleri:** birim (`engine` fonksiyonları), bileşen (CLI ↔ motor, MCP ↔ CLI arayüzü), sistem (girdi → N, kritik F, λ uçtan uca), kabul (Gherkin + gizli vektörler).
- **Bölüm testi ve sınır değerler:** kâhin vektör seçimi (`oracle/TOPLAMA_REHBERI.md`).
- **TDD'nin tersi:** önce karakterizasyon testi, yani G*Power'ın çıktısı test olarak yakalandı, sonra kod yazıldı.
- **Yeniden kullanım:** soyutlama düzeyinde kalındı, kod değil algoritma alındı.
- **Konfigürasyon yönetimi:** sürüm ve hash. **Host-target geliştirme:** Windows x86 hedef ↔ bağımsız Python yeniden yazımı.

## Bilinen sınırlamalar

- Noncentral F için `scipy.stats.ncf` (Boost) kullanıldı; G*Power DCDFLIB kullanıyor (L04). 40 sayısal vektörde 7 ondalık uyum var. N ≈ 1e12 gibi aşırı uçlarda aynılık doğrulanmadı (`ASSUMPTIONS.md` U03).
- Gösterim: JSON değerleri sayısal olarak G*Power ile aynıdır, ama yazım biçimi birebir değildir (24.375 ile 24.3750000).
- Birden çok alan aynı anda hatalıysa hangi hatanın önce bildirildiği G*Power'da ölçülmedi.
- Ajan değerlendirmesindeki GUI yolu gerçek tıklama yapmaz, hazır ekran görüntüleri okur. Bu yüzden GUI maliyetinin **alt sınırıdır**.

## Atıf ve etik

Bu çalışma YZM301 dersi kapsamında **eğitim amaçlıdır**. Yalnızca G*Power 3.1.9.7 (Windows) incelendi. G*Power ücretsizdir; satışı ve resmi sayfa dışında dağıtımı yasaktır. Bu repo G*Power'ı içermez ve dağıtmaz. Yazarların bilim dünyasına sunduğu emeğe saygıyla:

- Faul, F., Erdfelder, E., Lang, A.-G., & Buchner, A. (2007). G*Power 3: A flexible statistical power analysis program for the social, behavioral, and biomedical sciences. *Behavior Research Methods, 39*(2), 175–191.
- Faul, F., Erdfelder, E., Buchner, A., & Lang, A.-G. (2009). Statistical power analyses using G*Power 3.1: Tests for correlation and regression analyses. *Behavior Research Methods, 41*(4), 1149–1160.

Ticari tersine mühendislik aracı kullanılmadı; yalnızca Ghidra (açık kaynak) ve REA kullanıldı. Ajanlara gönderilen tüm klinik senaryolar kurgusaldır; gerçek hasta verisi yoktur.
