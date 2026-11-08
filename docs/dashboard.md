# Interactive run notebook

The GitHub Pages entry point is `index.html`. `dashboard.html` and
`dashboard/index.html` are generated aliases of the same page.

Run `python scripts/generate_dashboard.py` to rebuild them. The generator embeds
`scripts/dashboard_explorer.html`, `.css`, and `.js` into each page; there are no
client framework or CDN dependencies. Existing charts remain below the notebook.

The notebook supports run search, scope filters, sorting, pagination, tier
fingerprints, question and verdict filtering, answer previews, a native transcript
dialog, copied deep links, and two-run comparisons. Transcript files load on demand
from the original `results/` paths and are cached during the visit. Source filenames
are included explicitly because historical runs do not all use identical naming.

A shared URL uses `run`, `question`, and optional comma-separated `compare` query
parameters. Comparison differences are percentage points; the UI makes clear that
runs can contain different question sets. No benchmark records or scoring rules
are changed. Missing question verdicts are shown as ungraded in previews, while
the existing aggregate convention is disclosed in the run header.

## Validation

`node --check scripts/dashboard_explorer.js`

`python -m py_compile scripts/generate_dashboard.py`

With jsdom available on Node's module path:

`NODE_PATH=/path/to/node_modules node --test tests/dashboard.test.cjs`

The interaction tests cover all served URL paths, original transcript loading,
text escaping, filtering, pagination, two-run selection, deep links, clipboard,
transcript controls, fetch retries, and stale-response handling. jsdom tests do not
validate visual layout or native dialog focus trapping. Browser visual QA could
not be completed during this change because the connected browser tool failed.
