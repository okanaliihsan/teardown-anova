# İncelenen binary (konfigürasyon yönetimi)

Sommerville Böl. 7.3: "Hangi sürümü söktün? Dosya hash'ini kaydet."

| Alan | Değer |
|---|---|
| Ürün | G*Power 3.1.9.7 (Windows) — Help → About ekranı: `docs/gpower_about.png` |
| Kaynak | Yalnızca resmi sayfa: psychologie.hhu.de, G*Power sayfası (zip, ~20 MB) |
| Dosya | `GPowerNT.exe` (zip içindeki klasör: `GPower_3.1.9.7_143`) |
| SHA-256 | `C63E6A133EB6372932F810C08CC33DC35A06D1DDB658F897BD6C34A754EFC812` |
| Hash komutu | `Get-FileHash <yol>\GPowerNT.exe -Algorithm SHA256` (PowerShell) |
| Platform notu | [DOK] Resmi sayfa: Windows sürümü Microsoft Visual C++ çalışma zamanına ihtiyaç duyar ve `VC_redist.x86.exe` ile gelir → 32-bit (x86) native uygulama. Host (inceleme makinesi) Windows x64. |

Not: Ödev metni dosyayı `GPower.exe` diye anıyor; 3.1.9.7 zip'inde çalıştırılabilir dosyanın adı `GPowerNT.exe`. Binary repoya konmaz (`.gitignore`: `*.exe`).
