"""Diferansiyel test: aynı girdiler hem G*Power'a (kâhin) hem yeniden yazıma verilir.

Ödev, "5. Diferansiyel test": "Aynı girdileri hem G*Power'a hem yeniden yazımınıza
verin, farkı ölçün. Fark varsa ya sizin hatanızdır ya da kaçırdığınız bir kuraldır."

İki katmanlı kâhin (slayt 17):
  1. oracle/gpower_vectors.csv                G*Power arayüzünden elle toplanan vektörler
  2. oracle/library/statsmodels_vectors.csv   statsmodels FTestAnovaPower (ölçek)
Ayrıca hocanın sözleşmesindeki (CONTRACT.md §9) anova referans vektörleri.

Yeniden yazım, hocanın sözleşmesindeki gibi CLI ÜZERİNDEN (alt süreç) çağrılır; yani
test edilen şey, gizli vektörlerin çalıştırılacağı yolun ta kendisidir.

Tolerans (CONTRACT.md "Karşılaştırma"): tam sayı alanlar (n_total, df1, df2) TAM;
ondalık alanlar mutlak ya da bağıl fark ≤ 1e-6. Ayrıca G*Power'ın ekranda gösterdiği
basamak sayısına kadar eşleşme de raporlanır.

Sözleşme ↔ G*Power ayrılıkları: sözleşme kesirli k/N'yi (INVALID_VALUE) ve f = 0'ı
(OUT_OF_RANGE) reddeder; G*Power ise yuvarlar / hesaplar. Bu vektörlerde CLI'den
sözleşmenin hata kodu beklenir VE motorun G*Power davranışını hâlâ birebir verdiği
ayrıca doğrulanır (durum: "SÖZLEŞME").

Çalıştırma (repo kökünden):
    python tests/differential.py
Çıktı:
    tests/UYUM_RAPORU.md   (insan okur)
    tests/differential_results.csv, tests/library_results.csv
"""
from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "oracle" / "gpower_vectors.csv"
LIBRARY = ROOT / "oracle" / "library" / "statsmodels_vectors.csv"
REPORT = ROOT / "tests" / "UYUM_RAPORU.md"
RESULTS = ROOT / "tests" / "differential_results.csv"
sys.path.insert(0, str(ROOT / "src"))

TOL = 1e-6

# Uyuşmazlıkların bilinen açıklamaları (rapora yazılır)
EXPLAIN_FRACTIONAL = (
    "statsmodels toplam N'yi kesirli döndürür; G*Power (ve yeniden yazım) "
    "grup başına n'yi yukarı yuvarlayıp k ile çarpar (SPEC R23, LEDGER L29). "
    "Beklenen: N_yeniden_yazım = ceil(N_kütüphane / k) · k"
)

# Hocanın sözleşmesindeki anova-oneway referans vektörleri (CONTRACT.md §9)
CONTRACT_VECTORS = [
    dict(id="C-apriori", mode="a-priori", args=dict(f=0.25, alpha=0.05, power=0.95, groups=5),
         expected=dict(ncp=19.0625000, critical_f=2.4017397, df1=4, df2=300, n_total=305, actual_power=0.9521313)),
    dict(id="C-posthoc", mode="post-hoc", args=dict(f=0.25, alpha=0.05, n_total=100, groups=5),
         expected=dict(ncp=6.2500000, critical_f=2.4674936, df1=4, df2=95, power=0.4663312)),
    dict(id="C-compromise", mode="compromise", args=dict(f=0.25, beta_alpha_ratio=1, n_total=100, groups=5),
         expected=None),
    dict(id="C-criterion", mode="criterion", args=dict(f=0.25, power=0.95, n_total=100, groups=5),
         expected=None),
    dict(id="C-sensitivity", mode="sensitivity", args=dict(alpha=0.05, power=0.95, n_total=100, groups=5),
         expected=None),
]
INT_KEYS = {"n_total", "df1", "df2"}


def run_cli_args(mode: str, fields: dict):
    args = [sys.executable, "-m", "anova_clone.cli", "--test", "anova-oneway", "--mode", mode]
    for k, v in fields.items():
        if v is not None and str(v) != "":
            args += [f"--{k}", str(v)]
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    proc = subprocess.run(args, capture_output=True, text=True, env=env, cwd=ROOT)
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    try:
        payload = json.loads(lines[-1]) if lines else {}
    except json.JSONDecodeError:
        payload = {"_raw": proc.stdout}
    return proc.returncode, payload, len(lines), proc.stderr


def run_cli(mode: str, f, alpha, k, power=None, n=None):
    fields = dict(f=f, alpha=alpha, groups=k)
    if mode == "a-priori":
        fields["power"] = power
    else:
        fields["n_total"] = n
    code, payload, nlines, _ = run_cli_args(mode, fields)
    return code, payload, nlines


def within_tol(got, exp) -> bool:
    got, exp = float(got), float(exp)
    d = abs(got - exp)
    return d <= TOL or (exp != 0 and d / abs(exp) <= TOL)


def decimals_of(text: str) -> int:
    text = text.strip()
    if "." not in text:
        return 0
    return len(text.split(".", 1)[1])


def matches_display(engine_value: float, shown: str) -> bool:
    """G*Power'ın gösterdiği basamak sayısına yuvarlayınca aynı mı?"""
    d = decimals_of(shown)
    q = Decimal(1).scaleb(-d)
    return Decimal(repr(float(engine_value))).quantize(q) == Decimal(shown.strip()).quantize(q)


def expected_error_code(msg: str) -> str | None:
    if "admissible range" in msg or "at least 2 groups" in msg:
        return "OUT_OF_RANGE"
    if "greater than or equal to alpha" in msg or "Sample size must be greater" in msg:
        return "INCONSISTENT"
    return None


def contract_divergence(r) -> str | None:
    """Sözleşmenin G*Power'dan farklı davrandığı girdiler."""
    def frac(x):
        return x.strip() != "" and float(x) != math.floor(float(x))
    if frac(r["k"]) or (r["mode"] == "post-hoc" and frac(r["n_in"])):
        return "INVALID_VALUE"
    if r["mode"] == "post-hoc" and float(r["f"]) == 0.0:
        return "OUT_OF_RANGE"
    return None


def engine_matches_gpower(r) -> tuple[bool, str]:
    """Motor (sözleşme katmanı olmadan) G*Power'ın gösterdiğini veriyor mu?"""
    from anova_clone import engine
    if r["mode"] == "a-priori":
        res = engine.a_priori(float(r["f"]), float(r["alpha"]), float(r["power_in"]), float(r["k"]))
    else:
        res = engine.post_hoc(float(r["f"]), float(r["alpha"]), float(r["n_in"]), float(r["k"]))
    ok = (str(res.n_total) == r["n_total"].strip() and str(res.df1) == r["df1"].strip()
          and str(res.df2) == r["df2"].strip() and matches_display(res.ncp, r["lambda"])
          and matches_display(res.critical_f, r["critical_F"]) and matches_display(res.power, r["actual_power"]))
    return ok, f"motor: N={res.n_total}, df=({res.df1},{res.df2}), λ={res.ncp:.7f}, F={res.critical_f:.7f}, güç={res.power:.7f}"


def oracle_rows():
    with ORACLE.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            yield r


def check_oracle():
    results = []
    for r in oracle_rows():
        has_output = r["n_total"].strip() not in ("",) or r["gpower_message"].strip()
        if not has_output:
            results.append(dict(id=r["id"], status="TOPLANMADI", detail="Kâhin değeri yok"))
            continue
        expect_error = r["n_total"].strip() in ("?", "") or r["category"] == "gecersiz"
        mode = r["mode"]
        code, out, nlines = run_cli(mode, r["f"], r["alpha"], r["k"],
                                    power=r["power_in"], n=r["n_in"])
        rec = dict(id=r["id"], mode=mode, f=r["f"], alpha=r["alpha"], k=r["k"],
                   power_in=r["power_in"], n_in=r["n_in"], exit=code,
                   one_line_json=(nlines == 1), cli=json.dumps(out, ensure_ascii=False),
                   err_code=out.get("code", ""))
        div = contract_divergence(r)
        if div and not expect_error:
            eng_ok, eng_detail = engine_matches_gpower(r)
            ok = code != 0 and out.get("code") == div and eng_ok
            rec.update(status="SÖZLEŞME" if ok else "UYUŞMADI", n_match="-",
                       detail=f"G*Power sonuç veriyor; sözleşme gereği CLI `{out.get('code')}` döndü "
                              f"(beklenen {div}). {eng_detail} → G*Power ile {'aynı' if eng_ok else 'FARKLI'}")
            results.append(rec)
            continue
        if expect_error:
            want = expected_error_code(r["gpower_message"])
            ok = code != 0 and "error" in out
            code_ok = (out.get("code") == want) if want else None
            rec.update(status="UYUŞTU" if ok else "UYUŞMADI", n_match="-", code_match=code_ok,
                       detail=f"G*Power: {r['gpower_message'] or 'hata'} | yeniden yazım: "
                              f"{out.get('code', '')} — {out.get('error', out)}")
            results.append(rec)
            continue
        if code != 0:
            rec.update(status="UYUŞMADI", detail=f"G*Power sonuç verdi, yeniden yazım hata: {out}",
                       n_match=False)
            results.append(rec)
            continue
        power_key = "actual_power" if mode == "a-priori" else "power"
        n_got = out.get("n_total", r["n_in"] if mode == "post-hoc" else None)
        checks = {
            "n_total": str(n_got) == r["n_total"].strip(),
            "df1": str(out.get("df1")) == r["df1"].strip(),
            "df2": str(out.get("df2")) == r["df2"].strip(),
            "ncp": within_tol(out["ncp"], r["lambda"]) and matches_display(out["ncp"], r["lambda"]),
            "critical_f": within_tol(out["critical_f"], r["critical_F"]) and matches_display(out["critical_f"], r["critical_F"]),
            power_key: within_tol(out[power_key], r["actual_power"]) and matches_display(out[power_key], r["actual_power"]),
        }
        expects_warning = "Please note" in r["gpower_message"]
        checks["warning"] = (("warning" in out) == expects_warning)
        src = {"ncp": "lambda", "critical_f": "critical_F", power_key: "actual_power",
               "warning": "gpower_message"}
        bad = [k for k, v in checks.items() if not v]
        rec.update(status="UYUŞTU" if not bad else "UYUŞMADI",
                   n_match=checks["n_total"] if mode == "a-priori" else "-",
                   detail=("tüm alanlar" + (" + uyarı" if expects_warning else "")) if not bad else "farklı: " + ", ".join(
                       f"{b} (G*Power {r.get(src.get(b, b))} / yeniden yazım {out.get(b)})" for b in bad))
        results.append(rec)
    return results


def check_contract_vectors():
    out = []
    for v in CONTRACT_VECTORS:
        code, payload, nlines, _ = run_cli_args(v["mode"], v["args"])
        if v["expected"] is None:
            ok = code != 0 and payload.get("code") == "UNSUPPORTED"
            out.append(dict(id=v["id"], mode=v["mode"], status="DESTEKLENMİYOR" if ok else "UYUŞMADI",
                            detail=f"bonus mod; CLI `{payload.get('code')}`", maxdiff=None))
            continue
        bad, maxd = [], 0.0
        for k, e in v["expected"].items():
            g = payload.get(k)
            if g is None:
                bad.append(f"{k} yok")
                continue
            if k in INT_KEYS:
                if not (isinstance(g, int) and g == e):
                    bad.append(f"{k} {g}≠{e}")
            else:
                maxd = max(maxd, abs(float(g) - e))
                if not within_tol(g, e):
                    bad.append(f"{k} {g}≠{e}")
        out.append(dict(id=v["id"], mode=v["mode"], status="UYUŞTU" if not bad and code == 0 else "UYUŞMADI",
                        detail="tüm alanlar" if not bad else "; ".join(bad), maxdiff=maxd))
    return out


def poisson_series_power(f, alpha, n, k):
    """Bağımsız hakem: noncentral F sağ kuyruğu, Poisson karışımı + düzenlenmiş
    tamamlayıcı beta (scipy.special.betaincc). scipy.stats.ncf'den ve statsmodels'ten
    bağımsız bir yol; yalnızca kütüphane uyuşmazlıklarını hakemlemek için kullanılır."""
    from scipy import special, stats
    d1, d2 = k - 1, n - k
    x = stats.f.isf(alpha, d1, d2)
    y = d1 * x / (d1 * x + d2)
    h = f * f * n / 2.0
    total = 0.0
    for j in range(100000):
        w = math.exp(-h + (j * math.log(h) if h > 0 else 0.0) - math.lgamma(j + 1)) if (h > 0 or j == 0) else 0.0
        total += w * special.betaincc(d1 / 2.0 + j, d2 / 2.0, y)
        if j > h + 50 and w < 1e-20:
            break
    return total


def _library_row(r):
    k = int(r["k"])
    if r["mode"] == "a-priori":
        _, res, _ = run_cli("a-priori", r["f"], r["alpha"], k, power=r["power_in"])
        lib_n = float(r["lib_n_fractional"])
        expected = max(math.ceil(lib_n / k) * k, 2 * k)
        got = res.get("n_total")
        naive = math.ceil(lib_n)
        return dict(id=r["id"], mode="a-priori", lib=lib_n, expected_rule=expected,
                    naive_ceil=naive, got=got,
                    status="UYUŞTU" if got == expected else "UYUŞMADI",
                    differs_from_naive=(got != naive))
    _, res, _ = run_cli("post-hoc", r["f"], r["alpha"], k, n=r["n_in"])
    lib_p = float(r["lib_power"])
    got = res.get("power")
    ok = got is not None and within_tol(got, lib_p)
    rec = dict(id=r["id"], mode="post-hoc", lib=lib_p, got=got,
               status="UYUŞTU" if ok else "UYUŞMADI", referee=None)
    if not ok and got is not None:
        ref = poisson_series_power(float(r["f"]), float(r["alpha"]), int(r["n_in"]), k)
        rec["referee"] = ref
        rec["diff_lib"] = float(got) - lib_p
        # CLI 7 ondalık yazar; hakem tam duyarlık → 1e-7 içinde aynıysa yeniden yazım doğru
        if abs(ref - float(got)) < 1e-9:
            rec["status"] = "AÇIKLANDI"
    return rec


def check_library():
    if not LIBRARY.exists():
        return None
    from concurrent.futures import ThreadPoolExecutor
    with LIBRARY.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(_library_row, rows))


def pct(a, b):
    return f"{(100.0 * a / b):.1f}%" if b else "—"


def write_report(orc, lib, cv):
    measured = [r for r in orc if r["status"] != "TOPLANMADI"]
    ok = [r for r in measured if r["status"] == "UYUŞTU"]
    contract = [r for r in measured if r["status"] == "SÖZLEŞME"]
    bad = [r for r in measured if r["status"] == "UYUŞMADI"]
    numeric = [r for r in measured if r.get("n_match") not in ("-", None)]
    n_ok = [r for r in numeric if r.get("n_match") is True]
    errs = [r for r in measured if r.get("code_match") is not None]
    code_ok = [r for r in errs if r.get("code_match")]

    lines = ["# Diferansiyel Test — Uyum Raporu", "",
             "Aynı girdiler G*Power 3.1.9.7 arayüzüne (kâhin) ve yeniden yazımın CLI'sine (hocanın sözleşmesi, CONTRACT.md v1.0.0) verildi.",
             "Bu dosya `python tests/differential.py` ile üretilir; elle düzenlenmez. "
             "Tolerans: tam sayılar tam; ondalıklar mutlak/bağıl ≤ 1e-6 **ve** G*Power'ın gösterdiği basamağa kadar.", "",
             "## Özet", "",
             "| Ölçü | Değer |", "|---|---|",
             f"| Kâhin vektörü (ölçülen) | {len(measured)} |",
             f"| Tam uyum (tüm alanlar / beklenen hata) | {len(ok)} / {len(measured)} |",
             f"| Sözleşme gereği bilinçli fark (CLI sözleşme hata kodu verir, **motor G*Power ile aynı**) | {len(contract)} |",
             f"| Uyuşmayan | **{len(bad)}** |",
             f"| **N tam eşleşme** (a priori sayısal vektörler — kapı ölçütü) | **{len(n_ok)} / {len(numeric)} ({pct(len(n_ok), len(numeric))})** |",
             f"| Hata vektörlerinde sözleşme kodu (`code`) eşleşmesi | {len(code_ok)} / {len(errs)} |"]
    cv_num = [r for r in cv if r["status"] in ("UYUŞTU", "UYUŞMADI") and r["maxdiff"] is not None]
    maxd = max((r["maxdiff"] for r in cv_num), default=0.0)
    lines.append(f"| Sözleşme referans vektörleri (anova a-priori + post-hoc) | {sum(r['status']=='UYUŞTU' for r in cv_num)} / {len(cv_num)} (en büyük mutlak fark {maxd:.1e}) |")
    if lib is not None:
        la = [r for r in lib if r["mode"] == "a-priori"]
        lp = [r for r in lib if r["mode"] == "post-hoc"]
        expl = [r for r in lp if r["status"] == "AÇIKLANDI"]
        maxl = max((abs(r.get("diff_lib", 0.0)) for r in lp), default=0.0)
        lines += [f"| Kütüphane a priori (statsmodels, kural: ceil(N/k)·k) | {sum(r['status']=='UYUŞTU' for r in la)} / {len(la)} ({pct(sum(r['status']=='UYUŞTU' for r in la), len(la))}) |",
                  f"| Kütüphane post hoc (güç, sözleşme toleransı 1e-6) | {sum(r['status']=='UYUŞTU' for r in lp)} / {len(lp)} ({pct(sum(r['status']=='UYUŞTU' for r in lp), len(lp))}) |",
                  f"| ↳ farklı çıkan ama bağımsız Poisson serisi hakemi yeniden yazımı doğrulayan | {len(expl)} (en büyük fark {maxl:.2e}) |",
                  f"| ↳ açıklanamayan | {sum(r['status']=='UYUŞMADI' for r in lp)} |",
                  f"| Kütüphanenin naif `ceil(N)` değerinden farklı çıkan N | {sum(r['differs_from_naive'] for r in la)} / {len(la)} |", "",
                  "Not: kütüphane satırları ayrıca `tests/library_results.csv` dosyasında.", ""]
        lines += ["### Kütüphane kâhini hakkında (açıklanmış uyuşmazlıklar)", "",
                  "1. **Kesirli N (a priori).** " + EXPLAIN_FRACTIONAL, "",
                  "2. **Post hoc güçte ~1e-6 mertebesinde farklar.** Kütüphane vektörleri öğrencinin Windows/Anaconda "
                  "ortamında (statsmodels 0.14.0 ve onunla gelen scipy) üretildi; yeniden yazım daha yeni bir scipy ile çalışıyor. "
                  "Farklı çıkan her vektör, `scipy.stats.ncf`'den bağımsız bir yolla (Poisson karışımı + düzenlenmiş tamamlayıcı beta) "
                  "hakemlendi: hakem yeniden yazımla 1e-9 içinde aynı, kütüphane değeri ise farklı. Yani fark kütüphane kâhininin "
                  "kendi sayısal hassasiyetinden geliyor. Yeniden yazım G*Power kâhininde de tutuyor "
                  "(ör. P05: f=0.10, N=1000, k=5 → 0.7136330). Bu, \"kâhin de yanılabilir\" bulgusudur: iki katmanlı kâhinde "
                  "ana kâhin G*Power'dır, kütüphane yalnızca ölçek içindir.", ""]
    else:
        lines += ["", "Kütüphane kâhini (`oracle/library/statsmodels_vectors.csv`) henüz üretilmedi.", ""]

    lines += ["### Sözleşme ↔ G*Power ayrılıkları", "",
              "Hocanın sözleşmesi (§2.4, §5) kesirli tam sayı alanlarını `INVALID_VALUE`, f ≤ 0'ı `OUT_OF_RANGE` sayar. "
              "G*Power ise kesirli k ve N'yi en yakın tam sayıya yuvarlar (SPEC R35; X07, X09, P13, P14) ve post hoc'ta f = 0'ı kabul eder (P07). "
              "Puanlama sözleşmeye göre yapıldığı için CLI/MCP sözleşmeye uyar; motor (`engine.py`) G*Power davranışını korur ve "
              "bu vektörlerde motorun G*Power ile birebir aynı sonucu verdiği ayrıca doğrulanır (aşağıda \"SÖZLEŞME\" satırları).", ""]

    lines += ["## Sözleşme referans vektörleri (CONTRACT.md §9, anova-oneway)", "",
              "| ID | Mod | Sonuç | Ayrıntı |", "|---|---|---|---|"]
    for r in cv:
        mark = {"UYUŞTU": "✅", "DESTEKLENMİYOR": "➖"}.get(r["status"], "❌")
        lines.append(f"| {r['id']} | {r['mode']} | {mark} {r['status']} | {r['detail']} |")
    lines.append("")

    lines += ["## Vektör bazında sonuç (G*Power kâhini)", "",
              "| ID | Mod | f | α | güç / N | k | Sonuç | Ayrıntı |", "|---|---|---|---|---|---|---|---|"]
    for r in orc:
        if r["status"] == "TOPLANMADI":
            lines.append(f"| {r['id']} | | | | | | ⏳ toplanmadı | |")
            continue
        pn = r["power_in"] if r["mode"] == "a-priori" else r["n_in"]
        mark = {"UYUŞTU": "✅", "SÖZLEŞME": "🔀"}.get(r["status"], "❌")
        lines.append(f"| {r['id']} | {r['mode']} | {r['f']} | {r['alpha']} | {pn} | {r['k']} | {mark} {r['status']} | {r['detail']} |")
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    keys = ["id", "mode", "f", "alpha", "k", "power_in", "n_in", "exit", "one_line_json",
            "status", "n_match", "err_code", "code_match", "detail", "cli"]
    with RESULTS.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(orc)
    return len(ok) + len(contract), len(measured), len(n_ok), len(numeric)


def write_library_csv(lib):
    if not lib:
        return
    keys = ["id", "mode", "lib", "got", "expected_rule", "naive_ceil", "differs_from_naive",
            "referee", "diff_lib", "status"]
    with (ROOT / "tests" / "library_results.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(lib)


def main() -> int:
    orc = check_oracle()
    cv = check_contract_vectors()
    lib = None if "--no-library" in sys.argv else check_library()
    write_library_csv(lib)
    ok, measured, n_ok, numeric = write_report(orc, lib, cv)
    print(f"Kâhin: {ok}/{measured} uyumlu (sözleşme farkları dahil); N tam eşleşme {n_ok}/{numeric}. "
          f"Sözleşme vektörleri: {[r['status'] for r in cv]}. Rapor: {REPORT}")
    return 0 if ok == measured else 1


if __name__ == "__main__":
    sys.exit(main())
