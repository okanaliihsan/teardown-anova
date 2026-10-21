# Kurulum (Windows 11 x64) — gerçekte uygulanan adımlar

Bu dosya, ödevin "KURULUM (ilk iş)" bölümünün bu repoda **nasıl yapıldığını** kaydeder (Sommerville Böl. 7.3: konfigürasyon yönetimi, host-target geliştirme). Komutlar PowerShell içindir.

## Ortam özeti

| Bileşen | Sürüm | Not |
|---|---|---|
| Host | Windows x64 | REA Ghidra sağlayıcısı Windows'ta deneysel |
| Hedef binary | G*Power 3.1.9.7, `GPowerNT.exe` | 32-bit (x86) Visual C++ uygulaması; SHA-256 → `docs/BINARY.md` |
| Node.js | 24.21.0 | |
| npm | 11.19.0 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` gerekti |
| JDK | Temurin 21.0.12 (64-bit) | Makinedeki Java 24 silinmedi; `JAVA_HOME` 21'i gösteriyor |
| Ghidra | 12.1.4 PUBLIC | REA tam bu sürümü istiyor |
| REA | rea-agents 6.7.0 | Kanıt: `docs/rea_doctor_ghidra.json` |
| Ajan | Claude Code 2.1.299 | REA kaydı `rea setup --client claude_code` ile |

## 1. G*Power

1. Yalnızca resmi sayfadan (psychologie.hhu.de, G*Power sayfası) Windows zip'i indirildi.
2. Kurulum programı yok: zip çıkarıldı, `GPowerNT.exe` çalıştırıldı (gerekirse `VC_redist.x86.exe`).
3. Help → About → `docs/gpower_about.png`.
4. Hash:
   ```powershell
   Get-FileHash "<klasör>\GPowerNT.exe" -Algorithm SHA256
   ```

> Dikkat: Klasör yolunda `*`, boşluk veya parantez olmamalı; REA'nın Windows sağlayıcısı bu tür karakterli yolları reddedebiliyor. G*Power ve Ghidra bu yüzden `Desktop\re\` altına çıkarıldı.

## 2. Node.js, npm, JDK 21

```powershell
node -v                                              # 22.19+ veya 24.11+
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned  # npm.ps1 engeli için
winget install --exact --id EclipseAdoptium.Temurin.21.JDK
```

## 3. Ghidra 12.1.4

`github.com/NationalSecurityAgency/ghidra/releases` → `ghidra_12.1.4_PUBLIC_*.zip` → `Desktop\re\` altına çıkarıldı.

## 4. Ortam değişkenleri

```powershell
setx GHIDRA_INSTALL_DIR "C:\Users\<kullanıcı>\Desktop\re\ghidra_12.1.4_PUBLIC"
setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
setx REA_ANALYSIS_PROVIDER "ghidra"
```

## 5. REA

Yalnızca resmi paket: npm `rea-agents` (github.com/morluto/rea, rea.tools).

```powershell
npm install --global rea-agents
rea doctor --provider ghidra --json      # ghidra-* kontrollerinin hepsi ok:true
rea setup --client claude_code           # MCP kaydı + REA skill'i
```

## 6. Doğrulama (ödev isteri)

Claude Code içinde: *"REA araçları ve Ghidra sağlayıcısı bu oturumda kullanılabilir mi?"* → `docs/rea_check.png`.
