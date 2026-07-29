# Aura Standing Rules

## The record is the product
This repo is a dated, public log of whether the Ruby Alternator
improves answer quality. Its entire value is that the log is
untampered. `answers/`, `results/`, `logs/`, `questions/` and
`case-studies/` are evidence. Append to them; never edit,
regenerate, backfill or tidy past entries. If a run failed, the
record says it failed. Never retroactively improve results.

`CHARTER.md` defines the rules of the trial. Read it before changing
methodology.

## Three HTML files, similar names
`index.html` is the root page. `dashboard.html` and
`dashboard/index.html` are two different files, both plausibly "the
dashboard". Before editing either, check which one is actually
served, and name the exact file you changed in your report. Editing
one and claiming "the dashboard is updated" is wrong if the other is
live.

The repo page is `README.md` — it carries the trial status banner
and is the most-read file here. When the request says repo or
readme, edit `README.md`. Putting an image "in the repo" means
commit the asset and reference it from `README.md`. If you cannot
tell which surface is meant, stop and ask.

## Current status
Paused since 2026-07-26. Two causes, both infrastructure: the
systemd unit `node-app.service` runs with an empty environment so
`aura` was not on `PATH`, and the AMD GPU serving the local model is
unstable. Neither is a model or methodology failure — do not
describe them as such.

## Housekeeping
`files/` contains a committed `node_modules/`. Do not add more.

## Branch and secrets
The default branch is `master`, not `main`. Never inline a token
into a shell command; use `gh` or an env file.
