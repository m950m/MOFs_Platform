# Proposed Implementation Specification — MOF Electrochemistry Research Tool

**Status:** PROPOSAL. Nothing in this document is approved or selected until Mohammed writes his decision in each row of §1.
**Date prepared:** 2026-10-01
**Authority:** subordinate to `_docs/plan.md` sections 0–10. Where this document and the plan conflict, the plan wins. This file adds a *proposed* concrete configuration for the owner-held decisions in plan §5; it does not replace them.

---

## 0. How to use this document

1. Read §1 (eight decision rows). For each row: write `Approved`, `Approved with edit: …`, or `Rejected: …`. Only D1 requires owner-authored text.
2. Record the outcome in `_docs/decision-register.md` (to be created) using the template in plan §5.
3. Once D1–D3 are approved, GitHub issue #3 becomes Ready and execution starts per `_docs/proposals/agent-execution-plan.md`.
4. Silence is not approval. No row is filled by the agent.

## 1. Proposed owner decisions (recommendations, not selections)

| ID | Decision (from plan §5) | Proposal | Rationale | Fallback |
|---|---|---|---|---|
| **D1** | First exact research question, reaction(s), conditions, acceptance case | **OWNER-AUTHORED TEXT — only Mohammed writes this.** Template provided in §2.2. The *tool acceptance case* (§2.1) is question-agnostic and can be approved independently. | The scientific question is the one decision that cannot be delegated or defaulted. | None. Blocks #4–#13 only; #3 can start once D2+D3 are approved. |
| **D2** | First source contract | **Crossref REST (`api.crossref.org/works/{doi}`, public "polite" pool with `mailto` parameter) for metadata enrichment of manually entered DOIs.** Permitted fields: DOI, title, authors, container-title, issued date, license URL, link, `indexed`/`updated`. Manual entry remains the primary evidence path in the first slice; no full-text retrieval, no scraping, no CCDC automation (browser route stays manual). Failure behavior per §5.4. | Crossref is public, keyless, documented (checked 2026-09-24 in plan A.6), and its role is honestly narrow: it enriches a *lead*, it never verifies a sample. Manual-first matches plan §2 ("accept manually entered papers, DOIs, and evidence"). | Pure-manual slice 1 (no network at all); Crossref added in a later issue. |
| **D3** | Local stack | **L2 — Python 3.11+ / Streamlit local app / SQLite via stdlib `sqlite3`.** Runtime deps: `streamlit`, `httpx` (pinned at install). Dev deps: `pytest`, `ruff`. No ORM, no Docker, no Postgres, no server process beyond Streamlit. | The product's core loop (issues #10–#12) is *human inspection and correction of evidence cards* — a forms-and-tables review surface. A CLI makes that loop painful; Streamlit keeps the domain layer UI-free anyway (§3 layering), so a future CLI/other client can reuse it. | L1 (CLI + SQLite) — same domain layer, different adapter; switching later is cheap because of layering. |
| **D4** | What elevates an assertion to `reviewed` | A **named human** records a ReviewEvent confirming they inspected the **exact cited evidence location** (section/figure/table/page as captured). Stored: who, when, verdict (confirm/correct), reason. | Makes the threshold observable and auditable without inventing scientific judgment. | Owner defines stricter rule later; state machine already supports it. |
| **D5** | Cross-source sample equivalence rule | Two records may be linked `same reported tested sample` **only** when a human confirms both sources *explicitly designate the same sample* (shared batch identifier, or an explicit citation such as "the Sample-X prepared in ref. [12]"). Otherwise records stay separate with relation `unresolved` or `same parent framework`. **No automated cross-source merge, ever.** | Directly operationalizes plan A.5 §3 while finally setting the minimum evidence the contract left open. | Keep fully blocked (contract default); D5 just makes the human-review case concrete. |
| **D6** | Absence-of-testing filter | **No filter in the first slice.** Per-reaction outcomes are displayed (`not yet searched` / `no experimental test found within the documented search scope` / positive evidence) without excluding candidates. | A filter encodes a scientific prior; displaying outcomes lets the researcher apply their own. | Add a display-only toggle later, still non-excluding. |
| **D7** | Laboratory capability profile | A seeded profile file/table with entries `{name, status: current\|future\|unknown, notes}`. Seed **from prior statements** (no glovebox / no inert-gas line; difficulty with prolonged reflux under argon and inert storage; HHTP excluded on that basis) **but every entry starts `unknown` until Mohammed reconfirms it** — plan §2.5 requires reconfirmation before use in classification. | Preserves earlier input without treating it as a current universal fact. | Owner supplies a fresh profile from scratch. |
| **D8** | Interactive mock prototype | **Out of scope** (matches plan §7 backlog boundary). | The persisted, reviewable workflow (#4–#13) is strictly more informative than an ephemeral mock. | A separate owner-approved backlog decision, inserted explicitly, never silently. |

## 2. First workflow slice (issues #3–#13)

### 2.1 Tool acceptance case for the slice (question-agnostic, proposed)

> Given one manually entered source (a DOI) and one manually extracted preparation assertion for a named reported sample, the tool must:
> 1. Store source, sample, and assertion with all provenance fields (who, when, source pointer, evidence location or explicit `unknown`, epistemic type, review state).
> 2. Record the Crossref enrichment attempt: query, timestamp, returned permitted fields — or a typed failure (`no hit`, `rate limited`, `timeout`, `offline`) — without ever marking the sample `verified` from metadata.
> 3. Display a candidate card showing the sample as `needs verification`, with HER and OER outcomes both `not yet searched`.
> 4. After full app restart, all of the above **and one recorded human correction** persist.
> 5. Run the five synthetic identity cases from plan A.5 §4 as automated tests and return exactly the contract-mandated relations, with zero merges where the contract forbids them.

### 2.2 Research question template (D1 — Mohammed fills)

```text
Question (one sentence): Which MOF-related materials with documented experimental
  preparation warrant closer inspection for [reaction] under [conditions]?
Reactions in scope: HER / OER / both (evidence kept separate per reaction)
Material classes allowed: MOF / ZIF / composite / derived / unresolved
Hard requirements: … (e.g., documented experimental preparation)
Preferences (non-excluding): …
Known unknowns: …
Observable acceptance observation for the slice: … (e.g., "I can enter question,
  add one DOI with one evidence assertion, correct it, restart, and everything is there")
```

## 3. System architecture (proposed)

```
mofs_platform/
├── pyproject.toml                # pinned deps; no installs before D3 approval
├── AGENTS.md                     # repo instructions (from plan §9 step 3 — currently missing)
├── src/mofs_platform/
│   ├── app.py                    # Streamlit entry — thin wiring only
│   ├── smoke.py                  # headless smoke test target for CI (no UI)
│   ├── domain/                   # ★ pure Python, zero UI/network imports
│   │   ├── models.py             # frozen dataclasses: Source, Framework, Sample,
│   │   │                         #   OperatingState, Observation, Assertion,
│   │   │                         #   ModificationHypothesis, Question, LabCapability
│   │   ├── identity.py           # scoped comparison + merge policy (A.5 contract)
│   │   ├── review.py             # review-state transitions + ReviewEvent log
│   │   ├── evidence.py           # assertion recording, epistemic types
│   │   └── labfit.py             # capability matching → current/future/unknown + reasons
│   ├── db/
│   │   ├── connection.py         # sqlite3 connect, WAL, foreign_keys=ON
│   │   ├── schema.sql            # DDL v1
│   │   └── migrations/           # numbered SQL files + schema_version table
│   ├── sources/
│   │   ├── crossref.py           # polite client (mailto), timeout, backoff on 429
│   │   ├── failures.py           # typed failure taxonomy (§5.4)
│   │   └── fixtures/             # recorded JSON responses — tests never go live
│   └── ui/
│       ├── cards.py              # candidate-card renderer
│       └── pages/                # question / sources / evidence / review / lab-fit
├── tests/
│   ├── unit/                     # identity (5 contract cases), review, labfit, failures
│   └── integration/              # migrations, restart persistence, correction log
└── scripts/
    └── live_crossref_smoke.py    # optional manual-only live check (never in tests)
```

**Layering rules (enforced by import-linter-style discipline, checked in review):**
- `domain/` imports nothing from `streamlit`, `httpx`, or `ui/`. It is the testable core.
- `sources/` is an adapter: network in, typed results/failures out. Swappable with fixtures.
- `ui/` reads/writes through domain functions only; Streamlit `session_state` is never treated as evidence storage (plan A.6 §3).
- Every schema change is a numbered migration; no in-place edits to shipped migrations.

## 4. Data model (summary — full ER diagram in `diagrams.md`)

Tables (all with surrogate `id`, `created_at`; every asserted row carries provenance):

| Table | Key columns / constraints |
|---|---|
| `source` | doi UNIQUE-or-null, url, title, container, license_url, access_date, entry_method (`manual`\|`crossref`), rights_note |
| `framework` | name, aliases, metal_node, linker, cif_ref, structure_status (`experimental`\|`computational`\|`unknown`) |
| `sample` | designation, source_id FK, parent_framework_id FK-or-null, constituents, prep_history, activation, basis (`experimental`\|`computational`\|`hypothetical`) |
| `operating_state` | sample_id FK, stage (`before`\|`during`\|`after`\|`unknown`), phase_assignment, epistemic_type |
| `observation` | sample_id FK, source_id FK, reaction (`HER`\|`OER`\|`other`), value, unit, electrolyte, ph, basis, reference_convention, loading, duration — each nullable=unknown |
| `assertion` | subject_type, subject_id, relation, object_type, object_id, evidence_location, epistemic_type (`directly_reported`\|`author_interpretation`\|`tool_inference`\|`user_judgment`\|`unknown`), review_state (`needs_verification`\|`in_review`\|`reviewed`\|`conflicted`), source_id FK |
| `review_event` | assertion_id FK, actor, timestamp, verdict (`confirm`\|`correct`\|`conflict`), old_value, new_value, reason |
| `search_run` | provider, query, scope, timestamp, outcome (`no_hit`\|`rate_limited`\|`timeout`\|`offline`\|`restricted`\|`contradictory`\|`results`), note |
| `question` | text, version, created_at (append-only versions; corrections via new version + event) |
| `lab_capability` | name, status (`current`\|`future`\|`unknown`), notes, reconfirmed_by, reconfirmed_at |
| `modification_hypothesis` | parent_sample_id FK, change, rationale, source_id FK, label=`untested hypothesis` (invariant) |

**Hard invariants (tested):** no cross-source sample merge without a human-reviewed assertion satisfying D5; observation never silently re-attaches from sample → framework or operating state; `no_hit` never yields an "untested/novel" claim; conflicts append, never overwrite.

## 5. Source contract (D2 detail)

### 5.1 Permitted route
- `GET https://api.crossref.org/works/{doi}?mailto=<contact>` — public polite pool. No API key, no account.
- Response handling: map `message` fields to the permitted column set only; store `indexed`/`updated` and retrieval timestamp.

### 5.2 Explicitly prohibited
Automated full-text retrieval; publisher scraping; storing publisher PDFs/text; automated CCDC retrieval; any European PMC / Unpaywall / COD calls in this slice (they remain documented options for later issues).

### 5.3 Rights posture
Metadata stored is Crossref bibliographic metadata (documented as broadly reusable; abstracts excluded from storage by default). User-supplied excerpts are stored attributed to the entering user with the cited location, never as tool-verified content.

### 5.4 Failure taxonomy (issue #9)
| Failure | Detection | Recorded behavior |
|---|---|---|
| `no_hit` | 404 / empty | search_run row; sample stays `needs verification`; **never** "material unstudied" |
| `rate_limited` | HTTP 429 | exponential backoff (headers honored), then typed failure |
| `timeout` | client timeout | typed failure; retry only on manual re-run |
| `offline` | connection error | manual-only mode; UI states network unavailability |
| `restricted` | license/link indicates closed access | show citation + lawful link; stop |
| `contradictory` | fields conflict across runs/sources | keep both with timestamps; flag for review |

## 6. Review workflow (D4 detail)

State machine per assertion: `needs_verification → in_review → reviewed`, with `conflicted` reachable from any state and **terminal-preserve** (both claims retained). Transitions are only ever performed via `review.record_event(...)`, which appends a `review_event` row and updates state — there is no direct UPDATE path. See `diagrams.md` §3.

## 7. Testing strategy

| Layer | Tests |
|---|---|
| Identity (`domain/identity.py`) | The **five synthetic cases of plan A.5 §4 become five pytest cases** asserting exact scoped relations and merge permissions (Case 1 `different`; Case 2 composite + distinct samples; Case 3 shared parent/different activation; Case 4 observation stays on sample, phase = author interpretation; Case 5 `unresolved`, no merge). Plus D5 rule test: cross-source merge requires the human-reviewed explicit-designation assertion. |
| Review | Legal/illegal transitions; correction appends and preserves old value; conflict retains both. |
| Failures | Each taxonomy row simulated from fixtures; backoff honored; `no_hit` wording invariant. |
| Persistence | Migration up from empty; restart (close connection → reopen) preserves data + corrections; foreign keys enforced. |
| Sources | Fixtures only; a guard test asserts no test file constructs a live HTTP client. |
| UI | `streamlit.testing` AppTest boots each page against a seeded temp DB; card shows required labels/states. |
| Smoke (#3) | `python -m mofs_platform.smoke` → creates temp DB, runs migrations, round-trips one entity, exits 0. |

## 8. Dependencies & tooling

- Runtime: `streamlit`, `httpx` — exact pins written into `pyproject.toml` **at installation time, after D3 approval** (dependency rule in plan A.1/B.7 §4).
- Dev: `pytest`, `ruff`.
- Everything else: Python 3.11+ standard library (`sqlite3`, `dataclasses`, `pathlib`, `json`). Environment verified 2026-10-01: Python 3.14.4 with `sqlite3` 3.46.1 present; no `uv` on PATH → use `python3 -m venv`.
- No Docker, no Postgres, no cloud, no secrets (Crossref polite pool needs only a contact email, stored in local config, never committed with a private value).

## 9. Non-goals (explicit)

No scientific candidate selection; no cross-source automated merging; no full-text ingestion or storage; no ML/prediction; no 3D viewer (later, labeled); no multiuser/concurrency; no deployment; no QMOF ingestion; no novelty or performance claims; no publication of the repository or pushes without owner request.

## 10. Milestones mapped to issues

| Issue | Deliverable (incremental, each keeps all prior tests green) |
|---|---|
| #3 | Runnable empty project + `smoke` + migrations v1 + CI-runnable pytest; no invented data |
| #4 | Question entry, versioned save, correction, restart persistence |
| #5 | Lab capability table + seeded profile (D7), reconfirmation gate |
| #6 | Manual source entry + Crossref enrichment + failure recording |
| #7 | Assertion recording with epistemic types + provenance |
| #8 | Identity comparison engine; five contract cases as tests; merge guards |
| #9 | Full failure taxonomy behaviors + "no hit ≠ untested" invariants |
| #10 | Candidate card + source-trail drill-down |
| #11 | Review/correct UI + review_event log + conflict display |
| #12 | Lab-fit classification with reasons; reconfirmed-capabilities-only gate |
| #13 | End-to-end workflow test (fixture-driven) + export of a review summary |
