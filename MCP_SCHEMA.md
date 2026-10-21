# MCP_SCHEMA.md — `anova-power-clone` MCP sunucusu

Tek yönlü sabit etkili ANOVA omnibus güç analizi motorunu (`src/anova_clone/engine.py`)
MCP aracı olarak sunan ince adaptör. Hesap mantığı MCP katmanında **yoktur**:
`mcp_server.py` → `cli.run()` → `engine.a_priori / engine.post_hoc`. JSON biçimi
(alan adları, sıra, 7 ondalık, hata metni) CLI ile paylaşılan `cli.result_to_dict` /
`cli.error_to_dict` fonksiyonlarından gelir; bu yüzden aynı girdide CLI ve MCP **aynı
satırı** üretir (`tests/test_mcp.py`, 50 oracle vektörü).

- Taşıma: stdio, JSON-RPC 2.0, satır başına bir JSON mesajı (UTF-8). stdout yalnızca
  protokol içindir.
- Başlatma: `python -m anova_clone.mcp_server`, ya da kurulumsuz sarmalayıcılar
  `anova-mcp` (Unix) / `anova-mcp.cmd` (Windows).
- Sunucu: `serverInfo = {"name": "anova-power-clone", "version": "1.1.0"}`,
  `capabilities = {"tools": {}}`. `protocolVersion` istemcininki yankılanır; yoksa
  `2025-06-18`.
- Yöntemler: `initialize`, `notifications/initialized` (yanıt yok), `ping`,
  `tools/list`, `tools/call`.

## Araçlar

### `anova_oneway_a_priori`
Hedef güce ulaşmak için gereken toplam örneklem büyüklüğünü hesaplar.

| Girdi | Tip | Gerekli | Açıklama |
|---|---|---|---|
| `f` | number | evet | Cohen's f etki büyüklüğü (küçük .10, orta .25, büyük .40); aralık [1e-06, 50] |
| `alpha` | number | evet | Anlamlılık düzeyi α; aralık [1e-07, 0.9999999] |
| `power` | number | evet | Hedef güç 1−β; aralık [1e-07, 0.9999999], ≥ alpha |
| `groups` | number | evet | Grup sayısı k ≥ 2; kesirliyse en yakın tam sayıya yuvarlanır (.5 yukarı) |

### `anova_oneway_post_hoc`
Verilen toplam örneklemle ulaşılan istatistiksel gücü hesaplar.

| Girdi | Tip | Gerekli | Açıklama |
|---|---|---|---|
| `f` | number | evet | Cohen's f etki büyüklüğü; aralık [0, 50] (f = 0 kabul edilir, güç = α olur) |
| `alpha` | number | evet | Anlamlılık düzeyi α; aralık [1e-07, 0.9999999] |
| `n_total` | number | evet | Toplam örneklem N (tüm gruplar); > groups; kesirliyse yuvarlanır |
| `groups` | number | evet | Grup sayısı k ≥ 2; kesirliyse yuvarlanır |

## Çıktı (her iki araç)

`result.content[0].text` CLI stdout'u ile birebir aynı tek satır JSON'dur;
`result.structuredContent` aynı sözlüktür. Alan sırası tablodaki gibidir.

| Alan | Tip | Açıklama |
|---|---|---|
| `n_total` | integer | Toplam örneklem N (a priori'de k'nın katı) |
| `n_per_group` | integer / null | N / k; N k'ya bölünmüyorsa `null` |
| `actual_power` | number | Güç (a priori'de yuvarlanmış N ile gerçek güç); 7 ondalık |
| `power` | number | `actual_power` ile aynı değer (sözleşme belirsizliği için iki anahtar) |
| `critical` | number | Kritik F = F⁻¹(1−α; df1, df2); 7 ondalık |
| `df1` | integer | k − 1 |
| `df2` | integer | N − k |
| `ncp` | number | Noncentrality λ = f²·N; 7 ondalık |
| `warning` | string | Yalnızca post hoc'ta N k'nın katı değilse bulunur |
| `error` | string | Yalnızca geçersiz girdide bulunur (o zaman diğer alanlar yoktur) |

### Hatalar
- **Geçersiz girdi (alan aralığı vb.):** JSON-RPC başarılı yanıt, `isError: true`,
  text `{"error":"--<alan>: <G*Power metni>"}` (CLI ile aynı; alan öneki CLI seçenek adıdır).
- **Bilinmeyen araç, eksik ya da sayı olmayan argüman:** JSON-RPC hata `-32602`.
- **Bilinmeyen yöntem:** `-32601`. **Bozuk JSON:** `-32700` (`id: null`).
  **Geçersiz istek:** `-32600`.

## Örnek

İstek:
```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"anova_oneway_a_priori","arguments":{"f":0.25,"alpha":0.05,"power":0.95,"groups":10}}}
```
Yanıt:
```json
{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"{\"n_total\":390,\"n_per_group\":39,\"actual_power\":0.9523634,\"power\":0.9523634,\"critical\":1.9045377,\"df1\":9,\"df2\":380,\"ncp\":24.375}"}],"structuredContent":{"n_total":390,"n_per_group":39,"actual_power":0.9523634,"power":0.9523634,"critical":1.9045377,"df1":9,"df2":380,"ncp":24.375},"isError":false}}
```

Uyarılı post hoc (`n_total: 100, groups: 3`) → `structuredContent.warning`:
`"The total sample size (100) is not a multiple of the number of groups (3). The analysis was based on the average group size."`

Geçersiz girdi (`n_total: 3, groups: 3`):
```json
{"jsonrpc":"2.0","id":4,"result":{"content":[{"type":"text","text":"{\"error\":\"--n: Sample size must be greater than the number of groups (3).\"}"}],"structuredContent":{"error":"--n: Sample size must be greater than the number of groups (3)."},"isError":true}}
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

Proje kökündeki `.mcp.json` (repo ile birlikte gelir; göreli yol, Claude Code proje
kökünden başlatır):
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
