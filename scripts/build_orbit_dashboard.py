#!/usr/bin/env python3
"""Build ARCHIMEDES ORBITAL — the radial mission-control dashboard.

Reuses the data pipeline from generate_dashboard (same payload as the classic
mission dashboard) and pours it into a different presentation layer:
gauges, a polar tier ring, an Archimedean spiral timeline, radar comparison,
a sunburst and a Nightingale rose. Output is fully self-contained (no CDNs),
so it works from file://, GitHub Pages, or any static server.

Usage:  python3 scripts/build_orbit_dashboard.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from generate_dashboard import build_payload  # noqa: E402

TEMPLATE_PATH = ROOT / "scripts" / "orbit_template.html"
OUT_PATHS = [
    ROOT / "orbit.html",
    ROOT / "dashboard" / "orbit.html",
]


def main() -> None:
    payload = build_payload()
    if not payload.get("sessions"):
        print("no sessions found — dashboard not written")
        return

    data_json = json.dumps(payload, separators=(",", ":"))
    data_json = data_json.replace("</", "<\\/")  # keep the inline blob safe

    live_json = "null"
    live_path = ROOT / "results" / "live.json"
    try:
        live_json = live_path.read_text(encoding="utf-8").strip()
        json.loads(live_json)  # validate before embedding
    except (FileNotFoundError, json.JSONDecodeError):
        live_json = "null"

    page = (
        TEMPLATE_PATH.read_text(encoding="utf-8")
        .replace("@@DATA@@", data_json)
        .replace("@@LIVE@@", live_json)
        .replace("@@GENERATED@@", payload.get("generated", ""))
        .replace("@@MAXTIER@@", str(payload.get("maxTier", 0)))
    )
    if "@@" in page.replace("@@@", ""):
        leftover = [tok for tok in ("@@DATA@@", "@@LIVE@@", "@@GENERATED@@", "@@MAXTIER@@") if tok in page]
        if leftover:
            raise SystemExit(f"unreplaced placeholders: {leftover}")

    (ROOT / "dashboard").mkdir(exist_ok=True)
    for path in OUT_PATHS:
        path.write_text(page, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")
    print(
        f"  {len(payload['sessions'])} sessions · {len(payload['fullRuns'])} full runs · "
        f"{len(payload['ruby'])} archimedes snapshots · {len(payload.get('projections', []))} projections"
    )


if __name__ == "__main__":
    main()
