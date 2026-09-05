#!/usr/bin/env python3
"""
scrub_secrets.py — keep live credentials out of the trial record.

Why: results JSONs record Aura's full tool transcript. Any question that
makes the model `cat` an env file echoes real API keys into results/
(cf. session 10002, where DEEPSEEK_API_KEY landed in a recorded answer
and GitHub secret-scanning blocked the push). Run this on every file
BEFORE `git add`.

Modes:
    scrub_secrets.py FILE...           redact in place, print what changed
    scrub_secrets.py --check FILE...   exit 1 if any pattern hits, change nothing

Redaction preserves JSON/markdown structure: only the secret characters
are replaced, so scores and evidence stay intact.
"""

import re
import sys

PATTERNS = [
    # provider API keys: DeepSeek/OpenRouter-style sk- tokens (incl. sk-or-v1-...)
    ("api-key", re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "sk-REDACTED"),
    # Telegram bot tokens: <bot_id>:AA<hash>
    ("bot-token", re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_\-]{30,}"), "<REDACTED-BOT-TOKEN>"),
    # GitHub tokens
    ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"), "<REDACTED-GH-TOKEN>"),
    ("github-pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "<REDACTED-GH-PAT>"),
    # AWS / Slack
    ("aws-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<REDACTED-AWS-KEY>"),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}"), "<REDACTED-SLACK-TOKEN>"),
    # KEY=/TOKEN= assignments with long values, but keep obvious placeholders
    ("key-assignment", re.compile(
        r"((?:API_?KEY|TOKEN|SECRET|bot_token|PASSWORD)[A-Z_]*"
        r"(\s*[=:]\s*[\"']?))"
        r"(?!YOUR|REDACTED|CHANGE|xxx|example|<)([A-Za-z0-9_\-\.]{16,})"),
        None),  # replacement built via function below
]


def _assignment_repl(m):
    return m.group(1) + "<REDACTED>"


def scrub_text(text):
    """Return (scrubbed_text, {kind: count})."""
    counts = {}
    out = text
    for kind, rx, repl in PATTERNS:
        f = _assignment_repl if repl is None else (lambda m, r=repl: r)
        out, n = rx.subn(f, out)
        if n:
            counts[kind] = counts.get(kind, 0) + n
    return out, counts


def main():
    args = sys.argv[1:]
    check = False
    if args and args[0] == "--check":
        check = True
        args = args[1:]
    if not args:
        print("usage: scrub_secrets.py [--check] FILE...", file=sys.stderr)
        return 2

    total = 0
    for path in args:
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError as e:
            print(f"  WARN cannot read {path}: {e}", file=sys.stderr)
            continue
        scrubbed, counts = scrub_text(text)
        n = sum(counts.values())
        if n:
            total += n
            summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
            if check:
                print(f"SECRET HIT in {path}: {summary}")
            else:
                open(path, "w", encoding="utf-8").write(scrubbed)
                print(f"scrubbed {path}: {summary}")
    if check and total:
        print(f"FAILED --check: {total} secret pattern(s) present")
        return 1
    if not check:
        print(f"clean ({total} redaction(s) across {len(args)} file(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
