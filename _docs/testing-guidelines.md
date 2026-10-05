# Testing guidelines

Draft established 2026-10-01 to satisfy the issue #3 guidance requirement
("read `_docs/testing-guidelines.md` before writing tests"). Mohammed may amend
at any time; these rules bind agent-authored tests.

## Environment and commands

- No `uv` on PATH (verified 2026-10-01). Use `python3 -m venv .venv` then
  `pip install -e ".[dev]"`.
- Run: `pytest` (unit + integration), `python -m mofs_platform.smoke` (startup
  check). Every QA verdict must quote a command the owner can rerun himself.

## Core rules

1. **No live network in tests.** Source clients are exercised against recorded
   fixtures in `sources/fixtures/`. A guard test asserts no test constructs a
   live HTTP client. One optional manual-only live script may exist outside the
   test suite.
2. **Failure behavior is first-class.** Every failure-taxonomy row applicable
   to the selected route (no hit / rate limited / timeout / offline /
   bad response / bad input) has a test asserting the recorded outcome, and
   `no hit` never produces an "untested/novel" claim. Reserved vocabulary not
   yet reachable (e.g. `restricted`, `manual_capture`) is documented where
   defined and gains tests when its feature lands.
3. **Persistence is proven by restart.** The restart pattern — open connection,
   write, close, reopen, assert — is mandatory for anything claimed durable,
   including corrections.
4. **Temp databases.** Integration tests use `tmp_path`; no test writes to a
   real data file. Foreign keys ON; migrations run from empty in CI.
5. **The identity contract is executable.** The five synthetic cases of plan
   A.5 §4 are parameterized tests asserting exact scoped relations and merge
   permissions; plus one test that a cross-source merge without a human-reviewed
   explicit-designation assertion is rejected.
6. **Domain tests need no UI.** `domain/` imports nothing from Streamlit or
   HTTP libraries; unit tests import it directly.
7. **UI tests are headless.** Streamlit pages are checked with
   `streamlit.testing.v1.AppTest` against a seeded temp database — asserting
   required labels/states appear (e.g., `needs verification`, per-reaction
   `not yet searched`).
8. **A smoke test can fail.** The startup check exits non-zero on a broken
   entry point; it must never be an unconditional pass (issue #3).
9. **Tests assert behavior, not documentation strings.** Verify observable
   outcomes: stored rows, displayed states, exit codes.
10. **Keep the suite green and offline.** A fresh checkout must reproduce
    setup, startup, and all tests with no credentials and no network.

## Run order (owner mandate, 2026-10-04)

Testing is tiered — matching effort to blast radius:

1. **Unit tests for the changed module** run first (fast feedback where the
   change landed).
2. **Related integration tests** (the module's direct consumers) run second.
3. **The full regression suite runs only before merge/release** — on the
   release branch, right before opening the PR. Tiering changes WHEN the
   full sweep runs, not whether it runs: no merge without it.
