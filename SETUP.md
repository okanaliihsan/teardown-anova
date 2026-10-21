# Kurulum Rehberi (Windows)

Bu rehber, ödevin "KURULUM (ilk iş)" bölümünü adım adım uygular. Tüm komutlar **PowerShell** içindir.
Her adımın sonunda neyi kontrol edeceğin yazıyor; bir adım hata verirse durup hatayı kaydet (AGENT_COST.md ve süreç günlüğü için de işe yarar).

> Neden Windows? G*Power 3.1.9.7'nin arayüzünden referans değer (kâhin) toplamak zorundayız ve ödev yalnızca Windows sürümünün sökülmesine izin veriyor. REA'nın Ghidra sağlayıcısı Windows x64'te **deneysel** olarak çalışıyor; bu durumu README'de belirteceğiz.

---

## 0. Çalışma klasörleri

```powershell
mkdir C:\tools
mkdir C:\re\gpower        # G*Power binary'sinin sökülecek kopyası (REPO DIŞINDA)
```

**Neden ayrı klasör?** G*Power varsayılan olarak adında `*` ve `( )` geçen bir yola kurulur (`...\G*Power\`). REA'nın Windows sağlayıcısı komut yorumlayıcı karakterleri içeren yolları reddediyor. Ayrıca binary repoya girmemeli (etik kural 2).

---

## 1. G*Power 3.1.9.7

1. **Yalnızca resmi sayfadan** indir: https://www.psychologie.hhu.de/arbeitsgruppen/allgemeine-psychologie-und-arbeitspsychologie/gpower
2. Windows sürümünü (3.1.9.7) kur.
3. `GPower.exe`'yi sökme klasörüne kopyala ve iki dosyanın da hash'ini al:

```powershell
# Kurulum yolunu kendi makinene göre düzelt (Program Files veya Program Files (x86))
$src = Get-ChildItem "C:\Program Files*\G*Power\GPower.exe" | Select-Object -First 1
Copy-Item $src.FullName C:\re\gpower\GPower.exe
Get-FileHash $src.FullName              -Algorithm SHA256
Get-FileHash C:\re\gpower\GPower.exe    -Algorithm SHA256
```

**Kontrol:** İki hash aynı olmalı. Bu değeri README'ye yazacağız → bana gönder.
Ayrıca G*Power'ı açıp **Help → About** ekranının görüntüsünü al (sürüm kanıtı, konfigürasyon yönetimi).

---

## 2. Node.js (22.19+ veya 24.11+)

```powershell
winget install --exact --id OpenJS.NodeJS.LTS
# PowerShell'i kapatıp yeniden aç
node -v
npm -v
```

**Kontrol:** `node -v` en az `v22.19` veya `v24.11` göstermeli.

---

## 3. JDK 21 (64-bit, tam JDK)

```powershell
winget install --exact --id EclipseAdoptium.Temurin.21.JDK
# PowerShell'i kapatıp yeniden aç
java -version
javac -version
```

**Kontrol:** İkisi de `21.x` göstermeli. Kurulum yolunu not et (genelde `C:\Program Files\Eclipse Adoptium\jdk-21...`).

---

## 4. Ghidra 12.1.4

REA **tam olarak** Ghidra 12.1.4 sürümünü istiyor; başka sürüm `rea doctor` kontrolünden geçmez.

1. https://ghidra-sre.org adresinden (GitHub releases sayfasına yönlendirir) `ghidra_12.1.4_PUBLIC_*.zip` dosyasını indir.
2. `C:\tools\` içine çıkar → sonuç: `C:\tools\ghidra_12.1.4_PUBLIC\`

**Kontrol:** `C:\tools\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat` dosyası var olmalı.

---

## 5. Ortam değişkenleri (kalıcı)

```powershell
# JDK yolunu 3. adımda not ettiğinle değiştir
setx GHIDRA_INSTALL_DIR "C:\tools\ghidra_12.1.4_PUBLIC"
setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-21.0.X-hotspot"
setx REA_ANALYSIS_PROVIDER "ghidra"
# PowerShell'i kapatıp yeniden aç
```

---

## 6. Claude Code (ajan)

```powershell
irm https://claude.ai/install.ps1 | iex
```

Proje klasöründe (`git clone` ettiğin repo) `claude` yazıp oturum aç. Ücretli bir Claude aboneliği veya API hesabı gerekir.
Claude Code kullanamıyorsan Codex, Gemini CLI veya Cursor da REA ile çalışıyor; o zaman bana hangisini kullandığını söyle, komutları ona göre düzenlerim.

---

## 7. REA

**Uyarı:** Sahte paketler dolaşıyor. Yalnızca `github.com/morluto/rea`, `rea.tools` ve npm'deki `rea-agents` paketi.

```powershell
npm install --global rea-agents
rea doctor --provider ghidra --json
rea providers --json
```

**Kontrol:** `doctor` çıktısında `"healthy": true` görmelisin. Ghidra sürümü, `analyzeHeadless.bat`, `java.exe`, `javac.exe` ve JDK 21 kontrolleri geçmeli.
Hata alırsan çıktının tamamını bana gönder.

Ardından binary'yi tek başına test et:

```powershell
rea inspect "C:\re\gpower\GPower.exe" --provider ghidra --format json > C:\re\gpower\inspect.json
```

> `inspect.json` dosyasını **bana gönderme ve repoya koyma.** Temiz oda kuralı: yazım oturumu Ghidra çıktısını görmemeli. Sadece "çalıştı / hata verdi" bilgisini ve hata mesajını paylaş.

---

## 8. REA'yı Claude Code'a bağla

Önce otomatik kurulumu dene (PowerShell betik engeli varsa `npx` yerine `npx.cmd` yaz):

```powershell
npx rea-agents@latest setup --client claude_code
npx -y rea-agents@latest doctor --client claude_code --json
```

Otomatik kayıt Windows'ta çalışmazsa elle ekle (repo klasöründeyken):

```powershell
claude mcp add rea --scope project `
  -e REA_ANALYSIS_PROVIDER=ghidra `
  -e GHIDRA_INSTALL_DIR="C:\tools\ghidra_12.1.4_PUBLIC" `
  -e JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-21.0.X-hotspot" `
  -- cmd /c npx -y rea-agents@latest mcp
```

Claude Code'u yeniden başlat.

---

## 9. Hocanın istediği kontrol (README'ye girecek)

Claude Code içinde **aynen** şunu sor:

> REA araçları ve Ghidra sağlayıcısı bu oturumda kullanılabilir mi?

Cevabın ekran görüntüsünü `docs/rea_check.png` olarak kaydet.

---

## Bana göndereceklerin (kurulum sonunda)

- [ ] GPower.exe SHA-256 hash'i
- [ ] Help → About ekran görüntüsü (sürüm)
- [ ] `rea doctor --provider ghidra --json` çıktısı (ya da hatası)
- [ ] `docs/rea_check.png`
- [ ] Hangi ajanı kullandığın (Claude Code / diğer)
