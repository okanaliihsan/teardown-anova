# 60 saniyelik CLI demosu — senaryo

Ders slaytı 18: *"CLI koşunuzun ekran kaydı aynı zamanda demo videonuzdur."* Video yalnızca terminali gösterir, seslendirme gerekmez. Her komut bir kural gösterir; parantez içindeki kâhin kimliği, aynı girdinin G*Power ekran görüntüsüdür (`oracle/screenshots/`).

Windows'ta **Anaconda Prompt** içinde, repo kökünde:

```bat
gpower-clone --version

:: 1) Kılavuz örneği — G*Power ile aynı: N = 390, kritik F 1.9045377, güç 0.9523634   (A01)
gpower-clone --test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --power 0.95 --groups 10

:: 2) Gizli kural: N, k'nın katına yuvarlanır → 158 değil 159   (A02)
gpower-clone --test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --power 0.80 --groups 3

:: 3) Post hoc, N k'ya bölünmüyor → hesap yapılır + G*Power'ın uyarısı   (P02)
gpower-clone --test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --n_total 100 --groups 3

:: 4) Sınır: güç < α → G*Power'ın hata metni + sözleşme kodu INCONSISTENT, çıkış kodu 2   (A22)
gpower-clone --test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --power 0.04 --groups 3

:: 5) Sözleşme kontrolü: post-hoc'ta --power moda ilgisiz → UNKNOWN_PARAM
gpower-clone --test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --power 0.8 --groups 3

:: 6) Uyum raporunun özeti
type tests\UYUM_RAPORU.md | more
```

Kayıt (Windows 10/11): Anaconda Prompt penceresi seçiliyken **Windows + Alt + R** (Xbox Game Bar) kaydı başlatır ve durdurur. Video `Videolar\Yakalamalar` klasörüne düşer.
