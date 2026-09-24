# Active local backlog

Authority: [plan.md](plan.md), sections 0–8 and Appendix A.7. Sections 0–10 of the plan take precedence over historical appendices. Completed artifacts and review reports remain embedded in Appendix A; references below do not imply that separate files have been extracted.

Tasks 001 and 002 preserve completed documentation/analysis, not implemented software. Task 003 is the first pending implementation task. Tasks 004–013 describe only the first small workflow: record the question and laboratory profile, capture evidence through the selected route, then inspect, correct, save, and reopen it. Their details remain subject to Mohammed's first acceptance case; no question, source, stack, scientific candidate, or review threshold is selected here.

Work on one principal implementation task at a time. A blocked task becomes Ready only when its blocking dependencies and owner decisions are recorded. Future completion requires observable acceptance evidence, independent QA, and scientific review where applicable, following plan section 6; the historical reviews of tasks 001 and 002 do not approve future implementation.

This backlog does not schedule additional providers, automatic cross-source sample merging, modification generation, 3D visualization, prediction, deployment infrastructure, or benefit/novelty studies. HER is an example, and neither QMOF nor historical infrastructure choices are defaults.

Tasks 004–013 are sequential: each waits for the preceding task to be Done and its own owner decisions to be recorded. The completion and review requirements above apply to every task; their acceptance criteria describe future checks, not checks already performed.

## 001. Define the tested-sample identity contract

Goal: Specify evidence-based distinctions between frameworks, prepared samples, operating states, and observations.

Description: Document how identity comparisons preserve source evidence, missing fields, conflicting assertions, and human review without merging samples on shared names or identifiers. The completed contract and five explicitly synthetic cases are in plan Appendix A.5, with completed handoffs and reviews in Appendix A.8; this deliverable is documentation, not product code or verified catalyst data.

Status: Done

Dependencies and owner decisions:

- Basis: plan sections 2–3, the scientific evidence rules, and Appendix A.7's task 001 criteria.
- Documentation closure: independent QA PASS and scientific review are recorded in Appendix A.8; no remaining dependency reopens this completed task.
- Mohammed still owns the threshold for reviewing claims and any cross-source sample-equivalence criterion; these were not decided by the contract.

Acceptance criteria:

- [x] Appendix A.5 specifies minimum inputs for framework, prepared sample, operating state, and observation, and keeps missing values explicitly unknown.
- [x] Identity comparisons return the entity level, relation, reason, evidence, unknown/conflicting fields, review state, and merge permission; relations distinguish same reported sample, same parent, derived/composite, different, and unresolved.
- [x] Five labeled synthetic cases cover different linkers, nanoparticle additions, different activation, reconstructed operating states, and missing structures, with inputs, expected relations, evidence, and merge decisions.
- [x] Observations remain attached to the reported tested sample and measurement conditions; proposed modifications remain hypothetical children of documented parents without invented activity, synthesis success, or geometry.
- [x] Each asserted relation retains source/location, author or extraction method, epistemic type, and review status; missing evidence and conflicting assertions prevent unsupported merging.
- [x] A name, formula, DOI, MOFid, or CIF alone cannot establish tested-sample equivalence; within-source designation requires review, and cross-source equivalence remains an owner-held decision.
- [x] Appendix A.8 contains separate checkable PM, QA, and scientific-review handoffs, including the later completed documentation status.

Learning-to-project mapping:

| Source | Concept | Component | Timing | Problem | Artifact | What Mohammed must understand | What Codex may do |
|---|---|---|---|---|---|---|---|
| AI Dev Tools Zoomcamp; plan sections 2–3 and Appendix A.5 | Specification, entity identity, evidence provenance | Sample and observation linkage | Now: completed documentation; implementation later | False joins between materials and results | Reviewed contract, five synthetic cases, and Appendix A.8 reviews | Why a framework, tested sample, operating state, and observation differ; what evidence establishes a relation | Preserve the contract and reviews; implement only subsequently approved behavior |

## 002. Research first-source and stack options

Goal: Provide documented options from which Mohammed can select a first evidence route and a proportionate local stack.

Description: The completed analysis in plan Appendix A.6 records provider capabilities, access limits, evidence gaps, and local implementation tradeoffs without selecting an option. Appendix A.9 records correction of a QA finding, retest PASS, and scientific review; this work did not connect a source, initialize software, or validate a real catalyst.

Status: Done

Dependencies and owner decisions:

- Basis: the completed tested-sample identity contract in Appendix A.5 and the provider documentation cited and dated in Appendix A.6.
- Analysis closure: the corrected analysis and subsequent QA/scientific reviews are recorded in Appendix A.9.
- Mohammed selects the first precise research question and conditions, first source contract, and local stack; none was selected by this analysis.
- Provider documentation, available fields, and rights must be rechecked before a future live connection; the dated analysis is not ongoing access authorization.

Acceptance criteria:

- [x] Appendix A.6 provides named, dated, primary-source-supported options for literature discovery, structure/CIF discovery, and methods/full-text access, with unverified capabilities marked as gaps.
- [x] Provider entries describe routes, identifiers, fields, sample/measurement/structure availability, authentication, limits, rights, freshness, and unknowns; metadata, abstracts, inspected text, and manual evidence remain distinct.
- [x] A representative HER evidence route identifies where automated access stops and manual inspection is needed, without claiming that a real sample was verified.
- [x] At least two local stack options explain interaction, persistence, provenance, corrections, maintenance, portability, migration, and postponed capabilities without choosing a stack.
- [x] The decision table preserves Mohammed's choices and unresolved conditions without invented scores, performance guarantees, or implicit selection.
- [x] The analysis includes learning mappings, and Appendix A.9 preserves distinct handoffs, the QA correction and retest PASS, and scientific review of the evidence framing.

Learning-to-project mapping:

| Source | Concept | Component | Timing | Problem | Artifact | What Mohammed must understand | What Codex may do |
|---|---|---|---|---|---|---|---|
| AI Dev Tools Zoomcamp; Data Engineering Zoomcamp; primary provider documentation cited in Appendix A.6 | Source contracts, access boundaries, persistence tradeoffs | Evidence acquisition and local review | Now: completed analysis; connection and implementation later | Selecting an unsuitable source or losing provenance during correction | Appendix A.6 options analysis and Appendix A.9 reviews | What sources actually supply, what they omit, and the maintenance consequences of local choices | Preserve the sourced analysis; recheck documentation before approved connection; leave selection to Mohammed |

## 003. Bootstrap an empty runnable project

Goal: Establish an empty local project that starts successfully and has a passing meaningful smoke test.

Description: After Mohammed records the first research question, source contract, and local stack, initialize only the minimal project needed to run the selected local entry point. Verify startup and an observable empty/ready state before implementing API access, evidence ingestion, or scientific behavior.

Status: Blocked

Dependencies and owner decisions:

- Tasks 001 and 002 are complete: identity requirements and option analysis are preserved in plan Appendices A.5–A.9.
- Mohammed must select the first precise research question, relevant electrochemical conditions, and observable acceptance case for the first slice.
- Mohammed must select the initial source contract, including permitted route/content/fields, access rights, and failure behavior; a manual initial route must be explicit if selected.
- Mohammed must select the local stack, including interaction surface, persistence, and repository location.
- All three selections must be recorded before this task becomes Ready; this ticket does not supply defaults or treat silence as approval.

Acceptance criteria:

- [ ] The recorded owner decisions identify the question/acceptance case, source contract, and local stack before implementation begins.
- [ ] In the selected local environment, the documented start command launches the actual entry point and exposes a deterministic empty/ready state with no fabricated scientific records.
- [ ] The documented smoke-test command executes that entry point, verifies its observable startup behavior, and passes without live provider calls, credentials, or real catalyst data.
- [ ] A broken entry point or failed startup makes the smoke test fail; the check does not merely assert a constant or match documentation text.
- [ ] Setup, run, and test instructions reproduce the result; only justified dependencies for the selected bootstrap are introduced, with no ingestion, evidence schema, or scientific workflow implemented in this task.
- [ ] Actual command outcomes and independent QA against these criteria are recorded before marking the task Done.

Learning-to-project mapping:

| Source | Concept | Component | Timing | Problem | Artifact | What Mohammed must understand | What Codex may do |
|---|---|---|---|---|---|---|---|
| AI Dev Tools Zoomcamp; plan sections 6–8 and Appendix A.7 | Bounded implementation, reproducible setup, smoke testing | Local application entry point | Later: after the three owner selections | Starting feature work without a verifiably runnable foundation | Empty runnable project, run instructions, passing smoke test, and QA evidence | What startup success proves and why it does not validate chemistry or provider access | Bootstrap and test the selected stack only; do not choose the question, source, or stack |

## 004. Save and correct the first research question

Goal: Save a researcher-confirmed question and its screening criteria for the first workflow.

Description: Record the selected reaction/application, allowed material classes, conditions, hard requirements, preferences, and meaning of improvement in the chosen local interface. Show the recorded question for correction before it guides evidence review; laboratory-profile entry is a separate task.

Status: Blocked

Dependencies and owner decisions:

- Task 003 must be Done, providing the runnable project and selected interface/persistence.
- Mohammed must supply the first precise question, relevant conditions, allowed material classes, criteria, and observable acceptance case.
- Use the selected local stack; this task does not require automated natural-language interpretation or a new service.

Acceptance criteria:

- [ ] The researcher can enter, inspect, and correct the selected question and criteria before using them for review.
- [ ] Hard requirements, preferences, and unknowns remain distinct; the tool supplies no default reaction, numeric ranking, or universal definition of improvement.
- [ ] Saving, closing, and reopening preserves the corrected question and criteria.
- [ ] Behavioral checks cover a correction and incomplete inputs, showing the saved correction and explicit unknowns without invented criteria.

Learning-to-project mapping:

| Source | Concept | Component | Timing | Problem | Artifact | What Mohammed must understand | What Codex may do |
|---|---|---|---|---|---|---|---|
| Plan sections 2, 5, and 8; Data Engineering Zoomcamp | Explicit requirements and persistence | Research-question capture | Later: after task 003 and owner inputs | Screening against guessed or lost criteria | Reopenable question and correction checks | Requirements, preferences, and unknowns differ | Implement entry, correction, and saving in the selected stack |

## 005. Save the confirmed laboratory profile

Goal: Persist Mohammed's confirmed current, future, and unknown laboratory capabilities.

Description: Record the laboratory profile separately from the research question, using only capabilities supplied or confirmed by Mohammed. Allow correction and reopening of that profile without treating historical laboratory statements as current facts.

Status: Blocked

Dependencies and owner decisions:

- Task 004 must be Done, providing saved question entry in the selected local interface.
- Mohammed must confirm the current/future/unknown capability profile; unknown facts may remain unknown.
- Historical glovebox, inert-gas, reflux, storage, and HHTP statements are not defaults or universal material restrictions.

Acceptance criteria:

- [ ] The researcher can enter and inspect current capabilities, future capabilities, and unresolved facts as distinct profile entries.
- [ ] An unknown capability is treated as neither available nor unavailable, and a future capability is not counted as currently available.
- [ ] A researcher correction survives saving, closing, and reopening without introducing unconfirmed laboratory facts.
- [ ] A check using an incomplete profile verifies visible unknowns and persistence; capability entries alone do not classify a candidate's laboratory fit.

Learning-to-project mapping:

| Source | Concept | Component | Timing | Problem | Artifact | What Mohammed must understand | What Codex may do |
|---|---|---|---|---|---|---|---|
| Plan sections 2 and 5; Data Engineering Zoomcamp | Explicit uncertainty and persistent inputs | Laboratory-profile capture | Later: after task 004 and profile confirmation | Assuming equipment availability from old statements | Reopenable confirmed profile and incomplete-profile check | Current, future, unavailable, and unknown facts cannot be substituted for one another | Implement profile entry, correction, and persistence; never invent capabilities |

## 006. Capture source references through the selected route

Goal: Save references for the first question using only Mohammed's selected source route.

Description: Implement one small successful reference-capture path through the selected provider or attributed manual route. Preserve how each reference was obtained and what content was actually inspected; access restrictions apply immediately, while detailed failure handling is scoped to task 009.

Status: Blocked

Dependencies and owner decisions:

- Task 005 must be Done; the saved question, confirmed profile, and selected local stack are available.
- Mohammed's source contract must specify the provider or manual route, permitted input/query scope, fields/content, rights, and failure behavior.
- Recheck current primary provider documentation and applicable access/reuse rights before any live connection; an available URL does not itself permit text ingestion.

Acceptance criteria:

- [ ] One small query or supplied reference input uses the selected route and saves the resulting references against the recorded question.
- [ ] Each reference retains its source identifier, available version, retrieval/entry date, query or supplied input, and manual attribution where applicable.
- [ ] The record distinguishes inspected metadata, abstract, actual text version, and user-supplied passage; metadata-only leads remain `needs verification` and establish no sample identity, synthesis, or measured activity.
- [ ] References and inspection metadata survive restart; no prohibited content or unapproved provider is accessed, and retrieved text is treated as data rather than instructions.

Learning-to-project mapping:

| Source | Concept | Component | Timing | Problem | Artifact | What Mohammed must understand | What Codex may do |
|---|---|---|---|---|---|---|---|
| Selected provider's primary documentation; plan section 4 and Appendix A.6 | Source contracts and retrieval provenance | Reference capture | Later: after task 005 and access verification | Losing retrieval context or treating a reference as verified evidence | Saved references with query/input and inspection history | Discovery, inspection, and permission are separate facts | Implement only the selected permitted route and attributed manual reference entry |

## 007. Record attributed evidence assertions

Goal: Save individual claims with their source, evidence location, attribution, and uncertainty.

Description: Record assertions from permitted inspected content or attributed manual entries against saved source references. Keep direct reports, author interpretations, tool inferences, user judgments, and unknowns distinguishable without implementing sample matching or review approval in this task.

Status: Blocked

Dependencies and owner decisions:

- Task 006 must be Done, providing saved references and their source/inspection metadata.
- Use only content and manual entry permitted by Mohammed's selected source contract.
- Mohammed's review threshold remains open; this task must not mark assertions reviewed or infer scientific facts from discovery metadata.

Acceptance criteria:

- [ ] Each assertion links to its source and available version/retrieval date, exact evidence location when available, extraction author/method, epistemic type, and review state; manual entries identify their contributor and underlying source.
- [ ] Missing locations and scientific fields stay explicitly unknown and require verification rather than causing an otherwise valid evidence record to be rejected.
- [ ] Conflicting assertions retain their own provenance and remain inspectable without overwrite or averaging; metadata alone does not become a sample-specific scientific claim.
- [ ] Assertions and evidence pointers survive restart; checks cover a located assertion, missing location, conflicting assertions, and paper text remaining data rather than system instructions.

Learning-to-project mapping:

| Source | Concept | Component | Timing | Problem | Artifact | What Mohammed must understand | What Codex may do |
|---|---|---|---|---|---|---|---|
| Plan section 3 and Appendix A.5; Data Engineering Zoomcamp | Claim-level provenance and uncertainty | Evidence-assertion capture | Later: after task 006 | Unattributed claims or lost conflicting evidence | Reopenable assertions and provenance checks | A reported fact, interpretation, inference, and judgment have different evidentiary status | Implement attributed recording and persistence; preserve missing and conflicting evidence |

## 008. Link tested samples and observations without false merges

Goal: Link evidence to the correct tested sample while preserving distinct parent, sample, state, and observation identities.

Description: Record the source-supported relations between a framework, prepared sample, operating state, and observation using the identity contract. Preserve distinct modifications, preparation histories, and measurement conditions; shared identifiers or a proposed active phase cannot transfer results between entities.

Status: Blocked

Dependencies and owner decisions:

- Task 007 must be Done, providing attributed assertions and evidence locations.
- Apply plan section 3 and Appendix A.5, including all five explicitly synthetic identity cases.
- Cross-source tested-sample equivalence remains Mohammed's decision; retain separate records while its criterion is unset, and never merge automatically across sources.
- Within-source designation requires reviewed explicit evidence; use labeled reviewed/unreviewed synthetic fixtures for linkage checks here. Human review transitions belong to task 011; do not upgrade live assertions in this task.

Acceptance criteria:

- [ ] Relations preserve entity level, reason, evidence, unknown/conflicting fields, review state, and merge permission, distinguishing same reported sample, same parent, derived/composite, different, and unresolved.
- [ ] Observations retain reported values/units and independently known or unknown reaction, medium, reference/conversion, loading, duration, and protocol; each stays attached to its tested sample, not its parent or an inferred operating phase.
- [ ] Persisted records distinguish prepared samples, modifications, operating-state interpretations, and experimental/computational/hypothetical evidence where supported; unknown identities stay unknown.
- [ ] Behavioral checks cover different linkers, nanoparticle additions, different activation, reconstructed operating states, and missing structures; a shared name, formula, DOI, MOFid, or CIF alone never merges samples, and conflicts preserve unresolved relations.
- [ ] Links and conditions survive restart; within-source references can resolve to one reported sample only on reviewed explicit designation, while distinct observations and cross-source sample records remain separate.

Learning-to-project mapping:

| Source | Concept | Component | Timing | Problem | Artifact | What Mohammed must understand | What Codex may do |
|---|---|---|---|---|---|---|---|
| Plan section 3 and Appendix A.5 | Entity identity and evidence-based relations | Sample/state/observation linkage | Later: after task 007 | Assigning measurements to the wrong material | Persistent links and five synthetic behavioral checks | A parent structure or DOI does not identify a tested sample | Implement the documented identity boundaries; leave equivalence criteria to Mohammed |

## 009. Handle the selected source route's failures

Goal: Make failures of the chosen source route visible without corrupting saved work or bypassing access restrictions.

Description: Add and check the selected route's approved failure and recovery behavior around reference/evidence capture. Cover only failures applicable to that route, keeping missing scientific information distinct from invalid input or transport failure.

Status: Blocked

Dependencies and owner decisions:

- Task 008 must be Done, providing saved references, assertions, and sample/observation links to protect during failure checks.
- Mohammed's selected source contract must define failure behavior, permitted recovery/retry actions, and access boundaries.
- Network failure checks apply only if the selected route uses network access; manual entry is not permission to fetch restricted text or substitute a provider.

Acceptance criteria:

- [ ] No usable result and invalid input produce explicit outcomes without damaging existing records; missing scientific fields remain valid unknowns.
- [ ] If applicable, timeout, access denial, and provider-limit responses follow the contract, with retries only where allowed and valid.
- [ ] Unavailable or prohibited full text leaves a reference/link and a permitted inspection route where one exists, or an explicit access gap; no bypass or unapproved source fallback occurs.
- [ ] Focused failure/recovery checks show existing references, assertions, and links remain intact, and a failed retrieval is not reported as successful evidence capture.

Learning-to-project mapping:

| Source | Concept | Component | Timing | Problem | Artifact | What Mohammed must understand | What Codex may do |
|---|---|---|---|---|---|---|---|
| Selected provider's primary documentation; plan sections 2 and 8 | Explicit errors, access boundaries, recovery | Selected-route failure handling | Later: after task 008 and agreed failure behavior | Silent loss, false success, or unauthorized fallback | Observable failure outcomes and recovery checks | Missing evidence, invalid input, and denied access mean different things | Implement and check only applicable, contract-permitted handling |

## 010. Inspect candidates and their source trail

Goal: Let the researcher inspect why each candidate appeared and follow its claims to the recorded evidence.

Description: Present saved candidates, their sample context, and their source trail through the selected local interface. This task provides inspection only; assertion editing/review and laboratory-fit explanation remain separate tasks.

Status: Blocked

Dependencies and owner decisions:

- Task 009 must be Done, providing persistent evidence, identity links, and observable route failures.
- Use Mohammed's selected interface and saved question; no new interface technology, ranking rule, or shortlist size is selected.
- Follow the selected source contract when presenting links or content; unavailable text remains an access gap.

Acceptance criteria:

- [ ] Inspection shows the retrieval reason, material class, parent relation, modifications, tested sample/conditions, operating-state interpretation, and experimental/computational/hypothetical status where supported.
- [ ] Each claim exposes its source/location, inspected content level, and individual review state; unknowns, missing evidence, and conflicting assertions remain visible.
- [ ] Missing or incompatible electrochemical conditions do not imply comparable performance, and insufficient evidence produces no invented candidates or forced shortlist size.
- [ ] After restart, a focused inspection check follows a candidate to its saved evidence pointers and still exposes unresolved fields without fetching prohibited content.

Learning-to-project mapping:

| Source | Concept | Component | Timing | Problem | Artifact | What Mohammed must understand | What Codex may do |
|---|---|---|---|---|---|---|---|
| Plan sections 2–3 and Appendix A.5 | Traceability and contextual presentation | Candidate inspection | Later: after task 009 | Candidate lists hiding their evidence or uncertainty | Inspectable candidate/source trail and focused check | Inclusion is not validation, and observations need their sample conditions | Present recorded evidence and gaps without scientific ranking or material selection |

## 011. Correct and review individual assertions

Goal: Preserve attributed corrections and apply Mohammed's review rule to individual claims and relations.

Description: Let the researcher correct an assertion or relation while retaining its original content and the reason for the change. Record review decisions per assertion, including unresolved conflicts, without converting an entire material into a reviewed result.

Status: Blocked

Dependencies and owner decisions:

- Task 010 must be Done, providing inspection of saved candidates and their source trails.
- Mohammed must define the evidence threshold for marking a claim or relation `reviewed`; it is not supplied by the tool.
- Any human approval of cross-source tested-sample equivalence also requires Mohammed's criterion; until recorded, keep records separate and that equivalence unresolved, without blocking other assertion reviews.
- Corrections and inspection remain within the selected source contract and local stack.

Acceptance criteria:

- [ ] Each correction retains the original assertion and records the reviewer/contributor, date, change, and reason; conflicting source assertions are neither overwritten nor averaged.
- [ ] `needs verification`, `in review`, `reviewed`, and `conflicted` apply individually; a reviewed assertion records reviewer, date, supporting location, and satisfaction of Mohammed's threshold.
- [ ] Unsupported review transitions are rejected, within-source identity approval requires explicit designation evidence, and cross-source records never merge automatically.
- [ ] Correction/review checks include a conflict and insufficient evidence; reopening preserves history and decisions, with unsupported cases still unresolved.

Learning-to-project mapping:

| Source | Concept | Component | Timing | Problem | Artifact | What Mohammed must understand | What Codex may do |
|---|---|---|---|---|---|---|---|
| Plan sections 3 and 5; Appendix A.5; Data Engineering Zoomcamp | Human review and correction history | Assertion correction/review | Later: after task 010 and owner review rule | Losing corrections or approving claims without sufficient evidence | Reopenable correction history and review-rule checks | Review is assertion-specific and does not prove all claims about a material | Implement the owner-defined rule and attribution; never decide the threshold |

## 012. Explain laboratory fit from recorded requirements

Goal: Explain current, future, or unknown laboratory fit from sourced requirements and the confirmed profile.

Description: Relate reported preparation/testing requirements to Mohammed's saved laboratory profile for the selected question. Show the evidence and missing facts behind each assessment without guessing capabilities or asserting synthesis success.

Status: Blocked

Dependencies and owner decisions:

- Task 011 must be Done, providing inspectable requirements, assertion corrections, and review states.
- Use the confirmed profile saved in task 005 and the owner-selected question/conditions; Mohammed must reconfirm changed or unresolved capability facts when needed.
- Use only sourced requirements and the selected review rule; the tool does not choose capabilities, feasibility thresholds, or scientific conclusions.

Acceptance criteria:

- [ ] The assessment distinguishes possible with current capabilities, requires future capabilities, and unknown, with reasons pointing to the relevant requirements, evidence locations/review states, and profile entries.
- [ ] Future capabilities do not count as current; missing or conflicting requirements/capabilities cannot produce unsupported positive fit and remain visible with their reasons.
- [ ] Focused checks cover supported current fit, a documented future requirement, and insufficient/conflicting evidence, without inferring synthesis success or imposing historical HHTP restrictions.
- [ ] Reopening retains the assessment's reasons and recorded basis; a corrected requirement or profile cannot leave an outdated fit presented as current.

Learning-to-project mapping:

| Source | Concept | Component | Timing | Problem | Artifact | What Mohammed must understand | What Codex may do |
|---|---|---|---|---|---|---|---|
| Plan sections 2–3 and 5 | Evidence-based comparison with explicit uncertainty | Laboratory-fit explanation | Later: after task 011 and confirmed profile | Treating unknown requirements or future equipment as present feasibility | Inspectable fit reasons and focused checks | Fit depends on reported requirements and recorded capabilities, not a universal material label | Explain documented fit and gaps; never invent laboratory facts or promise experimental success |

## 013. Check the complete first evidence workflow

Goal: Verify the implemented first workflow against Mohammed's acceptance case from question entry through saved review.

Description: Exercise the existing small workflow end to end, including reopening saved work and the relevant incomplete/conflicting cases. Record observable results for independent QA and scientific review without adding features or treating software success as scientific validation.

Status: Blocked

Dependencies and owner decisions:

- Task 012 and the preceding sequential tasks 003–011 must be Done, with their focused check evidence available.
- Mohammed's recorded acceptance case, question/conditions, source contract, local stack, confirmed profile, and assertion-review rule define the check.
- Cross-source equivalence remains unresolved unless Mohammed has provided its criterion; a passing workflow does not require inventing one.
- Use only permitted evidence and clearly labeled synthetic fixtures where needed; benefit claims require a later evaluation set and manual baseline outside this task.

Acceptance criteria:

- [ ] The owner-approved case runs through saving/correcting the question and profile, capturing references/assertions, linking samples/observations, inspecting candidates, correcting/reviewing assertions, and explaining laboratory fit.
- [ ] Relevant missing/conflicting evidence and selected-route failure cases remain explicit without false sample merges, lost records, unsupported review/fit, or unauthorized access.
- [ ] After restart, the question, profile, references, sample conditions, provenance, corrections, review states, conflicts, and fit reasons remain inspectable; unsupported cases remain unresolved.
- [ ] Actual outcomes and any failures are recorded, independent QA checks the acceptance criteria, and scientific review checks the delivered evidence framing before completion; no catalyst validation, novelty, or measured benefit is claimed.

Learning-to-project mapping:

| Source | Concept | Component | Timing | Problem | Artifact | What Mohammed must understand | What Codex may do |
|---|---|---|---|---|---|---|---|
| Plan sections 6–8; AI Dev Tools Zoomcamp | End-to-end acceptance and independent review | Complete first evidence workflow | Later: after task 012 and preceding checks | Individually working steps failing as a research workflow | Recorded acceptance run and independent QA/scientific reviews | Workflow success does not establish catalytic success, novelty, or research benefit | Check existing behavior against the owner's case and report failures without expanding scope |
