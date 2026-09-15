#!/usr/bin/env python3
"""
Aura 50-Day Trial — dashboard generator.

Produces a single, self-contained, dependency-free HTML dashboard:
modern, simple, comparison-first. The page markup + CSS + JS are static;
only the data payload (``window.AURA_DATA``) is regenerated each run.

The dashboard is written to all three served locations so they never drift:
    index.html  ·  dashboard.html  ·  dashboard/index.html

``scripts/daily_run.sh`` calls this script directly, so the published
dashboard stays in sync with the latest benchmark results automatically.

Run from the repo root:
    python3 scripts/generate_dashboard.py
"""
from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT_PATHS = [
    ROOT / "index.html",
    ROOT / "dashboard.html",
    ROOT / "dashboard" / "index.html",
]

VERDICTS = ("correct", "partial", "incorrect")
# Full-run detection: a session whose question count is >= 90% of the largest
# session. This is robust to new 320-question runs without hard-coding IDs.
FULL_RUN_RATIO = 0.9


def q_verdict(q: dict) -> str:
    v = q.get("verdict")
    if v in VERDICTS:
        return v
    score = q.get("score")
    if isinstance(score, dict) and score.get("verdict") in VERDICTS:
        return score["verdict"]
    return "incorrect"


def short_model(model: str | None) -> str:
    model = model or "unknown"
    return model.split("/")[-1]


def load_sessions() -> list[dict]:
    """Aggregate every results/session_*.json into a compact per-session record."""
    sessions: list[dict] = []
    for path in sorted(RESULTS.glob("session_*.json")):
        try:
            data = json.loads(path.read_text())
        except Exception as exc:  # noqa: BLE001
            print(f"warn: skip {path.name}: {exc}")
            continue
        questions = data.get("questions") or []
        if not questions:
            continue
        tiers: dict[int, dict] = defaultdict(
            lambda: {"c": 0, "p": 0, "i": 0, "n": 0}
        )
        correct = partial = incorrect = 0
        for q in questions:
            v = q_verdict(q)
            tier = int(q.get("tier") or 0)
            tiers[tier]["n"] += 1
            if v == "correct":
                correct += 1
                tiers[tier]["c"] += 1
            elif v == "partial":
                partial += 1
                tiers[tier]["p"] += 1
            else:
                incorrect += 1
                tiers[tier]["i"] += 1
        total = len(questions)
        raw = data.get("session")
        if raw is None:
            m = re.search(r"(\d+)", path.stem)
            raw = m.group(1) if m else path.stem
        try:
            sid = int(raw)
        except (TypeError, ValueError):
            continue
        timestamp = data.get("timestamp") or ""
        # Runs recovered after a crash (OOM/provider outage) answer fewer
        # questions than planned — flagged so stats can exclude them and
        # the table can show an honest "partial" badge instead of "full".
        interrupted = bool(data.get("interrupted") or data.get("aborted"))
        sessions.append(
            {
                "id": sid,
                "interrupted": interrupted,
                "date": timestamp[:10],
                "model": short_model(data.get("model")),
                "arch": short_model(data.get("archimedes")),
                "n": total,
                "correct": correct,
                "partial": partial,
                "incorrect": incorrect,
                "rate": round(correct / total, 4) if total else 0.0,
                "weighted": round((correct + partial * 0.5) / total, 4) if total else 0.0,
                "tiers": {str(t): tiers[t] for t in sorted(tiers)},
            }
        )
    sessions.sort(key=lambda s: (s["date"], s["id"]))
    return sessions


def load_ruby() -> list[dict]:
    out: list[dict] = []
    for path in sorted(RESULTS.glob("ruby-stats-*.json")):
        try:
            d = json.loads(path.read_text())
        except Exception:  # noqa: BLE001
            continue
        ep = d.get("episodeStats") or {}
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", path.stem)
        out.append(
            {
                "date": date_match.group(0) if date_match else "",
                "total": ep.get("total", 0),
                "rubyPass": ep.get("archimedesSuccesses", 0),
                "rubyFail": ep.get("archimedesFailures", 0),
                "escalations": ep.get("largeModelInterventions", 0),
                "catch": round(d.get("verificationCatchRate") or 0, 4),
                "competence": [
                    {"cat": c.get("category"), "rate": round(c.get("successRate") or 0, 4),
                     "count": c.get("count", 0)}
                    for c in (d.get("competence") or [])
                ],
            }
        )
    out.sort(key=lambda s: s["date"])
    return out


def build_payload() -> dict:
    sessions = load_sessions()
    ruby = load_ruby()
    if not sessions:
        return {"generated": date.today().isoformat(), "sessions": [], "fullRuns": [],
                "ruby": ruby, "maxTier": 0, "kpi": {}}

    max_n = max(s["n"] for s in sessions)
    full_threshold = max_n * FULL_RUN_RATIO
    # A recovered run can clear the 90% threshold yet still be incomplete —
    # never count it as a full run.
    for s in sessions:
        s["full"] = s["n"] >= full_threshold and not s.get("interrupted")
    full_runs = [s for s in sessions if s["full"]]

    max_tier = 0
    for s in sessions:
        for t in s["tiers"]:
            max_tier = max(max_tier, int(t))

    total_graded = sum(s["n"] for s in sessions)
    best = max(full_runs, key=lambda s: s["rate"]) if full_runs else None
    latest_full = full_runs[-1] if full_runs else None
    first_full = full_runs[0] if full_runs else None

    kpi = {
        "bestRate": best["rate"] if best else 0,
        "bestId": best["id"] if best else None,
        "latestRate": latest_full["rate"] if latest_full else 0,
        "latestId": latest_full["id"] if latest_full else None,
        "graded": total_graded,
        "sessions": len(sessions),
        "fullRuns": len(full_runs),
        "delta": round((best["rate"] - first_full["rate"]), 4)
                 if best and first_full else 0,
        "firstId": first_full["id"] if first_full else None,
        "catch": ruby[-1]["catch"] if ruby else 0,
    }
    return {
        "generated": date.today().isoformat(),
        "sessions": sessions,
        "fullRuns": full_runs,
        "ruby": ruby,
        "maxTier": max_tier,
        "kpi": kpi,
    }


# ── HTML / CSS / JS template ──────────────────────────────────────────────
# Placeholders replaced at write time:  @@DATA@@   @@GENERATED@@
PAGE = r"""
<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aura Benchmark · Archimedes Alternator — Mission Dashboard</title>
<meta name="description" content="Daily, automated, unedited benchmark results for Aura's Archimedes Alternator. Full-run pass rates, tier heatmaps, verification catch rate, and relation graphs.">
<style>
:root{
  --bg:#070a10;--surface:#0d1219;--surface2:#111826;--text:#e9eef7;--muted:#93a0b4;--faint:#5c6a80;
  --line:#1c2534;--line2:#141b26;--acc:#5cd6c0;--acc2:#7aa2ff;--good:#4ade80;--warn:#fbbf24;--bad:#f87171;
  --grid:rgba(147,160,180,.10);--radius:10px;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;
}
[data-theme=light]{
  --bg:#eef1f6;--surface:#ffffff;--surface2:#f6f8fb;--text:#101725;--muted:#4d5b72;--faint:#8b98ac;
  --line:#dbe2ec;--line2:#e8edf4;--acc:#0d9488;--acc2:#3b5bdb;--good:#15803d;--warn:#b45309;--bad:#dc2626;
  --grid:rgba(16,23,37,.07);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 var(--sans);-webkit-font-smoothing:antialiased}
a{color:var(--acc2);text-decoration:none}
svg{display:block}
text{user-select:none}

/* ── command bar ─────────────────────────────────────── */
.bar{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:18px;padding:10px 20px;
  background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:11px;min-width:0}
.mark{width:32px;height:32px;flex:0 0 32px;border-radius:8px;display:grid;place-items:center;color:#04121c;
  background:linear-gradient(135deg,var(--acc),var(--acc2));font:800 17px var(--sans)}
.brand b{font-size:15px;letter-spacing:-.01em;display:block;line-height:1.15}
.brand i{font:10.5px var(--mono);font-style:normal;color:var(--faint);letter-spacing:.06em;text-transform:uppercase}
.ticker{flex:1;display:flex;gap:0;justify-content:center;flex-wrap:wrap;font:11.5px var(--mono)}
.ticker span{color:var(--muted);padding:3px 12px;border-left:1px solid var(--line)}
.ticker span:first-child{border-left:none}
.ticker b{color:var(--text);font-weight:700}
.ticker b.up{color:var(--good)}.ticker b.dn{color:var(--bad)}
.bar-right{display:flex;align-items:center;gap:8px}
.stamp{font:10.5px var(--mono);letter-spacing:.05em;color:var(--muted);border:1px solid var(--line);padding:6px 9px;border-radius:7px}
.stamp:hover{color:var(--text);border-color:var(--faint)}
.theme-btn{width:30px;height:30px;border-radius:7px;border:1px solid var(--line);background:none;color:var(--muted);cursor:pointer;font-size:13px}
.theme-btn:hover{color:var(--text);border-color:var(--faint)}

/* ── full-bleed grid ─────────────────────────────────── */
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px;padding:14px 20px 26px;max-width:none}
.cell{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px;min-width:0}
.cell h3{margin:0 0 2px;font-size:13px;font-weight:700;letter-spacing:.01em;display:flex;align-items:baseline;gap:10px}
.cell h3 small{font:10.5px var(--mono);font-weight:400;color:var(--faint);letter-spacing:.05em;text-transform:uppercase}
.c8{grid-column:span 8}.c4{grid-column:span 4}.c12{grid-column:span 12}.c6{grid-column:span 6}

/* ── KPI ribbon ──────────────────────────────────────── */
.kpis{grid-column:span 12;display:grid;grid-template-columns:repeat(7,1fr);gap:10px;background:none;border:none;padding:0}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:11px 13px 9px;position:relative;overflow:hidden}
.kpi::after{content:"";position:absolute;inset:0 0 auto 0;height:2px;background:var(--kc,var(--acc));opacity:.85}
.kpi .k{font:10px var(--mono);letter-spacing:.09em;text-transform:uppercase;color:var(--faint)}
.kpi .v{font:800 24px/1.1 var(--sans);letter-spacing:-.02em;margin-top:5px;font-variant-numeric:tabular-nums}
.kpi .h{font:10.5px var(--mono);color:var(--muted);margin-top:2px}
.kpi svg{position:absolute;right:10px;bottom:12px;opacity:.9}

/* ── controls ────────────────────────────────────────── */
.chips{display:flex;flex-wrap:wrap;gap:5px;margin:10px 0 12px}
.chip{border:1px solid var(--line);background:var(--surface2);color:var(--muted);padding:4px 9px;border-radius:999px;
  cursor:pointer;font:11px var(--mono);display:inline-flex;align-items:center;gap:6px;transition:.12s}
.chip:hover{border-color:var(--acc);color:var(--text)}
.chip.off{opacity:.38;border-style:dashed}
.chip .dot{width:7px;height:7px;border-radius:50%}
.btns{display:flex;gap:6px;flex-wrap:wrap}
.btn{border:1px solid var(--line);background:var(--surface2);color:var(--muted);padding:5px 11px;border-radius:7px;
  cursor:pointer;font:10.5px var(--mono);letter-spacing:.06em;text-transform:uppercase}
.btn:hover{border-color:var(--acc);color:var(--text)}
.btn.on{background:var(--acc);border-color:var(--acc);color:#04241c;font-weight:700}
.search{font:12px var(--mono);color:var(--text);background:var(--surface2);border:1px solid var(--line);border-radius:7px;padding:6px 10px;width:190px}
.search:focus{outline:none;border-color:var(--acc)}

/* ── run explorer ────────────────────────────────────── */
.expl{display:flex;flex-direction:column;gap:6px;margin-top:10px}
.exrow{display:grid;grid-template-columns:52px 74px 1fr 46px;gap:10px;align-items:center;padding:7px 9px;border-radius:8px;
  border:1px solid transparent;cursor:pointer;transition:.12s}
.exrow:hover{background:var(--surface2);border-color:var(--line)}
.exrow.off{opacity:.38}
.exrow .id{font:12px var(--mono);font-weight:700}
.exrow .dt{font:10.5px var(--mono);color:var(--faint)}
.exrow .ebar{height:6px;border-radius:3px;background:var(--line2);overflow:hidden}
.exrow .ebar i{display:block;height:100%;border-radius:3px}
.exrow .rt{font:12px var(--mono);font-weight:700;text-align:right}
.exnote{font:10.5px var(--mono);color:var(--faint);margin-top:10px;line-height:1.6}

/* ── heatmap ─────────────────────────────────────────── */
.heat{margin-top:14px}
.heat svg{width:100%;height:auto}

/* ── graphify gallery ────────────────────────────────── */
.gal-head{display:flex;align-items:baseline;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-bottom:12px}
.gal-head h2{margin:0;font-size:16px;font-weight:800;letter-spacing:-.01em}
.gal-head h2 em{font-style:normal;color:var(--acc)}
.gal-head p{margin:0;font:11px var(--mono);color:var(--faint)}
.g-three{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-top:14px}
.g-cell{background:var(--surface2);border:1px solid var(--line2);border-radius:9px;padding:12px;min-width:0}
.g-cell h4{margin:0 0 8px;font:11px var(--mono);font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.g-hint{font:10px var(--mono);color:var(--faint);margin:6px 0 0}

/* ── table ───────────────────────────────────────────── */
.tbl-tools{display:flex;gap:10px;align-items:center;margin-bottom:10px;flex-wrap:wrap}
.count{font:10.5px var(--mono);color:var(--faint)}
table{width:100%;border-collapse:collapse;font:12.5px var(--sans)}
th,td{text-align:left;padding:6px 10px;border-bottom:1px solid var(--line2);white-space:nowrap}
th{position:sticky;top:0;background:var(--surface);font:10px var(--mono);letter-spacing:.08em;text-transform:uppercase;
  color:var(--faint);cursor:pointer;user-select:none}
th:hover{color:var(--text)}
th.sa::after{content:" ↑";color:var(--acc)}
th.sd::after{content:" ↓";color:var(--acc)}
tbody tr:hover{background:var(--surface2)}
.tag{font:10px var(--mono);padding:1px 6px;border-radius:5px;border:1px solid var(--line)}
.tag.full{background:var(--acc);border-color:var(--acc);color:#04241c;font-weight:700}
.bar-mini{height:5px;border-radius:3px;background:var(--line2);overflow:hidden;width:80px;display:inline-block;vertical-align:middle;margin-right:8px}
.bar-mini>i{display:block;height:100%}
.empty{padding:26px;text-align:center;color:var(--faint);font:12px var(--mono)}

footer{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:16px 20px 30px;border-top:1px solid var(--line);
  color:var(--faint);font:11px var(--mono)}
footer code{color:var(--muted)}

/* tooltip + misc */
#tip{position:fixed;z-index:99;pointer-events:none;background:var(--text);color:var(--bg);padding:6px 9px;border-radius:7px;
  font:11.5px var(--mono);font-weight:600;opacity:0;transition:opacity .08s;white-space:nowrap;transform:translate(-50%,calc(-100% - 10px))}
.tick{font:10px var(--mono);fill:var(--faint)}
.gridline{stroke:var(--grid);stroke-width:1}
.axl{font:10px var(--mono);fill:var(--faint)}
@media(max-width:1180px){.kpis{grid-template-columns:repeat(4,1fr)}.c8,.c4{grid-column:span 12}.g-three{grid-template-columns:1fr}}
@media(max-width:640px){.kpis{grid-template-columns:repeat(2,1fr)}.ticker{display:none}.c6{grid-column:span 12}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
</head>
<body>
<header class="bar">
  <div class="brand">
    <span class="mark">A</span>
    <div><b>Aura Benchmark</b><i>Archimedes Alternator · daily · unedited</i></div>
  </div>
  <div class="ticker" id="ticker"></div>
  <div class="bar-right">
    <span class="stamp">updated @@GENERATED@@</span>
    <a class="stamp" href="https://github.com/dusancar-sudo/aura-50-day-trial" target="_blank" rel="noopener">GitHub ↗</a>
    <button class="theme-btn" id="themeBtn" title="Toggle theme (t)">◐</button>
  </div>
</header>

<main class="grid">
  <section class="kpis" id="kpis"></section>

  <section class="cell c8">
    <h3>Full-run pass rate <small>apples-to-apples · 320 questions</small></h3>
    <div style="position:relative"><svg id="trend" viewBox="0 0 1000 320" style="width:100%;height:auto"></svg></div>
  </section>

  <section class="cell c4">
    <h3>Run explorer <small>click to overlay</small></h3>
    <div class="expl" id="explorer"></div>
    <div class="exnote">Click a run to add or remove it from the tier comparison below. Full runs are on by default.</div>
  </section>

  <section class="cell c12">
    <h3>Tier comparison <small>every question tier 1–@@MAXTIER@@ · where runs gain or lose</small></h3>
    <div class="btns" style="margin-top:10px">
      <button class="btn" id="bFull">Full runs</button>
      <button class="btn" id="bRecent">Recent 12</button>
      <button class="btn" id="bClear">Clear</button>
      <input class="search" id="search2" placeholder="filter chips… (model / id)" style="width:200px;margin-left:auto">
    </div>
    <div class="chips" id="chips"></div>
    <svg id="overlay" viewBox="0 0 1000 300" style="width:100%;height:auto"></svg>
    <div class="heat">
      <h3 style="font-size:12px">Where runs lose points <small>avg rate per tier bucket · darker = weaker</small></h3>
      <svg id="heatmap" viewBox="0 0 1000 170" style="width:100%;height:auto"></svg>
    </div>
  </section>

  <section class="cell c4">
    <h3>Difficulty curve <small>avg by tier · full runs</small></h3>
    <svg id="difficulty" viewBox="0 0 480 280" style="width:100%;height:auto"></svg>
  </section>
  <section class="cell c4">
    <h3>Alternator competence <small>latest snapshot</small></h3>
    <svg id="competence" viewBox="0 0 480 280" style="width:100%;height:auto"></svg>
  </section>
  <section class="cell c4">
    <h3>Verification catch <small>verifier catching errors</small></h3>
    <svg id="catchTrend" viewBox="0 0 480 280" style="width:100%;height:auto"></svg>
  </section>

  <section class="cell c12">
    <div class="gal-head">
      <h2>Graphify <em>·</em> relation graphs of the benchmark</h2>
      <p>same data, different geometry · hover anything · generated locally, zero dependencies</p>
    </div>

    <div class="g-cell" style="padding:14px">
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:6px">
        <h4 style="margin:0;font-size:12px">Arc <span style="color:var(--faint);text-transform:none;letter-spacing:0">— sessions on a line, arcs tie same-model runs · arc height = distance in time · width = run size</span></h4>
        <input class="search" id="arcSearch" placeholder="highlight model / id / date…" style="margin-left:auto;width:220px">
      </div>
      <div style="overflow-x:auto"><svg id="gArc" viewBox="0 0 1000 430" style="width:100%;min-width:760px;height:auto"></svg></div>
    </div>

    <div class="g-three">
      <div class="g-cell">
        <h4>Chord — models ↔ tier buckets</h4>
        <svg id="gChord" viewBox="0 0 340 340" style="width:100%;height:auto"></svg>
        <p class="g-hint">ribbon width = questions answered</p>
      </div>
      <div class="g-cell">
        <h4>Flow — full runs → verdicts</h4>
        <svg id="gFlow" viewBox="0 0 340 340" style="width:100%;height:auto"></svg>
        <p class="g-hint">correct · partial (est.) · incorrect per run</p>
      </div>
      <div class="g-cell">
        <h4>Radial — every run on record</h4>
        <svg id="gRadial" viewBox="0 0 340 340" style="width:100%;height:auto"></svg>
        <p class="g-hint">spoke length = pass rate · ○ = full run</p>
      </div>
    </div>
  </section>

  <section class="cell c12">
    <div class="tbl-tools">
      <h3 style="margin:0">All sessions <small>every recorded run · sortable</small></h3>
      <input class="search" id="search" placeholder="filter by id, date, model…" style="margin-left:auto">
      <span class="count" id="rowCount"></span>
    </div>
    <div style="overflow:auto;max-height:420px">
      <table id="table"><thead></thead><tbody></tbody></table>
    </div>
  </section>
</main>

<footer>
  <span>Generated from <code>results/session_*.json</code> &amp; <code>ruby-stats-*.json</code>. Strict rate = correct ÷ total; weighted counts partial as ½; partial counts in the flow panel are estimates.</span>
  <span><a href="#top">top ↑</a></span>
</footer>

<div id="tip"></div>
<script id="datablob" type="application/json">@@DATA@@</script>
<script>
"use strict";
const DATA = JSON.parse(document.getElementById("datablob").textContent);
const $ = (id) => document.getElementById(id);
const PALETTE = ["#5cd6c0","#7aa2ff","#f472b6","#fbbf24","#a78bfa","#34d399","#fb923c","#38bdf8","#e879f9","#a3e635"];
const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const rateColor = (r) => r>=.5?css("--good"):r>=.25?css("--warn"):css("--bad");
const pct = (r,d=1)=>(r*100).toFixed(d)+"%";
const fmt = (n)=>n.toLocaleString();
const E = (tag,cls,txt)=>{const e=document.createElementNS("http://www.w3.org/2000/svg",tag);if(cls)e.setAttribute("class",cls);if(txt!=null)e.textContent=txt;return e;};
function el(tag,cls,txt){const e=document.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e;}
const A = (e, attrs) => { for (const k in attrs) e.setAttribute(k, attrs[k]); return e; };
const tip = $("tip");
function tipShow(html,ev){tip.innerHTML=html;tip.style.opacity=1;tipMove(ev);}
function tipMove(ev){const x=Math.min(Math.max(ev.clientX,70),innerWidth-70);tip.style.left=x+"px";tip.style.top=(ev.clientY-6)+"px";}
function tipHide(){tip.style.opacity=0;}
const runColor = (id) => PALETTE[id % PALETTE.length];
const modelColor = (()=>{const m={};let i=0;DATA.sessions.forEach(s=>{if(!(s.model in m))m[s.model]=PALETTE[i++%PALETTE.length];});return (mo)=>m[mo]||"#888";})();
function sparks(vals,w,h,col){const mn=Math.min(...vals),mx=Math.max(...vals),sp=(mx-mn)||1;
  const pts=vals.map((v,i)=>`${(i/(vals.length-1)*(w-4)+2).toFixed(1)},${(h-3-(v-mn)/sp*(h-6)).toFixed(1)}`).join(" ");
  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.2" stroke-linejoin="round"/></svg>`;}

/* ── theme ── */
function initTheme(){
  const saved=localStorage.getItem("aura-theme");
  const theme=saved||(matchMedia("(prefers-color-scheme: light)").matches?"light":"dark");
  document.documentElement.setAttribute("data-theme",theme);
  $("themeBtn").onclick=()=>{const cur=document.documentElement.getAttribute("data-theme");const nx=cur==="dark"?"light":"dark";
    document.documentElement.setAttribute("data-theme",nx);localStorage.setItem("aura-theme",nx);rerenderAll();};
  addEventListener("keydown",e=>{const t=e.target;
    const typing=t&&(t.tagName==="INPUT"||t.tagName==="SELECT");
    if((e.key==="t"||e.key==="T")&&!typing)$("themeBtn").click();
    if(e.key==="/"&&!typing){e.preventDefault();$("search").focus();}});
}

/* ── chart frame ── */
function frame(svg,vb,pl,pr,pt,pb,y0,y1,yt){
  const [W,H]=vb,cw=W-pl-pr,ch=H-pt-pb;svg.innerHTML="";
  const g=E("g");svg.appendChild(g);
  yt.forEach(t=>{const y=pt+ch*(1-(t-y0)/(y1-y0));
    g.appendChild(A(E("line","gridline"),{x1:pl,x2:W-pr,y1:y,y2:y}));
    g.appendChild(E("text","tick",t+"%")).setAttribute("transform",`translate(${pl-7},${y+3})`);g.lastChild.setAttribute("text-anchor","end");});
  return {g,W,H,pl,pr,pt,pb,cw,ch,y0,y1};
}
const fx=(f,i,n)=>f.pl+f.cw*(n<=1?.5:i/(n-1));
const fy=(f,v)=>f.pt+f.ch*(1-(v-f.y0)/(f.y1-f.y0));

/* ── ticker + KPIs ── */
function renderTicker(){
  const k=DATA.kpi,t=$("ticker");t.innerHTML="";
  const items=[[fmt(k.sessions)+" runs",""],["<b>"+k.fullRuns+"</b> full",""],
    ["best <b>"+pct(k.bestRate)+"</b>",""],["graded <b>"+fmt(k.graded)+"</b>",""],
    ["Δ <b class='"+(k.delta>=0?"up":"dn")+"'>"+(k.delta>=0?"+":"")+pct(k.delta)+"</b>",""],
    ["catch <b>"+pct(k.catch)+"</b>",""]];
  items.forEach(([h])=>{const s=el("span");s.innerHTML=h;t.appendChild(s);});
}
function renderKPIs(){
  const k=DATA.kpi,runs=DATA.fullRuns||[],snaps=DATA.ruby||[];
  const models=new Set(DATA.sessions.map(s=>s.model));
  const spark=(vals,col)=>sparks(vals,86,24,col);
  const cards=[
    {k:"Best full run",v:pct(k.bestRate),h:"S"+k.bestId,c:rateColor(k.bestRate),s:spark(runs.map(r=>r.rate*100),rateColor(k.bestRate))},
    {k:"Latest full run",v:pct(k.latestRate),h:"S"+k.latestId,c:rateColor(k.latestRate),s:spark(runs.map(r=>r.rate*100),css("--acc2"))},
    {k:"Improvement",v:(k.delta>=0?"+":"")+pct(k.delta),h:"S"+k.firstId+" → S"+k.bestId,c:k.delta>=0?css("--good"):css("--bad"),s:spark(runs.map(r=>r.rate*100),k.delta>=0?css("--good"):css("--bad"))},
    {k:"Verif. catch",v:pct(k.catch),h:"latest snapshot",c:css("--acc"),s:spark(snaps.map(s=>s.catch*100),css("--acc"))},
    {k:"Questions graded",v:fmt(k.graded),h:fmt(k.sessions)+" sessions",c:css("--text"),s:""},
    {k:"Models tried",v:models.size,h:"incl. local merges",c:css("--text"),s:""},
    {k:"Full / slice runs",v:k.fullRuns+" / "+(k.sessions-k.fullRuns),h:"slices < 90% of 320",c:css("--text"),s:""},
  ];
  const w=$("kpis");w.innerHTML="";
  cards.forEach(c=>{const d=el("div","kpi");d.style.setProperty("--kc",c.c);
    d.innerHTML=`<div class="k">${c.k}</div><div class="v" style="color:${c.c}">${c.v}</div><div class="h">${c.h}</div>${c.s}`;
    w.appendChild(d);});
}

/* ── trend ── */
function renderTrend(){
  const svg=$("trend"),runs=DATA.fullRuns||[];
  if(runs.length<2)return;
  const f=frame(svg,[1000,320],50,26,22,44,0,100,[0,25,50,75,100]);
  const pts=runs.map((r,i)=>[fx(f,i,runs.length),fy(f,r.rate*100)]);
  const d=pts.map((p,i)=>(i?"L":"M")+p[0].toFixed(1)+" "+p[1].toFixed(1)).join(" ");
  const area=E("path");area.setAttribute("d",d+` L ${pts[pts.length-1][0]} ${fy(f,0)} L ${pts[0][0]} ${fy(f,0)} Z`);
  area.setAttribute("fill",css("--acc"));area.setAttribute("fill-opacity",".08");f.g.appendChild(area);
  const ln=E("path");ln.setAttribute("d",d);ln.setAttribute("fill","none");ln.setAttribute("stroke",css("--acc"));
  ln.setAttribute("stroke-width","1.6");ln.setAttribute("stroke-linejoin","round");f.g.appendChild(ln);
  runs.forEach((r,i)=>{
    const [x,y]=pts[i];
    const c=E("circle");c.setAttribute("cx",x);c.setAttribute("cy",y);c.setAttribute("r",4);
    c.setAttribute("fill",css("--surface"));c.setAttribute("stroke",rateColor(r.rate));c.setAttribute("stroke-width","1.6");
    c.style.cursor="pointer";
    c.addEventListener("mouseenter",e=>{tipShow(`S${r.id} · ${r.date}<br>${pct(r.rate)} (${r.correct}/${r.n})`,e);});
    c.addEventListener("mousemove",tipMove);c.addEventListener("mouseleave",tipHide);
    f.g.appendChild(c);
    const lab=E("text","axl",pct(r.rate));lab.setAttribute("x",x);lab.setAttribute("y",y-12);lab.setAttribute("text-anchor","middle");
    lab.setAttribute("fill",rateColor(r.rate));lab.style.fontWeight="700";f.g.appendChild(lab);
    const xl=E("text","tick","S"+r.id);xl.setAttribute("x",x);xl.setAttribute("y",f.H-26);xl.setAttribute("text-anchor","middle");f.g.appendChild(xl);
    const dl=E("text","tick",r.date.slice(5));dl.setAttribute("x",x);dl.setAttribute("y",f.H-12);dl.setAttribute("text-anchor","middle");f.g.appendChild(dl);
  });
}

/* ── run explorer (drives overlay) ── */
let selected=new Set();
function seedDefault(){selected=new Set((DATA.fullRuns||[]).map(r=>r.id));}
function renderExplorer(){
  const runs=DATA.fullRuns||[],w=$("explorer");w.innerHTML="";
  runs.forEach((r,i)=>{
    const prev=runs[i-1],d=prev?r.rate-prev.rate:null;
    const row=el("div","exrow"+(selected.has(r.id)?"":" off"));
    row.innerHTML=`<span class="id">S${r.id}</span><span class="dt">${r.date}</span>
      <span class="ebar"><i style="width:${(r.rate*100).toFixed(0)}%;background:${runColor(r.id)}"></i></span>
      <span class="rt" style="color:${rateColor(r.rate)}">${d==null?"":(d>=0?"+":"")+(d*100).toFixed(1)}</span>`;
    row.title=r.model;
    row.onclick=()=>{if(selected.has(r.id))selected.delete(r.id);else selected.add(r.id);
      renderExplorer();renderChips();renderOverlay();};
    row.addEventListener("mouseenter",e=>tipShow(`S${r.id} · ${r.model}<br>${pct(r.rate)} (${r.correct}/${r.n})`,e));
    row.addEventListener("mousemove",tipMove);row.addEventListener("mouseleave",tipHide);
    w.appendChild(row);
  });
}

/* ── chips + overlay ── */
let chipFilter="";
function renderChips(){
  const w=$("chips");w.innerHTML="";
  const all=[...(DATA.fullRuns||[]),...DATA.sessions.filter(s=>!s.full)];
  const seen=new Set(),list=[];
  all.forEach(s=>{if(!seen.has(s.id)){seen.add(s.id);list.push(s);}});
  const q=chipFilter.toLowerCase();
  list.filter(s=>!q||("S"+s.id).toLowerCase().includes(q)||s.model.toLowerCase().includes(q)||s.date.includes(q))
    .slice(0,44).forEach(s=>{
    const on=selected.has(s.id),col=runColor(s.id);
    const c=el("button","chip"+(on?"":" off"));
    c.innerHTML=`<span class="dot" style="background:${col}"></span>S${s.id} <b style="color:var(--text)">${pct(s.rate)}</b>${s.full?'<span class="tag full">full</span>':""}`;
    c.onclick=()=>{if(selected.has(s.id))selected.delete(s.id);else selected.add(s.id);
      renderChips();renderExplorer();renderOverlay();};
    w.appendChild(c);
  });
}
function renderOverlay(){
  const svg=$("overlay"),picks=DATA.sessions.filter(s=>selected.has(s.id));
  if(!picks.length){svg.innerHTML="";return;}
  const tiers=[];for(let t=1;t<=DATA.maxTier;t++)tiers.push(String(t));
  const f=frame(svg,[1000,300],44,16,16,34,0,100,[0,25,50,75,100]);
  picks.forEach(s=>{
    const col=runColor(s.id);let d="",first=true;
    tiers.forEach((t,i)=>{
      const td=s.tiers[t];if(!td)return;
      const rate=(td.c+td.p*0.5)/td.n,x=fx(f,i,tiers.length),y=fy(f,rate*100);
      d+=(first?"M":"L")+x.toFixed(1)+" "+y.toFixed(1);first=false;
      const c=E("circle");c.setAttribute("cx",x);c.setAttribute("cy",y);c.setAttribute("r",1.9);c.setAttribute("fill",col);c.setAttribute("fill-opacity","0.85");
      c.addEventListener("mouseenter",e=>tipShow(`S${s.id} · tier ${t} · ${pct(rate)}`,e));
      c.addEventListener("mousemove",tipMove);c.addEventListener("mouseleave",tipHide);
      f.g.appendChild(c);
    });
    const ln=E("path");ln.setAttribute("d",d);ln.setAttribute("fill","none");ln.setAttribute("stroke",col);
    ln.setAttribute("stroke-width",s.full?"1.4":"1");ln.setAttribute("stroke-opacity",s.full?"0.8":"0.4");f.g.appendChild(ln);
  });
  const step=Math.max(1,Math.ceil(tiers.length/12));
  tiers.forEach((t,i)=>{if(i%step!==0&&i!==tiers.length-1)return;
    const tx=E("text","tick",t);tx.setAttribute("x",fx(f,i,tiers.length));tx.setAttribute("y",f.H-18);tx.setAttribute("text-anchor","middle");f.g.appendChild(tx);});
  const ax=E("text","tick","tier →");ax.setAttribute("x",f.W-14);ax.setAttribute("y",f.H-4);ax.setAttribute("text-anchor","end");f.g.appendChild(ax);
}

/* ── heatmap: full runs × tier buckets ── */
function renderHeat(){
  const svg=$("heatmap"),runs=DATA.fullRuns||[];if(!runs.length)return;
  const B=10,bk=Math.ceil(DATA.maxTier/B);svg.innerHTML="";
  const W=1000,H=170,pl=64,pt=8,cw=W-pl-14,chH=H-pt-30;
  const cellW=cw/B,cellH=chH/runs.length;
  const heatColor=(r)=>r==null?"var(--line2)":
    `color-mix(in srgb, ${css("--bad")} ${Math.max(0,(0.5-r)*200)}%, ${r>=.5?`color-mix(in srgb, ${css("--good")} ${(r-0.5)*160}%, ${css("--warn")} ${(1-r)*130}%)`:css("--warn")} ${Math.max(0,(r-.25)*130)}%)`;
  for(let b=0;b<B;b++){
    const tx=E("text","tick",(b*bk+1)+"–"+Math.min(DATA.maxTier,(b+1)*bk));
    tx.setAttribute("x",pl+b*cellW+cellW/2);tx.setAttribute("y",H-14);tx.setAttribute("text-anchor","middle");svg.appendChild(tx);
  }
  runs.forEach((r,ri)=>{
    const lab=E("text","tick","S"+r.id);lab.setAttribute("x",pl-8);lab.setAttribute("y",pt+ri*cellH+cellH/2+3);
    lab.setAttribute("text-anchor","end");lab.setAttribute("fill",runColor(r.id));svg.appendChild(lab);
    for(let b=0;b<B;b++){
      let c=0,p=0,n=0;
      for(let t=b*bk+1;t<=Math.min(DATA.maxTier,(b+1)*bk);t++){const td=r.tiers[String(t)];if(td){c+=td.c;p+=td.p;n+=td.n;}}
      const rate=n?(c+p*0.5)/n:null;
      const cell=E("rect");cell.setAttribute("x",pl+b*cellW+1);cell.setAttribute("y",pt+ri*cellH+1);
      cell.setAttribute("width",cellW-2);cell.setAttribute("height",cellH-2);cell.setAttribute("rx",3);
      cell.setAttribute("fill",rate==null?"var(--line2)":heatColor(rate));
      cell.addEventListener("mouseenter",e=>tipShow(`S${r.id} · tiers ${b*bk+1}–${Math.min(DATA.maxTier,(b+1)*bk)}<br>${rate==null?"no data":pct(rate)+" avg"}${n?` · ${n}q`:''}`,e));
      cell.addEventListener("mousemove",tipMove);cell.addEventListener("mouseleave",tipHide);
      svg.appendChild(cell);
    }
  });
}

/* ── trio: difficulty / competence / catch ── */
function renderDifficulty(){
  const svg=$("difficulty"),runs=DATA.fullRuns||[];if(!runs.length)return;
  const tiers=[];for(let t=1;t<=DATA.maxTier;t++)tiers.push(t);
  const pts=tiers.map(t=>{const vals=runs.map(r=>r.tiers[String(t)]).filter(td=>td).map(td=>(td.c+td.p*0.5)/td.n);
    return vals.length?{t,rate:vals.reduce((a,b)=>a+b,0)/vals.length}:null;}).filter(Boolean);
  if(pts.length<2)return;
  const f=frame(svg,[480,280],38,12,14,32,0,100,[0,25,50,75,100]);
  const d=pts.map((p,i)=>(i?"L":"M")+fx(f,i,pts.length).toFixed(1)+" "+fy(f,p.rate*100).toFixed(1)).join(" ");
  const area=E("path");area.setAttribute("d",d+` L ${fx(f,pts.length-1,pts.length)} ${fy(f,0)} L ${fx(f,0,pts.length)} ${fy(f,0)} Z`);
  area.setAttribute("fill",css("--acc2"));area.setAttribute("fill-opacity",".07");f.g.appendChild(area);
  const ln=E("path");ln.setAttribute("d",d);ln.setAttribute("fill","none");ln.setAttribute("stroke",css("--acc2"));ln.setAttribute("stroke-width","1.4");f.g.appendChild(ln);
  pts.forEach((p,i)=>{const x=fx(f,i,pts.length),y=fy(f,p.rate*100);
    const c=E("circle");c.setAttribute("cx",x);c.setAttribute("cy",y);c.setAttribute("r",2.2);c.setAttribute("fill",rateColor(p.rate));
    c.addEventListener("mouseenter",e=>tipShow(`tier ${p.t} · ${pct(p.rate)}`,e));
    c.addEventListener("mousemove",tipMove);c.addEventListener("mouseleave",tipHide);f.g.appendChild(c);});
  const step=Math.max(1,Math.ceil(pts.length/7));
  pts.forEach((p,i)=>{if(i%step&&i!==pts.length-1)return;
    const tx=E("text","tick",p.t);tx.setAttribute("x",fx(f,i,pts.length));tx.setAttribute("y",f.H-16);tx.setAttribute("text-anchor","middle");f.g.appendChild(tx);});
}
function renderCompetence(){
  const svg=$("competence");const snap=(DATA.ruby||[])[DATA.ruby.length-1];
  if(!snap||!snap.competence)return;
  const comp=snap.competence.filter(c=>c.count>0).sort((a,b)=>b.rate-a.rate);
  const W=480,H=280,pl=100,pr=40,pt=10,pb=8,rowH=(H-pt-pb)/comp.length;
  svg.innerHTML="";const g=E("g");svg.appendChild(g);
  comp.forEach((c,i)=>{
    const y=pt+i*rowH,bw=(W-pl-pr)*c.rate;
    const lab=E("text","tick",c.cat);lab.setAttribute("x",pl-10);lab.setAttribute("y",y+rowH/2+3);lab.setAttribute("text-anchor","end");g.appendChild(lab);
    const bg=E("rect");bg.setAttribute("x",pl);bg.setAttribute("y",y+rowH*0.24);bg.setAttribute("width",W-pl-pr);bg.setAttribute("height",rowH*0.52);bg.setAttribute("rx",4);bg.setAttribute("fill","var(--line2)");g.appendChild(bg);
    const b=E("rect");b.setAttribute("x",pl);b.setAttribute("y",y+rowH*0.24);b.setAttribute("width",Math.max(2,bw));b.setAttribute("height",rowH*0.52);b.setAttribute("rx",4);b.setAttribute("fill",rateColor(c.rate));
    b.addEventListener("mouseenter",e=>tipShow(`${c.cat} · ${pct(c.rate)} · ${c.count} tasks`,e));
    b.addEventListener("mousemove",tipMove);b.addEventListener("mouseleave",tipHide);g.appendChild(b);
    const vt=E("text","tick",pct(c.rate));vt.setAttribute("x",pl+Math.max(2,bw)+5);vt.setAttribute("y",y+rowH/2+3);vt.setAttribute("fill",rateColor(c.rate));vt.style.fontWeight="700";g.appendChild(vt);
  });
}
function renderCatch(){
  const svg=$("catchTrend"),snaps=DATA.ruby||[];if(snaps.length<2)return;
  const f=frame(svg,[480,280],38,12,14,32,0,100,[0,25,50,75,100]);
  const d=snaps.map((s,i)=>(i?"L":"M")+fx(f,i,snaps.length).toFixed(1)+" "+fy(f,s.catch*100).toFixed(1)).join(" ");
  const ln=E("path");ln.setAttribute("d",d);ln.setAttribute("fill","none");ln.setAttribute("stroke",css("--acc"));ln.setAttribute("stroke-width","1.6");f.g.appendChild(ln);
  snaps.forEach((s,i)=>{const x=fx(f,i,snaps.length),y=fy(f,s.catch*100);
    const c=E("circle");c.setAttribute("cx",x);c.setAttribute("cy",y);c.setAttribute("r",3);c.setAttribute("fill",css("--surface"));c.setAttribute("stroke",css("--acc"));c.setAttribute("stroke-width","1.4");
    c.addEventListener("mouseenter",e=>tipShow(`${s.date} · catch ${pct(s.catch)} · ${s.escalations} esc.`,e));
    c.addEventListener("mousemove",tipMove);c.addEventListener("mouseleave",tipHide);f.g.appendChild(c);});
  const step=Math.max(1,Math.ceil(snaps.length/6));
  snaps.forEach((s,i)=>{if(i%step&&i!==snaps.length-1)return;
    const tx=E("text","tick",s.date.slice(5));tx.setAttribute("x",fx(f,i,snaps.length));tx.setAttribute("y",f.H-16);tx.setAttribute("text-anchor","middle");f.g.appendChild(tx);});
}

/* ── graphify: ARC ─────────────────────────────────────
   nodes = sessions in chronological order; arcs connect each run to its
   nearest earlier runs on the SAME MODEL — dense where a model was drilled,
   silent where it was tried once. Hover focuses; search filters. */
function renderArc(){
  const svg=$("gArc");svg.innerHTML="";
  const nodes=[...DATA.sessions].sort((a,b)=>a.date===b.date?a.id-b.id:(a.date<b.date?-1:1));
  const W=1000,H=430,mL=34,mR=34,baseY=H-64;
  const X=i=>mL+i*((W-mL-mR)/(nodes.length-1));
  const byModel={};nodes.forEach((s,i)=>{(byModel[s.model]=byModel[s.model]||[]).push(i);});
  const edges=[];
  // long spans: consecutive full runs — the dramatic arcs
  const fulls=nodes.map((n,i)=>n.full?i:-1).filter(i=>i>=0);
  fulls.forEach((b,i)=>fulls.forEach((a,j)=>{if(j<i)edges.push({a,b,w:60+30*(i-j),hi:true});}));
  // texture: same-model chains to the two nearest earlier runs
  Object.values(byModel).forEach(ixs=>{
    ixs.forEach((b,j)=>{for(let k=Math.max(0,j-2);k<j;k++)edges.push({a:ixs[k],b,w:(nodes[b].n+nodes[ixs[k]].n)/2});});
  });
  const maxN=Math.max(...nodes.map(s=>s.n));
  const g=E("g");svg.appendChild(g);
  const arcs=edges.map(e=>{
    const x1=X(e.a),x2=X(e.b),rx=(x2-x1)/2;
    const ry=Math.min(Math.abs(rx)*0.9,(baseY-84));
    const p=E("path");
    p.setAttribute("d",`M${x1},${baseY} A${Math.max(rx,0.5)},${Math.max(ry,4)} 0 0 1 ${x2},${baseY}`);
    p.setAttribute("fill","none");p.setAttribute("stroke",e.hi?css("--acc"):modelColor(nodes[e.b].model));
    p.setAttribute("stroke-width",e.hi?(0.9+0.14*(e.w/60-1)).toFixed(2):(0.3+Math.sqrt(e.w)*0.1).toFixed(2));
    p.setAttribute("stroke-opacity",e.hi?"0.7":"0.22");
    p.addEventListener("mouseenter",ev=>tipShow(`S${nodes[e.a].id} ↔ S${nodes[e.b].id}<br>${nodes[e.b].model}`,ev));
    p.addEventListener("mousemove",tipMove);p.addEventListener("mouseleave",tipHide);
    g.appendChild(p);return p;
  });
  const dots=nodes.map((s,i)=>{
    const c=E("circle");c.setAttribute("cx",X(i));c.setAttribute("cy",baseY);
    c.setAttribute("r",1.6+3.4*Math.sqrt(s.n/maxN));c.setAttribute("fill",modelColor(s.model));
    if(s.full){c.setAttribute("stroke",css("--text"));c.setAttribute("stroke-width","1");}
    c.style.cursor="pointer";
    c.addEventListener("mouseenter",e=>{
      tipShow(`S${s.id} · ${s.date}<br>${s.model}<br>${pct(s.rate)} (${s.correct}/${s.n})${s.full?" · FULL":""}`,e);
      arcs.forEach((p,j)=>{const ed=edges[j];const on=ed.a===i||ed.b===i;
        p.setAttribute("stroke-opacity",on?0.95:0.04);if(on)p.setAttribute("stroke",css("--acc"));});
    });
    c.addEventListener("mousemove",tipMove);
    c.addEventListener("mouseleave",()=>{arcs.forEach((p,j)=>{const ed=edges[j];p.setAttribute("stroke-opacity",ed.hi?0.7:0.22);p.setAttribute("stroke",ed.hi?css("--acc"):modelColor(nodes[ed.b].model));});tipHide();});
    g.appendChild(c);return c;
  });
  nodes.forEach((s,i)=>{if(i%Math.ceil(nodes.length/14))return;
    const t=E("text","tick","S"+s.id);t.setAttribute("x",X(i));t.setAttribute("y",baseY+14);t.setAttribute("text-anchor","middle");t.setAttribute("transform",`rotate(52 ${X(i)} ${baseY+14})`);g.appendChild(t);});
  // legend: models
  const models=Object.keys(byModel).sort((a,b)=>byModel[b].length-byModel[a].length).slice(0,8);
  models.forEach((m,i)=>{
    const lx=mL+i*118,ly=26;
    g.appendChild(A(E("circle"),{cx:lx,cy:ly-3,r:4,fill:modelColor(m)}));
    const t=E("text","axl",`${m.slice(0,13)} ×${byModel[m].length}`);
    t.setAttribute("x",lx+8);t.setAttribute("y",ly);g.appendChild(t);
  });
  $("arcSearch").oninput=ev=>{
    const q=ev.target.value.toLowerCase();
    nodes.forEach((s,i)=>{const hit=!q||("s"+s.id).includes(q)||s.model.toLowerCase().includes(q)||s.date.includes(q);
      dots[i].setAttribute("opacity",hit?1:0.12);dots[i].setAttribute("r",hit?1.6+3.4*Math.sqrt(s.n/maxN):1.2);});
    arcs.forEach((p,j)=>{const ed=edges[j];
      const hit=!q||["a","b"].some(k=>{const s=nodes[ed[k]];return ("s"+s.id).includes(q)||s.model.toLowerCase().includes(q)||s.date.includes(q);});
      p.setAttribute("stroke-opacity",hit?(edges[j].hi?0.7:0.35):0.03);});
  };
}

/* ── graphify: CHORD (models ↔ tier buckets) ── */
function renderChord(){
  const svg=$("gChord");svg.innerHTML="";
  const models={},mq={};DATA.sessions.forEach(s=>{models[s.model]=1;mq[s.model]=(mq[s.model]||0)+s.n;});
  const mNames=Object.keys(models).filter(m=>mq[m]>=40),B=6,bk=Math.ceil(DATA.maxTier/B);
  const flows=[];const wOf={};
  DATA.sessions.forEach(s=>{
    const mi=mNames.indexOf(s.model);if(mi<0)return;
    for(let b=0;b<B;b++){
      let n=0;for(let t=b*bk+1;t<=Math.min(DATA.maxTier,(b+1)*bk);t++){const td=s.tiers[String(t)];if(td)n+=td.n;}
      if(n){const key=mi+"-"+b;wOf[key]=(wOf[key]||0)+n;}
    }
  });
  Object.entries(wOf).forEach(([k,w])=>{const[mi,b]=k.split("-").map(Number);flows.push({a:mi,b:mNames.length+B-1-b,w});});
  const ents=[...mNames.map((m,i)=>({name:m,col:modelColor(m),type:"m"})),
    ...Array.from({length:B},(_,b)=>({name:`T${b*bk+1}–${Math.min(DATA.maxTier,(b+1)*bk)}`,col:css("--acc2"),type:"t"}))];
  const tot={};flows.forEach(f=>{tot[f.a]=(tot[f.a]||0)+f.w;tot[f.b]=(tot[f.b]||0)+f.w;});
  ents.forEach((e,i)=>e.w=tot[i]||0);
  const total=ents.reduce((a,e)=>a+e.w,0);if(!total)return;
  const cx=170,cy=172,R=118,pad=0.028;
  let ang=-Math.PI/2;
  ents.forEach(e=>{e.span=(e.w/total)*(Math.PI*2);e.a0=ang;ang+=e.span;e.a1=ang;});
  const arcPath=(e,ri,ro)=>{
    const p=(r,a)=>`${cx+r*Math.cos(a)},${cy+r*Math.sin(a)}`;
    return `M${p(ro,e.a0+pad/2)} A${ro},${ro} 0 0 1 ${p(ro,e.a1-pad/2)} L${p(ri,e.a1-pad/2)} A${ri},${ri} 0 0 0 ${p(ri,e.a0+pad/2)} Z`;
  };
  const g=E("g");svg.appendChild(g);
  ents.forEach(e=>{
    const p=E("path");p.setAttribute("d",arcPath(e,R-14,R));
    p.setAttribute("fill",e.col);p.setAttribute("fill-opacity",e.type==="m"?0.9:0.45);
    p.addEventListener("mouseenter",ev=>tipShow(`${e.name} · ${fmt(e.w)} q`,ev));
    p.addEventListener("mousemove",tipMove);p.addEventListener("mouseleave",tipHide);
    g.appendChild(p);
    const mid=(e.a0+e.a1)/2,lt=E("text","tick",e.name.split(" + ")[0].slice(0,12));
    lt.setAttribute("x",cx+(R+9)*Math.cos(mid));lt.setAttribute("y",cy+(R+9)*Math.sin(mid)+3);
    lt.setAttribute("text-anchor",Math.cos(mid)>0?"start":"end");lt.setAttribute("transform",`rotate(${mid*180/Math.PI} ${lt.getAttribute("x")} ${lt.getAttribute("y")})`);
    g.appendChild(lt);
  });
  const off={};flows.sort((a,b)=>b.w-a.w).forEach(f=>{
    const A=ents[f.a],Bn=ents[f.b];
    const span=a=>(a.w>0?(f.w/a.w):0);
    const aw=(f.w/A.w)*(A.a1-A.a0-pad),bw=(f.w/Bn.w)*(Bn.a1-Bn.a0-pad);
    off[f.a]=off[f.a]||0;off[f.b]=off[f.b]||0;
    const a0=A.a0+pad/2+off[f.a],b0=Bn.a0+pad/2+off[f.b];
    off[f.a]+=aw;off[f.b]+=bw;
    const P=(r,t)=>`${cx+r*Math.cos(t)},${cy+r*Math.sin(t)}`;
    const r1=R-16,rib=E("path");
    rib.setAttribute("d",`M${P(r1,a0)} A${r1},${r1} 0 0 1 ${P(r1,a0+aw)} Q${cx},${cy} ${P(r1,b0+bw)} A${r1},${r1} 0 0 1 ${P(r1,b0)} Q${cx},${cy} ${P(r1,a0)} Z`);
    rib.setAttribute("fill",A.col);rib.setAttribute("fill-opacity","0.22");
    rib.addEventListener("mouseenter",ev=>tipShow(`${A.name} → ${Bn.name}<br>${fmt(f.w)} questions`,ev));
    rib.addEventListener("mousemove",tipMove);rib.addEventListener("mouseleave",tipHide);
    g.appendChild(rib);
  });
}

/* ── graphify: FLOW (full runs → verdicts) ── */
function renderFlow(){
  const svg=$("gFlow");svg.innerHTML="";
  const runs=DATA.fullRuns||[];if(!runs.length)return;
  const verdicts=["correct","partial (est.)","incorrect"];
  const split=r=>{const wc=r.rate*r.n;let part=Math.max(0,Math.round(2*(wc-r.correct)));part=Math.min(part,r.n-r.correct);
    return [r.correct,part,r.n-r.correct-part];};
  const rows=runs.map(r=>({r,v:split(r)}));
  const colTot=[0,1,2].map(j=>rows.reduce((a,x)=>a+x.v[j],0));
  const leftTot=rows.reduce((a,x)=>a+x.r.n,0);
  const W=340,H=340,pl=14,pr=14,top=26,bot=14;
  const scale=(n)=>(H-top-bot)*(n/leftTot);
  let y=top;const L=rows.map(x=>{const h=scale(x.r.n),o={y0:y,y1:y+h,r:x.r,v:x.v};y+=h+6;return o;});
  let ry=top;const R=[0,1,2].map(j=>{const h=scale(colTot[j]),o={y0:ry,y1:ry+h};ry+=h+8;return o;});
  const g=E("g");svg.appendChild(g);
  L.forEach((o,i)=>{
    const rc=E("rect");rc.setAttribute("x",pl);rc.setAttribute("y",o.y0);rc.setAttribute("width",9);rc.setAttribute("height",o.y1-o.y0);rc.setAttribute("rx",3);
    rc.setAttribute("fill",modelColor(o.r.model));
    rc.addEventListener("mouseenter",e=>tipShow(`S${o.r.id} · ${o.r.n}q`,e));rc.addEventListener("mousemove",tipMove);rc.addEventListener("mouseleave",tipHide);
    g.appendChild(rc);
    const t=E("text","tick","S"+o.r.id);t.setAttribute("x",pl+13);t.setAttribute("y",(o.y0+o.y1)/2+3);g.appendChild(t);
    let cy=o.y0;
    [0,1,2].forEach(j=>{
      const hh=scale(o.v[j]);
      const rh=E("path");
      const x0=pl+9,x1=W-pr-9,rh1=R[j];
      const yA=cy,yB=cy+hh;
      const yC=rh1.y0+ (R[j]._off||0);
      const yD=yC+hh;
      R[j]._off=(R[j]._off||0)+hh;
      rh.setAttribute("d",`M${x0},${yA} C${(x0+x1)/2},${yA} ${(x0+x1)/2},${yC} ${x1},${yC} L${x1},${yD} C${(x0+x1)/2},${yD} ${(x0+x1)/2},${yB} ${x0},${yB} Z`);
      rh.setAttribute("fill",[css("--good"),css("--warn"),css("--bad")][j]);rh.setAttribute("fill-opacity","0.3");
      rh.addEventListener("mouseenter",e=>tipShow(`S${o.r.id} → ${verdicts[j]}: ${o.v[j]}`,e));rh.addEventListener("mousemove",tipMove);rh.addEventListener("mouseleave",tipHide);
      g.appendChild(rh);
      cy=yB;
    });
  });
  R.forEach((o,j)=>{
    const rc=E("rect");rc.setAttribute("x",W-pr-9);rc.setAttribute("y",o.y0);rc.setAttribute("width",9);rc.setAttribute("height",o.y1-o.y0);rc.setAttribute("rx",3);
    rc.setAttribute("fill",[css("--good"),css("--warn"),css("--bad")][j]);g.appendChild(rc);
    const t=E("text","tick",verdicts[j]);t.setAttribute("x",W-pr-13);t.setAttribute("y",(o.y0+o.y1)/2+3);t.setAttribute("text-anchor","end");g.appendChild(t);
    const v=E("text","tick",fmt(colTot[j])+"q");v.setAttribute("x",W-pr-13);v.setAttribute("y",(o.y0+o.y1)/2+14);v.setAttribute("text-anchor","end");g.appendChild(v);
  });
}

/* ── graphify: RADIAL (all sessions) ── */
function renderRadial(){
  const svg=$("gRadial");svg.innerHTML="";
  const ss=[...DATA.sessions].sort((a,b)=>a.date===b.date?a.id-b.id:(a.date<b.date?-1:1));
  const cx=170,cy=172,r0=52,r1=138;
  const g=E("g");svg.appendChild(g);
  [0.25,0.5,0.75,1].forEach(f=>{
    const c=E("circle");c.setAttribute("cx",cx);c.setAttribute("cy",cy);c.setAttribute("r",r0+(r1-r0)*f);
    c.setAttribute("fill","none");c.setAttribute("stroke","var(--grid)");c.setAttribute("stroke-dasharray","2 3");g.appendChild(c);
    const t=E("text","tick",(f*100)+"%");t.setAttribute("x",cx+3);t.setAttribute("y",cy-(r0+(r1-r0)*f)-2);g.appendChild(t);
  });
  ss.forEach((s,i)=>{
    const a=-Math.PI/2+i/ss.length*Math.PI*2;
    const len=(r1-r0)*s.rate;
    const x1=cx+r0*Math.cos(a),y1=cy+r0*Math.sin(a);
    const x2=cx+(r0+len)*Math.cos(a),y2=cy+(r0+len)*Math.sin(a);
    const ln=E("line");ln.setAttribute("x1",x1);ln.setAttribute("y1",y1);ln.setAttribute("x2",x2);ln.setAttribute("y2",y2);
    ln.setAttribute("stroke",modelColor(s.model));ln.setAttribute("stroke-width",s.full?2.2:1.1);ln.setAttribute("stroke-opacity",s.full?1:0.5);
    ln.addEventListener("mouseenter",e=>tipShow(`S${s.id} · ${s.date}<br>${s.model}<br>${pct(s.rate)}${s.full?" · FULL":""}`,e));
    ln.addEventListener("mousemove",tipMove);ln.addEventListener("mouseleave",tipHide);
    g.appendChild(ln);
    if(s.full){
      const c=E("circle");c.setAttribute("cx",cx+(r1+5)*Math.cos(a));c.setAttribute("cy",cy+(r1+5)*Math.sin(a));c.setAttribute("r",2.6);
      c.setAttribute("fill",css("--text"));g.appendChild(c);
      const rr=r1+(i%2?11:24);
      const t=E("text","tick","S"+s.id);t.setAttribute("x",cx+rr*Math.cos(a));t.setAttribute("y",cy+rr*Math.sin(a)+3);
      t.setAttribute("text-anchor",Math.cos(a)>0.2?"start":Math.cos(a)<-0.2?"end":"middle");g.appendChild(t);
    }
  });
}

/* ── table ── */
let sortKey="id",sortDir=1,filter="";
function renderTable(){
  const tb=$("table"),thead=tb.querySelector("thead"),tbody=tb.querySelector("tbody");
  const cols=[["id","Session"],["date","Date"],["model","Model"],["n","Q"],["correct","Correct"],["rate","Rate"]];
  thead.innerHTML="<tr>"+cols.map(c=>`<th data-k="${c[0]}" class="${sortKey===c[0]?(sortDir>0?"sa":"sd"):""}">${c[1]}</th>`).join("")+"</tr>";
  thead.querySelectorAll("th").forEach(th=>th.onclick=()=>{const k=th.dataset.k;
    if(sortKey===k)sortDir=-sortDir;else{sortKey=k;sortDir=1;}renderTable();});
  let rows=DATA.sessions.filter(s=>{if(!filter)return true;const q=filter.toLowerCase();
    return ("S"+s.id).toLowerCase().includes(q)||s.date.includes(q)||s.model.toLowerCase().includes(q);});
  rows.sort((a,b)=>{let x=a[sortKey],y=b[sortKey];if(typeof x==="string"){x=x.toLowerCase();y=(""+y).toLowerCase();}
    return (x<y?-1:x>y?1:0)*sortDir;});
  tbody.innerHTML="";
  rows.slice(0,200).forEach(s=>{
    const tr=el("tr");
    tr.innerHTML=`<td><b style="font:12px var(--mono)">S${s.id}</b>${s.full?' <span class="tag full">full</span>':""}</td>
      <td style="font:11.5px var(--mono);color:var(--muted)">${s.date}</td><td style="color:${modelColor(s.model)}">${s.model}${s.arch?` <span style="color:var(--faint);font-size:10.5px">+ ${s.arch}</span>`:""}</td>
      <td>${s.n}</td><td>${s.correct}/${s.n}</td>
      <td><span class="bar-mini"><i style="width:${(s.rate*100).toFixed(0)}%;background:${rateColor(s.rate)}"></i></span>
      <b style="font:11.5px var(--mono);color:${rateColor(s.rate)}">${pct(s.rate)}</b></td>`;
    tbody.appendChild(tr);
  });
  if(!rows.length)tbody.innerHTML='<tr><td colspan="6" class="empty">No sessions match.</td></tr>';
  $("rowCount").textContent=rows.length===DATA.sessions.length?`${rows.length} runs`:`${rows.length} / ${DATA.sessions.length}`;
}

/* ── wiring ── */
function rerenderAll(){renderTicker();renderKPIs();renderTrend();renderOverlay();renderHeat();
  renderDifficulty();renderCompetence();renderCatch();renderArc();renderChord();renderFlow();renderRadial();}
function init(){
  initTheme();renderTicker();renderKPIs();seedDefault();
  renderExplorer();renderChips();renderTable();
  $("bFull").onclick=()=>{seedDefault();sync();};
  $("bRecent").onclick=()=>{selected=new Set(DATA.sessions.slice(-12).map(s=>s.id));sync();};
  $("bClear").onclick=()=>{selected.clear();sync();};
  const sync=()=>{renderChips();renderExplorer();renderOverlay();};
  $("search2").oninput=e=>{chipFilter=e.target.value;renderChips();};
  $("search").oninput=e=>{filter=e.target.value;renderTable();};
  rerenderAll();
}
init();
</script>
</body>
</html>
"""


def main() -> None:
    payload = build_payload()
    data_json = json.dumps(payload, separators=(",", ":"))
    # Neutralise any "</script>" sequences so the inline JSON blob is safe.
    data_json = data_json.replace("</", "<\\/")
    page = PAGE.replace("@@DATA@@", data_json).replace(
        "@@GENERATED@@", html.escape(payload["generated"])
    ).replace("@@MAXTIER@@", str(payload["maxTier"]))
    (ROOT / "dashboard").mkdir(exist_ok=True)
    for path in OUT_PATHS:
        path.write_text(page, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    print(
        f"  {len(payload['sessions'])} sessions · "
        f"{len(payload['fullRuns'])} full runs · "
        f"{len(payload['ruby'])} archimedes snapshots"
    )


if __name__ == "__main__":
    main()
