# Architecture — stable extension points for an open-source project

**Status:** adopted 2026-10-02 (owner requirement: stable architecture so external
contributors can enter precise compound data without destabilizing the core).
This document is binding for all implementation tasks; changes require an ADR
appendix here plus owner approval.

## Fixed layers (do not bypass)

```
ui/  ──▶  domain/  ──▶  db/ (SQLite + numbered migrations)
  │            │
  │            └──▶ sources/ (adapters: one file per provider, typed results/failures)
  └─ never touches db/ or sources/ directly
```

| Layer | Rule | Why it is fixed |
|---|---|---|
| `domain/` | Pure Python. Imports: stdlib only. No Streamlit, no HTTP, no file paths | Contributors can test all scientific logic offline, in seconds |
| `db/` | Every schema change = numbered migration in `db/migrations/`; never edit a shipped migration; `schema_migrations` tracks what applied | Contributor checkouts upgrade their local data safely, deterministically |
| `sources/` | One adapter per provider; returns typed results **or** typed failures; live calls only outside tests (fixtures replace them) | Adding a provider never touches domain or db code |
| `ui/` | Streamlit pages render through domain functions only; `session_state` is never storage | UI can be replaced (CLI, web) without touching science |
| Tests | Domain/UI/db tests offline via fixtures; restart-persistence pattern for anything durable; identity-contract cases as executable tests | A contributor PR that breaks provenance or identity rules fails CI, not the data |

## Identity invariants (owner-mandated, 2026-10-02)

1. **Same composition ≠ same compound.** Two records with identical elemental
   composition but different atomic arrangement (crystal structure/topology,
   CIF) or different morphology are **different compounds** — relation
   `different`, never merged.
2. **Every compound aggregates its own property profile** (issue #18): all
   recorded properties, each with source + conditions + review state, form the
   compound's unique feature card. Properties never transfer between compounds.
3. A mechanical framework key (MOFid/MOFkey — node+linker+topology encoding) is
   the preferred optional identifier at framework level; it distinguishes
   arrangements that formulas collapse, but never merges tested samples.

## Collaboration model (open source)

- **License:** Apache-2.0 (explicit patent grant; swap only by owner decision).
- **Contributors** submit data as **evidence packages** (standardized,
  attributable JSON export/import, defined before #13 closes) — every imported
  row enters with the contributor's attribution and review state
  `needs verification`. The import/review workflow is issue #19. A hosted
  multi-user server is **out of scope** until the owner explicitly decides.
- **Contribution safety:** PRs run the offline test suite; a PR may not weaken
  identity invariants, provenance capture, or review-state rules — such changes
  require an ADR + owner approval.

## Extension points (where contributors plug in)

| Want to add… | Implement… | Never touch |
|---|---|---|
| A new data provider | `sources/<provider>.py` adapter + fixtures | domain, db, existing sources |
| A new property type | domain model + migration + tests | sources, ui internals |
| A new review rule | `domain/review.py` transition + tests | migrations history |
| A UI surface | `ui/pages/<page>.py` via domain calls | db directly |
