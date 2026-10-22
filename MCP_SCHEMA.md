# MCP_SCHEMA.md — `anova-power-clone` MCP sunucusu (sözleşme v1.0.0)

Hocanın CLI sözleşmesinin (CONTRACT.md v1.0.0; özet `CONTRACT_NOTES.md`) MCP bonus
katmanı. Tek araç: **`power_analysis`**. Hesap mantığı MCP katmanında yoktur:

```
mcp_server.call_tool  ─┐
                       ├─> cli.run(params) ─> sözleşme doğrulaması ─> engine.a_priori / post_hoc
cli.main (argv→dict) ──┘
```

CLI ile MCP aynı `cli.run` fonksiyonunu çağırır. Bu yüzden aynı girdide CLI'nin stdout
satırı ile MCP'nin `content[0].text` değeri **bayt bayt aynıdır**. Bunu
`tests/test_mcp.py` doğrular: 50 oracle vektörü, 5 sözleşme referans vektörü ve her hata
kodundan en az bir vaka.

- **Taşıma:** stdio, JSON-RPC 2.0, satır başına bir JSON mesajı (UTF-8). stdout
  yalnızca protokol içindir.
- **Başlatma:** `python -m anova_clone.mcp_server`, ya da paket kurulmadan çalışan
  `anova-mcp` (Unix) / `anova-mcp.cmd` (Windows).
- **Sunucu bilgisi:** `serverInfo = {"name":"anova-power-clone","version":"1.1.0"}`,
  `capabilities = {"tools":{}}`. `protocolVersion` istemcininki yankılanır; yoksa
  `2025-06-18`.
- **Yöntemler:** `initialize`, `notifications/initialized` (yanıt yok), `ping`,
  `tools/list`, `tools/call`.

## Araç: `power_analysis`

### Girdi (`inputSchema`)

`test` ve `mode` zorunludur. Diğer alanlar moda göre gereklidir. Moda ilgisiz bir alan
verilirse `UNKNOWN_PARAM` döner. Değeri `null` olan alan verilmemiş sayılır.

| Alan | Tip | a-priori | post-hoc | Açıklama / §5 aralığı |
|---|---|---|---|---|
| `test` | string | zorunlu | zorunlu | Yalnızca `anova-oneway`. Başka değer → `UNSUPPORTED` |
| `mode` | string | `a-priori` | `post-hoc` | `compromise` / `criterion` / `sensitivity` / diğer → `UNSUPPORTED` |
| `f` | number | gerekli | gerekli | Cohen's f (küçük .10, orta .25, büyük .40); f > 0; motor ayrıca f ≤ 50 ister |
| `alpha` | number | gerekli | gerekli | (0, 1); motor ayrıca [1e-07, 0.9999999] ister |
| `power` | number | gerekli | **verilmemeli** | (0, 1); power ≥ alpha olmalı (eşitlik kabul edilir) |
| `groups` | number | gerekli | gerekli | Tam sayı, ≥ 2 (3.0 kabul edilir, 2.5 → `INVALID_VALUE`) |
| `n_total` | number | **verilmemeli** | gerekli | Tam sayı, ≥ 2 ve > groups |

Sayılar JSON number ya da sayısal string ("0.25") olarak verilebilir; ondalık ayırıcı
noktadır. `true`, `false`, `"abc"`, `NaN` ve sonsuz değerler → `INVALID_VALUE`.

### Başarı çıktısı

`content[0].text` CLI stdout'u ile aynı tek satır JSON'dur. `structuredContent` aynı
sözlüktür ve `isError: false` döner. Sayılar **yuvarlanmadan**, tam double olarak yazılır.

| Alan | Tip | a-priori | post-hoc | Açıklama |
|---|---|---|---|---|
| `ncp` | number | ✓ | ✓ | Noncentrality λ = f²·N |
| `critical_f` | number | ✓ | ✓ | Kritik F = F⁻¹(1−α; df1, df2) |
| `df1` | integer | ✓ | ✓ | k − 1 |
| `df2` | integer | ✓ | ✓ | N − k |
| `n_total` | integer | ✓ | ✓ (ek) | Toplam N; a priori'de k'nın katı |
| `actual_power` | number | ✓ | — | Yuvarlanmış N ile gerçek güç |
| `power` | number | — | ✓ | Ulaşılan güç |
| `n_per_group` | integer / null | ✓ (ek) | ✓ (ek) | N / k; bölünmüyorsa `null` |
| `warning` | string | — | yalnızca N k'nın katı değilse | G*Power uyarı metni (CLI bunu stderr'e de yazar) |

### Hata çıktısı

`isError: true` döner; `content[0].text` CLI'nin hata satırıyla aynıdır:
`{"error": "<mesaj>", "code": "<KOD>", "field": "<alan ya da null>"}`.

| Alan | Tip | Açıklama |
|---|---|---|
| `error` | string | İnsan okunur mesaj (G*Power'ın da reddettiği durumlarda G*Power metni) |
| `code` | string | Sözleşme hata kodu (aşağıdaki tablo) |
| `field` | string / null | Sorunlu sözleşme alanı; `NO_SOLUTION` ve konumsal argümanda `null` |

| `code` | Ne zaman | CLI çıkış kodu |
|---|---|---|
| `MISSING_PARAM` | `test`, `mode` ya da moda gerekli bir alan eksik | 2 |
| `UNKNOWN_PARAM` | Tanınmayan alan ya da moda ilgisiz alan (ör. post-hoc'ta `power`) | 2 |
| `INVALID_VALUE` | Sayı değil; tam sayı alanında kesirli değer | 2 |
| `OUT_OF_RANGE` | Sözleşme §5 aralığı ya da G*Power aralığı dışında | 2 |
| `INCONSISTENT` | power < alpha (field `power`); post-hoc N ≤ groups (field `n_total`) | 2 |
| `UNSUPPORTED` | Bilinmeyen `test` ya da `mode` | 2 |
| `NO_SOLUTION` | Girdiler geçerli ama çözücü sonuç üretemedi | 1 |

Doğrulama sırası: test/mode → alan kümesi (önce bilinmeyen, sonra eksik) → değer tipi →
§5 aralığı → motor. Mesajlar, G*Power'ın da reddettiği durumlarda G*Power metinleridir
(ör. "Power must be greater than or equal to alpha.").

JSON-RPC protokol hataları (sözleşme hatası değildir):
- Bilinmeyen araç adı ya da nesne olmayan `arguments` → `-32602`
- Bilinmeyen yöntem → `-32601`
- Bozuk JSON → `-32700`
- Geçersiz istek → `-32600`

## Örnekler (gerçek çıktı)

a-priori (sözleşme referans vektörü):
```json
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"power_analysis","arguments":{"test":"anova-oneway","mode":"a-priori","f":0.25,"alpha":0.05,"power":0.95,"groups":5}}}
```
```json
{"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"{\"ncp\":19.0625,\"critical_f\":2.40173969632139,\"df1\":4,\"df2\":300,\"n_total\":305,\"actual_power\":0.9521313274143564,\"n_per_group\":61}"}],"structuredContent":{"ncp":19.0625,"critical_f":2.40173969632139,"df1":4,"df2":300,"n_total":305,"actual_power":0.9521313274143564,"n_per_group":61},"isError":false}}
```

Hata (post-hoc'ta ilgisiz `power` alanı):
```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"power_analysis","arguments":{"test":"anova-oneway","mode":"post-hoc","f":0.25,"alpha":0.05,"power":0.8,"n_total":100,"groups":5}}}
```
```json
{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"{\"error\":\"Unknown or irrelevant parameter for post-hoc: power.\",\"code\":\"UNKNOWN_PARAM\",\"field\":\"power\"}"}],"structuredContent":{"error":"Unknown or irrelevant parameter for post-hoc: power.","code":"UNKNOWN_PARAM","field":"power"},"isError":true}}
```

Aynı post-hoc girdisinin CLI karşılığı:
```
gpower-clone --test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --n_total 100 --groups 5
{"ncp":6.25,"critical_f":2.467493623449646,"df1":4,"df2":95,"power":0.46633120262315364,"n_total":100,"n_per_group":20}
```

## Claude Code'a kayıt

Windows (proje kapsamı):
```
claude mcp add anova-power --scope project -- cmd /c <repo>\anova-mcp.cmd
```
Unix:
```
claude mcp add anova-power --scope project -- <repo>/anova-mcp
```

Proje kökündeki `.mcp.json` göreli yol kullanır; Claude Code sunucuyu proje kökünden
başlatır:
```json
{
  "mcpServers": {
    "anova-power": {
      "type": "stdio",
      "command": "cmd",
      "args": ["/c", "anova-mcp.cmd"],
      "env": {}
    }
  }
}
```
Unix'te `"command": "./anova-mcp", "args": []` kullanılır.
