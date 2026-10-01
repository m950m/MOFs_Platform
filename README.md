# MOFs_Platform

An evidence-traceable research tool for MOF-related electrochemistry (HER/OER):
discover materials with documented experimental preparation, keep each claim's
source and location, preserve tested-sample identity, and let the researcher —
not the tool — draw scientific conclusions.

**Status:** specification complete; implementation not started. Tasks 001–002 done
(documentation/analysis); issues #3–#13 blocked on owner decisions.

## Read first

1. [`_docs/plan.md`](_docs/plan.md) — sections 0–10 are the current specification;
   Appendices A–C are historical.
2. [`_docs/tasks.md`](_docs/tasks.md) → GitHub Issues — the active backlog.
3. [`_docs/proposals/`](_docs/proposals/) — proposed implementation spec, diagrams,
   and agent execution plan (2026-10-01), pending owner approval in
   [`_docs/decision-register.md`](_docs/decision-register.md).

## Authority

Scientific and product decisions belong to the owner (Mohammed). Agents propose;
they never select a source, stack, scientific question, or candidate on his behalf,
and silence is never treated as approval. See [`AGENTS.md`](AGENTS.md).

No product code, dependencies, or database schema exist yet; none may be added
before the owner records the prerequisite decisions.

## Run locally (issue #3 state)

Prerequisites: Python ≥ 3.11 (verified on 3.14.4). No credentials, no network
needed at runtime.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"   # streamlit + pytest + ruff (pinned)

# Start the app (local browser UI):
.venv/bin/streamlit run src/mofs_platform/app.py

# Startup smoke check (headless, prints PASS/FAIL, exit code reflects result):
.venv/bin/python -m mofs_platform.smoke

# Tests:
.venv/bin/pytest
```

A successful startup proves the entry point renders the empty/ready state —
nothing more. It does not validate provider access, chemistry, or data.
