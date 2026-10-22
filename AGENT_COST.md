# AGENT_COST.md — Ajan maliyet ve süreç günlüğü

Ödev isteri: *"hangi ajan, yaklaşık token ve maliyet, kaç iterasyon, neyi farklı yapardınız"*.

Bu çalışmada üç ayrı ajan rolü vardı. Temiz oda kuralı gereği **inceleyen** ile **yazan** ayrı oturumlardı. Üçüncü rol (koordinatör), iki oturum arasında yalnızca SPEC.md'yi ve G*Power kâhin değerlerini taşıdı; Ghidra çıktısını yazım oturumuna hiç aktarmadı.

| Rol | Ajan / model | Gördüğü girdiler | Ürettikleri |
|---|---|---|---|
| **Oturum 1 — inceleme** (kirli oda) | Claude Code 2.1.299, Claude Opus 5 (medium effort), Claude Pro aboneliği; REA 6.7.0 MCP + Ghidra 12.1.4 | `GPowerNT.exe`, `prompts/session1_inceleme.md` | `LEDGER.md`, `SPEC.md` (v1.0) |
| **Oturum 2 — yazım** (temiz oda) | Claude (Opus 5.5) alt ajanı, boş bir klasörde (`cleanroom/`), ağ yok | Yalnızca `SPEC.md` + `oracle/gpower_vectors.csv` (G*Power **arayüz** değerleri) | `src/`, `tests/test_*.py`, `ASSUMPTIONS.md`, `SESSION2_LOG.md` |
| **Koordinatör** | Claude (Opus 5.5), claude.ai | Her şey (ödev, slaytlar, LEDGER, SPEC, kâhin) | Kurulum rehberi, kâhin vektör tasarımı, `tests/differential.py`, SPEC v1.1, belgeler |

---

## Oturum 1 — inceleme (ölçülmüş)

Kaynak: Claude Code `/cost` ekranı → `docs/session1_cost.png`; ajanın kendi süreç kaydı → `docs/session1_process_log.png`.

| Ölçü | Değer |
|---|---|
| Model | claude-opus-5 (ana), claude-haiku-5-5 (yardımcı, ihmal edilebilir: 1.2k girdi, 244 çıktı) |
| Girdi token (önbelleksiz) | 5.0k |
| Çıktı token | 138.7k |
| Önbellekten okunan | **18.6M** |
| Önbelleğe yazılan | 284.6k |
| İstek sayısı | 106 (girdilerin %98'i önbellekten) |
| Tahmini maliyet (API fiyatıyla) | **$15.65**. Pro aboneliği kapsamında; ek ödeme yapılmadı ("Usage credits are off"). |
| API süresi / duvar saati | 32 dk 43 sn / 2 sa 6 dk (bekleme dahil) |
| Kullanıcı yönergesi | 1 ilk prompt + 2 kısa "devam et" |
| Ajan turu | ~45 |
| REA çağrısı | **114**: `procedure_pseudo_code` 31, `xrefs` 21, `search_strings` 16, `resolve_containing_procedure` 8, `procedure_callers` 7, `procedure_callees` 7, `procedure_info` 7, `read_bytes` 6, `search_bytes` 3 (+ sürücü üzerinden 106); doğrudan MCP: `open_binary` 2, `close_binary` 2, `binary_session` 1, `binary_overview` 1, `search_strings` 2 (zaman aşımına düşen), 1 `rea inspect` CLI çağrısı |
| Kodda değişiklik | 458 satır eklendi (ajanın kendi yazdığı geçici sürücü/betikler; repoya girmedi) |

**Takıldığı yerler (ajanın kendi kaydından):**
1. REA'nın varsayılan **330 sn Ghidra başlangıç süresi** bu binary için (1.8 MB `.text`, 9116 fonksiyon) yetmedi, iki çağrı düştü. Ortam değişkeni çalışan MCP sunucusuna işlemediği için ajan REA MCP sunucusunu kendi alt süreci olarak 90 dk sınırla çalıştıran, dosya kuyruklu bir sürücü yazdı.
2. `--snapshot`'ın analiz veritabanını MCP oturumuna taşıyacağını varsaydı; taşımıyor. Bir tur boşa gitti.
3. Sabit yanlış okundu (1e-5 ↔ 1e-06) → HALLUCINATIONS H5.
4. MANOVA fonksiyonu ANOVA sanıldı → HALLUCINATIONS H6.
5. Formül ayrıştırıcısının ad tablosundan fonksiyon işaretçisi çıkarmayı denedi; çıkmaz sokak.
6. Bir çağrıda yanlış adres girdi.
7. LEDGER.md'yi heredoc ile yazarken kabuk alıntılama hatası aldı, Write aracına geçti.

**Claude Code'un kendi tespiti:** Kullanımın **%73'ü 150k token'ın üzerindeki bağlamda** gerçekleşti; her istek büyüyen geçmişi yeniden taşıdı.

## Oturum 2 — yazım (ölçülmüş, alt ajan kullanım sayaçları)

| Tur | Konu | Toplam token | Araç çağrısı | Süre |
|---|---|---|---|---|
| 1 | SPEC v1.0 → motor + CLI + testler (TDD) | 107,748 | 22 | 7 dk 14 sn |
| 2 | CLI takma adları (CONTRACT.md yayımlanmadığı için) | 118,418 | 6 | 1 dk 51 sn |
| 3 | SPEC v1.1 (diferansiyel test bulguları) | 149,760 | 16 | 4 dk 33 sn |
| 4 | MCP adaptörü | 177,031 | 14 | 5 dk 49 sn |
| 5 | Hocanın CONTRACT.md'sine uyum (CLI/MCP yeniden; engine'e dokunulmadı) | 230,108 | 23 | 8 dk 48 sn |

Not: Alt ajan sayaçları önbellek kırılımı vermiyor; "toplam token" bağlamdaki toplam boyutu yansıtır. Her tur aynı oturumun devamı olduğu için bağlam birikiyor.

**Kod iterasyonu:** Tur 1'de motor tek seferde yazıldı ve SPEC v1.0'a göre ilk denemede yeşile döndü; oracle'a uydurma amaçlı düzeltme gerekmedi. Tek gerçek düzeltme döngüsü tur 3 oldu: diferansiyel test 4 uyuşmazlık buldu → SPEC v1.1 → motor düzeltildi.

## Koordinatör ve insan emeği (yaklaşık)

| İş | Süre |
|---|---|
| Kurulum (G*Power, Node, JDK 21, Ghidra 12.1.4, REA, Claude Code bağlantısı) | ~50 dk (insan + koordinatör) |
| G*Power kâhini: 50 vektör, 50 ekran görüntüsü | ~1.5 sa (insan) |
| Diferansiyel test düzeneği + 570 kütüphane vektörü | koordinatör; tam koşu ~5 dk (paralel) |

## AI ajanı (bonus katmanı) — ölçülmüş

`agent/EVAL_REPORT.md`, `agent/EVAL_RESULTS.json`. MCP ve GUI yollarının token, süre ve doğruluk karşılaştırması orada.

---

## Neyi farklı yapardık

1. **İncelemeyi kısa oturumlara bölmek.** Kullanımın %73'ü 150k+ bağlamdaydı. "Dizeler → hesap motoru → çözücü → doğrulama" gibi 3–4 ayrı oturum, her biri bir önceki oturumun LEDGER'ıyla başlasa, aynı bulguları çok daha az önbellek okumasıyla verirdi.
2. **REA zaman aşımını baştan ayarlamak.** `REA_GHIDRA_STARTUP_TIMEOUT_MS` kayıt sırasında (`.claude.json` → `mcpServers.rea.env`) verilseydi ajanın kendi sürücüsünü yazmasına gerek kalmazdı. Bu, oturumun en pahalı sapmasıydı.
3. **Kâhini incelemeden ÖNCE toplamak.** Oturum 1 bittiğinde kâhin değerleri henüz yoktu, bu yüzden `[AJAN]` iddialarını (L48 gibi) orada sınayamadı. Önce kâhin toplansaydı H1/H2 inceleme oturumunda yakalanırdı.
4. **`[AJAN]` etiketli kuralları SPEC'te "geçici" diye işaretlemek.** H1, `[AJAN]` düzeyindeki bir iddianın SPEC'e kesin kural gibi geçmesinden doğdu. Yazım ajanına "kâhin değeri olmayan senaryoyu bağlayıcı sayma" demek H4'ü önlerdi.
5. **Doğru işe doğru model.** Sınıflandırma (test ailesi seçimi) için hızlı/ucuz bir model (Haiku sınıfı) yeterli; derin akıl yürütme yalnızca spec çıkarmak ve kanıt yorumlamak için gerekli. Hesap ise hiç LLM gerektirmiyor (CLI/MCP).
6. **CONTRACT.md'yi ilk gün istemek.** Sözleşme geç yayımlandı. Biz de beklerken CLI'ye "her yazımı kabul et, bilinmeyeni yok say" katmanı ekledik (tur 2). Sözleşme ise tam tersini istiyor: tanınmayan alan `UNKNOWN_PARAM` hatası olmalı. Tur 2 bu yüzden tamamen geri alındı (tur 5). Tahmin edilen bir sözleşmeye yatırım yapmak yerine sözleşme yalnızca bir adaptörde toplandı. Bu tasarım sayesinde değişiklik motora dokunmadan iki dosyada kaldı.
