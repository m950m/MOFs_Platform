# Acceptance run 001 — complete first evidence workflow (issue #13)

**Date:** 2026-10-02 · **Project version:** 0.1.0 (main, task-013) · **Question:** owner-entered bifunctional HER+OER wording (question id 1) · **Source contract:** D2 (Crossref metadata + manual entry; no full text) · **Stack:** D3 (Python/Streamlit/SQLite) · **Review rule:** D4 (named human + exact cited location + reason) · **Equivalence:** D5 (no cross-source equivalence, ever) · **Profile:** all entries owner-entered (`unknown` until confirmed) · **Fixtures:** every record below is visibly labeled `(synthetic)` and lives in a throwaway database — separated from any real evidence.

| Step | Expected | Actual | Detail |
|---|---|---|---|
| S1 question save+correct | one saved question, corrected wording, v-history | PASS |  |
| S2 profile statuses | four statuses stored verbatim | PASS |  |
| S3 reference + route attempts | no_hit failure recorded, later success distinct (never relabeled) | PASS |  |
| S4 assertions + conflict pair | attributed assertions recorded; conflict keeps both claims, flags both | PASS |  |
| S5 samples/observation/state/compare | composite relation to documented parent; observation on composite only | PASS |  |
| S6 candidate card | card exposes reason, observation gaps, state interpretation, provenance | PASS |  |
| S7 review/correction/D5 | corrected reviewed claim → needs_verification (no inherited approval); D5 cross-source equivalence refused | PASS |  |
| S8 laboratory fit | possible/future/unknown outcomes correct; basis change marks outdated; rerun records current assessment | PASS |  |
| S10 restart persistence | question, references, assertions, samples, relations, attempts, fit assessments all inspectable after full close/reopen | PASS |  |

**Route-failure applicability:** the D2 route combines manual capture (offline — network failures inapplicable) with Crossref metadata enrichment (no_hit / rate_limited / timeout / offline / bad_response / bad_input all typed and tested in tests/test_route_failures.py). No prohibited content is fetched; no provider is substituted.

**Scientific boundary:** this run verifies software-workflow behavior only. It makes no claim of catalyst validation, novelty, synthesis success, or measured research benefit.

**Overall: ALL CHECKS PASS** (9/9 steps).
