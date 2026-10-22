# AI Ajanı Değerlendirme Raporu

Bu dosya `python agent/run_eval.py` ile üretilir. Ham kayıtlar: `agent/logs/`.

Ajan: Claude Code (headless `claude -p`) + `anova-power` MCP sunucusu + `agent/AGENT_PROMPT.md`.
GUI yolu: aynı ajan, MCP olmadan, yalnızca G*Power ekran görüntülerini okuyarak (en az 1–2 görüntü). Gerçek bir 'computer use' oturumu her tıklamada ek görüntü alacağı için bu, GUI maliyetinin **alt sınırıdır**.

## Özet

| Yol | Dil | Soru | Doğru etiket | Doğru cevap | Ort. girdi tok. | Ort. önbellek oku | Ort. önbellek yaz | Ort. çıktı tok. | Ort. süre (sn) | Toplam maliyet tahmini (USD) |
|---|---|---|---|---|---|---|---|---|---|---|
| GUI | en | 10 | 10/10 | 9/10 | 4 | 25,340 | 9,025 | 448 | 9.0 | 1.1414 |
| GUI | tr | 10 | 10/10 | 9/10 | 4 | 25,160 | 8,825 | 508 | 10.1 | 1.1356 |
| MCP | en | 10 | 10/10 | 10/10 | 5 | 36,957 | 7,748 | 427 | 9.2 | 1.0667 |
| MCP | tr | 10 | 10/10 | 10/10 | 5 | 35,662 | 8,522 | 434 | 9.1 | 1.1391 |

### MCP ile GUI karşılaştırması (en, aynı 10 soru)

| Ölçü (soru başına ortalama) | MCP | GUI (ekran görüntüsü) | GUI / MCP |
|---|---|---|---|
| Toplam işlenen token | 45,138 | 34,817 | 0.77× |
| Yeni (önbelleksiz) girdi token | 7,754 | 9,029 | 1.16× |
| Süre (sn) | 9.2 | 9.0 | 0.98× |
| Doğru cevap | 10/10 | 9/10 | |

Her iki yolda da Claude Code'un kendi sistem istemi ve araç tanımları aynı sabit maliyeti ekler; fark ekran görüntüsü okumaktan ve ek turlardan gelir. GUI yolu gerçek tıklama yapmadığı için alt sınırdır.

### MCP ile GUI karşılaştırması (tr, aynı 10 soru)

| Ölçü (soru başına ortalama) | MCP | GUI (ekran görüntüsü) | GUI / MCP |
|---|---|---|---|
| Toplam işlenen token | 44,622 | 34,497 | 0.77× |
| Yeni (önbelleksiz) girdi token | 8,527 | 8,829 | 1.04× |
| Süre (sn) | 9.1 | 10.1 | 1.11× |
| Doğru cevap | 10/10 | 9/10 | |

Her iki yolda da Claude Code'un kendi sistem istemi ve araç tanımları aynı sabit maliyeti ekler; fark ekran görüntüsü okumaktan ve ek turlardan gelir. GUI yolu gerçek tıklama yapmadığı için alt sınırdır.

## Güven kalibrasyonu (etiket seçimi)

| Güven aralığı | Seçim sayısı | Doğru | Oran |
|---|---|---|---|
| [0.00, 0.75) | 2 | 2 | 100% |
| [0.75, 0.90) | 0 | 0 | 0% |
| [0.90, 1.00] | 38 | 38 | 100% |

## Soru bazında

| Yol | Dil | Soru | Beklenen etiket | Ajanın etiketi (güven) | Araç çağrısı | Parametre | Cevap | Toplam token | Süre (sn) |
|---|---|---|---|---|---|---|---|---|---|
| GUI | en | Q01 | anova-oneway | anova-oneway (0.95) | Read, Read | — | ✅ | 36,675 | 9.5 |
| GUI | en | Q02 | anova-oneway | anova-oneway (0.95) | Read, Read | — | ✅ | 36,690 | 7.0 |
| GUI | en | Q03 | anova-oneway | anova-oneway (0.95) | Read, Read | — | ✅ | 36,701 | 6.8 |
| GUI | en | Q04 | anova-oneway | anova-oneway (0.95) | Read, Read | — | ✅ | 36,731 | 6.7 |
| GUI | en | Q05 | anova-oneway | anova-oneway (0.95) | Read, Read | — | ✅ | 36,811 | 7.0 |
| GUI | en | Q06 | anova-oneway | anova-oneway (0.95) | Read, Read | — | ✅ | 37,060 | 10.7 |
| GUI | en | Q07 | anova-oneway | anova-oneway (0.95) | Read, Read | — | ✅ | 36,867 | 8.5 |
| GUI | en | Q08 | anova-oneway | anova-oneway (0.97) | Read | — | ✅ | 36,190 | 9.2 |
| GUI | en | Q09 | t2-indep | t2-indep (0.97) | — | — | ✅ | 17,823 | 10.0 |
| GUI | en | Q10 | ambiguous | ambiguous (0.9) | Read | — | ❌ | 36,620 | 14.9 |
| GUI | tr | Q01 | anova-oneway | anova-oneway (0.97) | Read, Read | — | ✅ | 36,409 | 9.3 |
| GUI | tr | Q02 | anova-oneway | anova-oneway (0.95) | Read, Read | — | ✅ | 36,330 | 7.5 |
| GUI | tr | Q03 | anova-oneway | anova-oneway (0.97) | Read, Read | — | ✅ | 36,515 | 11.1 |
| GUI | tr | Q04 | anova-oneway | anova-oneway (0.95) | Read, Read | — | ✅ | 36,399 | 8.1 |
| GUI | tr | Q05 | anova-oneway | anova-oneway (0.95) | Read, Read | — | ✅ | 36,435 | 8.1 |
| GUI | tr | Q06 | anova-oneway | anova-oneway (0.95) | Read, Read | — | ✅ | 36,731 | 11.4 |
| GUI | tr | Q07 | anova-oneway | anova-oneway (0.95) | Read, Read | — | ✅ | 36,626 | 8.9 |
| GUI | tr | Q08 | anova-oneway | anova-oneway (0.97) | Read | — | ✅ | 35,781 | 9.3 |
| GUI | tr | Q09 | t2-indep | t2-indep (0.95) | — | — | ✅ | 17,691 | 14.4 |
| GUI | tr | Q10 | ambiguous | ambiguous (0.45) | Read | — | ❌ | 36,056 | 12.7 |
| MCP | en | Q01 | anova-oneway | anova-oneway (0.97) | ToolSearch, power_analysis | ✅ | ✅ | 51,858 | 9.7 |
| MCP | en | Q02 | anova-oneway | anova-oneway (0.95) | ToolSearch, power_analysis | ✅ | ✅ | 52,047 | 9.5 |
| MCP | en | Q03 | anova-oneway | anova-oneway (0.95) | ToolSearch, power_analysis | ✅ | ✅ | 52,041 | 7.8 |
| MCP | en | Q04 | anova-oneway | anova-oneway (0.95) | ToolSearch, power_analysis | ✅ | ✅ | 52,154 | 10.6 |
| MCP | en | Q05 | anova-oneway | anova-oneway (0.97) | ToolSearch, power_analysis | ✅ | ✅ | 52,198 | 10.3 |
| MCP | en | Q06 | anova-oneway | anova-oneway (0.95) | ToolSearch, power_analysis | ✅ | ✅ | 52,259 | 10.4 |
| MCP | en | Q07 | anova-oneway | anova-oneway (0.95) | ToolSearch, power_analysis | ✅ | ✅ | 52,401 | 10.3 |
| MCP | en | Q08 | anova-oneway | anova-oneway (0.97) | ToolSearch, power_analysis | ✅ | ✅ | 52,419 | 9.4 |
| MCP | en | Q09 | t2-indep | t2-indep (0.95) | — | — | ✅ | 17,089 | 9.1 |
| MCP | en | Q10 | ambiguous | ambiguous (0.6) | — | — | ✅ | 16,914 | 5.3 |
| MCP | tr | Q01 | anova-oneway | anova-oneway (0.95) | ToolSearch, power_analysis | ✅ | ✅ | 51,379 | 9.1 |
| MCP | tr | Q02 | anova-oneway | anova-oneway (0.97) | ToolSearch, power_analysis | ✅ | ✅ | 51,414 | 8.4 |
| MCP | tr | Q03 | anova-oneway | anova-oneway (0.97) | ToolSearch, power_analysis | ✅ | ✅ | 51,381 | 8.0 |
| MCP | tr | Q04 | anova-oneway | anova-oneway (0.95) | ToolSearch, power_analysis | ✅ | ✅ | 51,586 | 10.2 |
| MCP | tr | Q05 | anova-oneway | anova-oneway (0.96) | ToolSearch, power_analysis | ✅ | ✅ | 51,580 | 8.4 |
| MCP | tr | Q06 | anova-oneway | anova-oneway (0.95) | ToolSearch, power_analysis | ✅ | ✅ | 51,704 | 12.9 |
| MCP | tr | Q07 | anova-oneway | anova-oneway (0.95) | ToolSearch, power_analysis | ✅ | ✅ | 51,790 | 10.3 |
| MCP | tr | Q08 | anova-oneway | anova-oneway (0.95) | ToolSearch, power_analysis | ✅ | ✅ | 51,780 | 10.0 |
| MCP | tr | Q09 | t2-indep | t2-indep (0.95) | — | — | ✅ | 16,839 | 7.6 |
| MCP | tr | Q10 | ambiguous | ambiguous (0.9) | — | — | ✅ | 16,770 | 6.1 |

## Ajanın hesap yapmadığının kanıtı

MCP yolunda her sayısal cevap, logdaki `tool_result` içinde motorun döndürdüğü JSON'la eşleşir; ajan istemi (AGENT_PROMPT.md, kural 1) araç çağırmadan sayı yazmayı yasaklar, ve `Bash` dahil hesap yapabilecek tüm araçlar `--disallowedTools` ile kapalıdır.
