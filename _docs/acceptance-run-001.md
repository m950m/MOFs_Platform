# Acceptance run 001 — complete first evidence workflow (issue #13)

**Date:** 2026-10-02 (generation date) · **Project version:** 0.1.0 (branch task-013) · **Question:** the production question (owner-entered, data/platform.db id 1) is the context; this fixture run uses a shortened synthetic variant · **Source contract:** D2 (Crossref metadata + manual entry; no full text) · **Stack:** D3 (Python/Streamlit/SQLite) · **Review rule:** D4 (named human + exact cited location + reason) · **Equivalence:** D5 (no cross-source equivalence, ever) · **Profile:** no entry is seeded — every capability fact starts `unknown` until owner-entered (rule per plan §2.5; register D7 entry recorded 2026-10-02) · **Fixtures:** records are labeled `(synthetic)` or `fixture`, review actions in the fixture are performed by the script, and everything lives in a throwaway database — separated from any real evidence.

| Step | Expected | Actual | Detail |
|---|---|---|---|
| S1 question save+correct | one saved question, corrected wording, v-history | PASS |  |
| S2 profile statuses | four capability entries recorded (verbatim storage grounded in test_labprofile_domain) | PASS |  |
| S3 reference + route attempts | no_hit failure recorded, later success distinct (never relabeled) | PASS |  |
| S4 assertions + conflict pair | attributed assertions recorded; conflict keeps both claims, flags both | PASS |  |
| S5 samples/observation/state/compare | composite relation to documented parent; observation on composite only | PASS |  |
| S6 candidate card | card exposes reason, observation gaps, state interpretation, provenance | PASS |  |
| S7 review/correction/D5 | corrected reviewed claim → needs_verification (no inherited approval); D5 cross-source equivalence refused | PASS |  |
| S8 laboratory fit | possible/future/unknown outcomes correct; basis change marks outdated; rerun records current assessment | PASS |  |
| S9 restart persistence | question wording, route attempts, candidate-card chain, and relations inspectable after full close/reopen (profile/conflict/fit restarts grounded in their test modules) | PASS |  |

**Route-failure applicability:** the D2 route combines manual capture (offline — network failures inapplicable) with Crossref metadata enrichment (no_hit / rate_limited / timeout / offline / bad_response / bad_input all typed and tested in tests/test_route_failures.py). No prohibited content is fetched; no provider is substituted.

**Scientific boundary:** this run verifies software-workflow behavior only. It makes no claim of catalyst validation, novelty, synthesis success, or measured research benefit.

**Overall: ALL CHECKS PASS** (9/9 steps).

**Per-step Expected texts state the contract behavior; where a step's inline check is narrower, the clause is grounded in the named test modules (test_labprofile_domain, test_identity_domain, test_review, test_labfit, test_route_failures).**
