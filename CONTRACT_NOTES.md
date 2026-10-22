# Hocanın CLI sözleşmesi (CONTRACT.md v1.0.0) — anova-oneway için özet

Kaynak: https://gist.github.com/seyyah/08d3e031781d853b17366be8ba264211 (sözleşme 22.10.2026'da alındı). Bu dosya, sözleşmenin bu repoyu ilgilendiren kısmının özetidir; bağlayıcı olan gist'teki metindir.

## Çağrı
`gpower-clone --test <TEST_ID> --mode <MODE_ID> [--<alan> <değer> ...]`
- Alan adları alt çizgili: `--n_total`, `--beta_alpha_ratio`.
- Moda gerekli her alan açıkça verilmeli; varsayılan yok → eksikse `MISSING_PARAM`.
- Tanınmayan alan **veya moda ilgisiz alan** (ör. post-hoc'ta `--power`) → `UNKNOWN_PARAM`.
- Ondalık ayırıcı her zaman nokta; locale'den bağımsız. Ağ yok. Deterministik. Her çağrı ≤ 2 sn.
- stdout: yalnızca tek satır JSON. Log/uyarı/ilerleme → stderr.
- Çıkış kodu: 0 başarı, 2 geçersiz girdi, 1 iç hata (hesap başarısız).
- `--version` → `{"contract_version": "1.0.0", "name": "<takım-adı>", "engine": "<dil ve sürüm>"}`

## anova-oneway
| Mod | Girdi | Çıktı |
|---|---|---|
| a-priori | f, alpha, power, groups | ncp, critical_f, df1, df2, n_total, actual_power |
| post-hoc | f, alpha, n_total, groups | ncp, critical_f, df1, df2, power |
| compromise (bonus) | f, beta_alpha_ratio, n_total, groups | ncp, critical_f, df1, df2, alpha, beta, power |
| criterion (bonus) | f, power, n_total, groups | ncp, critical_f, df1, df2, alpha |
| sensitivity (bonus) | alpha, power, n_total, groups | ncp, critical_f, df1, df2, f |

Başarı: sayılar tam double hassasiyet (yuvarlama YOK); n_total/df1/df2 JSON tam sayı. Ek anahtarlar serbest (düzenek yok sayar).

Referans vektörler (sözleşme §9, anova-oneway):
| Mod | Girdi | Beklenen |
|---|---|---|
| a-priori | f .25, α .05, power .95, groups 5 | ncp 19.0625000, critical_f 2.4017397, df1 4, df2 300, n_total 305, actual_power 0.9521313 |
| post-hoc | f .25, α .05, n_total 100, groups 5 | ncp 6.2500000, critical_f 2.4674936, df1 4, df2 95, power 0.4663312 |
| compromise | f .25, beta_alpha_ratio 1, n_total 100, groups 5 | ncp 6.25, critical_f 1.4272492, df1 4, df2 95, alpha 0.2309247, beta 0.2309247, power 0.7690753 |
| criterion | f .25, power .95, n_total 100, groups 5 | ncp 6.25, critical_f 0.6552638, df1 4, df2 95, alpha 0.6245994 |
| sensitivity | α .05, power .95, n_total 100, groups 5 | ncp 19.5245874, critical_f 2.4674936, df1 4, df2 95, f 0.4418664 |

## Hata
`{"error": "<mesaj>", "code": "<KOD>", "field": "<alan>"}` (stdout, tek satır)
- MISSING_PARAM: moda gerekli alan yok
- UNKNOWN_PARAM: alan tanınmıyor ya da moda ilgisiz
- INVALID_VALUE: sayı değil, ya da tam sayı gereken yerde ondalık
- OUT_OF_RANGE: §5 aralık dışı
- INCONSISTENT: tek tek geçerli, birlikte anlamsız (örnek: "Power, alpha değerinden büyük olmalı", field power)
- UNSUPPORTED: bilinmeyen --test veya --mode
- NO_SOLUTION: girdiler geçerli ama G*Power sonuç üretemez

§5 aralıklar: alpha (0,1); power (0,1); f > 0; beta_alpha_ratio > 0; n_total tam sayı ≥ 2; groups tam sayı ≥ 2. Aralık dışı → OUT_OF_RANGE. Aralık içindeki değerleri G*Power'ın kabul edip etmediği takımın keşfidir.

## Puanlama
- Tam sayı alanlar tam eşleşme; ondalık alanlar mutlak ya da bağıl fark ≤ 1e-6.
- Hata vektörleri: `error` alanı + sıfırdan farklı çıkış kodu; `code` eşleşirse ek puan.
- Kapı: gizli a-priori vektörlerde N alanlarının ≥ %90'ı tam eşleşmeli.

## MCP (bonus)
- Tek araç: `power_analysis`. Girdi şeması CLI ile aynı alan adları; `test`, `mode` zorunlu; diğerleri moda göre.
- Çıktı: CLI stdout'u ile aynı JSON, text content. Hatada aynı hata JSON'u.
- Hesap mantığı MCP'ye kopyalanmaz. CLI ↔ MCP eşdeğerlik testi zorunlu (referans vektörlerin hepsinde).

## Ajan (bonus)
- MCP aracını çağırır, hesap yapmaz.
- Her araç çağrısı `logs/agent_calls.jsonl`'e satır başına bir JSON: `ts` (ISO 8601, ofsetli), `question`, `tool_input` (nesne), `tool_output` (nesne), `tokens_in`, `tokens_out`.
- Yalnızca kurgusal senaryolar.
- "Orta" gibi sözel etki büyüklüğünde sessizce varsayım yapılmaz; varsayım açıkça söylenir ya da sorulur.
