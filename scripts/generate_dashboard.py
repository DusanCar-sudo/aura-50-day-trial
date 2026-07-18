#!/usr/bin/env python3
"""
Aura 50-Day Trial — dashboard generator.
Reads all session JSON files from results/, generates a rich HTML dashboard.
Run from the aura-50-day-trial repo root.
"""

import json
import glob
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
RESULTS_DIR = ROOT / "results"
OUTPUT_FILE = ROOT / "index.html"

TIER_LABELS = {
    1: "Fundamentals", 2: "Diagnostics", 3: "Code Gen",
    4: "Memory", 5: "Ruby Alternator", 6: "Source Code",
    7: "Safety", 8: "Synthesis"
}


def load_sessions():
    sessions = []
    for f in sorted(RESULTS_DIR.glob("session_[0-9]*.json")):
        try:
            data = json.loads(f.read_text())
            questions = data.get("questions", [])
            total = len(questions)
            if total == 0:
                continue
            correct = sum(1 for q in questions if q.get("verdict") == "correct" or q.get("score", {}).get("verdict") == "correct")
            partial = sum(1 for q in questions if q.get("verdict") == "partial" or q.get("score", {}).get("verdict") == "partial")
            score = round(100 * (correct + partial * 0.5) / total, 1)

            # Per-tier breakdown
            tiers = {}
            for q in questions:
                t = q.get("tier", 0)
                v = q.get("verdict") or q.get("score", {}).get("verdict", "incorrect")
                if t not in tiers:
                    tiers[t] = {"correct": 0, "partial": 0, "total": 0}
                tiers[t]["total"] += 1
                if v == "correct":
                    tiers[t]["correct"] += 1
                elif v == "partial":
                    tiers[t]["partial"] += 1

            sessions.append({
                "session": data.get("session"),
                "model": data.get("model", "unknown"),
                "timestamp": data.get("timestamp", ""),
                "total": total,
                "correct": correct,
                "partial": partial,
                "score": score,
                "tiers": tiers,
                "mode": data.get("mode", "headless"),
            })
        except Exception as e:
            print(f"Warning: {f}: {e}")
    return sessions


def load_ruby_stats():
    snapshots = []
    for f in sorted(RESULTS_DIR.glob("ruby-stats-*.json")):
        try:
            data = json.loads(f.read_text())
            date = f.name.replace("ruby-stats-", "").replace(".json", "")
            snapshots.append({
                "date": date,
                "catchRate": data.get("verificationCatchRate"),
                "episodeStats": data.get("episodeStats", {}),
                "competence": data.get("competence", []),
            })
        except Exception as e:
            print(f"Warning: {f}: {e}")
    return snapshots


def build_html(sessions, ruby_snapshots):
    # Build data for charts
    s_labels = [f"S{s['session']}" for s in sessions]
    s_scores = [s['score'] for s in sessions]
    s_correct = [round(100 * s['correct'] / s['total'], 1) for s in sessions]
    s_models = [s['model'].split('/')[-1] for s in sessions]

    # Per-tier data for latest session
    latest = sessions[-1] if sessions else None
    tier_labels = []
    tier_scores = []
    if latest:
        for t in sorted(latest['tiers'].keys()):
            td = latest['tiers'][t]
            tier_labels.append(TIER_LABELS.get(t, f"Tier {t}"))
            sc = round(100 * (td['correct'] + td['partial'] * 0.5) / td['total'], 1) if td['total'] else 0
            tier_scores.append(sc)

    # Ruby catch rate
    catch_dates = [s['date'] for s in ruby_snapshots]
    catch_rates = [round(100 * s['catchRate'], 1) if s.get('catchRate') is not None else None for s in ruby_snapshots]

    # Stats summary
    latest_ruby = ruby_snapshots[-1] if ruby_snapshots else {}
    ep = latest_ruby.get("episodeStats", {})
    total_episodes = ep.get("total", "—")
    ruby_successes = ep.get("rubySuccesses", "—")
    ruby_failures = ep.get("rubyFailures", "—")
    ready = ep.get("readyForFineTune", False)

    latest_score = sessions[-1]['score'] if sessions else 0
    latest_model = sessions[-1]['model'].split('/')[-1] if sessions else "—"
    session_count = len(sessions)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aura 50-Day Trial</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f1724;
    --panel: #1a2332;
    --panel2: #1e2a3d;
    --border: #2a3a52;
    --text: #e8e8e8;
    --muted: #7a8a9a;
    --terracotta: #cc785c;
    --terracotta2: #e8956e;
    --teal: #4a9e8e;
    --blue: #4a7fb5;
    --green: #5a9e6e;
    --gold: #b5954a;
    --font: -apple-system, 'Segoe UI', system-ui, sans-serif;
    --mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: var(--font);
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 0;
  }}

  /* Header */
  .header {{
    background: linear-gradient(135deg, #0f1724 0%, #1a2540 50%, #0f1724 100%);
    border-bottom: 1px solid var(--border);
    padding: 2.5rem 2rem 2rem;
    position: relative;
    overflow: hidden;
  }}
  .header::before {{
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(204,120,92,0.06) 0%, transparent 70%);
    pointer-events: none;
  }}
  .header-inner {{
    max-width: 1200px;
    margin: 0 auto;
  }}
  .header-tag {{
    font-size: 0.7rem;
    font-family: var(--mono);
    color: var(--terracotta);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
  }}
  .header h1 {{
    font-size: 2.2rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.02em;
    line-height: 1.1;
  }}
  .header h1 span {{ color: var(--terracotta); }}
  .header-sub {{
    color: var(--muted);
    font-size: 0.95rem;
    margin-top: 0.5rem;
    max-width: 600px;
  }}
  .header-meta {{
    display: flex;
    gap: 2rem;
    margin-top: 1.5rem;
    flex-wrap: wrap;
  }}
  .meta-item {{
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }}
  .meta-value {{
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--terracotta);
    font-family: var(--mono);
    line-height: 1;
  }}
  .meta-label {{
    font-size: 0.72rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }}
  .badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(90,158,110,0.15);
    border: 1px solid rgba(90,158,110,0.3);
    color: var(--green);
    font-size: 0.72rem;
    font-family: var(--mono);
    padding: 0.25rem 0.6rem;
    border-radius: 4px;
    margin-top: 1rem;
    width: fit-content;
  }}
  .badge.warning {{
    background: rgba(181,149,74,0.15);
    border-color: rgba(181,149,74,0.3);
    color: var(--gold);
  }}

  /* Main layout */
  .main {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    display: grid;
    gap: 1.5rem;
  }}

  /* Cards */
  .card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.5rem;
  }}
  .card-title {{
    font-size: 0.72rem;
    font-family: var(--mono);
    color: var(--terracotta);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }}
  .card-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }}

  /* Chart grid */
  .chart-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }}
  .chart-full {{ grid-column: 1 / -1; }}
  canvas {{ width: 100% !important; }}

  /* Session table */
  .session-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }}
  .session-table th {{
    text-align: left;
    padding: 0.5rem 0.75rem;
    color: var(--muted);
    font-size: 0.7rem;
    font-family: var(--mono);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-bottom: 1px solid var(--border);
    font-weight: 400;
  }}
  .session-table td {{
    padding: 0.6rem 0.75rem;
    border-bottom: 1px solid rgba(42,58,82,0.5);
    color: var(--text);
  }}
  .session-table tr:last-child td {{ border-bottom: none; }}
  .session-table tr:hover td {{ background: rgba(255,255,255,0.02); }}
  .score-pill {{
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-family: var(--mono);
    font-size: 0.82rem;
    font-weight: 600;
  }}
  .score-high {{ background: rgba(90,158,110,0.2); color: var(--green); }}
  .score-mid {{ background: rgba(181,149,74,0.2); color: var(--gold); }}
  .score-low {{ background: rgba(181,80,57,0.2); color: #e05535; }}
  .mode-pill {{
    font-size: 0.68rem;
    font-family: var(--mono);
    color: var(--muted);
    background: rgba(255,255,255,0.05);
    padding: 0.1rem 0.4rem;
    border-radius: 3px;
  }}
  .mode-tui {{ color: var(--teal); background: rgba(74,158,142,0.1); }}

  /* Ruby stats row */
  .ruby-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
  }}
  .ruby-stat {{
    background: var(--panel2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
  }}
  .ruby-stat-value {{
    font-size: 1.6rem;
    font-weight: 700;
    font-family: var(--mono);
    color: var(--terracotta);
    line-height: 1;
    margin-bottom: 0.3rem;
  }}
  .ruby-stat-label {{
    font-size: 0.7rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }}

  .footer {{
    text-align: center;
    padding: 2rem;
    color: var(--muted);
    font-size: 0.75rem;
    font-family: var(--mono);
    border-top: 1px solid var(--border);
    margin-top: 1rem;
  }}

  @media (max-width: 768px) {{
    .chart-grid {{ grid-template-columns: 1fr; }}
    .ruby-grid {{ grid-template-columns: 1fr 1fr; }}
    .header h1 {{ font-size: 1.6rem; }}
    .meta-value {{ font-size: 1.4rem; }}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-inner">
    <div class="header-tag">▸ aura-50-day-trial / live</div>
    <h1>Ruby Alternator<br><span>50-Day Benchmark Trial</span></h1>
    <p class="header-sub">Daily, unedited, public proof — does Aura's local+cloud routing system get measurably better over 50 days of real use?</p>
    <div class="header-meta">
      <div class="meta-item">
        <div class="meta-value">{session_count}</div>
        <div class="meta-label">Sessions run</div>
      </div>
      <div class="meta-item">
        <div class="meta-value">{latest_score}%</div>
        <div class="meta-label">Latest score</div>
      </div>
      <div class="meta-item">
        <div class="meta-value">{total_episodes}</div>
        <div class="meta-label">Episodes captured</div>
      </div>
      <div class="meta-item">
        <div class="meta-value">{latest_model}</div>
        <div class="meta-label">Last model used</div>
      </div>
    </div>
    <div class="badge {'warning' if not ready else ''}">
      {'⚡ Fine-tune dataset ready' if ready else f'⟳ Accumulating episodes — {ruby_successes} successes / {ruby_failures} failures captured'}
    </div>
  </div>
</div>

<div class="main">

  <!-- Ruby stats -->
  <div class="card">
    <div class="card-title">Ruby Alternator — episode store</div>
    <div class="ruby-grid">
      <div class="ruby-stat">
        <div class="ruby-stat-value">{total_episodes}</div>
        <div class="ruby-stat-label">Total episodes</div>
      </div>
      <div class="ruby-stat">
        <div class="ruby-stat-value" style="color:var(--green)">{ruby_successes}</div>
        <div class="ruby-stat-label">Ruby successes</div>
      </div>
      <div class="ruby-stat">
        <div class="ruby-stat-value" style="color:#e05535">{ruby_failures}</div>
        <div class="ruby-stat-label">Caught & escalated</div>
      </div>
      <div class="ruby-stat">
        <div class="ruby-stat-value" style="color:var(--gold)">{round(100 * int(ruby_failures) / (int(ruby_successes) + int(ruby_failures)), 1) if ruby_successes != '—' and int(ruby_successes) + int(ruby_failures) > 0 else '—'}%</div>
        <div class="ruby-stat-label">Verification catch rate</div>
      </div>
    </div>
  </div>

  <!-- Charts -->
  <div class="chart-grid">
    <div class="card chart-full">
      <div class="card-title">Benchmark score by session</div>
      <canvas id="scoreChart" height="200"></canvas>
    </div>
    <div class="card">
      <div class="card-title">Score by tier — latest session</div>
      <canvas id="tierChart" height="260"></canvas>
    </div>
    <div class="card">
      <div class="card-title">Verification catch rate over time</div>
      <canvas id="catchChart" height="260"></canvas>
    </div>
  </div>

  <!-- Session log -->
  <div class="card">
    <div class="card-title">Session log</div>
    <table class="session-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Model</th>
          <th>Questions</th>
          <th>Score</th>
          <th>Mode</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        {''.join(f"""
        <tr>
          <td style="font-family:var(--mono);color:var(--muted)">S{s['session']}</td>
          <td style="font-family:var(--mono);font-size:0.8rem">{s['model'].split('/')[-1]}</td>
          <td style="font-family:var(--mono);color:var(--muted)">{s['correct']}/{s['total']} correct</td>
          <td><span class="score-pill {'score-high' if s['score'] >= 75 else 'score-mid' if s['score'] >= 40 else 'score-low'}">{s['score']}%</span></td>
          <td><span class="mode-pill {'mode-tui' if 'tui' in s.get('mode','') else ''}">{s.get('mode','headless')}</span></td>
          <td style="color:var(--muted);font-size:0.78rem;font-family:var(--mono)">{s['timestamp'][:10]}</td>
        </tr>""" for s in sessions)}
      </tbody>
    </table>
  </div>

</div>

<div class="footer">
  github.com/DusanCar-sudo/aura-50-day-trial &nbsp;·&nbsp; updated {now} &nbsp;·&nbsp; aura-code v0.10.5
</div>

<script>
const TERRACOTTA = '#cc785c';
const GREEN = '#5a9e6e';
const GOLD = '#b5954a';
const BLUE = '#4a7fb5';
const TEAL = '#4a9e8e';
const MUTED = '#7a8a9a';

const defaults = {{
  color: '#e8e8e8',
  borderColor: '#2a3a52',
  font: {{ family: "-apple-system, 'Segoe UI', system-ui, sans-serif" }},
}};
Chart.defaults.color = defaults.color;
Chart.defaults.borderColor = defaults.borderColor;

const gridOpts = {{
  grid: {{ color: 'rgba(42,58,82,0.5)' }},
  ticks: {{ color: MUTED, font: {{ size: 11 }} }},
}};

// Score trend
new Chart(document.getElementById('scoreChart'), {{
  type: 'line',
  data: {{
    labels: {json.dumps(s_labels)},
    datasets: [
      {{
        label: 'Weighted score %',
        data: {json.dumps(s_scores)},
        borderColor: TERRACOTTA,
        backgroundColor: 'rgba(204,120,92,0.08)',
        fill: true,
        tension: 0.3,
        pointBackgroundColor: TERRACOTTA,
        pointRadius: 5,
        pointHoverRadius: 7,
        borderWidth: 2.5,
      }},
      {{
        label: 'Correct only %',
        data: {json.dumps(s_correct)},
        borderColor: GREEN,
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.3,
        pointBackgroundColor: GREEN,
        pointRadius: 4,
        borderWidth: 1.5,
        borderDash: [4, 3],
      }}
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ position: 'top', labels: {{ color: MUTED, font: {{ size: 11 }} }} }},
      tooltip: {{ backgroundColor: '#1e2a3d', borderColor: '#2a3a52', borderWidth: 1 }},
    }},
    scales: {{
      x: gridOpts,
      y: {{ ...gridOpts, min: 0, max: 100, ticks: {{ ...gridOpts.ticks, callback: v => v + '%' }} }},
    }},
  }}
}});

// Tier breakdown
new Chart(document.getElementById('tierChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(tier_labels)},
    datasets: [{{
      label: 'Score %',
      data: {json.dumps(tier_scores)},
      backgroundColor: {json.dumps(tier_scores)}.map(v =>
        v >= 80 ? 'rgba(90,158,110,0.7)' : v >= 60 ? 'rgba(181,149,74,0.7)' : 'rgba(204,120,92,0.7)'
      ),
      borderColor: {json.dumps(tier_scores)}.map(v =>
        v >= 80 ? GREEN : v >= 60 ? GOLD : TERRACOTTA
      ),
      borderWidth: 1.5,
      borderRadius: 4,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{ backgroundColor: '#1e2a3d', borderColor: '#2a3a52', borderWidth: 1 }},
    }},
    scales: {{
      x: {{ ...gridOpts, ticks: {{ ...gridOpts.ticks, font: {{ size: 10 }} }} }},
      y: {{ ...gridOpts, min: 0, max: 100, ticks: {{ ...gridOpts.ticks, callback: v => v + '%' }} }},
    }},
  }}
}});

// Catch rate
new Chart(document.getElementById('catchChart'), {{
  type: 'line',
  data: {{
    labels: {json.dumps(catch_dates)},
    datasets: [{{
      label: 'Verification catch rate %',
      data: {json.dumps(catch_rates)},
      borderColor: GOLD,
      backgroundColor: 'rgba(181,149,74,0.08)',
      fill: true,
      tension: 0.3,
      pointBackgroundColor: GOLD,
      pointRadius: 5,
      borderWidth: 2.5,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        backgroundColor: '#1e2a3d',
        borderColor: '#2a3a52',
        borderWidth: 1,
        callbacks: {{ afterLabel: () => '↓ lower = Ruby improving' }}
      }},
    }},
    scales: {{
      x: gridOpts,
      y: {{ ...gridOpts, min: 0, max: 100, ticks: {{ ...gridOpts.ticks, callback: v => v + '%' }} }},
    }},
  }}
}});
</script>
</body>
</html>"""
    return html


def main():
    sessions = load_sessions()
    ruby_snapshots = load_ruby_stats()
    html = build_html(sessions, ruby_snapshots)
    OUTPUT_FILE.write_text(html)
    print(f"Dashboard written to {OUTPUT_FILE} ({len(sessions)} sessions, {len(ruby_snapshots)} ruby-stats snapshots)")


if __name__ == "__main__":
    main()
