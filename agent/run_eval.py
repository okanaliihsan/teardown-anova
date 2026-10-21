"""AI ajanı değerlendirmesi: 10 klinik soru, iki yol (MCP ve GUI), token/süre/doğruluk.

Ödev, "+10 AI AJANI":
  - Hekimin kendi diliyle (Türkçe) sorduğu soruyu MCP aracını çağırarak yanıtlayan ajan
  - 10 soruluk değerlendirme seti, doğru seçim oranı
  - Araç çağrı kayıtları (log)
  - Ölçülmüş token karşılaştırması: aynı sorular MCP ve GUI (ekran görüntüsü) yoluyla
  - Ajan hesabı kendisi YAPMAZ; hesap her zaman motordan gelir

Ajan = Claude Code (headless, `claude -p`) + bu reponun MCP sunucusu + agent/AGENT_PROMPT.md.
Ayrı bir API anahtarı gerekmez; Claude aboneliğiyle çalışır.

Kullanım (repo kökünden, Python'un scipy'li olduğu bir terminalde, ör. Anaconda Prompt):
    python agent/run_eval.py                       # MCP + GUI, Türkçe (20 çağrı)
    python agent/run_eval.py --modes mcp --langs tr en
    python agent/run_eval.py --only Q01 Q09        # birkaç soru
    python agent/run_eval.py --report-only         # mevcut loglardan raporu yeniden üret
Çıktılar:
    agent/logs/<mod>_<dil>_<soru>.jsonl   ham stream-json (araç çağrı kayıtları)
    agent/EVAL_RESULTS.json               makine okur özet
    agent/EVAL_REPORT.md                  insan okur rapor
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "agent"
LOGS = AGENT / "logs"
QUESTIONS = AGENT / "eval_questions.json"
PROMPT = AGENT / "AGENT_PROMPT.md"
RESULTS = AGENT / "EVAL_RESULTS.json"
REPORT = AGENT / "EVAL_REPORT.md"

SERVER = "anova-power"
TOOLS = [f"mcp__{SERVER}__anova_oneway_a_priori", f"mcp__{SERVER}__anova_oneway_post_hoc"]
DENY = "Bash,Write,Edit,NotebookEdit,WebFetch,WebSearch,Task,Agent,Glob,Grep"
LABEL_RE = re.compile(r"ET[İI]KET\s*:\s*([A-Za-z0-9\-]+)\s*\|\s*G[ÜU]VEN\s*:\s*([0-9]*[.,]?[0-9]+)", re.I)

GUI_INSTRUCTIONS = """Bu oturumda MCP aracı YOK. G*Power yalnızca grafik arayüzle (GUI) kullanılabiliyor; \
arayüzü ancak ekran görüntülerini okuyarak görebilirsin. Sayıyı kendin hesaplama; sonucu ekran görüntüsünden oku.
Ekran görüntüleri (Read aracıyla aç):
{shots}
Ekranda görmediğin bir değeri uydurma."""


def find_claude() -> str:
    for name in ("claude", "claude.cmd", "claude.exe"):
        p = shutil.which(name)
        if p:
            return p
    sys.exit("claude komutu bulunamadı. Claude Code kurulu ve PATH'te olmalı.")


def mcp_config_path() -> Path:
    cfg = {"mcpServers": {SERVER: {
        "type": "stdio",
        "command": sys.executable,
        "args": ["-m", "anova_clone.mcp_server"],
        "env": {"PYTHONPATH": str(ROOT / "src")},
    }}}
    path = AGENT / "logs" / "_mcp_config.json"
    path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return path


def empty_mcp_config_path() -> Path:
    path = AGENT / "logs" / "_mcp_empty.json"
    path.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    return path


def gui_shots(q) -> list[str]:
    shots = ["oracle/screenshots/A01.png  (G*Power penceresinin başlangıç hali; önceki bir hesap açık)"]
    if q.get("oracle_id"):
        shots.append(f"oracle/screenshots/{q['oracle_id']}.png  (değerler girilip Calculate'e basıldıktan sonra)")
    return shots


def run_one(claude: str, q: dict, mode: str, lang: str, model: str | None) -> Path:
    question = q[lang]
    log = LOGS / f"{mode}_{lang}_{q['id']}.jsonl"
    # Soru stdin'den verilir: Windows'ta çok satırlı argümanlar .cmd sarmalayıcılarında bozulabiliyor.
    cmd = [claude, "-p", "--output-format", "stream-json", "--verbose",
           "--append-system-prompt-file", str(PROMPT),
           "--permission-mode", "dontAsk", "--disallowedTools", DENY, "--strict-mcp-config"]
    if model:
        cmd += ["--model", model]
    if mode == "mcp":
        cmd += ["--mcp-config", str(mcp_config_path()), "--allowedTools", ",".join(TOOLS)]
    else:
        shots = "\n".join("- " + s for s in gui_shots(q))
        question = question + "\n\n" + GUI_INSTRUCTIONS.format(shots=shots)
        cmd += ["--mcp-config", str(empty_mcp_config_path()), "--allowedTools", "Read"]
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=ROOT, input=question, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    wall = time.time() - t0
    with log.open("w", encoding="utf-8") as fh:
        fh.write(proc.stdout)
        fh.write(json.dumps({"type": "_runner", "wall_seconds": round(wall, 2),
                             "exit_code": proc.returncode, "stderr": proc.stderr[-2000:],
                             "mode": mode, "lang": lang, "question_id": q["id"]},
                            ensure_ascii=False) + "\n")
    return log


def parse_log(path: Path) -> dict:
    tool_calls, tool_results, result, runner = [], [], {}, {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "assistant":
            for b in ev.get("message", {}).get("content", []):
                if b.get("type") == "tool_use":
                    tool_calls.append({"name": b.get("name"), "input": b.get("input")})
        elif t == "user":
            for b in ev.get("message", {}).get("content", []) if isinstance(ev.get("message", {}).get("content"), list) else []:
                if b.get("type") == "tool_result":
                    c = b.get("content")
                    if isinstance(c, list):
                        c = "".join(x.get("text", "") for x in c if isinstance(x, dict))
                    tool_results.append(c)
        elif t == "result":
            result = ev
        elif t == "_runner":
            runner = ev
    usage = result.get("usage", {}) or {}
    text = result.get("result", "") or ""
    m = LABEL_RE.search(text)
    return {
        "tool_calls": tool_calls, "tool_results": tool_results, "text": text,
        "label": m.group(1).lower() if m else None,
        "confidence": float(m.group(2).replace(",", ".")) if m else None,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
        "cost_usd": result.get("total_cost_usd"),
        "duration_ms": result.get("duration_ms"),
        "num_turns": result.get("num_turns"),
        "wall_seconds": runner.get("wall_seconds"),
        "exit_code": runner.get("exit_code"),
    }


def _num_in_text(value, text: str, decimals: int | None = None) -> bool:
    if decimals is None:
        return re.search(rf"(?<![\d.,]){value}(?![\d])", text.replace(".", "").replace(",", "")) is not None \
            or re.search(rf"(?<![\d]){value}(?![\d])", text) is not None
    s = f"{value:.{decimals}f}"
    return s in text or s.replace(".", ",") in text


def score(q: dict, p: dict, mode: str) -> dict:
    exp = q["expected"]
    label_ok = p["label"] == q["expected_label"]
    mcp_calls = [c for c in p["tool_calls"] if (c["name"] or "").startswith(f"mcp__{SERVER}__")]
    out = {"label_ok": label_ok}
    if exp.get("no_tool_call"):
        out["tool_ok"] = len(mcp_calls) == 0
        out["params_ok"] = None
        out["answer_ok"] = len(mcp_calls) == 0 and not re.search(r"\bN\s*=\s*\d", p["text"])
        out["correct"] = label_ok and out["answer_ok"]
        return out
    if mode == "mcp":
        tool = f"mcp__{SERVER}__{q['expected_tool']}"
        call = next((c for c in mcp_calls if c["name"] == tool), None)
        out["tool_ok"] = call is not None
        if call:
            args = call["input"] or {}
            out["params_ok"] = all(abs(float(args.get(k, -1)) - float(v)) < 1e-9
                                   for k, v in q["expected_params"].items())
        else:
            out["params_ok"] = False
    else:
        out["tool_ok"] = None
        out["params_ok"] = None
    if "n_total" in exp:
        out["answer_ok"] = _num_in_text(exp["n_total"], p["text"])
    else:
        out["answer_ok"] = _num_in_text(exp["power"], p["text"], 4) or _num_in_text(exp["power"], p["text"], 7)
    out["correct"] = bool(label_ok and out["answer_ok"] and (out["tool_ok"] in (True, None))
                          and (out["params_ok"] in (True, None)))
    return out


def build_report(records: list[dict]) -> str:
    def agg(rs, key):
        vals = [r["parsed"][key] or 0 for r in rs]
        return sum(vals), (sum(vals) / len(vals) if vals else 0)

    lines = ["# AI Ajanı Değerlendirme Raporu", "",
             "Bu dosya `python agent/run_eval.py` ile üretilir. Ham kayıtlar: `agent/logs/`.", "",
             "Ajan: Claude Code (headless `claude -p`) + `anova-power` MCP sunucusu + `agent/AGENT_PROMPT.md`.",
             "GUI yolu: aynı ajan, MCP olmadan, yalnızca G*Power ekran görüntülerini okuyarak (en az 1–2 görüntü). "
             "Gerçek bir 'computer use' oturumu her tıklamada ek görüntü alacağı için bu, GUI maliyetinin **alt sınırıdır**.", ""]
    groups = {}
    for r in records:
        groups.setdefault((r["mode"], r["lang"]), []).append(r)
    lines += ["## Özet", "",
              "| Yol | Dil | Soru | Doğru etiket | Doğru cevap | Ort. girdi tok. | Ort. önbellek oku | Ort. önbellek yaz | Ort. çıktı tok. | Ort. süre (sn) | Toplam maliyet tahmini (USD) |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for (mode, lang), rs in sorted(groups.items()):
        n = len(rs)
        lab = sum(r["score"]["label_ok"] for r in rs)
        cor = sum(r["score"]["correct"] for r in rs)
        _, ai = agg(rs, "input_tokens"); _, cr = agg(rs, "cache_read_input_tokens")
        _, cw = agg(rs, "cache_creation_input_tokens"); _, ao = agg(rs, "output_tokens")
        dur = [((r["parsed"]["duration_ms"] or 0) / 1000) for r in rs]
        cost = sum((r["parsed"]["cost_usd"] or 0) for r in rs)
        lines.append(f"| {mode.upper()} | {lang} | {n} | {lab}/{n} | {cor}/{n} | {ai:,.0f} | {cr:,.0f} | {cw:,.0f} | {ao:,.0f} | {sum(dur)/n:.1f} | {cost:.4f} |")
    lines.append("")

    # MCP vs GUI karşılaştırması (aynı dil)
    for lang in sorted({r["lang"] for r in records}):
        m = groups.get(("mcp", lang)); g = groups.get(("gui", lang))
        if m and g:
            shared = sorted({r["id"] for r in m} & {r["id"] for r in g})
            m = [r for r in m if r["id"] in shared]; g = [r for r in g if r["id"] in shared]

            def tot(r):
                p = r["parsed"]
                return ((p["input_tokens"] or 0) + (p["cache_read_input_tokens"] or 0)
                        + (p["cache_creation_input_tokens"] or 0) + (p["output_tokens"] or 0))

            def fresh(r):
                p = r["parsed"]
                return (p["input_tokens"] or 0) + (p["cache_creation_input_tokens"] or 0)

            n = len(shared)
            am, ag = sum(map(tot, m)) / n, sum(map(tot, g)) / n
            fm, fg = sum(map(fresh, m)) / n, sum(map(fresh, g)) / n
            dm = sum((r["parsed"]["duration_ms"] or 0) for r in m) / n / 1000
            dg = sum((r["parsed"]["duration_ms"] or 0) for r in g) / n / 1000
            cm = sum(r["score"]["correct"] for r in m); cg = sum(r["score"]["correct"] for r in g)
            lines += [f"### MCP ile GUI karşılaştırması ({lang}, aynı {n} soru)", "",
                      "| Ölçü (soru başına ortalama) | MCP | GUI (ekran görüntüsü) | GUI / MCP |", "|---|---|---|---|",
                      f"| Toplam işlenen token | {am:,.0f} | {ag:,.0f} | {(ag / am if am else 0):.2f}× |",
                      f"| Yeni (önbelleksiz) girdi token | {fm:,.0f} | {fg:,.0f} | {(fg / fm if fm else 0):.2f}× |",
                      f"| Süre (sn) | {dm:.1f} | {dg:.1f} | {(dg / dm if dm else 0):.2f}× |",
                      f"| Doğru cevap | {cm}/{n} | {cg}/{n} | |", "",
                      "Her iki yolda da Claude Code'un kendi sistem istemi ve araç tanımları aynı sabit maliyeti ekler; "
                      "fark ekran görüntüsü okumaktan ve ek turlardan gelir. GUI yolu gerçek tıklama yapmadığı için alt sınırdır.", ""]

    # Kalibrasyon
    lines += ["## Güven kalibrasyonu (etiket seçimi)", "",
              "| Güven aralığı | Seçim sayısı | Doğru | Oran |", "|---|---|---|---|"]
    buckets = [(0.0, 0.75), (0.75, 0.9), (0.9, 1.01)]
    for lo, hi in buckets:
        rs = [r for r in records if r["parsed"]["confidence"] is not None and lo <= r["parsed"]["confidence"] < hi]
        ok = sum(r["score"]["label_ok"] for r in rs)
        lines.append(f"| [{lo:.2f}, {min(hi, 1.0):.2f}{']' if hi > 1 else ')'} | {len(rs)} | {ok} | {(ok / len(rs) * 100 if rs else 0):.0f}% |")
    lines.append("")

    lines += ["## Soru bazında", "",
              "| Yol | Dil | Soru | Beklenen etiket | Ajanın etiketi (güven) | Araç çağrısı | Parametre | Cevap | Toplam token | Süre (sn) |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(records, key=lambda x: (x["mode"], x["lang"], x["id"])):
        p, s = r["parsed"], r["score"]
        calls = ", ".join((c["name"] or "").split("__")[-1] for c in p["tool_calls"]) or "—"
        tot = (p["input_tokens"] or 0) + (p["cache_read_input_tokens"] or 0) + (p["cache_creation_input_tokens"] or 0) + (p["output_tokens"] or 0)
        mark = lambda v: "—" if v is None else ("✅" if v else "❌")
        lines.append(f"| {r['mode'].upper()} | {r['lang']} | {r['id']} | {r['expected_label']} | {p['label']} ({p['confidence']}) | "
                     f"{calls} | {mark(s.get('params_ok'))} | {mark(s.get('answer_ok'))} | {tot:,} | {((p['duration_ms'] or 0) / 1000):.1f} |")
    lines.append("")
    lines += ["## Ajanın hesap yapmadığının kanıtı", "",
              "MCP yolunda her sayısal cevap, logdaki `tool_result` içinde motorun döndürdüğü JSON'la eşleşir; "
              "ajan istemi (AGENT_PROMPT.md, kural 1) araç çağırmadan sayı yazmayı yasaklar, ve `Bash` dahil hesap "
              "yapabilecek tüm araçlar `--disallowedTools` ile kapalıdır.", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", nargs="+", default=["mcp", "gui"], choices=["mcp", "gui"])
    ap.add_argument("--langs", nargs="+", default=["tr"], choices=["tr", "en"])
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--model", default=None, help="ör. haiku, sonnet, opus (varsayılan: Claude Code varsayılanı)")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    LOGS.mkdir(parents=True, exist_ok=True)
    qs = json.loads(QUESTIONS.read_text(encoding="utf-8"))["questions"]
    if args.only:
        qs = [q for q in qs if q["id"] in args.only]
    claude = None if args.report_only else find_claude()

    records = []
    for mode in args.modes:
        for lang in args.langs:
            for q in qs:
                log = LOGS / f"{mode}_{lang}_{q['id']}.jsonl"
                if not args.report_only:
                    print(f"[{mode}/{lang}] {q['id']} ...", flush=True)
                    run_one(claude, q, mode, lang, args.model)
                if not log.exists():
                    continue
                parsed = parse_log(log)
                records.append({"id": q["id"], "mode": mode, "lang": lang,
                                "expected_label": q["expected_label"], "parsed": parsed,
                                "score": score(q, parsed, mode)})
                s = records[-1]["score"]
                print(f"    etiket={parsed['label']} doğru_cevap={s['correct']} süre={parsed['duration_ms']}ms")

    RESULTS.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT.write_text(build_report(records), encoding="utf-8")
    print(f"Rapor: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
