"""Diferansiyel test: aynı girdiler hem G*Power'a (kâhin) hem yeniden yazıma verilir.

Ödev, "5. Diferansiyel test": "Aynı girdileri hem G*Power'a hem yeniden yazımınıza
verin, farkı ölçün. Fark varsa ya sizin hatanızdır ya da kaçırdığınız bir kuraldır."

İki katmanlı kâhin (slayt 17):
  1. oracle/gpower_vectors.csv           G*Power arayüzünden elle toplanan vektörler
  2. oracle/library/statsmodels_vectors.csv   statsmodels FTestAnovaPower (ölçek)

Yeniden yazım, sözleşmedeki gibi CLI ÜZERİNDEN (alt süreç) çağrılır; yani test
edilen şey, hocanın gizli vektörlerini çalıştıracağı yolun ta kendisidir.

Tolerans (ödev, "e) TOLERANS"):
  - n_total, df1, df2: TAM eşleşme
  - λ, kritik F, güç: G*Power'ın ekranda gösterdiği ondalık basamak sayısına kadar

Çalıştırma (repo kökünden):
    python tests/differential.py
Çıktı:
    tests/UYUM_RAPORU.md   (insan okur)
    tests/differential_results.csv   (satır satır sonuç)
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

# Uyuşmazlıkların bilinen açıklamaları (rapora yazılır)
EXPLAIN_FRACTIONAL = (
    "statsmodels toplam N'yi kesirli döndürür; G*Power (ve yeniden yazım) "
    "grup başına n'yi yukarı yuvarlayıp k ile çarpar (SPEC R23, LEDGER L29). "
    "Beklenen: N_yeniden_yazım = ceil(N_kütüphane / k) · k"
)


def run_cli(mode: str, f, alpha, k, power=None, n=None):
    args = [sys.executable, "-m", "anova_clone.cli", "--test", "anova-oneway",
            "--mode", mode, "--f", str(f), "--alpha", str(alpha), "--groups", str(k)]
    if mode == "a-priori":
        args += ["--power", str(power)]
    else:
        args += ["--n", str(n)]
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    proc = subprocess.run(args, capture_output=True, text=True, env=env, cwd=ROOT)
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    payload = json.loads(lines[-1]) if lines else {}
    return proc.returncode, payload, len(lines)


def decimals_of(text: str) -> int:
    text = text.strip()
    if "." not in text:
        return 0
    return len(text.split(".", 1)[1])


def matches_display(engine_value: float, shown: str) -> bool:
    """G*Power'ın gösterdiği basamak sayısına yuvarlayınca aynı mı?"""
    d = decimals_of(shown)
    q = Decimal(1).scaleb(-d)
    return Decimal(repr(engine_value)).quantize(q) == Decimal(shown.strip()).quantize(q)


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
                   one_line_json=(nlines == 1), cli=json.dumps(out, ensure_ascii=False))
        if expect_error:
            ok = code != 0 and "error" in out
            rec.update(status="UYUŞTU" if ok else "UYUŞMADI",
                       detail=f"G*Power: {r['gpower_message'] or 'hata'} | yeniden yazım: {out.get('error', out)}",
                       n_match="-")
            results.append(rec)
            continue
        if code != 0:
            rec.update(status="UYUŞMADI", detail=f"G*Power sonuç verdi, yeniden yazım hata: {out}",
                       n_match=False)
            results.append(rec)
            continue
        power_key = "actual_power" if "actual_power" in out else "power"
        checks = {
            "n_total": str(out.get("n_total")) == r["n_total"].strip(),
            "df1": str(out.get("df1")) == r["df1"].strip(),
            "df2": str(out.get("df2")) == r["df2"].strip(),
            "lambda": matches_display(float(out["ncp"]), r["lambda"]),
            "critical_F": matches_display(float(out["critical"]), r["critical_F"]),
            "power": matches_display(float(out[power_key]), r["actual_power"]),
        }
        bad = [k for k, v in checks.items() if not v]
        rec.update(status="UYUŞTU" if not bad else "UYUŞMADI",
                   n_match=checks["n_total"],
                   detail="tüm alanlar" if not bad else "farklı: " + ", ".join(
                       f"{b} (G*Power {r[{'power': 'actual_power'}.get(b, b)]} / yeniden yazım "
                       f"{out.get({'lambda': 'ncp', 'critical_F': 'critical', 'power': power_key}.get(b, b))})"
                       for b in bad))
        results.append(rec)
    return results


def check_library():
    if not LIBRARY.exists():
        return None
    out = []
    with LIBRARY.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            k = int(r["k"])
            if r["mode"] == "a-priori":
                code, res, _ = run_cli("a-priori", r["f"], r["alpha"], k, power=r["power_in"])
                lib_n = float(r["lib_n_fractional"])
                expected = max(math.ceil(lib_n / k) * k, 2 * k)
                got = res.get("n_total")
                naive = math.ceil(lib_n)
                status = "UYUŞTU" if got == expected else "UYUŞMADI"
                out.append(dict(id=r["id"], mode="a-priori", lib=lib_n, expected_rule=expected,
                                naive_ceil=naive, got=got, status=status,
                                differs_from_naive=(got != naive)))
            else:
                code, res, _ = run_cli("post-hoc", r["f"], r["alpha"], k, n=r["n_in"])
                lib_p = float(r["lib_power"])
                got = res.get("power", res.get("actual_power"))
                ok = got is not None and abs(float(got) - lib_p) < 5e-7
                out.append(dict(id=r["id"], mode="post-hoc", lib=lib_p, got=got,
                                status="UYUŞTU" if ok else "UYUŞMADI"))
    return out


def pct(a, b):
    return f"{(100.0 * a / b):.1f}%" if b else "—"


def write_report(orc, lib):
    measured = [r for r in orc if r["status"] != "TOPLANMADI"]
    ok = [r for r in measured if r["status"] == "UYUŞTU"]
    numeric = [r for r in measured if r.get("n_match") not in ("-", None)]
    n_ok = [r for r in numeric if r.get("n_match") is True]

    lines = ["# Diferansiyel Test — Uyum Raporu", "",
             "Aynı girdiler G*Power 3.1.9.7 arayüzüne (kâhin) ve yeniden yazımın CLI'sine verildi.",
             "Bu dosya `python tests/differential.py` ile üretilir; elle düzenlenmez.", "",
             "## Özet", "",
             "| Ölçü | Değer |", "|---|---|",
             f"| Kâhin vektörü (ölçülen) | {len(measured)} |",
             f"| Tam uyum (tüm alanlar / beklenen hata) | {len(ok)} / {len(measured)} ({pct(len(ok), len(measured))}) |",
             f"| **N tam eşleşme** (sayısal vektörler) | **{len(n_ok)} / {len(numeric)} ({pct(len(n_ok), len(numeric))})** |",
             f"| Henüz toplanmamış vektör | {len(orc) - len(measured)} |", ""]
    if lib is not None:
        la = [r for r in lib if r["mode"] == "a-priori"]
        lp = [r for r in lib if r["mode"] == "post-hoc"]
        lines += [f"| Kütüphane a priori (statsmodels, kural: ceil(N/k)·k) | {sum(r['status']=='UYUŞTU' for r in la)} / {len(la)} ({pct(sum(r['status']=='UYUŞTU' for r in la), len(la))}) |",
                  f"| Kütüphane post hoc (güç, |fark| < 5e-7) | {sum(r['status']=='UYUŞTU' for r in lp)} / {len(lp)} ({pct(sum(r['status']=='UYUŞTU' for r in lp), len(lp))}) |",
                  f"| Kütüphanenin naif `ceil(N)` değerinden farklı çıkan N | {sum(r['differs_from_naive'] for r in la)} / {len(la)} |", ""]
        lines += ["### Kütüphane kâhini hakkında (açıklanmış uyuşmazlık)", "", EXPLAIN_FRACTIONAL, ""]
    else:
        lines += ["Kütüphane kâhini (`oracle/library/statsmodels_vectors.csv`) henüz üretilmedi.", ""]

    lines += ["## Vektör bazında sonuç (G*Power kâhini)", "",
              "| ID | Mod | f | α | güç / N | k | Sonuç | Ayrıntı |", "|---|---|---|---|---|---|---|---|"]
    for r in orc:
        if r["status"] == "TOPLANMADI":
            lines.append(f"| {r['id']} | | | | | | ⏳ toplanmadı | |")
            continue
        pn = r["power_in"] if r["mode"] == "a-priori" else r["n_in"]
        mark = "✅" if r["status"] == "UYUŞTU" else "❌"
        lines.append(f"| {r['id']} | {r['mode']} | {r['f']} | {r['alpha']} | {pn} | {r['k']} | {mark} {r['status']} | {r['detail']} |")
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    keys = ["id", "mode", "f", "alpha", "k", "power_in", "n_in", "exit", "one_line_json",
            "status", "n_match", "detail", "cli"]
    with RESULTS.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(orc)
    return len(ok), len(measured), len(n_ok), len(numeric)


def main() -> int:
    orc = check_oracle()
    lib = check_library()
    ok, measured, n_ok, numeric = write_report(orc, lib)
    print(f"Kâhin: {ok}/{measured} tam uyum; N tam eşleşme {n_ok}/{numeric}. Rapor: {REPORT}")
    return 0 if ok == measured else 1


if __name__ == "__main__":
    sys.exit(main())
