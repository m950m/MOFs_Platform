# MOFs_Platform

An evidence-traceable research tool for MOF-related electrochemistry (HER/OER):
discover materials with documented experimental preparation, keep each claim's
source and location, preserve tested-sample identity, and let the researcher —
not the tool — draw scientific conclusions.

**Documentation site:** [m950m.github.io/MOFs_Platform](https://m950m.github.io/MOFs_Platform/)
— user-facing docs (getting started, a page per screen, workflows, FAQ),
built from `docs/` with MkDocs Material (`pip install -e ".[docs]"`) and
deployed to GitHub Pages automatically on merge to `main`.

**Status:** the evidence engine (#3–#13) AND the owner's vision layer are
implemented — #14 (consistency hints), #15 (AI question refinement, D10),
#16 (active search, D9), #18 (compound profiles), #20 (sample corrections),
#24 (structure index, D12 slice 1) are closed with independent
spec-compliance + QA gate reports; #17 (lab-vs-industry number streams) and
#19 (contributor packages) hold the remaining small slices. Owner decisions
D1–D5 and D7–D12 are recorded; D6 and D8 remain open in
[`_docs/decision-register.md`](_docs/decision-register.md).

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

Prerequisites: Python ≥ 3.11 (verified on 3.14.4). Runs fully offline for
recording, review, and structure imports. Outbound network happens ONLY on
explicit researcher actions (Crossref/OpenAlex search + enrichment) — no API
keys needed for those; the optional AI question-refinement assistant (D10)
needs a Z.ai GLM API key supplied per session or via `MOFS_AI_API_KEY` (never
stored). Data is stored in `data/platform.db` (override with the
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
