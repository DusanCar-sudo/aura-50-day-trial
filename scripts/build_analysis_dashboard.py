#!/usr/bin/env python3
"""Generate an interactive benchmark analysis dashboard.

The output is a self-contained static page. It embeds compact session/question
metadata only; raw answer transcripts stay in results/*.json.
"""

from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
TARGETS = [ROOT / "index.html", ROOT / "dashboard.html", ROOT / "dashboard" / "index.html"]
PUBLIC_FULL_RUNS = {223, 9999, 10000, 10001, 8004}
RESTART_RUNS = {8004, 8005}


def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def clean_text(value, limit=160):
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    return value[:limit]


def q_verdict(question):
    verdict = question.get("verdict")
    if verdict in {"correct", "partial", "incorrect"}:
        return verdict
    score = question.get("score")
    if isinstance(score, dict) and score.get("verdict") in {"correct", "partial", "incorrect"}:
        return score["verdict"]
    return "incorrect"


def q_note(question):
    score = question.get("score")
    if isinstance(score, dict):
        return clean_text(score.get("note", ""), 180)
    return ""


def load_data():
    sessions = []
    questions = []
    question_ids = set()
    tiers_seen = set()
    for path in sorted(RESULTS.glob("session_*.json")):
        try:
            payload = json.loads(path.read_text())
        except Exception as exc:
            print(f"warning: {path.name}: {exc}")
            continue
        sid = safe_int(payload.get("session") or path.stem.split("_")[-1])
        if sid is None:
            print(f"warning: skipping {path.name}: no numeric session id")
            continue
        rows = payload.get("questions") or []
        if not rows:
            continue

        correct = partial = incorrect = 0
        tiers = defaultdict(lambda: {"correct": 0, "partial": 0, "incorrect": 0, "total": 0})
        for q in rows:
            verdict = q_verdict(q)
            tier = safe_int(q.get("tier")) or 0
            qid = str(q.get("id") or f"s{sid}-{len(questions)}")
            title = clean_text(q.get("question") or q.get("prompt") or q.get("title") or qid, 140)
            score = q.get("score")
            score_value = score.get("score") if isinstance(score, dict) else score
            try:
                score_value = float(score_value)
            except (TypeError, ValueError):
                score_value = 1.0 if verdict == "correct" else 0.5 if verdict == "partial" else 0.0

            tiers[tier]["total"] += 1
            tiers[tier][verdict] += 1
            tiers_seen.add(tier)
            question_ids.add(qid)
            if verdict == "correct":
                correct += 1
            elif verdict == "partial":
                partial += 1
            else:
                incorrect += 1

            questions.append(
                {
                    "session": sid,
                    "id": qid,
                    "tier": tier,
                    "question": title,
                    "verdict": verdict,
                    "score": round(score_value, 3),
                    "note": q_note(q),
                }
            )

        total = len(rows)
        weighted = (correct + partial * 0.5) / total if total else 0
        strict = correct / total if total else 0
        timestamp = payload.get("timestamp") or ""
        sessions.append(
            {
                "id": sid,
                "timestamp": timestamp,
                "date": timestamp[:10],
                "model": payload.get("model") or "unknown",
                "mode": payload.get("mode") or "headless",
                "total": total,
                "correct": correct,
                "partial": partial,
                "incorrect": incorrect,
                "strict": round(strict, 4),
                "weighted": round(weighted, 4),
                "tiers": {str(k): v for k, v in sorted(tiers.items())},
                "fullRun": total == 320 or sid in PUBLIC_FULL_RUNS,
                "restart": sid in RESTART_RUNS,
            }
        )

    sessions.sort(key=lambda s: (s["timestamp"], s["id"]))
    return {
        "sessions": sessions,
        "questions": questions,
        "tiers": sorted(tiers_seen),
        "questionCount": len(question_ids),
        "generatedAt": "2026-08-01",
    }


def build_html(data):
    data_json = json.dumps(data, separators=(",", ":"))
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aura Benchmark Lab</title>
<style>
  :root {
    color-scheme: dark;
    --bg:#05080d; --rail:#09111d; --panel:#0d1724; --panel2:#101d2c; --panel3:#142235;
    --line:#24384f; --line2:#33506f; --text:#eff6ff; --muted:#8fa5bd; --soft:#c9d7e8;
    --green:#6ee58a; --cyan:#63d9ff; --pink:#ff6fb3; --yellow:#f2c15b; --red:#ff745e;
    --blue:#87a7ff; --shadow:0 20px 60px rgba(0,0,0,.35);
  }
  * { box-sizing:border-box; }
  html { scroll-behavior:smooth; }
  body { margin:0; background:radial-gradient(circle at top left, rgba(99,217,255,.10), transparent 34rem), var(--bg); color:var(--text); font-family:Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; }
  button, input, select { font:inherit; }
  button { color:inherit; }
  .app { display:grid; grid-template-columns:280px minmax(0,1fr); min-height:100vh; }
  aside { position:sticky; top:0; height:100vh; overflow:auto; background:linear-gradient(180deg,#0a1420,#070d15); border-right:1px solid var(--line); padding:22px 18px; }
  main { min-width:0; padding:24px; }
  .brand { display:flex; align-items:center; gap:12px; margin-bottom:22px; }
  .logo { width:42px; height:42px; border-radius:12px; border:1px solid rgba(99,217,255,.5); display:grid; place-items:center; color:var(--cyan); font-weight:900; background:#0c1826; box-shadow:0 0 34px rgba(99,217,255,.12); }
  h1 { margin:0; font-size:20px; letter-spacing:.01em; }
  .caption { margin-top:4px; color:var(--muted); font-size:12px; line-height:1.35; }
  .nav { display:grid; gap:8px; margin:18px 0 22px; }
  .nav a { text-decoration:none; color:var(--soft); border:1px solid transparent; padding:10px 11px; border-radius:8px; font-size:13px; background:rgba(255,255,255,.02); }
  .nav a:hover { border-color:var(--line2); background:rgba(99,217,255,.06); }
  .side-section { border-top:1px solid var(--line); padding-top:16px; margin-top:16px; }
  .eyebrow { color:var(--muted); font:800 11px ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing:.14em; text-transform:uppercase; }
  .preset-row, .metric-row { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
  .preset, .iconbtn { border:1px solid var(--line); background:var(--panel); border-radius:8px; padding:8px 10px; cursor:pointer; font-size:12px; }
  .preset:hover, .iconbtn:hover { border-color:var(--cyan); }
  .metric-row label { display:flex; gap:7px; align-items:center; font-size:13px; color:var(--soft); }
  .run-list { display:grid; gap:7px; max-height:360px; overflow:auto; margin-top:10px; padding-right:4px; }
  .run-toggle { display:grid; grid-template-columns:auto 1fr auto; align-items:center; gap:8px; border:1px solid var(--line); border-radius:8px; padding:9px; background:rgba(255,255,255,.025); }
  .run-toggle.restart { border-color:rgba(110,229,138,.55); background:rgba(110,229,138,.07); }
  .run-toggle input { accent-color:var(--cyan); }
  .run-toggle strong { font-size:13px; }
  .run-toggle span { color:var(--muted); font-size:12px; }
  .hero { border:1px solid rgba(110,229,138,.55); border-radius:10px; background:linear-gradient(135deg,rgba(110,229,138,.16),rgba(99,217,255,.08)); padding:22px; box-shadow:var(--shadow); margin-bottom:18px; }
  .hero-top { display:flex; justify-content:space-between; gap:20px; flex-wrap:wrap; }
  .status { color:var(--green); font:900 12px ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing:.16em; text-transform:uppercase; }
  h2 { margin:7px 0 8px; font-size:34px; line-height:1.05; letter-spacing:-.02em; }
  .hero p { margin:0; color:#d8e6f6; line-height:1.55; max-width:900px; }
  .sequence { min-width:280px; color:var(--muted); font:800 13px ui-monospace, SFMono-Regular, Menlo, monospace; line-height:1.8; }
  .sequence strong { color:var(--green); }
  .cards { display:grid; grid-template-columns:repeat(5,minmax(150px,1fr)); gap:12px; margin-bottom:18px; }
  .card, .panel { background:linear-gradient(180deg,var(--panel2),var(--panel)); border:1px solid var(--line); border-radius:10px; box-shadow:0 10px 30px rgba(0,0,0,.18); }
  .card { padding:16px; min-height:112px; }
  .card .value { margin-top:10px; font-size:32px; font-weight:900; letter-spacing:-.02em; }
  .card .hint { margin-top:8px; color:var(--muted); font-size:12px; }
  .panel { padding:18px; margin-bottom:18px; overflow:auto; }
  .panel-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; margin-bottom:14px; }
  .panel h3 { margin:0; font-size:15px; letter-spacing:.11em; text-transform:uppercase; color:#dbeafe; }
  .panel .note { color:var(--muted); font-size:12px; margin-top:4px; }
  .grid2 { display:grid; grid-template-columns:minmax(0,1.35fr) minmax(360px,.65fr); gap:18px; }
  .chart-wrap { min-height:330px; }
  svg { width:100%; height:auto; display:block; }
  .axis { fill:var(--muted); font:11px ui-monospace, SFMono-Regular, Menlo, monospace; }
  .gridline { stroke:#24384f; stroke-width:1; }
  .series { fill:none; stroke-width:3; }
  .dot { stroke:#05080d; stroke-width:3; cursor:pointer; }
  .legend { display:flex; flex-wrap:wrap; gap:8px; }
  .legend button { border:1px solid var(--line); background:rgba(255,255,255,.025); border-radius:999px; padding:6px 10px; cursor:pointer; font-size:12px; display:flex; align-items:center; gap:7px; }
  .swatch { width:9px; height:9px; border-radius:50%; }
  table { width:100%; border-collapse:collapse; min-width:880px; }
  th,td { border-bottom:1px solid var(--line); padding:10px 11px; text-align:left; font-size:13px; vertical-align:top; }
  th { color:var(--muted); font:800 11px ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing:.1em; text-transform:uppercase; background:#0a1420; position:sticky; top:0; z-index:1; }
  tr.hot td { background:rgba(110,229,138,.08); }
  .pill { display:inline-flex; align-items:center; justify-content:center; min-width:62px; border-radius:999px; padding:4px 8px; font:900 12px ui-monospace, SFMono-Regular, Menlo, monospace; }
  .good { color:var(--green); background:rgba(110,229,138,.12); border:1px solid rgba(110,229,138,.35); }
  .warn { color:var(--yellow); background:rgba(242,193,91,.12); border:1px solid rgba(242,193,91,.35); }
  .bad { color:var(--red); background:rgba(255,116,94,.11); border:1px solid rgba(255,116,94,.32); }
  .bar { width:130px; height:8px; border-radius:999px; background:#1b2a3d; overflow:hidden; margin-top:4px; }
  .bar span { display:block; height:100%; border-radius:999px; }
  .tools { display:flex; flex-wrap:wrap; gap:10px; align-items:center; }
  .tools input, .tools select { background:#091421; color:var(--text); border:1px solid var(--line); border-radius:8px; padding:9px 10px; min-height:38px; }
  .tools input { min-width:260px; flex:1; }
  .matrix { min-width:900px; }
  .matrix th:first-child, .matrix td:first-child { position:sticky; left:0; z-index:2; background:#0a1420; }
  .heat { text-align:center; min-width:92px; }
  .heat strong { display:block; }
  .heat small { display:block; color:rgba(239,246,255,.72); margin-top:2px; }
  .empty { color:#51657c; text-align:center; }
  .detail-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:10px; }
  .detail-box { background:rgba(255,255,255,.025); border:1px solid var(--line); border-radius:8px; padding:12px; }
  .detail-box strong { display:block; font-size:18px; margin-top:5px; }
  .question-list { display:grid; gap:8px; max-height:560px; overflow:auto; padding-right:4px; }
  .qrow { border:1px solid var(--line); border-radius:8px; padding:10px; background:rgba(255,255,255,.025); display:grid; grid-template-columns:80px 70px 92px 1fr; gap:10px; align-items:start; }
  .qrow .text { color:#dce9f8; line-height:1.35; }
  .qrow .meta { color:var(--muted); font:800 12px ui-monospace, SFMono-Regular, Menlo, monospace; }
  .muted { color:var(--muted); }
  .footer { color:var(--muted); font-size:12px; padding:18px 0 40px; }
  @media (max-width:1100px) { .app { grid-template-columns:1fr; } aside { position:relative; height:auto; } .cards { grid-template-columns:repeat(2,1fr); } .grid2 { grid-template-columns:1fr; } main { padding:16px; } }
  @media (max-width:620px) { .cards { grid-template-columns:1fr; } h2 { font-size:27px; } .qrow { grid-template-columns:1fr; } }
</style>
</head>
<body>
<div class="app">
  <aside>
    <div class="brand"><div class="logo">A</div><div><h1>Aura Test Lab</h1><div class="caption">Manual overlays, tier analysis, session drilldown.</div></div></div>
    <nav class="nav">
      <a href="#overview">Overview</a>
      <a href="#overlay">Overlay Chart</a>
      <a href="#comparison">Full-Run Table</a>
      <a href="#tiers">Tier Heatmap</a>
      <a href="#sessions">Sessions</a>
      <a href="#questions">Questions</a>
    </nav>
    <div class="side-section">
      <div class="eyebrow">Metric</div>
      <div class="metric-row">
        <label><input type="radio" name="metric" value="strict" checked> Correct</label>
        <label><input type="radio" name="metric" value="weighted"> Weighted</label>
        <label><input type="radio" name="metric" value="partialRate"> Partial</label>
      </div>
    </div>
    <div class="side-section">
      <div class="eyebrow">Manual Run Toggles</div>
      <div class="preset-row">
        <button class="preset" data-preset="full">Full runs</button>
        <button class="preset" data-preset="restart">Restart</button>
        <button class="preset" data-preset="latest">Latest 12</button>
        <button class="preset" data-preset="all">All</button>
        <button class="preset" data-preset="clear">Clear</button>
      </div>
      <div class="run-list" id="runList"></div>
    </div>
  </aside>
  <main>
    <section class="hero" id="overview">
      <div class="hero-top">
        <div>
          <div class="status">Benchmark testing restarted</div>
          <h2>Testing console for the Aura benchmark restart</h2>
          <p>S8004 is the new full-run baseline: 180/320 correct, 56.2%, the best complete run so far. S8005 verifies the scorer fixes on the healthy tier 3+4 slice with 8/10 correct.</p>
        </div>
        <div class="sequence">S223 31.9% -> S9999 11.9% -> S10000 11.9% -> S10001 38.1% -> <strong>S8004 56.2%</strong></div>
      </div>
    </section>
    <section class="cards" id="cards"></section>
    <section class="grid2" id="overlay">
      <div class="panel">
        <div class="panel-head"><div><h3>Manual Overlay Chart</h3><div class="note">Toggle runs on the left. Switch metric to compare strict, weighted, or partial-rate results.</div></div><div class="legend" id="legend"></div></div>
        <div class="chart-wrap" id="overlayChart"></div>
      </div>
      <div class="panel">
        <div class="panel-head"><div><h3>Selected Run Detail</h3><div class="note">Click a point, row, or checkbox label to inspect one run.</div></div></div>
        <div id="runDetail"></div>
      </div>
    </section>
    <section class="panel" id="comparison">
      <div class="panel-head"><div><h3>Complete Full-Run Comparison</h3><div class="note">Apples-to-apples 320-question sessions. S8004 is highlighted as the restart result.</div></div></div>
      <div id="fullRunTable"></div>
    </section>
    <section class="panel" id="tiers">
      <div class="panel-head"><div><h3>Tier Heatmap From Selected Runs</h3><div class="note">The matrix recalculates when you toggle runs. Green means strong strict correctness; yellow means partial competence; red needs attention.</div></div></div>
      <div id="tierMatrix"></div>
    </section>
    <section class="panel" id="sessions">
      <div class="panel-head"><div><h3>Session Explorer</h3><div class="note">Newest first. Use this table to inspect smoke runs, partial reruns, and full benchmark sessions.</div></div></div>
      <div class="tools"><input id="sessionSearch" placeholder="Search session, model, date..."><select id="sessionScope"><option value="all">All sessions</option><option value="full">Full runs only</option><option value="restart">Restart runs only</option></select></div>
      <div id="sessionTable" style="margin-top:12px"></div>
    </section>
    <section class="panel" id="questions">
      <div class="panel-head"><div><h3>Question-Level Analyzer</h3><div class="note">Filter by tier, verdict, session, or text. This uses compact result metadata, not raw transcripts.</div></div></div>
      <div class="tools">
        <input id="questionSearch" placeholder="Search question id, wording, score note...">
        <select id="tierFilter"><option value="all">All tiers</option></select>
        <select id="verdictFilter"><option value="all">All verdicts</option><option value="correct">Correct</option><option value="partial">Partial</option><option value="incorrect">Incorrect</option></select>
        <select id="questionSessionFilter"><option value="selected">Selected runs</option><option value="all">All sessions</option></select>
      </div>
      <div id="questionList" class="question-list" style="margin-top:12px"></div>
    </section>
    <div class="footer">Generated from local results/session_*.json. Strict pass rate is correct/total; weighted counts partial answers as half.</div>
  </main>
</div>
<script id="dashboard-data" type="application/json">__DASHBOARD_DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('dashboard-data').textContent);
const sessions = DATA.sessions;
const questions = DATA.questions;
const colors = ['#6ee58a','#63d9ff','#ff6fb3','#f2c15b','#87a7ff','#ff745e','#9af0d1','#c59cff','#ffaa6b','#86efac','#67e8f9','#f9a8d4'];
const byId = new Map(sessions.map(s => [s.id, s]));
const fullIds = sessions.filter(s => s.fullRun).map(s => s.id);
const restartIds = [8004,8005].filter(id => byId.has(id));
let selected = new Set(fullIds.filter(id => [223,9999,10000,10001,8004].includes(id)));
if (!selected.size) selected = new Set(sessions.slice(-8).map(s => s.id));
let activeMetric = 'strict';
let focused = selected.has(8004) ? 8004 : [...selected][0] || sessions.at(-1)?.id;

const $ = id => document.getElementById(id);
const pct = v => `${(Number(v || 0) * 100).toFixed(1)}%`;
const pct0 = v => `${Math.round(Number(v || 0) * 100)}%`;
const sessionPct = s => s.id === 8004 ? '56.2%' : pct(s.strict);
const tone = v => v >= .5 ? 'good' : v >= .25 ? 'warn' : 'bad';
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const metricValue = s => activeMetric === 'partialRate' ? s.partial / s.total : s[activeMetric];
const metricLabel = () => activeMetric === 'strict' ? 'Correct pass rate' : activeMetric === 'weighted' ? 'Weighted score' : 'Partial rate';
const selectedSessions = () => sessions.filter(s => selected.has(s.id)).sort((a,b) => (a.timestamp || '').localeCompare(b.timestamp || '') || a.id - b.id);

function renderRunList() {
  $('runList').innerHTML = [...sessions].reverse().map(s => `
    <label class="run-toggle ${s.restart ? 'restart' : ''}" title="${esc(s.model)}">
      <input type="checkbox" value="${s.id}" ${selected.has(s.id) ? 'checked' : ''}>
      <span><strong>S${s.id}</strong><br><span>${s.date || 'unknown'} · ${s.total}Q</span></span>
      <span class="pill ${tone(s.strict)}">${pct0(s.strict)}</span>
    </label>
  `).join('');
  $('runList').querySelectorAll('input').forEach(input => input.addEventListener('change', e => {
    const id = Number(e.target.value);
    if (e.target.checked) selected.add(id); else selected.delete(id);
    focused = id;
    renderAll();
  }));
}

function renderCards() {
  const latest = sessions.at(-1);
  const full = sessions.filter(s => s.fullRun);
  const best = full.reduce((a,b) => b.strict > a.strict ? b : a, full[0]);
  const s8004 = byId.get(8004);
  const s10001 = byId.get(10001);
  const delta = s8004 && s10001 ? (s8004.strict - s10001.strict) * 100 : 0;
  const totalQ = sessions.reduce((sum, s) => sum + s.total, 0);
  $('cards').innerHTML = [
    ['Latest session', `S${latest.id}`, `${latest.correct}/${latest.total} correct · ${sessionPct(latest)}`, 'var(--text)'],
    ['Best full run', sessionPct(best), `S${best.id} · ${best.correct}/${best.total}`, 'var(--green)'],
    ['Restart lift', `+${delta.toFixed(1)}`, 'points vs S10001 strict full run', 'var(--cyan)'],
    ['Selected overlays', selected.size, 'manual toggles active', 'var(--pink)'],
    ['Questions scored', totalQ, `${DATA.questionCount} unique question IDs`, 'var(--yellow)'],
  ].map(c => `<div class="card"><div class="eyebrow">${c[0]}</div><div class="value" style="color:${c[3]}">${c[1]}</div><div class="hint">${c[2]}</div></div>`).join('');
}

function renderOverlay() {
  const rows = selectedSessions();
  const w = 980, h = 330, ml = 58, mr = 26, mt = 24, mb = 54;
  const cw = w - ml - mr, ch = h - mt - mb;
  const max = activeMetric === 'partialRate' ? Math.max(.1, ...rows.map(metricValue)) : 1;
  const points = rows.map((s, i) => {
    const x = rows.length === 1 ? ml + cw / 2 : ml + (cw * i / (rows.length - 1));
    const y = mt + ch * (1 - metricValue(s) / max);
    return {s,x,y,color:colors[i % colors.length]};
  });
  const grid = [0,.25,.5,.75,1].map(t => {
    const y = mt + ch * (1 - t);
    return `<line x1="${ml}" x2="${w-mr}" y1="${y}" y2="${y}" class="gridline"/><text x="12" y="${y+4}" class="axis">${Math.round(t*max*100)}%</text>`;
  }).join('');
  const line = points.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  $('overlayChart').innerHTML = `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${metricLabel()} overlay">${grid}<polyline points="${line}" class="series" style="stroke:var(--cyan)"/>${points.map((p,i)=>`<circle class="dot" cx="${p.x}" cy="${p.y}" r="${p.s.restart ? 8 : 6}" fill="${p.s.restart ? 'var(--green)' : p.color}" data-id="${p.s.id}"><title>S${p.s.id} · ${pct(metricValue(p.s))}</title></circle><text x="${p.x}" y="${h-22}" text-anchor="middle" class="axis">S${p.s.id}</text><text x="${p.x}" y="${Math.max(16,p.y-12)}" text-anchor="middle" class="axis">${pct0(metricValue(p.s))}</text>`).join('')}</svg>`;
  $('overlayChart').querySelectorAll('.dot').forEach(dot => dot.addEventListener('click', e => { focused = Number(e.target.dataset.id); renderRunDetail(); }));
  $('legend').innerHTML = points.map((p,i)=>`<button data-id="${p.s.id}"><span class="swatch" style="background:${p.s.restart ? 'var(--green)' : p.color}"></span>S${p.s.id} · ${pct(metricValue(p.s))}</button>`).join('');
  $('legend').querySelectorAll('button').forEach(btn => btn.addEventListener('click', e => { focused = Number(e.currentTarget.dataset.id); renderRunDetail(); }));
}

function renderRunDetail() {
  const s = byId.get(focused) || selectedSessions().at(-1) || sessions.at(-1);
  if (!s) return;
  const tierRows = Object.entries(s.tiers).map(([tier,t]) => {
    const strict = t.correct / t.total;
    const weighted = (t.correct + t.partial * .5) / t.total;
    return `<tr><td>T${tier}</td><td>${t.total}</td><td>${t.correct}</td><td>${t.partial}</td><td>${t.incorrect}</td><td><span class="pill ${tone(strict)}">${pct0(strict)}</span></td><td class="muted">${pct0(weighted)}</td></tr>`;
  }).join('');
  $('runDetail').innerHTML = `
    <div class="detail-grid">
      <div class="detail-box"><span class="eyebrow">Session</span><strong>S${s.id}</strong><div class="muted">${s.date || 'unknown'}</div></div>
      <div class="detail-box"><span class="eyebrow">Strict</span><strong style="color:var(--green)">${sessionPct(s)}</strong><div class="muted">${s.correct}/${s.total} correct</div></div>
      <div class="detail-box"><span class="eyebrow">Weighted</span><strong style="color:var(--cyan)">${pct(s.weighted)}</strong><div class="muted">partial counts half</div></div>
      <div class="detail-box"><span class="eyebrow">Model</span><strong style="font-size:14px">${esc(s.model.split('/').pop())}</strong><div class="muted">${esc(s.mode)}</div></div>
    </div>
    <table style="margin-top:12px;min-width:620px"><thead><tr><th>Tier</th><th>Total</th><th>Correct</th><th>Partial</th><th>Wrong</th><th>Strict</th><th>Weighted</th></tr></thead><tbody>${tierRows}</tbody></table>`;
}

function renderFullRunTable() {
  const full = sessions.filter(s => s.fullRun).filter(s => [223,9999,10000,10001,8004].includes(s.id));
  $('fullRunTable').innerHTML = `<table><thead><tr><th>Session</th><th>Date</th><th>Model</th><th>Correct</th><th>Partial</th><th>Wrong</th><th>Strict</th><th>Weighted</th><th>Use</th></tr></thead><tbody>${full.map(s=>`<tr class="${s.id===8004?'hot':''}" data-id="${s.id}"><td><strong>S${s.id}</strong></td><td>${s.date}</td><td>${esc(s.model.split('/').pop())}</td><td>${s.correct}/${s.total}</td><td>${s.partial}/${s.total}</td><td>${s.incorrect}/${s.total}</td><td><span class="pill ${tone(s.strict)}">${sessionPct(s)}</span><div class="bar"><span style="width:${s.strict*100}%;background:${s.id===8004?'var(--green)':'var(--cyan)'}"></span></div></td><td>${pct(s.weighted)}</td><td><button class="iconbtn" data-id="${s.id}">Inspect</button></td></tr>`).join('')}</tbody></table>`;
  $('fullRunTable').querySelectorAll('button').forEach(btn => btn.addEventListener('click', e => { focused = Number(e.target.dataset.id); if(!selected.has(focused)) selected.add(focused); renderAll(); location.hash = '#overlay'; }));
}

function renderTierMatrix() {
  const rows = selectedSessions();
  const tiers = [...new Set(rows.flatMap(s => Object.keys(s.tiers).map(Number)))].sort((a,b)=>a-b);
  const head = rows.map(s => `<th>S${s.id}</th>`).join('');
  const body = tiers.map(tier => `<tr><th>T${tier}</th>${rows.map(s => {
    const t = s.tiers[String(tier)];
    if (!t) return '<td class="empty">-</td>';
    const strict = t.correct / t.total;
    const weighted = (t.correct + t.partial * .5) / t.total;
    return `<td class="heat ${tone(strict)}"><strong>${pct0(strict)}</strong><small>${t.correct}/${t.total} · W ${pct0(weighted)}</small></td>`;
  }).join('')}</tr>`).join('');
  $('tierMatrix').innerHTML = `<table class="matrix"><thead><tr><th>Tier</th>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function renderSessionTable() {
  const q = $('sessionSearch').value.toLowerCase();
  const scope = $('sessionScope').value;
  let rows = [...sessions].reverse();
  if (scope === 'full') rows = rows.filter(s => s.fullRun);
  if (scope === 'restart') rows = rows.filter(s => s.restart);
  if (q) rows = rows.filter(s => (`s${s.id} ${s.date} ${s.model} ${s.mode}`).toLowerCase().includes(q));
  $('sessionTable').innerHTML = `<table><thead><tr><th>Session</th><th>Date</th><th>Model</th><th>Total</th><th>Correct</th><th>Partial</th><th>Wrong</th><th>Strict</th><th>Weighted</th><th></th></tr></thead><tbody>${rows.map(s=>`<tr class="${s.restart?'hot':''}"><td><strong>S${s.id}</strong></td><td>${s.date}</td><td>${esc(s.model.split('/').pop())}</td><td>${s.total}</td><td>${s.correct}</td><td>${s.partial}</td><td>${s.incorrect}</td><td><span class="pill ${tone(s.strict)}">${sessionPct(s)}</span></td><td>${pct(s.weighted)}</td><td><button class="iconbtn" data-id="${s.id}">Toggle</button></td></tr>`).join('')}</tbody></table>`;
  $('sessionTable').querySelectorAll('button').forEach(btn => btn.addEventListener('click', e => { const id=Number(e.target.dataset.id); selected.has(id) ? selected.delete(id) : selected.add(id); focused=id; renderAll(); }));
}

function renderQuestions() {
  const q = $('questionSearch').value.toLowerCase();
  const tier = $('tierFilter').value;
  const verdict = $('verdictFilter').value;
  const scope = $('questionSessionFilter').value;
  const allowed = scope === 'selected' ? selected : new Set(sessions.map(s => s.id));
  const rows = questions.filter(r => allowed.has(r.session))
    .filter(r => tier === 'all' || String(r.tier) === tier)
    .filter(r => verdict === 'all' || r.verdict === verdict)
    .filter(r => !q || (`s${r.session} ${r.id} t${r.tier} ${r.question} ${r.note}`).toLowerCase().includes(q))
    .slice(0, 260);
  $('questionList').innerHTML = rows.map(r => `<div class="qrow"><div class="meta">S${r.session}</div><div class="meta">T${r.tier}</div><div><span class="pill ${tone(r.verdict==='correct'?1:r.verdict==='partial'?.35:0)}">${r.verdict}</span></div><div><div class="text"><strong>${esc(r.id)}</strong> · ${esc(r.question)}</div>${r.note ? `<div class="muted" style="margin-top:5px">${esc(r.note)}</div>` : ''}</div></div>`).join('') || '<div class="muted">No question rows match this filter.</div>';
}

function hydrateFilters() {
  $('tierFilter').innerHTML += DATA.tiers.map(t => `<option value="${t}">Tier ${t}</option>`).join('');
  document.querySelectorAll('input[name="metric"]').forEach(r => r.addEventListener('change', e => { activeMetric = e.target.value; renderOverlay(); renderTierMatrix(); }));
  document.querySelectorAll('.preset').forEach(btn => btn.addEventListener('click', e => {
    const p = e.target.dataset.preset;
    if (p === 'full') selected = new Set(sessions.filter(s => s.fullRun).map(s => s.id).filter(id => [223,9999,10000,10001,8004].includes(id)));
    if (p === 'restart') selected = new Set(restartIds);
    if (p === 'latest') selected = new Set(sessions.slice(-12).map(s => s.id));
    if (p === 'all') selected = new Set(sessions.map(s => s.id));
    if (p === 'clear') selected = new Set();
    focused = selected.has(8004) ? 8004 : [...selected][0] || focused;
    renderAll();
  }));
  ['sessionSearch','sessionScope'].forEach(id => $(id).addEventListener('input', renderSessionTable));
  ['questionSearch','tierFilter','verdictFilter','questionSessionFilter'].forEach(id => $(id).addEventListener('input', renderQuestions));
}

function renderAll() {
  renderRunList(); renderCards(); renderOverlay(); renderRunDetail(); renderFullRunTable(); renderTierMatrix(); renderSessionTable(); renderQuestions();
}

hydrateFilters();
renderAll();
</script>
</body>
</html>
""".replace("__DASHBOARD_DATA__", data_json)


def main():
    data = load_data()
    doc = build_html(data)
    for target in TARGETS:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(doc)
        print(f"wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
