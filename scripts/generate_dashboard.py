#!/usr/bin/env python3
"""
Aura 50-Day Trial — dashboard generator.

dashboard.html is a self-contained bundle (Dušan's hand-tuned design): the page
markup lives in a `__bundler/template` JSON string and every asset — including
the data payload — is a gzip+base64 entry in the `__bundler/manifest`. This
script does NOT regenerate the page; it only re-encodes the `window.AURA_DATA`
resource inside the existing bundle so the design survives untouched, and
patches the template to add the Matrix tab if it's not already there.

Payload:
  SESSIONS         — per-session aggregates (unchanged shape, used by all tabs)
  RUBY_SNAPSHOTS   — ruby-stats-*.json snapshots (unchanged shape)
  QUESTION_RUNS    — question id -> chronological attempt history, each attempt
                     keeping session / timestamp / verdict / model / note so any
                     verdict on the dashboard can be traced to the run that
                     produced it
  RUNS             — attempt-generation aggregates: RUNS[n] covers every
                     question's (n+1)-th attempt, with per-tier tallies
  TIER_RUN_MATRIX  — tier × run-generation heatmap data

Run from the aura-50-day-trial repo root:
    python3 scripts/generate_dashboard.py
    cp dashboard.html index.html
"""
import base64
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
RESULTS_DIR = ROOT / "results"
BUNDLE_FILE = ROOT / "dashboard.html"

DATA_MARKER = b"window.AURA_DATA"

MONTH_NAMES = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}


def q_verdict(q):
    v = q.get("verdict")
    if not v:
        score = q.get("score") or {}
        if isinstance(score, dict):
            v = score.get("verdict")
    return v if v in ("correct", "partial") else "incorrect"


def load_sessions():
    """Per-session aggregates + raw per-question rows, one pass over results/."""
    sessions = []
    raw = []
    for f in sorted(RESULTS_DIR.glob("session_[0-9]*.json")):
        try:
            data = json.loads(f.read_text())
        except Exception as e:
            print(f"Warning: {f}: {e}")
            continue
        questions = data.get("questions", [])
        if not questions:
            continue
        s_ts = data.get("timestamp", "")
        s_id = data.get("session")
        model = data.get("model", "unknown")
        correct = partial = 0
        tiers = {}
        for q in questions:
            v = q_verdict(q)
            try:
                t = int(q.get("tier", 0))
            except (TypeError, ValueError):
                t = 0
            tiers.setdefault(t, {"correct": 0, "partial": 0, "total": 0})
            tiers[t]["total"] += 1
            if v == "correct":
                correct += 1
                tiers[t]["correct"] += 1
            elif v == "partial":
                partial += 1
                tiers[t]["partial"] += 1
            note = ""
            score = q.get("score")
            if isinstance(score, dict):
                note = score.get("note", "") or ""
            raw.append({
                "id": q.get("id"), "tier": t, "verdict": v,
                "session": s_id, "model": model, "note": note,
                "timestamp": q.get("timestamp") or s_ts,
            })
        total = len(questions)
        sessions.append({
            "session": s_id, "model": model, "timestamp": s_ts,
            "total": total, "correct": correct, "partial": partial,
            "incorrect": total - correct - partial,
            "score": round(100 * (correct + partial * 0.5) / total, 1),
            "tiers": tiers, "mode": data.get("mode", "headless"),
        })
    return sessions, raw


def build_runs(raw):
    """Group attempts by question id, chronologically; derive per-run aggregates."""
    by_q = {}
    for r in sorted(raw, key=lambda r: r["timestamp"] or ""):
        if not r["id"]:
            continue
        by_q.setdefault(r["id"], {"tier": r["tier"], "attempts": []})
        by_q[r["id"]]["attempts"].append({
            "session": r["session"], "timestamp": r["timestamp"],
            "verdict": r["verdict"], "model": r["model"], "note": r["note"],
        })

    max_runs = max((len(q["attempts"]) for q in by_q.values()), default=0)
    runs = []
    for n in range(max_runs):
        tiers = {}
        correct = partial = total = 0
        sess = set()
        ts_all = []
        for q in by_q.values():
            if len(q["attempts"]) <= n:
                continue
            a = q["attempts"][n]
            t = q["tier"]
            tiers.setdefault(t, {"correct": 0, "partial": 0, "total": 0})
            tiers[t]["total"] += 1
            total += 1
            if a["verdict"] == "correct":
                correct += 1
                tiers[t]["correct"] += 1
            elif a["verdict"] == "partial":
                partial += 1
                tiers[t]["partial"] += 1
            sess.add(str(a["session"]))
            if a["timestamp"]:
                ts_all.append(a["timestamp"])
        runs.append({
            "run": n + 1, "tiers": tiers, "total": total,
            "correct": correct, "partial": partial,
            "incorrect": total - correct - partial,
            "score": round(100 * (correct + partial * 0.5) / total, 1) if total else 0,
            "sessions": sorted(sess),
            "from": min(ts_all)[:10] if ts_all else "",
            "to": max(ts_all)[:10] if ts_all else "",
        })
    return by_q, runs


def load_ruby_stats():
    snapshots = []
    for f in sorted(RESULTS_DIR.glob("ruby-stats-*.json")):
        try:
            data = json.loads(f.read_text())
            snapshots.append({
                "date": f.name.replace("ruby-stats-", "").replace(".json", ""),
                "catchRate": data.get("verificationCatchRate"),
                "episodeStats": data.get("episodeStats", {}),
                "competence": data.get("competence", []),
            })
        except Exception as e:
            print(f"Warning: {f}: {e}")
    return snapshots


def _model_family(model):
    m = model.lower()
    if "deepseek" in m:
        return "deepseek"
    if "granite" in m:
        return "granite"
    if "glm" in m or "zhipu" in m:
        return "glm"
    if "nemotron" in m or "nvidia" in m:
        return "nemotron"
    if "unspecified" in m or not m or m == "unknown":
        return "unknown"
    return model.split("/")[-1][:12].lower()


def _date_bucket(date_str):
    """Collapse nearby dates into a labelled bucket for grouping."""
    if not date_str or date_str == "unknown":
        return "unknown"
    d = date_str[:10]
    # Bucket: everything up to and including 2026-07-21 → jul-17-21
    if d <= "2026-07-21":
        return "jul-17-21"
    if d <= "2026-07-22":
        return "jul-22"
    return "jul-23"


def _run_label(family, zero_memory, bucket):
    model_display = {
        "deepseek": "DeepSeek",
        "granite": "Granite",
        "glm": "GLM",
        "nemotron": "Nemotron",
        "unknown": "Unknown model",
    }.get(family, family.title())

    date_display = {
        "jul-17-21": "Jul 17–21",
        "jul-22": "Jul 22",
        "jul-23": "Jul 23",
        "unknown": "?",
    }.get(bucket, bucket)

    suffix = " (0mem)" if zero_memory else ""
    return f"{model_display} {date_display}{suffix}"


def build_tier_run_matrix():
    """
    Build the tier × run-generation heatmap data.

    Groups sessions by (model_family, zero_memory, date_bucket) into runs,
    then for each (tier, run) computes correct/total/rate.
    """
    # Load raw question-level data per session
    sessions_data = []
    for f in sorted(RESULTS_DIR.glob("session_[0-9]*.json")):
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        qs = data.get("questions", [])
        if not qs:
            continue
        sessions_data.append({
            "session": data.get("session"),
            "model": data.get("model", "unknown"),
            "zero_memory": bool(data.get("zero_memory", False)),
            "timestamp": data.get("timestamp", ""),
            "questions": qs,
        })

    # Group sessions into run buckets
    groups = {}  # run_id → {label, model, zero_memory, date_bucket, session_ids, questions[]}
    for s in sessions_data:
        family = _model_family(s["model"])
        zm = s["zero_memory"]
        bucket = _date_bucket(s["timestamp"][:10] if s["timestamp"] else "")
        run_id = f"{family}_{'zm' if zm else 'reg'}_{bucket}"
        if run_id not in groups:
            groups[run_id] = {
                "id": run_id,
                "label": _run_label(family, zm, bucket),
                "model": s["model"],
                "zero_memory": zm,
                "date_bucket": bucket,
                "session_ids": [],
                "questions": [],
            }
        groups[run_id]["session_ids"].append(str(s["session"]))
        groups[run_id]["questions"].extend(s["questions"])

    # Sort runs by bucket then family (puts early runs first)
    bucket_order = {"jul-17-21": 0, "jul-22": 1, "jul-23": 2, "unknown": 3}
    family_order = {"deepseek": 0, "granite": 1, "glm": 2, "nemotron": 3}
    run_order = sorted(
        groups.values(),
        key=lambda g: (
            bucket_order.get(g["date_bucket"], 9),
            family_order.get(_model_family(g["model"]), 5),
            0 if not g["zero_memory"] else 1,
        ),
    )

    # Collect all tiers that appear anywhere
    all_tiers = set()
    for g in groups.values():
        for q in g["questions"]:
            try:
                t = int(q.get("tier", 0))
                if t > 0:
                    all_tiers.add(t)
            except (TypeError, ValueError):
                pass

    # Derive short tier labels from first question text seen for each tier
    tier_labels = {}
    for g in groups.values():
        for q in g["questions"]:
            try:
                t = int(q.get("tier", 0))
            except (TypeError, ValueError):
                continue
            if t > 0 and t not in tier_labels:
                text = q.get("question", "") or q.get("id", "")
                words = text.split()[:4]
                tier_labels[t] = " ".join(words) if words else f"Tier {t}"

    # Per-tier stats per run
    matrix_tiers = []
    grand_correct = {g["id"]: 0 for g in run_order}
    grand_total = {g["id"]: 0 for g in run_order}

    for tier in sorted(all_tiers):
        cells = {}
        for g in run_order:
            qs_for_tier = [q for q in g["questions"] if _safe_int(q.get("tier")) == tier]
            if not qs_for_tier:
                cells[g["id"]] = None  # no data — will show as "—"
                continue
            correct = sum(1 for q in qs_for_tier if q_verdict(q) == "correct")
            partial = sum(1 for q in qs_for_tier if q_verdict(q) == "partial")
            total = len(qs_for_tier)
            rate = (correct + partial * 0.5) / total if total else 0.0
            # Deduplicate session_ids contributing to this tier cell
            sess_ids = sorted(set(
                str(q.get("session") or g["session_ids"][0])
                for q in qs_for_tier
                if q.get("session") is not None
            ))
            cells[g["id"]] = {
                "correct": correct,
                "partial": partial,
                "total": total,
                "rate": round(rate, 4),
                "sessions": sess_ids,
            }
            grand_correct[g["id"]] += correct
            grand_total[g["id"]] += total

        short_label = tier_labels.get(tier, f"Tier {tier}")
        matrix_tiers.append({
            "tier": tier,
            "label": f"T{tier} · {short_label}",
            "cells": cells,
        })

    # Totals row
    totals = {}
    for g in run_order:
        c = grand_correct[g["id"]]
        t = grand_total[g["id"]]
        totals[g["id"]] = {
            "correct": c,
            "total": t,
            "rate": round(c / t, 4) if t else 0.0,
        }

    runs_out = [
        {
            "id": g["id"],
            "label": g["label"],
            "model": g["model"],
            "zero_memory": g["zero_memory"],
            "date_bucket": g["date_bucket"],
            "sessions": sorted(set(g["session_ids"])),
        }
        for g in run_order
    ]

    return {"runs": runs_out, "tiers": matrix_tiers, "totals": totals}


def _safe_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def inject(payload_js):
    """Swap the AURA_DATA resource inside the bundle's manifest, in place."""
    html = BUNDLE_FILE.read_text()
    m = re.search(r'(<script type="__bundler/manifest">\n?)(.*?)(\n?</script>)', html, re.S)
    if not m:
        raise SystemExit("dashboard.html: no __bundler/manifest section found")
    manifest = json.loads(m.group(2).strip())
    key = None
    for k, v in manifest.items():
        data = base64.b64decode(v["data"])
        if v.get("compressed"):
            data = gzip.decompress(data)
        if data.lstrip().startswith(DATA_MARKER):
            key = k
            break
    if key is None:
        raise SystemExit("dashboard.html: no window.AURA_DATA resource in manifest")
    packed = base64.b64encode(gzip.compress(payload_js.encode())).decode()
    manifest[key] = {"mime": "application/javascript", "compressed": True, "data": packed}
    html = html[:m.start(2)] + json.dumps(manifest) + html[m.end(2):]
    BUNDLE_FILE.write_text(html)


# ---------------------------------------------------------------------------
# Template patching — adds the Matrix tab to the __bundler/template if absent.
# All edits are idempotent: checked for the presence of the sentinel string
# "'matrix', 'Matrix'" before applying.
# ---------------------------------------------------------------------------

_MATRIX_PANEL_HTML = """\

  <div style="padding:1.4rem 1.6rem;display:{{ show.matrix }}" ref="{{ refs.matrix }}">
    <div style="background:var(--surface-card);border:1px solid var(--border-default);border-radius:12px;padding:1.2rem">
      <div style="font-family:var(--font-mono);font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;color:var(--text-muted);margin-bottom:.7rem">Tier × Run Matrix — pass-rate heatmap</div>

      <!-- Run selector chips -->
      <div style="display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:.8rem">
        <sc-for list="{{ matrixCols }}" as="mcol" hint-placeholder-count="4">
          <div sc-camel-on-click="{{ mcol.onClick }}" style="background:{{ mcol.chipBg }};border:1px solid {{ mcol.chipBorder }};border-radius:6px;color:{{ mcol.chipFg }};cursor:pointer;font-family:var(--font-mono);font-size:.65rem;padding:.35rem .65rem;transition:all .12s">
            {{ mcol.label }}
          </div>
        </sc-for>
      </div>

      <!-- Overlay comparison chart -->
      <svg ref="{{ refs.matrixChart }}" style="width:100%;display:block;margin-bottom:.8rem" height="240"></svg>

      <!-- Heatmap table -->
      <div style="overflow:auto;max-height:55vh">
        <sc-raw-table style="border-collapse:collapse;font-family:var(--font-mono);font-size:.7rem;white-space:nowrap">
          <sc-raw-thead>
            <sc-raw-tr>
              <sc-raw-th style="background:var(--surface-recessed);border-bottom:2px solid var(--border-default);color:var(--text-muted);font-size:.6rem;font-weight:700;letter-spacing:.08em;min-width:160px;padding:.6rem .8rem;position:sticky;left:0;text-align:left;text-transform:uppercase;z-index:3">Tier</sc-raw-th>
              <sc-for list="{{ matrixCols }}" as="mcol" hint-placeholder-count="4">
                <sc-raw-th style="background:var(--surface-recessed);border-bottom:2px solid var(--border-default);border-left:1px solid var(--border-default);color:{{ mcol.thColor }};font-size:.62rem;font-weight:600;min-width:120px;padding:.6rem .8rem;text-align:center;transition:opacity .15s;opacity:{{ mcol.opacity }}">{{ mcol.label }}</sc-raw-th>
              </sc-for>
            </sc-raw-tr>
          </sc-raw-thead>
          <sc-raw-tbody>
            <sc-for list="{{ matrixRows }}" as="mrow" hint-placeholder-count="30">
              <sc-raw-tr style-hover="opacity:.85">
                <sc-raw-td style="background:var(--surface-card);border-bottom:1px solid var(--border-default);color:var(--text-heading);font-size:.68rem;font-weight:600;padding:.45rem .8rem;position:sticky;left:0;z-index:1">{{ mrow.label }}</sc-raw-td>
                <sc-for list="{{ mrow.cells }}" as="mcell" hint-placeholder-count="4">
                  <sc-raw-td title="{{ mcell.tooltip }}" style="background:{{ mcell.bg }};border-bottom:1px solid var(--border-default);border-left:1px solid var(--border-default);color:{{ mcell.fg }};font-size:.66rem;padding:.45rem .7rem;text-align:center;transition:opacity .15s;opacity:{{ mcell.opacity }}">{{ mcell.text }}</sc-raw-td>
                </sc-for>
              </sc-raw-tr>
            </sc-for>
          </sc-raw-tbody>
          <sc-raw-tfoot>
            <sc-raw-tr>
              <sc-raw-td style="background:var(--surface-recessed);border-top:2px solid var(--border-default);color:var(--text-muted);font-size:.6rem;font-weight:700;letter-spacing:.08em;padding:.6rem .8rem;position:sticky;left:0;text-transform:uppercase">Total</sc-raw-td>
              <sc-for list="{{ matrixTotals }}" as="mtotal" hint-placeholder-count="4">
                <sc-raw-td style="background:{{ mtotal.bg }};border-left:1px solid var(--border-default);border-top:2px solid var(--border-default);color:{{ mtotal.fg }};font-size:.68rem;font-weight:700;padding:.6rem .7rem;text-align:center;transition:opacity .15s;opacity:{{ mtotal.opacity }}">{{ mtotal.text }}</sc-raw-td>
              </sc-for>
            </sc-raw-tr>
          </sc-raw-tfoot>
        </sc-raw-table>
      </div>
    </div>
  </div>
"""

_MATRIX_JS_METHODS = """\

  heatColor(pct) {
    const p = Math.max(0, Math.min(100, pct)) / 100;
    let r, g, b;
    if (p <= 0.5) {
      const t = p * 2;
      r = Math.round(229 + (212 - 229) * t);
      g = Math.round(62  + (144 - 62)  * t);
      b = Math.round(62  + (58  - 62)  * t);
    } else {
      const t = (p - 0.5) * 2;
      r = Math.round(212 + (56  - 212) * t);
      g = Math.round(144 + (161 - 144) * t);
      b = Math.round(58  + (105 - 58)  * t);
    }
    return `rgba(${r},${g},${b},0.82)`;
  }

  matrixColors(idx) {
    const palette = ['#f472b6','#60a5fa','#34d399','#fbbf24','#a78bfa','#fb923c','#2dd4bf','#f87171'];
    const stroke = ['#ec4899','#3b82f6','#10b981','#f59e0b','#8b5cf6','#f97316','#14b8a6','#ef4444'];
    return { fill: palette[idx % palette.length], stroke: stroke[idx % stroke.length] };
  }

  handleMatrixRunToggle(runId) {
    this.setState(prev => {
      const selected = prev.matrixSelectedRuns || [];
      const next = selected.includes(runId) ? selected.filter(r => r !== runId) : [...selected, runId];
      return { matrixSelectedRuns: next };
    });
  }

  buildMatrixVals() {
    const MATRIX = window.AURA_DATA?.TIER_RUN_MATRIX;
    if (!MATRIX) return { matrixCols: [], matrixRows: [], matrixTotals: [], matrixRawData: null };
    const selected = this.state.matrixSelectedRuns;
    const allRuns = MATRIX.runs ?? [];
    const hasSelection = selected && selected.length > 0;
    const activeRuns = hasSelection ? allRuns.filter(r => selected.includes(r.id)) : allRuns;

    const matrixCols = allRuns.map((run, ri) => {
      const isActive = !hasSelection || selected.includes(run.id);
      return {
        id: run.id,
        label: run.label,
        thColor: isActive ? 'var(--aura-cyan)' : 'var(--text-muted)',
        chipBg: isActive ? 'rgba(244,114,182,.15)' : 'var(--surface-recessed)',
        chipBorder: isActive ? 'rgba(244,114,182,.4)' : 'var(--border-default)',
        chipFg: isActive ? '#f472b6' : 'var(--text-muted)',
        opacity: isActive ? '1' : '0.35',
        onClick: () => this.handleMatrixRunToggle(run.id),
      };
    });

    const matrixRows = (MATRIX.tiers ?? []).map(t => ({
      tier: t.tier,
      label: t.label,
      cells: allRuns.map(run => {
        const cell = t.cells?.[run.id];
        const isActive = !hasSelection || selected.includes(run.id);
        if (!cell) return { text: '—', bg: 'var(--surface-recessed)', fg: 'var(--text-muted)', tooltip: 'No data for this run', opacity: '0.35' };
        const pct = Math.round(cell.rate * 100);
        const bg = this.heatColor(pct);
        const fg = pct >= 50 ? '#0c1322' : 'var(--text-heading)';
        const tooltip = `${run.label} · ${cell.correct}/${cell.total} = ${pct}%` + (cell.sessions?.length ? ` · sessions: ${cell.sessions.join(', ')}` : '');
        return { text: `${cell.correct}/${cell.total} ${pct}%`, bg, fg, tooltip, opacity: isActive ? '1' : '0.35' };
      }),
    }));

    const matrixTotals = allRuns.map(run => {
      const tot = MATRIX.totals?.[run.id] ?? {};
      const isActive = !hasSelection || selected.includes(run.id);
      const pct = tot.total > 0 ? Math.round(tot.rate * 100) : 0;
      const bg = tot.total > 0 ? this.heatColor(pct) : 'var(--surface-recessed)';
      const fg = pct >= 50 ? '#0c1322' : 'var(--text-heading)';
      return { text: tot.total > 0 ? `${tot.correct}/${tot.total} ${pct}%` : '—', bg, fg, opacity: isActive ? '1' : '0.35' };
    });

    return { matrixCols, matrixRows, matrixTotals, matrixRawData: MATRIX };
  }

  drawMatrixCompare() {
    const svg = d3.select(this.refs.matrixChart.current);
    const node = svg.node(); if (!node) return;
    const MATRIX = this.matrixRawData || window.AURA_DATA?.TIER_RUN_MATRIX;
    if (!MATRIX || !MATRIX.tiers || MATRIX.tiers.length < 2) return;
    const W = node.getBoundingClientRect().width; if (W < 10) return;
    const H = 240, m = { top: 20, right: 100, bottom: 30, left: 40 };
    const w = W - m.left - m.right, h = H - m.top - m.bottom;
    const c = this.colors();
    svg.selectAll('*').remove();
    const g = svg.append('g').attr('transform', `translate(${m.left},${m.top})`);

    const selected = this.state.matrixSelectedRuns;
    const hasSelection = selected && selected.length > 0;
    const runs = MATRIX.runs ?? [];
    const activeRuns = hasSelection ? runs.filter(r => selected.includes(r.id)) : runs;
    if (activeRuns.length < 1) return;

    // X: tiers as ordinal scale
    const tierLabels = MATRIX.tiers.map(t => `T${t.tier}`);
    const x = d3.scalePoint().domain(tierLabels).range([0, w]).padding(0.3);
    const y = d3.scaleLinear().domain([0, 100]).range([h, 0]);

    // Grid
    g.append('g').call(d3.axisLeft(y).ticks(5).tickSize(-w).tickFormat(''))
      .call(g2 => g2.select('.domain').remove())
      .call(g2 => g2.selectAll('line').attr('stroke', c.grid));

    // Y axis labels
    g.append('g').call(d3.axisLeft(y).ticks(5).tickFormat(d => d + '%'))
      .call(g2 => g2.selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', 9).attr('font-family', "'IBM Plex Mono',monospace"))
      .call(g2 => g2.select('.domain').remove());

    // X axis labels
    g.append('g').attr('transform', `translate(0,${h})`)
      .call(d3.axisBottom(x).tickFormat(d => d))
      .call(g2 => g2.selectAll('text').attr('fill', 'var(--text-muted)').attr('font-size', 9).attr('font-family', "'IBM Plex Mono',monospace").attr('text-anchor', 'end').attr('transform', 'rotate(-35)'))
      .call(g2 => g2.select('.domain').remove());

    // Draw one line per active run
    activeRuns.forEach((run, ri) => {
      const mc = this.matrixColors(ri);
      const dataPoints = MATRIX.tiers.map(t => {
        const cell = t.cells?.[run.id];
        return cell ? Math.round(cell.rate * 100) : null;
      });

      // Filter out nulls for line drawing
      const pts = dataPoints.map((v, i) => ({ tier: tierLabels[i], val: v, idx: i })).filter(p => p.val !== null);
      if (pts.length < 2) return;

      const line = d3.line()
        .x(d => x(d.tier))
        .y(d => y(d.val))
        .curve(d3.curveCatmullRom.alpha(0.5));

      g.append('path').datum(pts)
        .attr('fill', 'none').attr('stroke', mc.stroke).attr('stroke-width', 2.5)
        .attr('d', line).attr('opacity', 0.85);

      // Dots
      g.selectAll('circle.run-pts-' + ri).data(pts).join('circle')
        .attr('cx', d => x(d.tier)).attr('cy', d => y(d.val)).attr('r', 3.5)
        .attr('fill', mc.stroke).attr('stroke', mc.fill).attr('stroke-width', 1.5)
        .attr('opacity', 0.9);

      // Legend label at end
      const last = pts[pts.length - 1];
      if (last) {
        g.append('text').attr('x', x(last.tier) + 6).attr('y', y(last.val) + 3)
          .attr('fill', mc.stroke).attr('font-size', 9).attr('font-family', "'IBM Plex Mono',monospace")
          .text(run.label).attr('opacity', 0.85);
      }
    });
  }
"""


def _patch_template(template_src):
    """Apply Matrix tab patches to the dashboard template source. Idempotent.

    v1 sentinel: "'matrix', 'Matrix'" present → original matrix tab exists
    v2 sentinel: "matrixSelectedRuns" present → upgraded with selectors + overlay chart
    """
    # If already at v2, skip
    if "matrixSelectedRuns" in template_src:
        return template_src, False

    patches_applied = 0

    # ── Stage A: First-time patching (v0 → v1) ───────────────────────
    if "'matrix', 'Matrix'" not in template_src:
        # 1 — Add refs.matrix + refs.matrixChart
        OLD = "refs = {\n    overview: React.createRef(), sessions: React.createRef(), ruby: React.createRef(),\n    tiers: React.createRef(), timeline: React.createRef(),"
        NEW = "refs = {\n    overview: React.createRef(), sessions: React.createRef(), ruby: React.createRef(),\n    tiers: React.createRef(), timeline: React.createRef(), matrix: React.createRef(), matrixChart: React.createRef(),"
        if OLD in template_src:
            template_src = template_src.replace(OLD, NEW, 1)
            patches_applied += 1

        # 2 — Add matrix tab to tabsDef
        OLD = "['overview', 'Overview'], ['sessions', 'Sessions'], ['ruby', 'Ruby Alternator'],\n      ['tiers', 'Tier Breakdown'], ['timeline', 'Timeline'],"
        NEW = "['overview', 'Overview'], ['sessions', 'Sessions'], ['ruby', 'Ruby Alternator'],\n      ['tiers', 'Tier Breakdown'], ['timeline', 'Timeline'], ['matrix', 'Matrix'],"
        if OLD in template_src:
            template_src = template_src.replace(OLD, NEW, 1)
            patches_applied += 1

        # 3 — Add show.matrix to show object
        OLD = "timeline: this.state.tab === 'timeline' ? 'flex' : 'none',"
        NEW = "timeline: this.state.tab === 'timeline' ? 'flex' : 'none',\n      matrix: this.state.tab === 'matrix' ? 'flex' : 'none',"
        if OLD in template_src:
            template_src = template_src.replace(OLD, NEW, 1)
            patches_applied += 1

        # 4 — Add JS methods before renderVals
        OLD = "\n  renderVals() {"
        NEW = _MATRIX_JS_METHODS + "\n  renderVals() {"
        if OLD in template_src and "heatColor" not in template_src:
            template_src = template_src.replace(OLD, NEW, 1)
            patches_applied += 1

        # 5 — Spread buildMatrixVals into return
        OLD = "      sessionLabels, heatRows, timelineRows, latestLabel: `S${latest.session ?? '—'}`,\n    };"
        NEW = "      sessionLabels, heatRows, timelineRows, latestLabel: `S${latest.session ?? '—'}`,\n      ...this.buildMatrixVals(),\n    };"
        if OLD in template_src:
            template_src = template_src.replace(OLD, NEW, 1)
            patches_applied += 1

        # 6 — Add matrix panel before tooltip
        TOOLTIP_ANCHOR = '\n  <div ref="{{ refs.tooltip }}"'
        if TOOLTIP_ANCHOR in template_src:
            template_src = template_src.replace(TOOLTIP_ANCHOR, _MATRIX_PANEL_HTML + TOOLTIP_ANCHOR, 1)
            patches_applied += 1

        # 7 — Add drawMatrixCompare to drawTab
        OLD = "if (tab === 'tiers') { this.drawTierDetail(latest); }"
        NEW = "if (tab === 'tiers') { this.drawTierDetail(latest); }\n    if (tab === 'matrix') { this.drawMatrixCompare(); }"
        if OLD in template_src and "drawMatrixCompare" not in template_src:
            template_src = template_src.replace(OLD, NEW, 1)
            patches_applied += 1

        return template_src, patches_applied > 0

    # ── Stage B: Upgrade v1 → v2 (already has old matrix, needs selector + chart) ──

    # Replace old JS methods with new ones (heatColor + buildMatrixVals stay same name but change impl)
    # Find the old methods block
    old_methods_start = template_src.find("heatColor(pct)")
    if old_methods_start > 0:
        # Find end of buildMatrixVals — the next "}" at indent level after the method
        # Look for "  drawMatrixCompare" or "  renderVals" or next method
        method_end = template_src.find("  renderVals()", old_methods_start)
        if method_end < 0:
            method_end = template_src.find("\n  drawMatrixCompare", old_methods_start)
        if method_end > 0:
            # Replace everything from the heatColor method start to just before renderVals
            old_block = template_src[old_methods_start:method_end]
            template_src = template_src.replace(old_block, _MATRIX_JS_METHODS.lstrip("\n"), 1)
            patches_applied += 1

    # Replace old matrix panel HTML with new one (with chips + chart + opacity)
    idx = template_src.find("Tier × Run Matrix")
    if idx > 0:
        # Find the enclosing <div ref="{{ refs.matrix }}"> ... </div>
        panel_start = template_src.rfind("<div", 0, idx)
        # Find the closing </div> of the panel (there are nested divs — count depth)
        depth = 0
        panel_end = idx
        for i in range(panel_start, len(template_src)):
            if template_src[i:i+4] == "<div":
                depth += 1
            elif template_src[i:i+5] == "</div":
                depth -= 1
                if depth == 0:
                    panel_end = i + 6  # include "</div>"
                    break
        if panel_end > panel_start:
            old_panel = template_src[panel_start:panel_end]
            template_src = template_src.replace(old_panel, _MATRIX_PANEL_HTML.strip(), 1)
            patches_applied += 1

    # Add refs.matrixChart to refs list if missing
    if "matrixChart" not in template_src:
        OLD = "matrix: React.createRef()"
        NEW = "matrix: React.createRef(), matrixChart: React.createRef()"
        if OLD in template_src:
            template_src = template_src.replace(OLD, NEW, 1)
            patches_applied += 1

    # Add drawMatrixCompare to drawTab if missing
    if "drawMatrixCompare" not in template_src:
        OLD = "if (tab === 'tiers') { this.drawTierDetail(latest); }"
        NEW = "if (tab === 'tiers') { this.drawTierDetail(latest); }\n    if (tab === 'matrix') { this.drawMatrixCompare(); }"
        if OLD in template_src:
            template_src = template_src.replace(OLD, NEW, 1)
            patches_applied += 1

    # Add matrixSelectedRuns to componentDidUpdate matrix tab handling
    if "matrixSelectedRuns" not in template_src:
        OLD = "drawMatrixCompare"
        if OLD in template_src:
            pass  # state is initialized in renderVals return values, not constructor

    return template_src, patches_applied > 0


def inject_template(template_src):
    """Write a patched template back into dashboard.html's __bundler/template block."""
    html = BUNDLE_FILE.read_text()
    # The template JSON is stored with </script> escaped as </script> so the
    # HTML parser doesn't terminate the outer <script> block early. The real closing
    # tag is the first literal </script> after the opening tag.
    m = re.search(
        r'(<script type="__bundler/template">)(.*?)(</script>)',
        html, re.S,
    )
    if not m:
        raise SystemExit("dashboard.html: no __bundler/template section found")
    # Escape all </ sequences so embedded </body>, </html>, </script> etc. are safe.
    encoded = json.dumps(template_src).replace("</", "<\\u002F")
    new_block = m.group(1) + "\n" + encoded + "\n" + m.group(3)
    html = html[:m.start()] + new_block + html[m.end():]
    BUNDLE_FILE.write_text(html)


def main():
    sessions, raw = load_sessions()
    question_runs, runs = build_runs(raw)
    ruby = load_ruby_stats()
    matrix = build_tier_run_matrix()

    payload = (
        "window.AURA_DATA = {\n"
        f"  SESSIONS: {json.dumps(sessions)},\n"
        f"  RUBY_SNAPSHOTS: {json.dumps(ruby)},\n"
        f"  QUESTION_RUNS: {json.dumps(question_runs)},\n"
        f"  RUNS: {json.dumps(runs)},\n"
        f"  TIER_RUN_MATRIX: {json.dumps(matrix)}\n"
        "};\n"
    )
    inject(payload)

    # Patch the template to add the Matrix tab (idempotent)
    html = BUNDLE_FILE.read_text()
    m = re.search(r'<script type="__bundler/template">(.*?)</script>', html, re.S)
    if m:
        current_template = json.loads(m.group(1).strip())
        patched, changed = _patch_template(current_template)
        if changed:
            inject_template(patched)
            print("  Template patched: Matrix tab added")
        else:
            print("  Template already has Matrix tab")
    else:
        print("  Warning: no __bundler/template section found; skipping template patch")

    multi = sum(1 for q in question_runs.values() if len(q["attempts"]) > 1)
    n_runs = len(matrix["runs"])
    n_tiers = len(matrix["tiers"])
    print(f"Dashboard data injected: {BUNDLE_FILE}")
    print(f"  {len(sessions)} sessions, {len(question_runs)} questions, "
          f"{len(runs)} run generations ({multi} questions with reruns), "
          f"{len(ruby)} ruby-stats")
    print(f"  Matrix: {n_runs} run columns × {n_tiers} tiers")
    print("  Remember: cp dashboard.html index.html")


if __name__ == "__main__":
    main()
