# MOFs_Platform

An evidence-traceable research tool for MOF-related electrochemistry (HER/OER):
discover materials with documented experimental preparation, keep each claim's
source and location, preserve tested-sample identity, and let the researcher —
not the tool — draw scientific conclusions.

**Status:** the first complete evidence workflow is DONE — issues #3–#13 all
closed with independent QA + scientific-review evidence (acceptance run:
[`_docs/acceptance-run-001.md`](_docs/acceptance-run-001.md)). The backlog now
holds the owner-approved vision layer (#14–#19: consistency hints, question
refinement, active search, lab-vs-industry benchmarks, compound profiles,
contributor packages). Owner decisions D1–D5 are recorded;
D6–D8 remain open in [`_docs/decision-register.md`](_docs/decision-register.md).

## Read first

1. [`_docs/plan.md`](_docs/plan.md) — sections 0–10 are the current specification;
   Appendices A–C are historical.
2. [`_docs/tasks.md`](_docs/tasks.md) → GitHub Issues — the active backlog.
3. [`_docs/proposals/`](_docs/proposals/) — proposed implementation spec, diagrams,
   and agent execution plan (2026-10-01), pending owner approval in
   [`_docs/decision-register.md`](_docs/decision-register.md).
4. Related project: [`scientific-data-lifecycle-atlas`](https://github.com/m950m/scientific-data-lifecycle-atlas) —
   a separate methodology reference (data-lifecycle stages, FAIR, documented
   failure modes). Kept independent by design; it may import real runtime
   evidence from this repository after the core engine (issues #3–#13) completes.

## Authority

Scientific and product decisions belong to the owner (Mohammed). Agents propose;
they never select a source, stack, scientific question, or candidate on his behalf,
and silence is never treated as approval. See [`AGENTS.md`](AGENTS.md).

New dependencies require the owner's approval first (see `AGENTS.md`).

## Run locally

Prerequisites: Python ≥ 3.11 (verified on 3.14.4). No credentials, no network
needed at runtime. Data is stored in `data/platform.db` (override with the
`MOFS_DB_PATH` environment variable); the schema is created by numbered
migrations on first run.

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
