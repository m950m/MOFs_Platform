# Contributing to MOFs Platform

Thank you for contributing precise compound data and code. This project is
**local-first and provenance-complete**: there is no hosted server and no
accounts — contributors submit **evidence packages** (attributed JSON) or
code changes, and the owner's human review decides what is trusted. Read
[`ARCHITECTURE.md`](ARCHITECTURE.md) first — its fixed layers and identity
invariants are binding on every contribution.

## 1. The evidence-package format

Contributors supply compound data as a **schema-v1 evidence package** — a
single JSON file:

- **Schema:** [`_docs/package-schema-v1.json`](_docs/package-schema-v1.json)
  (strict key sets — unknown keys are rejected)
- **Published example:** [`_docs/package-schema-v1-example.json`](_docs/package-schema-v1-example.json)

What a package may contain: `sources`, `samples`, `observations`,
`assertions`, and optional `compounds` (grouping only their own
within-package members). Every row carries provenance: who contributed it,
what was actually inspected (`inspected_level`), where in the source each
claim lives (`evidence_location`), and the epistemic type of every claim.

Import semantics you must know before writing one:

- **Packages are never anonymous** — a contributor name is required.
- Every imported row enters as **`needs_verification`**; the import never
  auto-promotes review states. The owner's review (D4: named human, exact
  cited location, reason) is the only path to `reviewed`.
- Imported records **coexist as new separate rows** — nothing merges into
  or overwrites local records. Packages carrying local-linking keys
  (`existing_local_id`, `merge_into`, …) are **rejected**.
- Validation is strict and collects **every** reason: schema drift, wrong
  `schema_version`, missing provenance, and unresolvable within-package
  references all produce a full rejection list.

**How to submit:** open an issue (or PR) with the package JSON attached.
The owner reviews it and imports it into their local store through the
Sources → *Evidence packages* section. There is no upload endpoint by
decision — attribution and review happen on the owner's machine.

## 2. Running the offline test suite

```bash
git clone https://github.com/m950m/MOFs_Platform && cd MOFs_Platform
python -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pytest -q          # the full suite — 250+ tests, all offline
.venv/bin/ruff check src tests scripts
.venv/bin/python -m mofs_platform.smoke
```

- **No live network in tests, ever.** Outbound clients (Crossref, OpenAlex,
  the optional AI assistant) are exercised through injected mock transports;
  a guard test fails the suite if any test constructs a real HTTP client.
- Databases in tests are temporary (`tmp_path`) and migrated from empty —
  no test touches a real data file.
- Follow the tiered run order for your own loop: unit tests of the changed
  module → related integration tests → the full suite before opening the PR.

## 3. The rules every PR must honor

Per [`ARCHITECTURE.md`](ARCHITECTURE.md) — a PR that breaks any of these is
rejected regardless of everything else:

- **Identity invariants are untouchable.** No merge paths (samples are
  never merged, D5), observations attach only to samples, properties never
  climb between a sample and its compound, same composition with a
  different arrangement stays a separate record.
- **Provenance is untouchable.** Attribution (who/when/where) and
  append-only history (previous/updated snapshots) are mandatory on every
  mutation; `unknown` is never silently filled; metadata never claims
  measurement; `no_hit` never means "unstudied".
- **The fixed layers hold:** UI → domain → db/sources. The UI never imports
  `db/` or `sources/` directly.
- **Delivery gates** ([`_docs/process.md`](_docs/process.md)): plan-first
  comment on the issue, a `task-*` branch (no direct commits to main),
  independent spec-compliance review + QA before merge, and the full
  regression suite green immediately before the PR.
- **No new mandatory dependencies** without an owner decision; the AI
  assistant is optional and never a requirement for any flow.

## Questions

Open an issue with the `question` label — the owner answers every one.
