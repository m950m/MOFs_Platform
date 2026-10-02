# Retrospective — core engine sprint (2026-10-02)

Scope: issues #3–#13 (bootstrap → complete first evidence workflow), delivered
in one working day, plus a whole-system audit and this retrospective before the
v0.1.0 release. Format follows plan B.6 (sprint review/retrospective).

## What went well

1. **The QA loop caught real, non-obvious defects** — 3 rounds on #8 (silent
   conflict absorption, hardcoded `source_id=1`, preselected `HER`), a missing
   UI surface on #11, and a lint regression on its own fix. Per-issue QA with
   separate context earned its cost.
2. **The two whole-system audits found what per-issue QA structurally could
   not**: state-machine dead ends (conflicted exit), cross-feature provenance
   holes (cross-source observation attachment), and approval invalidation on
   re-capture. Lesson: per-issue gates are necessary but insufficient — a
   system-level audit belongs at every milestone boundary.
3. **Proportionality guard worked**: no speculative abstractions crept in; the
   one dead constant and one layer violation were flagged by reviewers and
   fixed same-day.
4. **Owner decisions stayed owner-held**: D1–D5 recorded through focused
   questions; nothing inferred.

## What went badly / nearly went badly

1. **#11 shipped once with no UI at all** — domain logic existed but the
   researcher could not reach it. Root cause: implementing "the criteria" as
   domain checks and treating UI as implicit. Rule adopted: every AC whose
   subject is the researcher ships with its UI surface in the same task.
2. **Two lint-gate misses** (dead assignments in #11's fix commit; the
   acceptance script was outside the lint scope entirely). Rule adopted:
   the gate is `ruff check src tests scripts` — and scripts are first-class.
3. **Same-second timestamps hid staleness** (#12 outdated marking) — content
   digests replaced timestamps as the basis signature. Lesson: correctness
   checks must not depend on clock granularity.
4. **Test-expectation drift under rendering changes** (markdown escaping broke
   two string assertions). Minor, but noted: display-escaping happens at the
   render boundary; tests should assert content, not exact rendered bytes.

## Rule changes adopted (binding)

- CI runs `ruff check src tests scripts` + `pytest` + the acceptance script
  (`.github/workflows/ci.yml`); scripts are first-class artifacts.
- Cross-source observation attachment is refused at the domain layer (D5).
- Conflict resolution is an explicit attributed human action
  (`resolve_conflict`), never a side effect.
- Reference re-capture warns about dependent reviewed records
  (`source_dependency_warning`).

## Deferred consciously (not lost)

- `in_review` transition + tests (reserved vocabulary; issue #11 caveat).
- Atomic migration runner (current runner is fine on healthy disks; note in
  ARCHITECTURE.md).
- Flash/reset idiom extraction into `_widgets.py` (8 pages; deliberate
  repetition until #14–#16 add pages — regressions covered by AppTest).
- Flash/reset consistency for `obs_source` and lineage selects.
- `operating_state` own source pointer (A.5 field; #11/#18 grooming).

## Next

1. v0.1.0 tagged and released; real usage on actual papers this week.
2. Vision layer (#14–#19) specs refined from real usage gaps before building.
3. #18's first migration must introduce the first-class compound entity
   (architecture review: the most expensive available mistake is doing it
   retroactively).
