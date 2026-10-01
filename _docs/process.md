# Work process

Extracted 2026-10-01 from `_docs/plan.md` Appendix A.4 (original
`mof_coder_kickoff/_docs/process.md`), with the backlog pointer updated to the
current decision that GitHub Issues are the active backlog. Plan sections 0–10
remain authoritative. Referenced by issue #3 working rules.

One active task. The main agent session is the orchestrator; it assigns bounded
roles, checks handoffs, and reports decisions requiring Mohammed. It does not
claim to have performed independent QA or scientific review itself.

## Roles and sequence

1. **Owner — Mohammed:** states the problem and lab constraints; approves
   scientific meaning, scope, stack, and final interpretation. Only the owner
   accepts a scientific decision.
2. **PM:** grooms one task into a testable goal, acceptance criteria, exclusions,
   and constraints; records open owner decisions. No code or scientific verdicts.
3. **Scientific reviewer:** checks terminology, material identity, source
   evidence, and the distinction between a reported fact and hypothesis. Can
   block a scientific claim. No code or unsourced assertion.
4. **Engineer (data and software):** implements the groomed task within its
   boundaries; records inputs/outputs, provenance, failure handling, and tests
   where there is executable behavior. Flags contradictions without rewriting
   acceptance criteria.
5. **QA:** independently checks each criterion against the delivered
   artifact/behavior and reports PASS/FAIL with evidence. Does not modify the work.
6. **Scientific reviewer, after QA, for science-bearing tasks:** checks the
   delivered scientific content. A QA PASS alone does not close a scientific task.
7. **Orchestrator:** returns FAIL to the relevant role; reports remaining
   decisions to the owner. Closes a task only after all applicable checks pass
   and owner-held decisions have been made.

For documentation tasks, PM and science review may refine the document; the
engineer writes it; QA checks exact criteria; the scientific reviewer then
checks interpretation. No agent may treat its own self-check as independent QA.
Where real independent sessions are available (separate agent contexts), use
them; otherwise conduct separate reviews without claiming independence that did
not happen.

## Stop conditions

- Missing owner decision that changes product scope or scientific meaning:
  record the question and stop dependent work.
- Missing/blocked primary evidence: preserve as unverified, do not infer the
  missing fact.
- Repeated FAIL: return with specific observations and retest; avoid an
  unbounded loop.
- A task is Done only if all criteria PASS, sources are traceable, unresolved
  caveats are visible, and Mohammed can explain key scientific choices.

GitHub Issues (`m950m/MOFs_Platform/issues`) are the single active backlog;
`_docs/tasks.md` is a migration-time index only. Handoff notes and verdicts are
recorded as issue comments with dates.
