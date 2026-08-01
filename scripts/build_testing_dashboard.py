#!/usr/bin/env python3
"""Build the public Aura benchmark dashboard as a testing-focused static page."""

from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT = [ROOT / "index.html", ROOT / "dashboard.html", ROOT / "dashboard" / "index.html"]


FULL_RUN_IDS = [223, 9999, 10000, 10001, 8004]
HIGHLIGHT_IDS = {8004, 8005}


def verdict(q: dict) -> str:
    v = q.get("verdict")
    if v in {"correct", "partial", "incorrect"}:
        return v
    score = q.get("score")
    if isinstance(score, dict) and score.get("verdict") in {"correct", "partial", "incorrect"}:
        return score["verdict"]
    return "incorrect"


def load_sessions() -> list[dict]:
    sessions = []
    for path in sorted(RESULTS.glob("session_*.json")):
        try:
            data = json.loads(path.read_text())
        except Exception as exc:
            print(f"warning: {path.name}: {exc}")
            continue
        questions = data.get("questions") or []
        if not questions:
            continue
        tiers = defaultdict(lambda: {"correct": 0, "partial": 0, "incorrect": 0, "total": 0})
        correct = partial = incorrect = 0
        for q in questions:
            v = verdict(q)
            tier = int(q.get("tier") or 0)
            tiers[tier]["total"] += 1
            tiers[tier][v] += 1
            if v == "correct":
                correct += 1
            elif v == "partial":
                partial += 1
            else:
                incorrect += 1
        total = len(questions)
        correct_rate = correct / total if total else 0
        weighted_rate = (correct + partial * 0.5) / total if total else 0
        raw_session = data.get("session") or path.stem.split("_")[-1]
        try:
            session_id = int(raw_session)
        except (TypeError, ValueError):
            print(f"warning: skipping {path.name}: no numeric session id")
            continue
        sessions.append(
            {
                "session": session_id,
                "timestamp": data.get("timestamp") or "",
                "date": (data.get("timestamp") or "")[:10],
                "model": data.get("model") or "unknown",
                "total": total,
                "correct": correct,
                "partial": partial,
                "incorrect": incorrect,
                "correct_rate": correct_rate,
                "weighted_rate": weighted_rate,
                "tiers": dict(sorted(tiers.items())),
                "mode": data.get("mode") or "headless",
            }
        )
    return sorted(sessions, key=lambda s: (s["timestamp"], s["session"]))


def pct(v: float, places: int = 1) -> str:
    return f"{v * 100:.{places}f}%"


def esc(v: object) -> str:
    return html.escape(str(v), quote=True)


def bar(width: float, color: str = "var(--green)") -> str:
    return (
        '<div class="bar"><span style="width:'
        + f"{max(0, min(100, width * 100)):.1f}%;background:{color}"
        + '"></span></div>'
    )


def tone(rate: float) -> str:
    if rate >= 0.5:
        return "good"
    if rate >= 0.25:
        return "warn"
    return "bad"


def trend_svg(full_runs: list[dict]) -> str:
    width, height = 840, 220
    pad_l, pad_r, pad_t, pad_b = 54, 24, 20, 42
    chart_w = width - pad_l - pad_r
    chart_h = height - pad_t - pad_b
    if len(full_runs) < 2:
        return ""
    pts = []
    for i, s in enumerate(full_runs):
        x = pad_l + chart_w * i / (len(full_runs) - 1)
        y = pad_t + chart_h * (1 - s["correct_rate"])
        pts.append((x, y, s))
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts)
    circles = []
    labels = []
    for x, y, s in pts:
        highlight = s["session"] == 8004
        circles.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{7 if highlight else 5}" '
            f'class="{"dot hot" if highlight else "dot"}"><title>S{s["session"]}: {pct(s["correct_rate"])}</title></circle>'
        )
        labels.append(
            f'<text x="{x:.1f}" y="{height - 16}" text-anchor="middle" class="axis">S{s["session"]}</text>'
        )
        labels.append(
            f'<text x="{x:.1f}" y="{max(14, y - 12):.1f}" text-anchor="middle" class="point-label">{pct(s["correct_rate"])}</text>'
        )
    grid = "\n".join(
        f'<line x1="{pad_l}" x2="{width-pad_r}" y1="{pad_t + chart_h*(1-t/100):.1f}" y2="{pad_t + chart_h*(1-t/100):.1f}" class="gridline"/>'
        f'<text x="12" y="{pad_t + chart_h*(1-t/100)+4:.1f}" class="axis">{t}%</text>'
        for t in (0, 25, 50, 75, 100)
    )
    return f"""
      <svg viewBox="0 0 {width} {height}" role="img" aria-label="Full-run pass-rate trend">
        {grid}
        <polyline points="{line}" class="trend-line"/>
        {''.join(circles)}
        {''.join(labels)}
      </svg>
    """


def full_run_rows(full_runs: list[dict]) -> str:
    rows = []
    for s in full_runs:
        hot = " is-hot" if s["session"] == 8004 else ""
        rows.append(
            f"""
            <tr class="{hot.strip()}">
              <td><strong>S{s["session"]}</strong></td>
              <td>{esc(s["date"])}</td>
              <td>{esc(s["model"].split("/")[-1])}</td>
              <td>{s["correct"]}/{s["total"]}</td>
              <td>{s["partial"]}/{s["total"]}</td>
              <td><span class="pill {tone(s["correct_rate"])}">{pct(s["correct_rate"])}</span></td>
              <td>{bar(s["correct_rate"], "var(--green)" if s["session"] == 8004 else "var(--cyan)")}</td>
              <td>{'Restart baseline, best full run' if s["session"] == 8004 else 'Previous full run'}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def latest_rows(sessions: list[dict], n: int = 14) -> str:
    rows = []
    for s in reversed(sessions[-n:]):
        hot = " is-hot" if s["session"] in HIGHLIGHT_IDS else ""
        rows.append(
            f"""
            <tr class="{hot.strip()}">
              <td><strong>S{s["session"]}</strong></td>
              <td>{esc(s["date"])}</td>
              <td>{esc(s["model"].split("/")[-1])}</td>
              <td>{s["total"]}</td>
              <td>{s["correct"]}</td>
              <td>{s["partial"]}</td>
              <td>{s["incorrect"]}</td>
              <td><span class="pill {tone(s["correct_rate"])}">{pct(s["correct_rate"])}</span></td>
              <td><span class="muted">{pct(s["weighted_rate"])}</span></td>
            </tr>
            """
        )
    return "\n".join(rows)


def tier_matrix(full_runs: list[dict]) -> str:
    tiers = sorted({tier for s in full_runs for tier in s["tiers"]})
    header = "".join(f"<th>S{s['session']}</th>" for s in full_runs)
    rows = []
    for tier in tiers:
        cells = []
        for s in full_runs:
            t = s["tiers"].get(tier)
            if not t:
                cells.append('<td class="empty">-</td>')
                continue
            rate = t["correct"] / t["total"] if t["total"] else 0
            cells.append(
                f'<td class="heat {tone(rate)}"><strong>{pct(rate, 0)}</strong><span>{t["correct"]}/{t["total"]}</span></td>'
            )
        rows.append(f"<tr><th>T{tier}</th>{''.join(cells)}</tr>")
    return f"""
      <table class="matrix-table">
        <thead><tr><th>Tier</th>{header}</tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    """


def build() -> str:
    sessions = load_sessions()
    full_runs = [s for s in sessions if s["session"] in FULL_RUN_IDS]
    latest = sessions[-1]
    restart = next(s for s in sessions if s["session"] == 8004)
    tier_slice = next(s for s in sessions if s["session"] == 8005)
    best_full = max(full_runs, key=lambda s: s["correct_rate"])
    total_questions = sum(s["total"] for s in sessions)
    delta = restart["correct_rate"] - next(s for s in sessions if s["session"] == 10001)["correct_rate"]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aura Benchmark Testing Dashboard</title>
<style>
  :root {{
    --bg:#071016; --panel:#101a27; --panel2:#141f2e; --line:#26384e;
    --text:#eaf2ff; --muted:#91a4bb; --cyan:#63d9ff; --green:#6ee58a;
    --yellow:#f2c15b; --red:#ff6b57; --ink:#071016;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text); font-family:Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; }}
  header {{ border-bottom:1px solid var(--line); background:linear-gradient(180deg,#0d1924,#071016); }}
  .wrap {{ width:min(1480px, calc(100vw - 40px)); margin:0 auto; }}
  .top {{ display:flex; align-items:center; justify-content:space-between; gap:20px; padding:22px 0 18px; }}
  .brand {{ display:flex; align-items:center; gap:14px; }}
  .mark {{ width:42px; height:42px; border:1px solid rgba(99,217,255,.45); border-radius:10px; display:grid; place-items:center; color:var(--cyan); font-weight:800; background:#0b1723; }}
  h1 {{ margin:0; font-size:25px; letter-spacing:.01em; }}
  .sub {{ color:var(--muted); font-size:13px; margin-top:4px; }}
  .live {{ display:flex; align-items:center; gap:8px; color:var(--green); font:700 12px ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing:.12em; text-transform:uppercase; }}
  .live::before {{ content:""; width:8px; height:8px; border-radius:50%; background:var(--green); box-shadow:0 0 18px var(--green); }}
  .hero {{ padding:22px 0; border-top:1px solid rgba(99,217,255,.08); }}
  .restart {{ border:1px solid rgba(110,229,138,.55); background:linear-gradient(135deg,rgba(110,229,138,.18),rgba(99,217,255,.08)); border-radius:8px; padding:18px 20px; display:grid; grid-template-columns:1.3fr .7fr; gap:18px; }}
  .restart h2 {{ margin:0 0 8px; color:var(--green); font-size:22px; }}
  .restart p {{ margin:0; color:#d5e5f7; line-height:1.5; }}
  .sequence {{ font:700 13px ui-monospace, SFMono-Regular, Menlo, monospace; color:var(--muted); line-height:1.8; }}
  .sequence strong {{ color:var(--green); }}
  main {{ padding:22px 0 44px; }}
  .cards {{ display:grid; grid-template-columns:repeat(5,minmax(150px,1fr)); gap:12px; margin-bottom:16px; }}
  .card, .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; }}
  .card {{ padding:16px; }}
  .label {{ color:var(--muted); font:700 11px ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing:.12em; text-transform:uppercase; }}
  .value {{ font-size:31px; font-weight:800; margin-top:8px; line-height:1; }}
  .hint {{ color:var(--muted); font-size:12px; margin-top:8px; }}
  .grid {{ display:grid; grid-template-columns:1.25fr .75fr; gap:16px; margin-bottom:16px; }}
  .panel {{ padding:18px; overflow:auto; }}
  .panel h3 {{ margin:0 0 12px; font-size:15px; letter-spacing:.08em; text-transform:uppercase; color:#cfe3f8; }}
  table {{ width:100%; border-collapse:collapse; min-width:760px; }}
  th,td {{ border-bottom:1px solid var(--line); padding:10px 11px; text-align:left; font-size:13px; }}
  th {{ color:var(--muted); font:700 11px ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing:.1em; text-transform:uppercase; background:#0c1723; }}
  tr.is-hot td {{ background:rgba(110,229,138,.08); }}
  .pill {{ display:inline-block; min-width:58px; text-align:center; padding:4px 8px; border-radius:999px; font:800 12px ui-monospace, SFMono-Regular, Menlo, monospace; }}
  .pill.good {{ color:var(--green); background:rgba(110,229,138,.12); border:1px solid rgba(110,229,138,.35); }}
  .pill.warn {{ color:var(--yellow); background:rgba(242,193,91,.12); border:1px solid rgba(242,193,91,.35); }}
  .pill.bad {{ color:var(--red); background:rgba(255,107,87,.11); border:1px solid rgba(255,107,87,.32); }}
  .bar {{ width:130px; height:8px; border-radius:999px; background:#203044; overflow:hidden; }}
  .bar span {{ display:block; height:100%; border-radius:999px; }}
  svg {{ width:100%; height:auto; display:block; }}
  .gridline {{ stroke:#24364b; stroke-width:1; }}
  .axis {{ fill:var(--muted); font:11px ui-monospace, SFMono-Regular, Menlo, monospace; }}
  .trend-line {{ fill:none; stroke:var(--cyan); stroke-width:3; }}
  .dot {{ fill:var(--cyan); stroke:#071016; stroke-width:3; }}
  .dot.hot {{ fill:var(--green); }}
  .point-label {{ fill:#dcecff; font:700 12px ui-monospace, SFMono-Regular, Menlo, monospace; }}
  .matrix-table {{ min-width:900px; }}
  .matrix-table th:first-child {{ position:sticky; left:0; z-index:2; }}
  .heat {{ text-align:center; }}
  .heat span {{ display:block; color:rgba(234,242,255,.72); font-size:11px; margin-top:2px; }}
  .heat.good {{ background:rgba(110,229,138,.24); color:#dfffe7; }}
  .heat.warn {{ background:rgba(242,193,91,.24); color:#fff4d8; }}
  .heat.bad {{ background:rgba(255,107,87,.22); color:#ffe1dd; }}
  .empty {{ color:#52667e; text-align:center; }}
  .muted {{ color:var(--muted); }}
  .footer {{ color:var(--muted); font-size:12px; padding-top:8px; }}
  @media (max-width: 980px) {{
    .restart, .grid {{ grid-template-columns:1fr; }}
    .cards {{ grid-template-columns:repeat(2,1fr); }}
    .wrap {{ width:min(100vw - 24px, 1480px); }}
  }}
</style>
</head>
<body>
<header>
  <div class="wrap top">
    <div class="brand">
      <div class="mark">A</div>
      <div>
        <h1>Aura Benchmark Testing Dashboard</h1>
        <div class="sub">Public test runs, scorer health, and full-run comparison for the 50-day trial.</div>
      </div>
    </div>
    <div class="live">Testing restarted</div>
  </div>
  <div class="wrap hero">
    <section class="restart">
      <div>
        <h2>Benchmark testing restarted on 2026-08-01</h2>
        <p>S8004 completed the full 320-question benchmark with <strong>{restart["correct"]}/{restart["total"]} correct ({pct(restart["correct_rate"])})</strong>, the best full-run result so far. S8005 then reran the healthy tier 3+4 slice after scorer fixes with <strong>{tier_slice["correct"]}/{tier_slice["total"]} correct ({pct(tier_slice["correct_rate"], 0)})</strong>.</p>
      </div>
      <div class="sequence">S223 31.9% -> S9999 11.9% -> S10000 11.9% -> S10001 38.1% -> <strong>S8004 56.2%</strong></div>
    </section>
  </div>
</header>
<main class="wrap">
  <section class="cards">
    <div class="card"><div class="label">Latest Session</div><div class="value">S{latest["session"]}</div><div class="hint">{latest["correct"]}/{latest["total"]} correct · {pct(latest["correct_rate"])}</div></div>
    <div class="card"><div class="label">Best Full Run</div><div class="value" style="color:var(--green)">{pct(best_full["correct_rate"])}</div><div class="hint">S{best_full["session"]} · {best_full["correct"]}/{best_full["total"]}</div></div>
    <div class="card"><div class="label">Restart Lift</div><div class="value" style="color:var(--cyan)">+{delta*100:.1f}</div><div class="hint">points vs S10001 full run</div></div>
    <div class="card"><div class="label">Sessions Tracked</div><div class="value">{len(sessions)}</div><div class="hint">Newest rows appear first</div></div>
    <div class="card"><div class="label">Questions Scored</div><div class="value">{total_questions}</div><div class="hint">Raw JSON-backed results</div></div>
  </section>

  <section class="grid">
    <div class="panel">
      <h3>Full-Run Pass Rate Trend</h3>
      {trend_svg(full_runs)}
    </div>
    <div class="panel">
      <h3>Restart Run Summary</h3>
      <table style="min-width:420px">
        <tbody>
          <tr><th>Run</th><td>S8004 full benchmark</td></tr>
          <tr><th>Model</th><td>{esc(restart["model"])}</td></tr>
          <tr><th>Correct</th><td>{restart["correct"]}/{restart["total"]} ({pct(restart["correct_rate"])})</td></tr>
          <tr><th>Partial</th><td>{restart["partial"]}/{restart["total"]}</td></tr>
          <tr><th>Follow-up</th><td>S8005 tier 3+4: {tier_slice["correct"]}/{tier_slice["total"]} correct</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <section class="panel">
    <h3>Comparison Table: Complete 320-Question Runs</h3>
    <table>
      <thead><tr><th>Session</th><th>Date</th><th>Model</th><th>Correct</th><th>Partial</th><th>Correct Pass Rate</th><th>Bar</th><th>Interpretation</th></tr></thead>
      <tbody>{full_run_rows(full_runs)}</tbody>
    </table>
  </section>

  <section class="panel" style="margin-top:16px">
    <h3>Latest Benchmark Sessions</h3>
    <table>
      <thead><tr><th>Session</th><th>Date</th><th>Model</th><th>Total</th><th>Correct</th><th>Partial</th><th>Incorrect</th><th>Correct Pass Rate</th><th>Weighted</th></tr></thead>
      <tbody>{latest_rows(sessions)}</tbody>
    </table>
  </section>

  <section class="panel" style="margin-top:16px">
    <h3>Tier Coverage Matrix: Full-Run Comparison</h3>
    {tier_matrix(full_runs)}
  </section>
  <div class="footer">Generated from results/session_*.json. Correct pass rate is strict correct/total; weighted score counts partial answers as half credit.</div>
</main>
</body>
</html>
"""


def main() -> None:
    html_doc = build()
    for path in OUT:
        path.write_text(html_doc)
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
