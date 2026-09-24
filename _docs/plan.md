# MOF Electrochemistry Research Tool — Codex Project Specification

**Status date:** 24 September 2026  
**Scientific and product decision owner:** Mohammed  
**Purpose:** A self-contained English handoff for a Codex project and, after review, a GitHub repository. Tasks 001 and 002 produced reviewed documentation and analysis. No product code exists yet. Implementation task 003 awaits decisions reserved for the owner.

## 0. Reading order and authority

Sections 0–10 state the **current specification**. Appendix A preserves the complete preparatory Codex package, including the identity contract, provider and stack options, role descriptions, tasks, and review reports. Appendix B contains English copies of the nine attached project files from an older phase. Appendix C contains an English version of an earlier research brief. The historical appendices are background; where their first-use-case assumptions conflict with a current decision, use the current decision. Do not select a scientific candidate, provider, or stack on Mohammed's behalf.

| Previous assumption | Current decision | Consequence for Codex |
|---|---|---|
| QMOF band-gap comparison is the first use case | The initial use case helps investigate MOF-related candidates for an electrochemical question; HER is an example. | Do not begin QMOF ingestion or band-gap comparison because it appears in older files. QMOF could become relevant later if its data serve an approved question. |
| Search only pristine MOFs | Include MOFs, ZIFs, MOF-containing composites, and MOF-derived nanomaterials. | Identify each candidate's material class and relation to its parent. |
| Show only synthesized candidates | Include experimental, computational, and insufficiently verified records, each clearly labeled. | A computed result or metadata record is not a measured catalyst result. |
| Use PostgreSQL, Docker, and a particular interface | These appear in historical plans and are not currently selected. | The L1/L2 options in Appendix A are comparisons, not an implementation decision. |
| Always return five materials | Five was an example of a research shortlist. | Return only candidates the inspected evidence supports and show any shortfall. |

The discussion of agent roles drew on [AI-Native Development: Specifications, Loop and Graph Engineering](https://aishippingblog.com/p/ai-native-development-specifications). Its workflow motivates specifications, bounded tasks, implementation, and independent checks; its example is not a scientific specification for this project.

## 1. Problem, user, and purpose

The first user is a graduate student or researcher investigating a question in electrochemistry who needs to know **why each candidate appeared, the source of each claim, and what remains unknown**. The product helps discover literature, develop a review nucleus, inspect one material in depth, and compare reported preparation and testing requirements against a documented laboratory capability profile. The researcher reviews the evidence, writes the scientific conclusions, and chooses materials.

The broader project direction is traceable, reproducible scientific materials data engineering. MOF-related electrochemistry is the first bounded case study. Potential improvements in search time, error rates, or research quality remain hypotheses to evaluate, not established achievements or an approved paper contribution.

HER is an illustrative first reaction, not the limit of the tool. The precise first question, relevant conditions, and acceptance metric for the first implemented slice have not been selected.

## 2. Confirmed product behavior

1. **Interpret the research question.** Record the reaction/application, allowed material classes, hard requirements, preferences, current and future laboratory capabilities, and unknowns. Show the interpreted question for the researcher to correct. Define the meaning of an “improvement” from that particular question, rather than fixing catalytic activity or stability as a universal target.
2. **Discover evidence.** Use existing databases and documented legal APIs where appropriate; accept manually entered papers, DOIs, and evidence. If automated full-text access is prohibited or unavailable, show the reference, link, and permitted route. Record whether metadata, an abstract, an actual text version, or a user-supplied passage was inspected.
3. **Label candidate status.** Distinguish an experimentally prepared material, a computational proposal/study, and a new untested hypothesis. Display metadata-only leads as `needs verification` and identify the missing evidence. Do not infer a synthesis method, sample identity, or HER measurement from a title or database index.
4. **Keep sample identity intact.** Compare experimental performance at the level of the **reported tested sample with its documented modifications and conditions**, not a generic MOF name or a parent framework. Link, but do not collapse, the parent, composite/derivative, prepared sample, operating state, and observation.
5. **Assess laboratory fit.** Separate “possible with currently recorded capabilities,” “requires future capabilities,” and “unknown,” with reasons and evidence. Earlier discussions reported no glovebox/inert-gas line, difficulty with prolonged reflux under argon and inert storage, and exclusion of HHTP on that basis. Reconfirm the current laboratory profile before using those inputs to classify a candidate; they are not universal material facts.
6. **Support researcher-led review.** Suggest papers, comparison themes, disagreements, and questions requiring inspection; let the researcher follow source locations and correct links or extracted data. The tool does not write the scientific conclusion or assert novelty from an unsuccessful search.
7. **Suggest modifications.** Begin with evidence-motivated changes to a documented parent. Display the change, rationale, supporting source, and an explicit **untested hypothesis** label. Entirely new designs, subsequent theoretical evaluation, and predictive performance modeling are possible later work, not demonstrated first-version abilities.
8. **Handle three-dimensional structure honestly.** After structure identity and provenance are settled, a later feature may display colored atomic coordinates from a documented CIF. Label it a **crystal structure model**. It does not show nanoparticle morphology, the distribution of added components, or necessarily the active phase during reaction. Label an illustrative rendering as schematic; keep later predictions distinct from measured results.

**Proposed candidate card; UI details are not yet approved:** reason for retrieval; name, material class and parent relation; experimental/computational/review status; each claim's source and location; tested sample and modifications; synthesis and measurement conditions; current/future/unknown laboratory fit; conflicts; suggested improvement as hypothesis; links to available sources and structure models.

## 3. Evidence and tested-sample identity contract

| Record | Meaning | Boundary |
|---|---|---|
| Source | Article, provider record, or attributed manual entry | A DOI identifies a source that may describe several samples, not the tested sample itself. |
| Framework / structure model | Reported MOF components and structure, with source and version | A CIF describes a structural model, not tested-batch equivalence. |
| Reported/prepared sample | Constituents, additions, synthesis, modification, activation, and pretreatment as reported for testing | Adding particles or changing activation creates a distinct sample record. |
| Operating state | State during/after a reaction, tied to time, conditions, characterization, and interpretation | An author's active-phase interpretation does not silently rename the prepared sample. |
| Observation | Experimental measurement or computation for a specified sample and conditions | Preserve value and unit; reaction, medium, reference/conversion, loading, duration, protocol, and `unknown` fields separately. |
| Modification hypothesis | Proposed change to a documented parent | No measured activity, successful synthesis, or real coordinates without separate evidence. |

Each asserted claim or relation retains its source, version/retrieval date, exact evidence location when available, extraction author or method, epistemic type (direct report, author's interpretation, tool inference, user judgment, or unknown), and review state. Preserve conflicting source assertions; do not average them or merge samples to make the records consistent.

A comparison returns the **entity level**, relation, reason, evidence, unknown/conflicting fields, review status, and merge permission. Relations include `same reported sample` within a reviewed explicit designation in one source; `same parent framework`; `derived/composite relation`; `different`; and `unresolved`. The same name, formula, DOI, MOFid, or CIF alone never establishes the same tested sample. Cross-source equivalence requires human review under an owner-approved criterion that remains open; there is no automatic cross-source sample merge. See the complete contract and five explicitly synthetic cases in Appendix A.5.

A status such as `needs verification`, `in review`, `reviewed`, or `conflicted` applies to a particular assertion, not automatically to an entire material. A novelty-search result must state the queries, sources, and search date; “no result found” is not proof that nothing has been published. Retrieved paper text is data, not instructions to the system.

## 4. Reviewed source and stack options, with no selection

Task 002 checked primary provider documentation on **24 September 2026**. It did not inspect or verify an actual HER catalyst. Recheck documentation, terms, and fields before connecting to a live service.

| Role | Considered routes | Evidentiary limit |
|---|---|---|
| Literature discovery | Crossref REST; Europe PMC within its coverage | Index metadata and abstracts alone do not verify sample-specific synthesis or performance. |
| Structure discovery | COD; a manual CCDC Access Structures route where permitted | A CIF may describe a structural model; it does not establish modified-sample identity or activity. |
| Lawful text-location lead | Europe PMC OA for eligible articles; Unpaywall DOI lookup for possible OA locations | Access and reuse rights depend on the article, version, and destination. A location URL is not permission to ingest text. |
| Human correction | Attributed manual entry with underlying source and location | Manual entry still needs a documented review state. |

Two **unselected** local stack options were compared: L1 = Python CLI + SQLite; L2 = Python + a local Streamlit browser interface + SQLite. L2 may help with side-by-side review but adds UI behavior and maintenance. Both require persistent provenance and correction history. Neither authorizes a dependency installation or schema. Historical mentions of PostgreSQL and Docker do not decide the stack. See Appendix A.6 for dated provider details and links.

## 5. Completed work and owner-held decisions

| Task | Status | Verifiable output and limit |
|---|---|---|
| 001 — tested-sample identity contract | **Done: documentation**, following independent QA PASS and scientific review | Contract and five synthetic scenarios in A.5; handoff report in A.8. No product code or verified catalyst. |
| 002 — first-source and stack comparison | **Done: analysis**, after a QA finding was corrected, retested PASS, and scientifically reviewed | Dated, sourced options in A.6; handoff report in A.9. No source or stack selected and no real sample validated. |
| 003 — bootstrap a runnable local project | **Blocked** | Requires the owner's first precise research/acceptance question, initial source contract, and local stack selection. Preparing repository instructions and role definitions can proceed without treating task 003 as started. |

**Decisions reserved for Mohammed:** the first exact question and relevant electrochemical conditions/acceptance observation; first provider and permitted fields/access/failure contract; local interface, persistence, and repository location; current/future/unknown lab capability profile; what evidence permits a claim to become `reviewed`; and whether/how a person may judge two sources to describe the “same reported tested sample.” A later evaluation set and manual baseline must also be defined before claims of benefit. Do not fill an unanswered field by guessing or by treating silence as approval.

Decision record template:

~~~text
Decision ID / date / owner: ... / ... / Mohammed
First precise research question and relevant conditions: ...
Observable acceptance case for the first slice: ...
Selected first source, permitted API route and fields, rights, and failure behavior: ...
Selected local UI, persistence, and repository: ...
Current / future / unknown laboratory capabilities: ...
Evidence-review threshold and cross-source sample equivalence rule: ...
Reason, supporting source, alternative, and implications for task 003: ...
~~~

## 6. Codex roles and task handoffs

| Role | Responsibility | Limit and deliverable |
|---|---|---|
| Mohammed, owner | States the question and constraints; decides product scope, scientific interpretation, and acceptance | A written owner decision; Codex does not decide for him. |
| Orchestrator, main Codex thread | Tracks one active task, delegates bounded roles, receives verdicts and escalates owner decisions | Updated backlog and handoff record; cannot call its own self-check independent QA. |
| PM | Defines the goal, observable criteria, exclusions, dependencies, and unknowns | No code, stack choice, or catalyst verdict; produces a groomed ticket. |
| Scientific reviewer before execution | Examines material identity, scientific language, claim type, and evidence | No invented references or owner decisions; produces a checkable review. |
| Engineer | Implements the accepted task with explicit inputs, outputs, errors, provenance, and meaningful checks | Does not rewrite acceptance criteria or bypass access controls; delivers actual artifacts. |
| Independent QA | Examines the actual output against **each** criterion, reporting PASS/FAIL and test evidence | Does not fix the output or rely solely on the engineer's account. |
| Scientific reviewer after QA | Examines the delivered science-bearing content | Software QA PASS alone does not validate chemistry. |

Sequence: required owner decision → PM ticket → scientific check where applicable → engineer output → independent QA → engineer correction on FAIL → final scientific review for science-bearing work → orchestrator closes only after applicable checks pass. Parallelize only genuinely independent work; QA must inspect a completed artifact. If actual subagents are unavailable, use separate review sessions and describe their real independence accurately.

**Technical distinction:** `AGENTS.md` supplies project instructions that Codex reads; the `_docs/team/*.md` role descriptions in Appendix A do not instantiate agents. Official Codex documentation describes local custom agents as TOML files under `.codex/agents/`, each with `name`, `description`, and `developer_instructions`. Request delegation explicitly for a bounded task and inspect the separate reports. [Official subagents guide](https://learn.chatgpt.com/docs/agent-configuration/subagents).

## 7. First implementation slice and evaluation

After Mohammed records the prerequisites, PM grooms task 003: an executable local project and a meaningful smoke test for the chosen source, question, and stack, followed by a small evidence route that visibly preserves missing fields and human review. An initial smoke test need not demonstrate catalytic success, 3D visualization, DFT, or prediction. When implementing the identity behavior, use cases with different linkers, nanoparticle additions, different activation, reconstructed operating states, and missing structures; verify observable behavior instead of merely comparing documentation strings.

**Possible later evaluation measures, not measured results:** correct attribution of sample/value/source; detection of conflicts and unknowns; retrieval coverage on a human-reviewed reference set; direct traceability to evidence locations; and time, steps, and errors versus a well-organized manual review. Neither publication novelty nor academic impact follows from a working prototype alone.

## 8. Software Engineering, lightweight Project Management, and course mapping

Carry forward relevant engineering principles from the older control documents: separate source retrieval, validation, identity, storage, and presentation where real boundaries exist; define inputs, outputs, errors and corrections; retain source versions and provenance; test meaningful behavior and failure cases; explain new dependencies; keep secrets out of Git. Use one active backlog, one principal implementation task at a time, clear Ready/Done criteria, a decision/risk log, and reviewable Git changes. These rules do not impose the older technical architecture.

| Originating course/source | Concept | Platform component | Timing | Problem solved | Verifiable artifact | Mohammed must understand | Codex may do |
|---|---|---|---|---|---|---|---|
| Alexey article; AI Dev Tools Zoomcamp | Specification, acceptance, role handoffs | Backlog and review | **Now** | Prevent agents filling gaps with assumptions | Tasks 001/002 and review reports; task 003 after owner decisions | Meaning of PASS, scope and vetoes | Groom/check bounded tickets. |
| Task 001; scientific evidence policy | Identity and provenance | Framework/sample/state/observation relations | **Now as contract; implementation later** | Prevent false sample and result joins | Synthetic contract cases; later behavioral tests | What each entity represents and what proves identity | Implement approved behavior and tests. |
| Provider documentation in A.6 | Legal source contract | Discovery and evidence capture | **Now for selection; later for connection** | Avoid treating metadata as verified preparation | Written provider decision and later contract | What each API supplies and omits | Connect only the selected permitted route. |
| Data Engineering Zoomcamp | Python/SQL, storage and validation | Local evidence records | **Later, after stack choice** | Preserve retrieval and human correction history | Repeatable retrieval and observable failure behavior | Raw source versus reviewer correction | Implement the selected workflow. |
| Documented CIF source | Atomic visualization | Structural viewer | **Later** | Show a traceable structure model | Viewer identifying CIF and source with honest label | CIF versus tested sample and morphology | Build and check the approved viewer. |
| DFT/ML, HPC, Kubernetes courses | Simulation, prediction, scaling | Possible separate study or later need | **Foundation only / not relevant now** | No current first-slice need justifies these dependencies | Recorded postponement and reason | Validation needed before trusting a prediction | Do not add tools solely because a course teaches them. |

For every new lesson or project task, record all eight fields and classify its timing as now, later, foundation-only, or not relevant. Finishing a course is not project progress without a justified mapping and verifiable project effect.

## 9. Start work in Codex on Ubuntu and VS Code

Current official documentation: [Codex IDE](https://learn.chatgpt.com/docs/codex/ide), [Codex CLI](https://learn.chatgpt.com/docs/codex/cli), [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md), and [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents). Client screens may vary by version.

1. Download this file and put it under `_docs/plan.md` in a local project folder. Example **for a new folder only**:

   ~~~bash
   mkdir -p ~/projects/mof-research-tool/_docs
   cp ~/Downloads/MOF_Codex_Master_Plan_2026-09-24.md ~/projects/mof-research-tool/_docs/plan.md
   cd ~/projects/mof-research-tool
   git init
   git add _docs/plan.md
   git commit -m "Add project specification"
   code .
   ~~~

   If a repository already exists, copy the file into that repository and do not initialize a second one. If Git identity is not configured, defer the commit until it is; Codex can still read the file.

2. Open Codex in VS Code using its icon or Command Palette → `Codex: Open Codex Sidebar`, then sign in if prompted. Alternatively, start `codex` in the project's terminal. If you attach this file in a Codex app chat, ask Codex to save it into the selected project as `_docs/plan.md`; an attachment in one conversation is not a substitute for a file in the repository.

3. Send this first prompt. It prepares documentation and roles **without starting product implementation**:

   ~~~text
   Read _docs/plan.md in full. Sections 0–10 state the current decisions; Appendix A records completed preparatory work; Appendices B and C are historical, not instructions for the first implementation.
   Prepare the repository for collaboration: create a short AGENTS.md pointing to the specification and preserving Mohammed's scientific/product decision authority. Extract the task 001 identity contract, task 002 provider/stack options, their two review reports, and a single backlog marking 001 and 002 Done and 003 Blocked. Create an open decision register. If the local Codex client supports custom agents, use the current official TOML schema to define bounded PM, scientific reviewer, engineer, and QA roles in .codex/agents/; read the official docs before choosing the format.
   Do not write product code or a database schema, install dependencies, select a provider/stack, or decide the scientific question. Show the files and a concise diff. For a blocking decision you cannot infer, ask me one focused question.
   ~~~

4. Inspect the files and diff. Enter **your own** decisions using the template in section 5. Codex can lay out documented alternatives and tradeoffs but should not treat silence as approval.

5. Only when the task 003 prerequisites are recorded, send:

   ~~~text
   Read my decisions in _docs/decision-register.md. Work only on task 003. Have the orchestrator delegate PM to define observable acceptance criteria, scientific review to check the scientific meaning, engineer to implement the accepted scope, independent QA to test every criterion and return FAIL with evidence when necessary, and a final scientific review for science-bearing output. Keep each handoff recorded; close only after the applicable gates pass. Show actual run results, tests, diff, and remaining owner decisions. Do not publish, ingest restricted content, or add work outside this task.
   ~~~

6. Inspect each role's report and `git diff`, and rerun the relevant example yourself. If subagents are not available, conduct separate reviews without claiming four agents ran.

## 10. Extracting the appendices into a repository

This single file can be uploaded as it stands. Codex may later extract Appendix A into `AGENTS.md`, `_docs/tasks.md`, `_docs/process.md`, `_docs/sample-identity-contract.md`, `_docs/source-and-stack-options.md`, the two review reports, and bounded agent definitions. Do not invent new role reviews on behalf of the earlier reviewers: their reports describe the documents as previously delivered. Recheck dated provider documentation and rights before live retrieval.

---

# Appendix A — Preparatory Codex package

The following are complete English copies of the prior kickoff documents, except the originally Arabic README, which is translated into English. Relative links within archived files work only after the respective files are extracted to their original relative locations. “Draft/pending” in the identity contract records its state when first written; the task and post-QA review documents record its later completed documentation status.


## A.1 — AGENTS.md: kickoff instructions

Source: `mof_coder_kickoff/AGENTS.md`

````markdown
# Working context for Codex

Read `plan.md`, `_docs/process.md`, and the current task before acting. Read only the role file relevant to the role you are performing. The owner is the scientific and product decision maker.

## Boundaries

- Product: evidence-linked exploration, review support, and improvement hypotheses for MOFs, ZIFs, MOF composites and MOF-derived nanomaterials in electrochemistry.
- Current work: one task at a time. Tasks 001 and 002 are complete as documentation/analysis. Task 003 is blocked on owner choices. No product code, dependencies, database schema, deployment, or GitHub issues until their prerequisites are settled.
- Never equate a generic name, DOI, common formula, MOFid, or structural resemblance with identical tested samples. Keep identity, lineage, and observation separate.
- Distinguish source fact, author's interpretation, tool inference, user judgment, and unknown. Link every material claim to a source and location when available.
- Keep experimental results, computational results, hypotheses, and later predictions separate.
- A crystallographic 3D view from CIF represents a structural model, not necessarily nanoparticle morphology or the active phase under reaction conditions.
- Do not bypass source access controls. Show metadata and a lawful access route when full text is unavailable.
- Never silently revise an owner decision or historical source file. Ask one focused question when an essential decision cannot be inferred.

## Documents

- `plan.md`: current product agreement and explicitly open decisions.
- `_docs/process.md`: roles, workflow, and stop rules.
- `_docs/task-template.md`: standard for a groomed task.
- `_docs/tasks.md`: active local backlog until a repository and issue tracker are chosen.
- `_docs/team/*.md`: bounded agent roles.

For each course or project task, record its source, concept, served component, timing (`now`, `later`, `foundation-only`, `not relevant`), problem, verifiable artifact, what Mohammed must understand, and what Codex may do.
````


## A.2 — plan.md: working product specification

Source: `mof_coder_kickoff/plan.md`

````markdown
# Product specification — working draft, 2026-09-24

## Purpose and owner

The tool helps a researcher answer an electrochemical materials question using MOFs, ZIFs, MOF-containing composites, and MOF-derived nanomaterials. It discovers and organizes evidence, supports literature review and deeper inspection, compares candidate samples against the research question and laboratory constraints, and proposes evidence-motivated modifications. Mohammed remains responsible for scientific interpretation and selection.

HER is an initial example, not the limit of electrochemical questions. The earlier QMOF band-gap comparison is no longer the first task. This does not invalidate QMOF as a potential source of structural data when relevant.

## Confirmed behavior

1. Search legally accessible existing databases and APIs; allow manual entry of references and data. When automated full-text access is restricted, show the source and a permitted route to it. Record exactly which content was actually read.
2. Show both experimentally prepared and computationally studied candidates with explicit labels. An item found only in metadata remains visible as `needs verification`, with the missing evidence named.
3. The unit for comparing experimental performance is the tested **sample**, including all documented additions, derivation and preparation/activation steps, not just a framework nickname. Keep its parent MOF, crystalline structure, pre-test sample, operating state, and result linked but distinct.
4. Separate candidates feasible under currently recorded laboratory capabilities from those requiring future capabilities; treat unknown capability as unknown.
5. Every candidate and improvement has cited supporting sources. Separate what a paper reports from an untested improvement hypothesis. First propose changes to a documented material; wholly new designs come later.
6. Support human-led review by suggesting sources, comparison themes, disagreements, and gaps. The researcher writes conclusions and makes decisions.
7. A colored atomic 3D view may use a traceable CIF. Label that view as a crystal structure model, not an image of the tested composite or operating phase. True 3D particle morphology requires suitable source data; a schematic must be labeled schematic.

## Candidate card: proposed display, not yet UI-approved

Why it answers the question; sample identity and MOF relationship; direct evidence and verification status; electrochemical result with measurement context; preparation and lab feasibility now/future; disagreements and gaps; proposed modification explicitly labeled hypothesis; links to detailed sources and available structural view.

## Later research/development ideas, not first-slice commitments

- De novo material proposals beyond modifications of documented parents.
- A separate theoretical study/evaluation pipeline for modification hypotheses.
- Predictive performance models with domain, uncertainty, validation, and version recorded.
- 3D morphology reconstruction where actual imaging data supports it.

## Open decisions — do not fill with guesses

- First representative electrochemical question and target reaction/conditions for acceptance testing.
- First legally usable API/dataset and source contract; access terms, fields, versions, failure behavior.
- Minimum evidence needed to elevate a candidate from `needs verification` to `reviewed`.
- Laboratory capability profile and how future scenarios are recorded.
- Stack, repository location, UI form, and storage engine.
- Evaluation set, baseline manual workflow, sample identity equivalence thresholds, and review owner.

## Evidence and claims

No list position proves catalytic activity or novelty. Preserve source type, access, exact evidence location, measurement conditions, extraction method, and reviewer correction. An unsuccessful novelty search is a statement about searched sources and date, never proof of absence.
````


## A.3a — PM role

Source: `mof_coder_kickoff/_docs/team/pm.md`

````markdown
# Product manager agent

Read the active task and `plan.md`. Groom only one task. Replace vague language with observable acceptance criteria, awkward cases, dependencies, and exclusions. Preserve owner decisions and label proposed changes as proposals. If scientific meaning is unclear, write one focused question for Mohammed. Do not write code or decide material identity.

Done when an engineer unfamiliar with the chat could complete the task, every criterion can be checked, and moved work appears in a follow-up task. Record changes in the task handoff note.
````


## A.3b — Scientific reviewer role

Source: `mof_coder_kickoff/_docs/team/scientific-reviewer.md`

````markdown
# Scientific reviewer agent

Check whether a task or artifact correctly separates framework, sample, derivative/composite, operating phase, experiment, literature assertion, and untested hypothesis. Demand a cited source for real scientific claims. Report PASS/FAIL per scientific requirement with evidence location and precise ambiguity. Never invent a source, solve a product choice on behalf of Mohammed, write code, or silently modify acceptance criteria.

For task 001, review both before implementation (criteria) and after QA (finished contract). Synthetic examples are checks of logic, not claims about real materials.
````


## A.3c — Engineer role

Source: `mof_coder_kickoff/_docs/team/engineer.md`

````markdown
# Data and software engineer agent

Implement one groomed task against its criteria. For executable tasks, preserve source and version provenance, make failure behavior explicit, use minimal dependencies, and test meaningful behavior. For task 001, deliver the contract document and synthetic examples only. Do not change task acceptance criteria, install a package, select a stack, or close the task. Explain any blocker to the orchestrator.
````


## A.3d — QA role

Source: `mof_coder_kickoff/_docs/team/qa.md`

````markdown
# QA agent

Independently inspect the actual artifact against every acceptance criterion. Report `PASS` or `FAIL` for each criterion, what was inspected, and any test commands/results. One failed criterion means overall FAIL. Report errors and missing evidence; do not fix them, change the task, or trust the engineer's description of its own work. Record the verdict in the task handoff note.
````


## A.4 — Role workflow and handoffs

Source: `mof_coder_kickoff/_docs/process.md`

````markdown
# Work process

One active task. The main Codex session is the orchestrator; it assigns bounded roles, checks handoffs, and reports decisions requiring Mohammed. It does not claim to have performed independent QA or scientific review itself.

## Roles and sequence

1. **Owner — Mohammed:** states the problem and lab constraints; approves scientific meaning, scope, stack, and final interpretation. Only the owner accepts a scientific decision.
2. **PM:** grooms one task into a testable goal, acceptance criteria, exclusions, and constraints; records open owner decisions. No code or scientific verdicts.
3. **Scientific reviewer:** checks terminology, material identity, source evidence, and the distinction between a reported fact and hypothesis. Can block a scientific claim. No code or unsourced assertion.
4. **Engineer (data and software):** implements the groomed task within its boundaries; records inputs/outputs, provenance, failure handling, and tests where there is executable behavior. Flags contradictions without rewriting acceptance criteria.
5. **QA:** independently checks each criterion against the delivered artifact/behavior and reports PASS/FAIL with evidence. Does not modify the work.
6. **Scientific reviewer, after QA, for science-bearing tasks:** checks the delivered scientific content. A QA PASS alone does not close a scientific task.
7. **Orchestrator:** returns FAIL to the relevant role; reports remaining decisions to the owner. Closes a task only after all applicable checks pass and owner-held decisions have been made.

For task 001, PM and science review may refine the contract; the engineer writes the document; QA checks exact examples; the scientific reviewer then checks interpretation. No agent may treat its own self-check as independent QA.

## Stop conditions

- Missing owner decision that changes product scope or scientific meaning: record the question and stop dependent work.
- Missing/blocked primary evidence: preserve as unverified, do not infer the missing fact.
- Repeated FAIL: return with specific observations and retest; avoid an unbounded loop.
- A task is Done only if all criteria PASS, sources are traceable, unresolved caveats are visible, and Mohammed can explain key scientific choices.

Keep `_docs/tasks.md` the only active local backlog. If the owner later chooses GitHub issues, migrate once and make the tracker the single source of active tasks.
````


## A.5 — Tested-sample identity contract

Source: `mof_coder_kickoff/_docs/sample-identity-contract.md`

````markdown
# Tested-sample identity and provenance contract — Task 001

**Status:** documentation draft for independent QA and scientific review. All examples below are **synthetic**; their source labels, sample names, and observations are invented test fixtures, not publications or catalyst claims. This contract describes comparison behavior, not a database schema or an approved matching algorithm.

## 1. Objects and minimum inputs

Keep four object levels separate. An identifier is a record reference within this tool; it is not a claim that another record describes the same physical batch. Every missing field is stored/displayed as `unknown` with a reason where known, never silently inferred from a similar name.

| Level | Minimum inputs, including allowed `unknown` values | Identity boundary |
|---|---|---|
| **Framework / structural model** | Internal record ID; reported name and aliases; reported metal node and linker identity; available structure reference and CIF accession/file plus source/version, or `unknown`; report of framework connectivity/topology if available; source pointer and location supporting each asserted structural attribute. | A model or parent material description, possibly shared by several samples. A matching name, formula, MOFid, or CIF can suggest a framework relation, but does not identify the prepared/tested sample. A CIF is a model of atomic structure, not nanoparticle morphology or proof of the operating phase. |
| **Reported/prepared sample** | Internal record ID; originating source pointer and its explicit sample designation if present; linked parent framework ID or `unknown`; reported constituents (including nanoparticles, supports, coatings and amounts where available); preparation, modification, activation and pretreatment history with distinguishing conditions or `unknown`; whether this is reported experimentally, computational only, or hypothetical; source locations for each assertion. | The paper's specifically designated material at the point of testing. An altered composition, processing/activation history, or derivation is a distinct sample record. Even matching recipes from separate laboratories do not prove the same physical batch. |
| **Operating state** | Internal record ID; linked reported sample ID; time/stage (`before`, `during`, `after`, or `unknown`); reaction and environment as reported or `unknown`; phase/composition assignment and supporting characterization, cited author interpretation, tool inference, or `unknown`; evidence location and review state. | A state of a sample under particular conditions, not a synonym or automatic replacement for the prepared sample. Multiple or uncertain phases can coexist as competing assertions. |
| **Observation** | Internal record ID; reported tested sample ID; source pointer and location; observation type and reported value/unit or `unknown`; measurement context (reaction, electrolyte/pH, potential or current basis, reference electrode/conversion, loading, duration and relevant protocol as available, each independently `unknown`); stated operating-state ID if established, otherwise `unknown`; whether reported experimental, computational, or a hypothesis. | A measured or computed result belongs to the specified reported tested sample under the stated conditions. It does not transfer to its parent framework or a conjectured active phase. Distinct tests of one reported sample remain distinct observations. |

The list is a **minimum recording contract**, not a requirement that every publication supply every value. Unknown values lower comparability and review status; they are not filled with guesses. Capture the exact text, figure/table/panel, supplementary section, or data row when available. A DOI identifies a source, which may describe several samples and tests; it is never itself a sample key.

## 2. Evidence attached to every asserted relation

Store a relation assertion as: `(subject record, relation, object record, reason, source pointer, evidence location or explicitly unknown, assertion author/method, epistemic type, review state)`. Source pointer may be a DOI, accession, stable URL or a manual-entry source record; a manual entry records who supplied it and what underlying source it cites. Include source version/access date where applicable. `Epistemic type` is one of **directly reported**, **author interpretation**, **tool inference**, **user judgment**, or **unknown**. An algorithm's suggested link is tool inference until checked against evidence. A reason should name the discriminating features, not merely repeat a score.

Review state is `needs verification` (metadata only, location missing, or uninspected source), `in review` (evidence inspected but relation not accepted), `reviewed` (human checked a cited, specific relation), or `conflicted` (incompatible assertions retained). The state applies to the **assertion**, not universally to the material. Report who reviewed and when for `reviewed`, if that state is used. A missing exact location does not erase the source pointer but cannot support an automatic merge: request a location or manual inspection and keep `needs verification`. Record each conflicting claim with its own provenance; set the comparison to `unresolved` where the conflict affects identity, and present both for review. Never overwrite one source with another.

## 3. Comparison result and merge policy

A comparison returns **level compared**, **relation**, **reason**, **evidence references**, **unknown/conflicting fields**, **review state**, and **merge permission**. It can return multiple scoped relations, such as `same parent framework` *and* `different prepared samples`. These are not inconsistent. The relation vocabulary is:

| Relation | Meaning | Merge policy |
|---|---|---|
| `same reported sample` | Two references **within one source** explicitly designate its same sample (for example, a methods label and a figure label linked in that source). This is sameness of the **reported sample designation**, not proof of a physical batch identity or sameness across laboratories. | The references may resolve to one within-source sample record once the explicit designation is reviewed. Preserve separate observations and test conditions. Across sources, retain separate records and require human review pending an owner-approved equivalence criterion. |
| `same parent framework` | Cited evidence connects both samples to the same specified parent/framework record. | A parent link may be shared; **never** merge the sample records from this relation alone. |
| `derived/composite relation` | A cited preparation/transformation links a derived product, or a cited addition links a composite, to a parent. Name which of **derived** or **composite** is supported; neither is synonymous with identical tested sample. | Preserve parent and product/composite as separate sample records with a directional lineage link. |
| `different` | Cited discriminating linker, constituent, modification, activation, or other identity-relevant difference establishes distinct records **at the stated level**. | Do not merge at that level. They may still share a parent framework if separately supported. |
| `unresolved` | Evidence is absent, incomplete, only suggestive, or contradictory for the requested relation. | Do not merge. List the missing or conflicting evidence and request review. |

At sample level, shared generic names, common formula, DOI, MOFid, structural resemblance, or **even the same CIF alone** never justify `same reported sample`. The same CIF can describe a parent model used for differently activated, loaded, or prepared samples. Similar names without a CIF are not automatically `different` either. Structural data that are absent or contradictory remain `unknown` or `conflicted`; avoid forcing framework equivalence or difference from a nickname. A discriminating explicit linker can establish difference without a CIF; a cited common parent designation can establish a parent link even when a CIF is missing, subject to review of that evidence. Cross-source sample equivalence is always review required; the minimum evidence for approving it remains an owner decision. No automated merge across sources follows from this contract.

## 4. Synthetic decision cases

All names `Framework-F`, `Linker-L`, `Linker-M`, `Nano-N`, `Sample-A`, `Sample-B` and source IDs below are **invented synthetic inputs**. `Doc-S1` and the like are fictional evidence documents. The cited locations are fixture locations for testing the provenance rule, not real citations. Each record would retain the full source, extraction and review fields defined above.

### Case 1 — Same generic name, different linker

**Inputs:** Fictional `Doc-S1`, Methods §2, explicitly describes `Sample-A` as a `Co-framework` with `Linker-L`. Fictional `Doc-S2`, Methods §1, explicitly describes `Sample-B` with the same generic name and `Linker-M`. No real CIFs or results are asserted. **Expected:** `different` at framework and sample levels because the cited linker identities differ; identical generic text is insufficient. Each synthetic source assertion has its own pointer, location, and method (`fixture transcription`), initially `needs verification` until human review.

### Case 2 — Same parent plus added nanoparticles

**Inputs:** Fictional `Doc-S3`, Methods §1, labels a prepared `Sample-A` with parent `Framework-F`; Methods §2 labels `Sample-B` as `Sample-A` with `Nano-N` added; the parent link is explicit. Its Results fig. 1 also calls `Sample-B` by that designation. **Expected:** `same parent framework`; `derived/composite relation`, subtype **composite** from `Sample-A` to `Sample-B`; `different` prepared samples. The Results reference and Methods reference may be `same reported sample` for **Sample-B within Doc-S3**, subject to checking the explicit designation. The inputs do not document a transformed framework, so the contract makes no **derived** claim.

### Case 3 — Same structural reference, different activation

**Inputs:** Fictional `Doc-S4`, Methods §2, ties both `Sample-A` and `Sample-B` to `Framework-F` and the same **fictional** structural-model reference `Model-F`; §3 reports `Sample-A` activated under protocol P and `Sample-B` under protocol Q. **Expected:** `same parent framework` based on the explicit framework designation and model reference; `different` prepared samples based on distinct cited activation histories. Even a byte-identical CIF at this point would not permit a sample merge. No result is assigned merely by sharing `Model-F`.

### Case 4 — Reconstructed operating phase

**Inputs:** Fictional `Doc-S5`, Methods §1, designates prepared and tested `Sample-A`; Results fig. 2 records observation `Obs-1` under specified but synthetic test-condition record `Cond-1`. Results fig. 3 describes a changed signal during operation and the paper **interprets** it as reconstructed `Phase-R`. **Expected:** `Sample-A` remains the reported tested sample; operating-state record `State-R` is linked to it, with the phase assignment labeled **author interpretation** and its figure location retained. The relation between pre-test material and proposed operating phase is a **related/reconstructed state**, not `same reported sample` or a sample rename. `Obs-1` stays attached to `Sample-A` and `Cond-1`; any link to `State-R` has its own evidentiary status and does not transfer the measurement to a hypothesized phase. If fig. 3 or the phase assignment were absent, report operating-phase identity `unresolved` instead.

### Case 5 — Similar names, missing CIF

**Inputs:** Fictional `Doc-S6`, metadata only, mentions `Sample-A` called `ZIF-like F`; fictional `Doc-S7`, metadata only, mentions `Sample-B` called `ZIF F`. CIF, full text, linker, preparation history, and exact evidence locations are `unknown`; neither source explicitly designates a shared parent. **Expected:** `unresolved` for framework and sample comparison; **no merge**. Show both pointers and the missing information, mark assertions `needs verification`, and offer lawful routes to inspect the underlying sources. An exact source location or other cited structural/preparation evidence could later resolve a **specific** relation; name similarity cannot.

### Compact decision table

| Synthetic case | Returned relation(s), scoped to level | May records merge? | Deciding evidence or uncertainty |
|---|---|---|---|
| 1. Shared name, distinct linkers | `different` frameworks and samples | No | `Doc-S1` Methods §2 versus `Doc-S2` Methods §1: L versus M. |
| 2. Nanoparticle addition | `same parent framework`; `derived/composite relation` (**composite**); `different` prepared samples; within-source references to B may be `same reported sample` | Only duplicate within-source references to explicitly designated B after review; never A with B | `Doc-S3` Methods §§1–2 and Results fig. 1; no evidence of framework derivation. |
| 3. Distinct activation | `same parent framework`; `different` prepared samples | Parent reference may be shared; samples cannot merge | `Doc-S4` Methods §§2–3: same model, protocols P versus Q. |
| 4. Reconstructed state | Reported sample linked to **related operating state**; operating-phase assignment is author interpretation; if unsupported, `unresolved` phase | No sample/state merge; keep `Obs-1` on A | `Doc-S5` Methods §1, Results figs. 2–3; state identity depends on observed signal and attributed interpretation. |
| 5. Similar names, absent CIF | `unresolved` framework and sample | No | Metadata-only `Doc-S6`/`Doc-S7`; missing structure, preparation and exact source locations. |

## 5. Proposed modifications

An improvement proposal starts from a **documented parent** record and creates a distinct **hypothetical** child record with a directional `proposed modification of` link. Store the proposed change, its rationale, the supporting paper/record and evidence location when available, who proposed/extracted it, and its `hypothesis`/review status. The proposal has `unknown` preparation success, real crystal coordinates, operating phase and measured activity unless separate evidence later documents them. A schematic, if ever displayed, must say `schematic`; this contract generates no geometry. Later theoretical results or experiments become separate sourced observations linked to the appropriate version of the sample; they do not retroactively turn the original proposal into a reported experiment.

## 6. Learning-to-project mapping

| Originating course/source | Concept | Component served | Timing | Problem solved | Verifiable artifact | Mohammed understands | Codex may do |
|---|---|---|---|---|---|---|---|
| AI Dev Tools Zoomcamp article; project rules in `plan.md` and task 001 | Spec-driven work, evidence provenance and entity identity | Candidate/sample linkage and later review support | now | Prevent false joins of sample identity and electrochemical results | This contract, five synthetic examples, decision table and independent review | Why parent framework, prepared sample, operating state and observation have different identities; how to interpret missing evidence | Draft and revise the contract; later implement only an approved behavior and its checks |
````


## A.6 — Provider and local-stack options

Source: `mof_coder_kickoff/_docs/source-and-stack-options.md`

````markdown
# First source and local stack: decision options (Task 002)

**Documentation checked:** 2026-09-24. **Status:** research for Mohammed's choice, not a selected source or stack. HER below is a workflow fixture; medium, electrode, reaction conditions and comparison metric are not yet set. No real catalyst, paper, CIF or experimental observation was verified in this task. The linked pages are the providers' own documentation, not evidence that a particular article contains a particular sample.

## 1. Distinct source roles and access boundaries

`Metadata` means a bibliographic/index record; an indexed abstract, if present, is still not an inspected method or measurement. `Full text` means the article contents were actually lawfully retrieved and inspected, recording version, location and license. A URL advertised by an index is a **lead**, not proof that full text can be downloaded, analyzed or redistributed. A manually entered claim must identify who entered it, its underlying source and exact location or explicitly say `unknown`. Every candidate starts `needs verification` until its sample and claims receive evidence review under [the sample identity contract](sample-identity-contract.md).

The following table records *documented capabilities*, not successful retrievals. A dash in the methods/measurements column means the **route itself does not return structured, verified tested-sample facts**, even if some optional text field might mention them. An unknown is a deliberate gap, not permission to infer availability.

| Source role / option and primary documentation | Access, identifier and relevant fields | Does this route return sample preparation / HER conditions / structural data? | Authentication, limits, reuse and full-text boundary | Update/version and remaining unknowns |
|---|---|---|---|---|
| **Discovery A: Crossref REST**: [REST overview](https://www.crossref.org/documentation/retrieve-metadata/rest-api/), [API reference](https://api.crossref.org/), [access and limits](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/), [full-text caveat](https://www.crossref.org/documentation/retrieve-metadata/text-and-data-mining/). | `/works` search; `/works/{doi}` DOI lookup. Deposited work metadata may include title, authors, date, DOI, abstracts, license metadata, links and update information; field presence is record-dependent. | **No / No / No** as structured verified sample facts. An abstract may contain a narrative claim; Crossref collects metadata and may point to full text, but does not provide the full text itself. | Public without signup; polite requests identify an email; premium Plus needs key. Limits vary by pool and interval shown in response headers (documentation lists public 5 concurrent 1; polite 10 concurrent 3; Plus 150 with no concurrency cap); handle 429/403 and back off. Crossref says almost all metadata may be used for any purpose, while some abstracts may be copyrighted. An article's license/link must be checked separately before text retrieval/reuse. | Record each retrieved `indexed`/`updated` metadata value where present and retrieval timestamp. API documentation inspected 2026-09-24; provider last-update line for limits page 2025-10-16. A particular work's deposited abstract/license/link completeness, actual quota interval and lawful text access remain **unknown until queried/checked**. |
| **Discovery B: Europe PMC article REST**: [REST reference](https://dev.europepmc.org/RestfulWebService), [developer scope](https://dev.europepmc.org/developers). | `search?query=...&format=json`; source/article IDs (including PMID/PMCID or DOI when present), title, authors and date; `lite` returns key metadata, `core` may include abstract and full-text links. Scope is life-sciences literature, so coverage of MOF electrochemistry is **unverified and may be narrow**. | **No / No / No** from the search record as verified sample facts. An accessible abstract is not the methods; a separately permitted OA full-text record can be inspected if one exists. | Public web service documented; authentication requirement and a numeric request limit **not verified** in the cited page. Copyright page restricts automated download to designated services and licensed subsets. Per-article license must be checked. | REST production and test endpoints and release notes are documented; record actual service release and retrieval timestamp when used. Whether a target HER paper is indexed or in OA subset is **unknown**. |
| **Structure A: Crystallography Open Database (COD)**: [REST API](https://wiki.crystallography.net/RESTful_API/), [obtain/revisions](https://wiki.crystallography.net/howtoobtaincod/), [entry rights example](https://www.crystallography.net/cod/9001172.html). | `/cod/result` supports `text`, `doi`, formula, elements and JSON/CSV/IDs/URLs; `/cod/{id}.cif` retrieves the structure file. An ID and optional `@revision` identify a COD crystallographic record/version. The text search covers bibliographic and compound-name metadata. | **No / No / Yes, if a matching CIF exists.** A CIF describes a structural model. It does not prove a particular catalyst sample, loaded nanoparticles, activation, morphology, operating phase or HER result. | Anonymous retrieval and bulk copy are documented. A numeric API rate limit or key policy was **not verified**; provider asks users not to overload servers and to pause between successive file fetches. COD entry pages state data/database are CC0 and ask acknowledgment of original structure authors; check the cited original source. This says nothing about copyright of linked papers. | Entry URL defaults to newest revision; `@revision` retrieves a specified version. Record COD ID, revision, original source and retrieval date. Whether a candidate has a relevant COD record, original structure experimental versus theoretical, completeness/quality and its precise relation to the tested sample require case-specific review. |
| **Structure B: CCDC Access Structures (manual route)**: [download help](https://support.ccdc.cam.ac.uk/support/solutions/articles/103000306361/), [search help](https://support.ccdc.cam.ac.uk/support/solutions/articles/103000306200/create_ticket), [advanced-search boundary](https://support.ccdc.cam.ac.uk/support/solutions/articles/103000306225-how-do-i-access-the-advanced-features-of-webcsd-online-structure-search-), [deposit scope](https://support.ccdc.cam.ac.uk/support/solutions/articles/103000306356). | Browser search by deposition number, article DOI, structure DOI, CSD refcode or compound name; where available, a result page offers deposited CIF download. Deposition/refcode identifies a structural record, not the tested electrocatalyst sample. | **No / No / Yes, via an available deposited CIF.** Some deposited calculated structures may not be curated into CSD/ICSD; record status rather than assume experimental. | Free Access Structures **browser** download requires acceptance of conditions; some advanced search needs a CSD license. A general automated retrieval API, its authentication/rate limits and CIF redistribution permission were **not verified** for this free route. Therefore it is **a manual source lead, not an approved ingestion API**. Do not confuse the separately licensed CSD Python API with free Access Structures. | Save deposition identifier, cited article, file metadata and retrieval date when manually acquired under permitted terms. Coverage, exact usage terms for a chosen CIF and its relation to a prepared sample remain **unknown** until checked. |
| **Methods/text A: Europe PMC OA subset**: [developer protocols](https://dev.europepmc.org/developers), [copyright/reuse](https://dev.europepmc.org/Copyright), [REST reference](https://dev.europepmc.org/RestfulWebService). | For an eligible article with a PMCID and available OA text, official REST/OAI/FTP routes provide full-text XML; search/core metadata and abstract are separate from that text. | **Possible narrative text / Possible narrative text / only if that article contains accessible structure data.** The service does not guarantee normalized sample/condition fields. A researcher must inspect exact Methods/figure/table/supplement locations and link observations to the reported tested sample. | Programmatic retrieval only through designated APIs/download services for eligible subsets; website crawling/bulk scraping prohibited. Articles retain copyright and licenses differ by item: verify the article's license before storage/reuse/redistribution. Authentication and numeric per-request limit **not verified** on cited pages. | Record PMCID, article version/license, XML retrieval time and passage location. A particular MOF HER article's inclusion in this life-sciences collection and availability of supplements are **unknown**. No universal full-text route. |
| **Methods/text B: Unpaywall DOI lookup as a lawful-location lead**: [API and current endpoint notice](https://data.unpaywall.org/products/api), [response format](https://unpaywall.org/data-format), [terms](https://unpaywall.org/legal/terms-of-service). | `GET /v2/:doi` returns DOI-level bibliographic/OA-status data and OA locations (URL, version and license where known); the `/v2/search` endpoint was retired **2026-09-18** and must not be proposed for discovery. | **No / No / No** in the API response as inspected sample data. The destination might offer an authorized full text, but only after checking that host, version and permissions and actually inspecting the text. | API v2 requires an email parameter; the provider asks users to limit use to 100,000 calls/day. The free-feature terms grant a limited, revocable use license to the service; article reuse depends on each destination's own license. No promise to redistribute destination PDFs or text. | Record DOI, returned location/version/license fields and retrieval time; OA-location fields may change. The legality of automated retrieval from a specific destination and article-specific reuse remain **unknown until verified**. |

**Availability failure policy (proposed behavior, not a selected source contract):** distinguish no hit, missing optional field, restricted full text, failed/limited API request, contradictory metadata and outdated record. Preserve the query/identifier, provider, timestamp, response status and any safe response metadata. Never turn “no hit” into “material unstudied.” Preserve `needs verification` when no sample-specific content is inspected. Avoid storing publisher text or a CIF where redistribution/retention rights are unclear; store its citation and lawful access link pending review.

## 2. Representative HER evidence route (workflow fixture)

**Unfixed question:** “Which MOF-related prepared samples warrant closer inspection for HER under conditions Mohammed will specify?” This is *not* a performance comparison and produces no ranked catalyst claim.

1. **Discover:** use Crossref `/works` with HER and MOF terms, or Europe PMC search for its limited collection; capture returned query, provider, work DOI/ID, title, metadata date, abstract **if available**, license/link metadata and retrieval timestamp. At this point the output is **indexed metadata** (or an accessible abstract), never a verified sample.
2. **Open the source record:** resolve the DOI through the publisher or an authorized repository; optionally query Unpaywall v2 by DOI for OA-location leads. If a Europe PMC article is in the licensed OA subset, its XML is a possible lawful full-text route; otherwise show publisher/repository link and stop automation at access terms. Record which version/contents were **actually read**. A paywall or unknown license does not authorize scraping.
3. **Inspect sample evidence:** a human checks methods, sample designations, ligands/metal, added particles, activation, electrode preparation, electrolyte/pH, current/potential basis, reference conversion, loading and test duration **as reported**; absent values remain `unknown`. Capture exact page/section/table/figure and extraction author. If the full text is inaccessible, ask for a lawful user-supplied reference/excerpt or manual evidence entry and keep `needs verification`; never infer a sample from title/abstract.
4. **Look for structure separately:** query COD by the paper DOI or documented structure identifiers; otherwise offer the CCDC browser route. Record structure ID, version, source and experimental/computational status **if established**. A CIF only links a framework/model when the paper supports that link; it is not a tested-sample identity key and does not imply HER activity.
5. **Review:** apply the identity contract to framework, prepared sample, operating state and observation independently. Experimental observations, computational descriptors, authors' interpretations and later improvement hypotheses remain different records. A researcher must accept or correct sample-specific claims before comparison; no provider search rank proves performance, novelty or current laboratory feasibility.

## 3. Two local implementation options (not selected)

Both options could use Python to query an **owner-selected** provider only after its legal source contract is accepted. `sqlite3` in Python supplies a local disk-based database without a separate database server ([Python docs](https://docs.python.org/3/library/sqlite3.html)); SQLite's own guide describes a cross-platform single-file format and warns against many direct network clients or concurrent writers ([SQLite guidance](https://www.sqlite.org/whentouse.html)). These are technology characteristics, **not** a database schema proposal.

| Concern | **Option L1 — Python CLI + SQLite** | **Option L2 — Python + Streamlit local browser UI + SQLite** |
|---|---|---|
| User surface and workflow | Terminal commands to import bibliographic metadata, list unresolved items, enter/revise evidence with prompts or structured local files, and export a review table. The command interface is a proposed design, not existing code. | Local browser forms, source links and an editable review queue; [Streamlit widgets/data editor](https://docs.streamlit.io/develop/api-reference) provide a starting surface. Changes must be explicitly saved to SQLite; [Session State](https://docs.streamlit.io/develop/concepts/architecture/session-state) is session-scoped and is **not** durable evidence storage. |
| Setup/maintenance | Python standard library can cover CLI and SQLite, with minimal third-party UI dependencies. Manual entry of many nuanced claims in a terminal may be cumbersome; commands and validation still need design/testing. | Extra Streamlit dependency and browser app behavior; faster inspect/correct interaction, but reruns/session handling and editing persistence require additional engineering and tests ([execution model](https://docs.streamlit.io/get-started/fundamentals/main-concepts)). |
| Provenance and corrections | Both require an explicit persisted source/version/location, who/when/how extracted, review state and correction history; a CLI can support this, but must be designed for it. | Same underlying requirements; editable widgets alone do **not** provide audit trails. Present original versus corrected values and save corrections as separate, reviewable events when implemented. |
| Portability and migration | Local SQLite file plus documented export format can move machines; separate any original CIF/text files and rights metadata. Future relational migration requires mapping/testing, not a promised automatic conversion. | Same SQLite/export route if business logic is independent of UI. Streamlit screen state is not portable evidence; keep persisted records apart from the UI so a later API/web client can reuse them. |
| Identity-contract fit and postponed work | Distinct framework/sample/state/observation records and unresolved relationships can be represented; CLI is less natural for side-by-side scientific evidence and complex manual review. Postpone 3D view, prediction, multiuser sync and broad source coverage. | The same distinct records with a potentially clearer human review surface. Postpone 3D view, prediction, multiuser deployment, complex concurrent editing and broad source coverage. |

Neither option includes Postgres, cloud infrastructure, machine learning, background scraping or a visualization renderer by default. Their addition needs a demonstrated product problem and owner decision. No stack, library, schema or repository has been initialized by this task.

## 4. Decisions reserved for Mohammed

| Decision Mohammed must make | Concrete choices presented, not selected | Evidence to settle it; current unknown |
|---|---|---|
| **First discovery source and legal evidence route** | Crossref metadata; Europe PMC within its coverage; optional Unpaywall DOI lookup for lawful-location leads; COD for potentially relevant structure, CCDC browser when needed. These roles are complementary rather than interchangeable. | Choose the *first* source contract and permitted content, query fields, handling of errors/rights and whether manual entry is the initial inspection path. Coverage and availability for the first precise question remain untested. |
| **Initial local stack and interaction surface** | L1 Python CLI + SQLite, or L2 Python + Streamlit + SQLite. | Choose based on actual manual review burden and willingness to maintain a browser UI. Deployment target, repository, OS portability needs, simultaneous users and backup/export expectations remain unknown. |
| **First scientific acceptance question** | HER as an example, with MOFs/ZIFs/composites/derived materials within overall scope. | Specify target reaction medium, measurement conditions and a claim/metric the first slice must verify; no numerical threshold or ranking is assumed. Lab current/future capabilities and what counts as `reviewed` remain open. |

The task 001 cross-source sample-equivalence threshold is also still owner-held. Until set, separate records and request human review; a DOI, CIF, name, formula or MOFid cannot silently merge tested samples.

## 5. Learning-to-project mapping

| Originating course/source | Concept | Component served | Timing | Problem solved | Verifiable artifact | Mohammed must understand | Codex may do |
|---|---|---|---|---|---|---|---|
| AI Dev Tools Zoomcamp; Crossref, COD, CCDC, Europe PMC and Unpaywall provider documentation | Requirements and legal source contract | Evidence acquisition, access and provenance | `now` for decision analysis; implementation `later` | Avoid mistaking an index hit or structure for a tested catalyst | Checked source table, linked official docs and HER stop point | What each route returns, what it does not, and why sample-specific evidence requires source inspection | Research options, then implement one approved source contract after the owner chooses |
| Data Engineering Zoomcamp; task 001 identity contract; Python/SQLite/Streamlit documentation | Persistence and human correction tradeoffs | Local evidence and sample records | `now` for comparison; implementation `later` | Preserve uncertain identities and corrections in a maintainable workflow | Two local stack options and decision table | Distinct framework/sample/state/observation records, provenance and migration costs | Describe options; later build only the selected workflow and verifiable checks |
````


## A.7 — Active tasks

Source: `mof_coder_kickoff/_docs/tasks.md`

````markdown
# Active local backlog

## 001. Define the tested-sample identity contract — Done (documentation)

### Goal

Specify how the tool distinguishes a framework, a modified/prepared sample, an operating state, and an electrochemical observation so two different samples are never automatically merged on name alone.

### Acceptance criteria

- [x] `_docs/sample-identity-contract.md` lists the minimum input fields separately for a framework, reported/prepared sample, operating state, and observation; defines the output of an identity comparison, uncertainty, review state, and the consequence of absent or conflicting structural data. Missing values remain explicitly unknown.
- [x] It distinguishes `same reported sample`, `same parent framework`, `derived/composite relation`, `different`, and `unresolved`, with a reason and evidence for each decision. It does not claim that two laboratories' batches are physically identical.
- [x] Five clearly labeled synthetic examples cover: same generic name but different linker (`different` samples); same framework plus nanoparticles (`derived/composite relation`); same structure with different activation (distinct prepared samples sharing a parent); reconstructed operating phase (related operating state, not a renamed tested sample); and missing CIF with similar names (`unresolved` unless other cited evidence establishes the precise relation). Each example gives its inputs, expected relation(s), and the evidence or absence of evidence that determines them.
- [x] An observation points to the reported tested sample and stated measurement conditions, and does not silently move to the parent MOF or an inferred active phase.
- [x] Proposed modifications create new hypothetical records linked to a documented parent; no fabricated crystal geometry, measured activity, or synthesis success is attached.
- [x] Each asserted identity or lineage relation records a pointer to the source and exact evidence location when available, the assertion's author/extraction method, and a review status. The contract states how to handle missing locations and conflicting claims; ambiguity or conflict prevents automatic merge. It specifies that a shared generic name, formula, DOI, MOFid, or CIF does not alone establish the same tested sample.
- [x] The contract defines what `same reported sample` means within an explicitly documented source/sample designation and flags cross-source sample equivalence for human review pending an owner-approved criterion. It includes a compact decision table showing the returned state and whether any records may be merged for each of the five synthetic cases.
- [x] PM, QA, and scientific reviewer each leave separate, checkable handoff notes in `_docs/task-001-review.md`.

### Out of scope

Product code, database schema, dependency choice, real API ingestion, novelty claims, 3D renderer, performance predictions, and claims about any specific real catalyst.

### Constraints and dependencies

Read `plan.md`, `AGENTS.md`, and the role/process files. Use synthetic examples labeled as such. No assumption that matching MOFid or CIF proves identical tested batches. Existing old project files are historical context, not the new implementation contract.

### Learning-to-project mapping

| Originating course/source | Concept | Component served | Timing | Problem solved | Verifiable artifact | Mohammed understands | Codex may do |
|---|---|---|---|---|---|---|---|
| AI Dev Tools Zoomcamp article; project scientific-source rules | Spec-driven development, evidence traceability, entity identity | Candidate/sample linkage | now | Prevent false material/result joins | Identity contract and five reviewed examples | Levels of identity and why test results attach to samples | Draft contract, examples, revisions and QA checks |

## 002. Research first-source and stack options — Done (analysis)

### Goal

Give Mohammed a sourced comparison from which he can select an initial legal data source and a proportionate local implementation stack. Use HER only as a representative example; the exact electrochemical question and acceptance conditions remain an owner decision.

### Acceptance criteria

- [x] `_docs/source-and-stack-options.md` compares concrete, named options in each of three source roles: literature discovery/metadata, MOF structure/CIF, and methods or full-text access. Each option links to primary provider/API/access documentation checked on a stated date. A role with no viable verified option is marked as a gap with the attempted documentation, not filled by inference.
- [x] A source table records for every option: provider and access route; identifiers and relevant available fields; whether the route actually returns a sample-specific preparation, electrochemical measurement conditions, or structure; authentication, query/rate limits, licensing/redistribution and full-text restrictions as documented; update/version or retrieval date; and unavailable or unverified details. Distinguish indexed metadata, accessible abstract, legally accessible full text, and user-entered evidence. Do not treat DOI, CIF or a generic material name as a tested-sample identifier.
- [x] Trace one representative HER question through discovery → source record → sample/evidence inspection using the *documented* capabilities of the options. Identify the point where automation must stop and a researcher needs to open a paper or enter data manually. Do not assert that any real sample was verified unless its supporting content was actually accessed and cited.
- [x] Describe at least two proportionate local stack options with the role of Python, persistence/storage, and a user interaction surface in each. Compare setup/maintenance burden, provenance and manual correction support, portability and data migration, and fit with the identity contract; list what each option postpones. No option is chosen by the agent.
- [x] Include a side-by-side decision table identifying what Mohammed must select (first source, initial stack, exact first question and measurement conditions) and which facts remain unknown. Give tradeoffs without invented scores, guarantees or a disguised final selection.
- [x] Add the task-to-project mapping below to the deliverable, including what Mohammed must understand and what Codex may do. PM, engineer/researcher, QA and scientific reviewer leave distinct checkable notes in `_docs/task-002-review.md`; QA verifies links/claims against documentation and reviewer verifies scientific framing before closure.

### Out of scope

Selecting a source or stack, implementing API calls, registering credentials, creating a database schema, initializing a repository, bypassing access controls, collecting full texts without permission, validating real catalysts, and making novelty or performance claims. Task 003 remains blocked pending owner choices.

### Constraints and dependencies

Use `plan.md`, `AGENTS.md`, `_docs/process.md`, and `_docs/sample-identity-contract.md`. Prefer the primary provider's current documentation over secondary summaries; record uncertainty when terms or fields cannot be confirmed. Preserve separate framework, tested sample, operating state, and observation identities. The term HER names the example only; reaction medium, potential/current conventions and comparison metrics are not yet fixed by the owner.

### Learning-to-project mapping

| Originating course/source | Concept | Component served | Timing | Problem solved | Verifiable artifact | Mohammed understands | Codex may do |
|---|---|---|---|---|---|---|---|
| AI Dev Tools Zoomcamp; source-provider API and access documentation | Requirements, source contract, legal API discovery | Evidence acquisition and provenance | now | Avoid an unsupported or inaccessible first source | Sourced source-options table and HER evidence-route example | What each source actually supplies, its missing fields, and access limits | Inspect provider documentation and prepare comparison; no source selection |
| Data Engineering Zoomcamp; project identity contract | Python ingestion and storage tradeoffs | Local evidence records and human correction | now for option analysis; implementation later | Choose a maintainable first local workflow | Two local stack options with migration and provenance tradeoffs | Why sample identity and measurement context need separate records | Describe technical options; implement only after owner selection |

## 003. Bootstrap an empty runnable project — Blocked

Requires the owner-selected stack, initial source contract, and accepted first vertical question. Initialize the project with a passing meaningful smoke test before implementing API access. Do not use QMOF merely because it appears in old files.
````


## A.8 — Task 001 review report

Source: `mof_coder_kickoff/_docs/task-001-review.md`

````markdown
# Task 001 role handoffs

## PM — 2026-09-24

**Grooming status:** Ready for a documentation-only engineering draft. The task remains limited to sample identity and provenance; no product code, external-source ingestion, 3D renderer, performance prediction, or real-catalyst assertion is authorized by this task.

**Refinements made to `_docs/tasks.md`:** Minimum inputs and comparison outputs are now separated by framework, reported/prepared sample, operating state, and observation. The five synthetic examples have expected relations, input/evidence expectations, and an inspectable decision table. Each identity or lineage assertion must retain its source pointer, evidence location when available, extraction method/author, and review status. Missing or conflicting evidence prevents automatic merging. Matching a generic name, formula, DOI, MOFid, or CIF alone cannot establish identical tested samples. Cross-source sample equivalence requires human review pending owner-approved rules.

**Why:** An engineer can now produce a contract that QA can check against exact examples and failure cases. A DOI may contain several different samples; structural similarity may identify a parent framework while leaving batch preparation and the tested sample uncertain.

**One owner question, for a later decision:** What minimum evidence should permit a human reviewer to mark references in two different sources as the *same reported tested sample*, if ever? Until Mohammed defines this criterion, preserve separate sample records with their cited relationship and mark cross-source equivalence unresolved/review required. This question does not block the documentation draft.

**Handoff to engineer:** Write `_docs/sample-identity-contract.md` against the revised criteria. Make the decision table and five examples synthetic; do not invent real papers or geometry. Call out any scientific ambiguity for the separate scientific review. No code.

## Engineer — 2026-09-24

**Artifact:** `_docs/sample-identity-contract.md`. I drafted the documentation-only contract and five explicitly synthetic cases (same generic name/different linker; added nanoparticles; shared parent/different activation; reported reconstruction during operation; missing CIF/similar names) with inputs, expected scoped relations, evidence locations or explicitly missing locations, and a compact decision/merge table.

**Criterion coverage for independent checking:** Section 1 defines distinct framework, prepared sample, operating-state, and observation inputs, including unknown values; sections 2–3 define assertion provenance, epistemic/review state, comparison output, missing/conflicting data, within-source designation, cross-source human review and merge policy; section 4 contains the five cases and decision table; section 5 keeps modification proposals hypothetical without geometry, activity, or successful synthesis claims. Observation context and its tested-sample pointer appear in sections 1 and 4. Section 6 records the task-to-project learning mapping. No executable tests apply to this documentation-only task; this self-check is **not** a QA verdict.

**Open owner decision carried forward:** The threshold, if any, for human approval of cross-source references as the same reported tested sample remains undefined. The contract keeps cross-source records separate and flags review rather than inventing a rule. No other blocker for QA. No real catalyst assertion, code, package, stack or source access was introduced. **Handoff:** QA checks each acceptance criterion independently; scientific reviewer then checks the finished interpretation. Task remains open.

## QA — 2026-09-24

**Verdict: PASS for the task 001 acceptance criteria.** Inspected the delivered `_docs/sample-identity-contract.md` directly against all eight criteria in `_docs/tasks.md`, with `plan.md`, `AGENTS.md`, `_docs/process.md`, and `_docs/team/qa.md` as scope and process constraints. This is a documentation-only task; no executable tests apply. Read commands: `cat` on each inspected file. The attempted `git status --short` reported that this scratch folder is not a Git repository; it did not affect document review.

| Criterion | Result | Independent evidence in delivered artifact |
|---|---|---|
| 1. Four levels, minimum inputs, comparison output, uncertainty and missing/conflicting structure | **PASS** | Section 1 has separate input rows for framework, reported/prepared sample, operating state, and observation, each allowing explicit `unknown`; sections 2–3 define review states, conflicting assertions, comparison output and no forced equivalence when structure is missing. |
| 2. Five scoped relations, reason and evidence; no physical batch identity claim | **PASS** | Section 3 defines `same reported sample`, `same parent framework`, `derived/composite relation`, `different`, and `unresolved`, with discriminating reason, evidence, and merge rules. It explicitly denies physical batch equivalence across laboratories. |
| 3. Five clearly synthetic cases with inputs, expected relations and deciding evidence | **PASS** | Section 4 labels all five as fictional: (1) distinct linkers ⇒ different framework/sample; (2) nanoparticle addition ⇒ shared parent, composite relation, distinct samples; (3) P/Q activation ⇒ shared parent and distinct samples; (4) reconstruction ⇒ separate linked operating state and observation remaining on sample; (5) similar metadata names with missing CIF ⇒ unresolved. The fictional document locations or their absence are specified in each case. |
| 4. Observation binds tested sample and measurement conditions | **PASS** | Section 1 requires tested sample ID and separately recorded reaction, electrolyte/pH, electrical basis/reference, loading, duration and protocol or `unknown`. Case 4 keeps `Obs-1` on `Sample-A` with `Cond-1`, not on the parent or interpreted `Phase-R`. |
| 5. Hypothetical modifications separated from evidence of results | **PASS** | Section 5 creates a distinct hypothetical child of a documented parent and explicitly leaves preparation success, geometry, operating phase and measured activity `unknown`. |
| 6. Provenance, missing locations/conflicts, and unsafe identity keys | **PASS** | Section 2 specifies source pointer, location or `unknown`, assertion author/method, epistemic type and review state; conflicts are preserved and block merging. Section 3 expressly disallows generic name, formula, DOI, MOFid or CIF alone as sample identity proof. |
| 7. Within-source designation, cross-source review, and five-case decision table | **PASS** | Section 3 limits `same reported sample` to explicit within-source designation, keeps distinct observations, and requires human review for cross-source equivalence pending an owner-approved criterion. Section 4's compact table supplies returned states and merge permissions for all five cases. |
| 8. Separate PM, QA and scientific reviewer handoff notes | **PASS for handoff-note presence** | This file contains dated PM and engineer notes, this independent QA note, and a separate scientific reviewer's pre-implementation note with checkable conditions. The scientific reviewer has **not yet reviewed the finished contract after QA**; that required process step remains pending. |

**Process status:** QA PASS does not close task 001. `_docs/process.md` requires a scientific reviewer to inspect the completed science-bearing artifact after QA. The unresolved owner criterion for cross-source equivalence remains explicit; the current contract forbids automated cross-source merges. No changes were made to the contract, task, or code.

## Scientific reviewer

Pending independent interpretation review after QA.

## Scientific reviewer — pre-implementation, 2026-09-24

**Verdict: PASS for drafting the documentation-only identity contract; scientific closure remains pending the finished-artifact review.** I checked the criteria in `_docs/tasks.md` against `plan.md`. They keep framework, prepared/tested sample, operating state, and observation distinct; prohibit automatic merges from shared names, DOI, formula, MOFid, or CIF; and require traceable evidence, uncertainty, and a human decision for cross-source sample equivalence. No real-material scientific claim or unapproved identity threshold is needed to draft the contract.

**Scientific checks the engineer must preserve:**

1. In the nanoparticle example, call an added nanoparticle material a **composite** when that is all the synthetic inputs establish; do not infer a chemically derived framework. A genuinely derived product needs a stated transformation and its evidence. Both are related to a parent, not identical to its tested sample.
2. The different-activation case shares a parent framework only insofar as the synthetic inputs establish its framework identity. Distinct activation histories mean distinct prepared sample records even if the same CIF is cited.
3. A reconstructed operating phase needs explicit supporting observation or a clearly attributed literature assertion. If merely postulated, mark it inferred/hypothetical; never transfer the measured result from the reported tested sample to the phase.
4. `Same reported sample` may link references within one source to an explicitly designated sample, while still allowing different observations and test conditions. It never asserts physical identity of two batches. Across sources, keep separate records and request human review until Mohammed sets a criterion.
5. For each relation, distinguish a directly reported fact, an author's interpretation, a tool inference, and an unknown. Missing exact evidence location lowers review status and prevents an unsupported automatic merge; contradictory source claims remain visible rather than being overwritten.

**Blockers:** None for a synthetic, documentation-only draft. The owner-held cross-source equivalence rule blocks automated cross-source merging, not this contract. Any real-catalyst identity or operating-phase claim later requires a traceable scientific source.

## Scientific reviewer — post-QA, 2026-09-24

**Verdict: PASS for the finished task 001 documentation.** Independently read `_docs/sample-identity-contract.md` after the QA PASS and checked its scientific interpretation against all task 001 criteria and the pre-implementation review above. Task 001 **can be marked complete as a documentation-only identity contract**. This verdict does not approve executable identity matching, source ingestion, or claims about real catalysts.

**Checkable findings:** Section 1 distinguishes structural framework, reported/prepared sample, operating state, and observation; an observation remains on the specifically reported tested sample with separately recorded measurement context. Sections 2–3 retain an evidence pointer, evidence location or explicit absence, epistemic type, reviewer status, and conflict; none of name, formula, DOI, MOFid, or CIF alone proves identical tested samples. Within-source `same reported sample` means a checked sample designation, not identical laboratory batches. Cross-source records remain separate. Section 4's five synthetic cases correctly distinguish different linkers, nanoparticle addition as **composite** (without asserting chemical derivation), different activation histories, author-interpreted operating-phase reconstruction, and unresolved identity from metadata-only similar names. Its decision table keeps samples distinct where necessary. Section 5 leaves modification proposals hypothetical, with no invented coordinates, activity, or synthesis result.

**Scientific caveat retained:** The fictional reconstruction in case 4 represents an **author interpretation** supported by a described signal, not proof that the phase was uniquely identified or caused `Obs-1`. The document explicitly keeps the observation on `Sample-A` and would mark phase identity unresolved without the supporting assertion. For future real records, the evidence type and strength must be checked case by case.

**Owner-held decision remains open:** Mohammed has not defined evidence sufficient to approve equivalence of reported tested samples across different sources. The contract prohibits automated cross-source merging and requests human review. This open rule does **not** prevent closing this bounded documentation task; it blocks future behavior that would require such a criterion.
````


## A.9 — Task 002 review report

Source: `mof_coder_kickoff/_docs/task-002-review.md`

````markdown
# Task 002 role handoffs

## PM — 2026-09-24

**Grooming status:** Ready for sourced option research only. I expanded `_docs/tasks.md` with an observable deliverable, primary-documentation and access checks for each source role, a HER evidence-route example, two local stack options, explicit owner decisions, exclusions, and a learning-to-project mapping. Task 001 remains complete and untouched.

**Reason for the refinements:** A generic list of APIs cannot establish whether a provider supplies sample-specific experimental methods or merely paper metadata. The option table must expose that gap and the lawful manual route before any source or stack is selected. A documented API is not automatically a legal full-text route. Python and storage choices need to support the identity contract and corrections, not be justified by course coverage alone.

**Owner-held decisions:** Mohammed selects the initial source, initial stack, and precise first HER question including target conditions after inspecting the comparison. These decisions are not prerequisites for researching options, but task 003 cannot start without them. No recommendation is a selection.

**Handoff to source/technical researcher:** Write `_docs/source-and-stack-options.md` using the primary documentation cited near each concrete claim. Mark unknown terms/fields explicitly; show where an automated evidence route stops and a manual action begins. Present two proportionate local technology options and their tradeoffs. Do not obtain restricted full text, build code, or claim a source verified a real catalyst without actually inspecting its evidence.

## Engineer or researcher — 2026-09-24

**Deliverable:** `_docs/source-and-stack-options.md`. I checked primary provider documentation on 2026-09-24 and recorded two discovery options (Crossref, Europe PMC), two structure routes (COD API, CCDC Access Structures browser), and two text/rights routes (Europe PMC OA subset, Unpaywall DOI-level location lead). The table distinguishes fields, identifiers, metadata/abstract/text, sample/measurement/structure availability, authentication, rate and copyright/redistribution boundaries, freshness and explicit unknowns. Europe PMC is scoped to its documented literature corpus; CCDC is a manual lead, not an approved automated ingestion route. Unpaywall article search was retired 2026-09-18; only its documented DOI lookup is presented.

**Acceptance coverage:** Section 2 traces a representative HER question through discovery, lawful access boundary and human inspection, without identifying or validating a real catalyst. Section 3 gives two proportionate Python/SQLite local choices (CLI or Streamlit browser) with provenance, corrections, maintenance, migration and postponed work; section 4 preserves owner choices and unknowns; section 5 supplies the full learning-to-project mapping. No code, API ingestion, license-dependent download, dependency installation, stack selection or database schema was made. This is an engineering self-check, **not** independent QA or scientific approval.

**Open decisions / handoff:** Mohammed still chooses the precise HER acceptance question and conditions, first source contract, and initial stack. Provider-specific live record fields, exact corpus coverage, CCDC automated/redistribution rights, Europe PMC numeric quota, and legal article-by-article full-text reuse remain unverified; the document marks the resulting stop points. QA should verify each link and associated claim against the cited provider docs, then scientific review should check identity/evidence framing. Task 003 remains blocked pending owner decisions.

### Engineer remediation after QA FAIL — 2026-09-24

Corrected only the Unpaywall limit wording in `_docs/source-and-stack-options.md`, section 1: it now says the provider asks users to limit use to **100,000 calls/day**, with no unsupported “per provider” qualification. The cited [official REST API page](https://data.unpaywall.org/products/api) gives that limit but does not define a per-provider allowance. No source or stack decision, task criterion, other claim, or QA verdict was changed. Return the corrected claim for independent QA recheck; post-QA scientific review and owner decisions remain pending.

## QA

### Independent review — 2026-09-24

**Overall: FAIL (one unsupported rate-limit qualification).** Inspected the actual `_docs/source-and-stack-options.md`, all six acceptance criteria in `_docs/tasks.md`, and `plan.md`, `AGENTS.md`, `_docs/process.md`, `_docs/team/qa.md`, and `_docs/sample-identity-contract.md`. This research-only task has no executable tests. Commands: `cat`, `sed`, `nl` for the local files; opened/searched primary provider documentation using web search on 2026-09-24. No source option, task, code, or stack was modified.

| Acceptance criterion | Result | Evidence / defect |
|---|---|---|
| 1. Named source options in three roles, primary documentation and check date | **PASS** | Section 1 names Crossref and Europe PMC for discovery, COD and CCDC for structure, and Europe PMC OA plus Unpaywall as a lawful full-text *location lead* for methods. It dates the documentation check and links official documentation; the sole Unpaywall lead explicitly disclaims full-text retrieval. |
| 2. Per-option fields, access/limits/rights, unknowns and identity boundaries | **FAIL** | Table rows and section 1 otherwise provide the requested fields and preserve source/structure/tested-sample boundaries. **Precise defect:** `_docs/source-and-stack-options.md:18` says the Unpaywall API requests “no more than 100,000 calls/day **per provider**.” Its linked official [REST API page](https://data.unpaywall.org/products/api) says only “Please limit use to 100,000 calls per day”; it does not define a per-provider allowance. Remove the added qualification or substantiate it from official docs. The page also confirms email parameter, v2 DOI lookup and retirement of `/v2/search` on 18 September 2026. |
| 3. Representative HER route and human stopping point | **PASS** | Section 2 traces search → DOI/OA-location lead → actual Methods/measurement inspection or manual entry → separately linked CIF. It explicitly stops at access restrictions and says no real sample or result was inspected/verified. |
| 4. Two proportionate local stacks and tradeoffs | **PASS** | Section 3 compares Python CLI + SQLite with Python + local Streamlit + SQLite, including correction history, persistence, migration, burden, and postponed capabilities. Neither is selected. SQLite and Streamlit limitations align with their own documentation. |
| 5. Owner decision table and unknowns without hidden selection | **PASS** | Section 4 leaves source, stack, exact HER conditions/metric and other unknowns to Mohammed, with no scores or promised performance. |
| 6. Mapping and distinct role handoffs | **PASS for mapping/handoff-note presence** | Section 5 has source, concept, component, timing, problem, artifact, owner knowledge, and delegated Codex work. This file contains PM and researcher notes, this independent QA note, and a distinct pre-work scientific-review note. The required scientific review of the finished document **after QA** remains pending. |

**Provider cross-check sample:** Crossref [REST overview](https://www.crossref.org/documentation/retrieve-metadata/rest-api/), [limits](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/) and [full-text boundary](https://www.crossref.org/documentation/retrieve-metadata/text-and-data-mining/) support metadata fields, public/polite/Plus pools and the fact that a text URL does not guarantee access. COD [search/CIF/revision API](https://wiki.crystallography.net/RESTful_API/), [download guidance](https://wiki.crystallography.net/howtoobtaincod/) and [entry license example](https://www.crystallography.net/cod/9001172.html) support structure retrieval, revision and CC0, but not tested-catalyst facts. CCDC [Access Structures](https://support.ccdc.cam.ac.uk/support/solutions/articles/103000306361/) and [licensed advanced search](https://support.ccdc.cam.ac.uk/support/solutions/articles/103000306225-how-do-i-access-the-advanced-features-of-webcsd-online-structure-search-) support the manual CIF route and license caveat. Europe PMC [REST](https://dev.europepmc.org/RestfulWebService), [developer protocols](https://dev.europepmc.org/developers) and [copyright](https://dev.europepmc.org/Copyright) distinguish search/abstract from permitted OA text and prohibit general website bulk scraping. Unpaywall [API documentation](https://data.unpaywall.org/products/api) and [terms](https://unpaywall.org/legal/terms-of-service) support the DOI-only lead and destination rights caveat, subject to the defect above.

**Handoff:** Return only the rate-limit wording to the researcher for correction, then ask QA to recheck that changed claim. Do not mark task 002 Done before both QA PASS and post-QA scientific review; owner choices still gate task 003.

### QA retest — 2026-09-24

**Verdict: PASS on all six acceptance criteria.** Reopened `_docs/source-and-stack-options.md`, checked line 18 and the continued presence of sections 1–5 with `rg -n`, and compared the corrected Unpaywall sentence with the provider's [official REST API documentation](https://data.unpaywall.org/products/api). It now states that the provider asks users to limit use to **100,000 calls/day**, without assigning an undocumented per-provider allowance. The documented email parameter, v2 DOI route, and retired search route are unchanged. The other five criteria passed in the preceding review and their relevant sections remain present; no new defect found in the corrected statement. The prior FAIL is resolved. No source option, task, or code was changed by QA.

**Process status:** Task 002 still needs post-QA scientific review of the finished document and then Mohammed's decisions before task 003 can start. QA PASS alone does not close a science-bearing task.

## Scientific reviewer

Pending independent scientific framing review after QA.

## Scientific reviewer — pre-work, 2026-09-24

**Verdict: PASS for option research only.** The task criteria require separate literature/metadata, structure/CIF, and full-text/methods roles; provider documentation and legal access checks; and an explicit point where sample-level verification stops. The exact HER question, conditions and source selection properly remain Mohammed's decisions. No scientific claim about a real catalyst is required to produce this options document.

**Scientific constraints for the research handoff:**

1. Literature metadata, an abstract and a paper DOI may locate a source, but do not themselves establish a prepared sample, its composition, its synthesis, or measured HER performance. Mark a metadata-only hit `needs verification` and name the missing evidence.
2. A CIF or structure record describes a reported structural model, and its source/version and experimental versus computational status should be stated if documented. Neither a shared CIF nor a MOF identifier proves identity of the actual tested sample, nanoparticle distribution, reconstructed operating phase, or HER activity. Preserve the identity levels in `_docs/sample-identity-contract.md`.
3. Methods/full-text access and reuse permissions are separate questions from metadata API availability. The representative route should stop at the documented access boundary, direct the researcher to a lawful paper route or manual entry, and state what content was actually inspected. Provider terms that could not be verified remain `unknown`.
4. A representative HER query is a **workflow fixture** until Mohammed specifies reaction conditions and comparison metrics. Do not compare overpotential, current density, Tafel slope, stability or any other performance measure without their reported testing context, and do not infer that a structurally indexed MOF was tested for HER.
5. Keep an experimental observation, a computational descriptor, an author's mechanistic interpretation, and a tool-generated improvement hypothesis distinct. Source availability or search ranking cannot establish activity, novelty, or feasibility in Mohammed's laboratory.

**Blockers:** None for researching documented options. Selecting and implementing the first source/stack and setting the first scientific acceptance question remain owner-held gates for task 003. If primary provider documentation cannot substantiate a particular field, route or permission, report the gap instead of claiming it works.

## Scientific reviewer — post-QA, 2026-09-24

**Verdict: PASS for the finished analysis-only task 002 memo.** Independently inspected `_docs/source-and-stack-options.md` after the QA retest PASS against task 002 and the sample-identity contract. The corrected Unpaywall request-limit wording does not change any scientific inference. This review approves the evidence framing of an options document, not a provider, stack, catalyst, or source license for ingestion.

**Scientific findings:** Section 1 distinguishes indexed metadata, abstract, actually inspected lawful full text, and attributed manual entry. Its table presents Crossref and Europe PMC discovery records as source leads, COD/CCDC structures as structural models, Europe PMC OA as conditional text access, and Unpaywall as a DOI-level location lead. The absence of structured sample methods and HER conditions is marked rather than inferred from an abstract, DOI or CIF. Section 2 labels its HER question a workflow fixture, identifies the automated access stopping point, preserves missing measurement conditions as `unknown`, and requires the researcher to inspect sample and observation evidence before comparison. Section 3's two local stacks preserve the possibility of distinct framework, sample, operating-state and observation records and human correction; neither claims to implement those safeguards already. Sections 4–5 retain all scientific decisions and the learning mapping. No real HER activity, novelty, mechanistic causation, experimental feasibility, or computational prediction is asserted.

**Caveats for later work:** A deposited CIF can represent a model with uncertain relation to the actual electrocatalyst; any future identity link needs paper-specific evidence. An accessible full-text version does not guarantee that its supplementary preparation details or measurement conventions are available. When a real sample is reviewed, experimental measurements, theoretical descriptors and proposed modifications must remain distinct, with conditions and source location attached. Europe PMC coverage and per-item reuse rights remain case-specific; metadata search rankings provide no scientific validation.

**Task status:** The bounded source/stack comparison can be marked complete for documentation purposes after this scientific PASS. Mohammed still decides the first scientific question and conditions, initial source contract, and stack; these owner-held decisions block task 003 implementation, not closure of this research memo.
````


## A.10 — Task template

Source: `mof_coder_kickoff/_docs/task-template.md`

````markdown
# Task template

## Goal

What must be true afterward.

## Acceptance criteria

- [ ] Observable case, including errors, missing evidence, and conflicting sources.

## Out of scope

Work deferred, without silently dropping it.

## Constraints and dependencies

Files, prior decisions, sources, permissions, and blocked choices.

## Learning-to-project mapping

| Originating course/source | Concept | Component served | Timing | Problem solved | Verifiable artifact | Mohammed understands | Codex may do |
|---|---|---|---|---|---|---|---|

## Handoff evidence

PM refinement; engineering output; QA PASS/FAIL per criterion and commands if relevant; scientific reviewer verdict and source locations; owner decision if needed.
````


## A.11 — Kickoff README: English translation

Source: `mof_coder_kickoff/README.md`

````markdown
# Kickoff package for the MOF electrochemistry research tool

This package transfers the owner's decisions into bounded Codex tasks. Start with `AGENTS.md`, then `plan.md` and `_docs/process.md`, then the active task in `_docs/tasks.md`.

**Current status:** The specification is still being refined. Task 001 produced the sample identity contract and task 002 compared sources and stacks; both received PM, QA, and scientific-review handoffs. No first source, technology stack, or user interface has been chosen. Task 003 begins after the owner's prerequisite decisions.

The older files that made QMOF and band-gap comparison the first use case reflect a previous phase. Do not silently alter or delete them; record the effect of the changed scope. QMOF may still provide useful structural information if a source review shows that it serves the approved question.

## Codex continuation request after choosing source and stack

> Read `AGENTS.md`, `plan.md`, `_docs/process.md`, tasks 001 and 002, and their reviews. After the owner records the first source, technology stack, and exact test question, ask PM to groom task 003, then request scientific review, Engineer implementation, and independent QA. Start with a small local project and a verifiable smoke test. Do not expand the task without an explicit scope decision.

This request defines the orchestrator's role; it does not authorize publishing a repository, accessing restricted sources, or conducting an actual theoretical study.
````


# Appendix B — Nine historical project files

These preserve the earlier decisions and software/project-management principles. They are background when they conflict with sections 0–10.


## B.1 — 00_Project_Charter.md

Source: `project_sources/01-00_Project_Charter.md`

````markdown
---
type: project-charter
status: draft
domain: MOF
---

# Project Charter

## Official Name

**MOF Scientific Data Platform — Research, Review & Codex Engineering Lab**

## Priority Order

1. Build a functioning scientific data platform.
2. Apply and master Data Engineering principles.
3. Learn professional Codex-assisted engineering.
4. Produce a structured literature-review seed.
5. Prepare the basis for a possible Data/Methods paper.

The paper is a secondary outcome until the vertical MVP pipeline works.

## Primary User

A graduate student or researcher in computational materials science who needs to search, compare, and filter MOF structure/property data while tracing every value to its source, version, and calculation context.

## First Vertical Use Case

Filter and compare MOFs using:

- metal composition;
- crystal/structure context;
- band-gap values;
- source/version metadata;
- validation status.

## MVP Domain Decision

- Approved domain: MOF
- Future validation domain: Polymers
- The MVP does not support both domains.

## Product Boundary

The platform is not:
- a machine-learning model;
- a general-purpose materials database;
- a replacement for source databases;
- an autonomous scientific agent.

It is a reproducible data infrastructure layer between scientific sources and analysis.
````


## B.2 — 02_MVP_Scope.md

Source: `project_sources/02-02_MVP_Scope.md`

````markdown
# MVP Scope

## In Scope

- MOF domain only.
- QMOF as the leading candidate primary dataset.
- Materials Project/MPContribs evaluation where relevant.
- Batch ingestion.
- Immutable raw snapshots.
- Dataset and retrieval versioning.
- Source metadata and checksums.
- Staging and validation.
- Quarantine for invalid/unparseable records.
- Scientific core entities.
- Property observations.
- Band gap as the first main property.
- Structure/composition context.
- PostgreSQL.
- Python and SQL.
- Docker for reproducible local execution.
- Automated tests.
- One analytical mart.
- Research-source and claim traceability.
- Codex-assisted implementation with human review.

## Out of Scope

- Polymers in the MVP.
- Real-time streaming.
- Machine learning.
- LLM transformations of scientific facts.
- PDF extraction.
- Large dashboard.
- Production deployment.
- Kubernetes.
- Multi-cloud.
- Autonomous multi-agent development.
- Private company data.
- Full systematic-review publication during the MVP.

## Change Rule

Anything outside scope requires:
1. a written reason;
2. cost and value analysis;
3. impact on timeline;
4. an explicit scope decision.
````


## B.3 — 01_Project_Vision.md

Source: `project_sources/03-01_Project_Vision.md`

````markdown
# Project Vision

## Problem

Scientific MOF data is distributed across datasets, publications, repositories, and versions. Values may be difficult to compare because scientific context, calculation method, source version, structure identity, units, or provenance can be missing or separated from the value.

## User

The primary user is a computational-materials researcher or graduate student who needs reliable and traceable MOF data for exploration, comparison, screening, or later modeling.

## Platform Function

The platform will:

1. retrieve versioned scientific data;
2. preserve immutable raw snapshots;
3. validate and standardize records without erasing source meaning;
4. model materials, structures, and property observations explicitly;
5. retain provenance and calculation context;
6. expose a research-oriented analytical mart;
7. produce reproducible queries and reports.

## Differentiator

This is not an API-to-database loader.

Its value is the traceable chain:

```text
Scientific source
→ retrieval snapshot
→ validation
→ scientific semantics
→ warehouse entity
→ analytical record
→ reproducible result
```

## Success

The MVP succeeds when a researcher can answer the first use case and trace each returned property value to:

- source;
- dataset version;
- retrieval batch;
- structure/material identifier;
- unit;
- available calculation context;
- transformation and validation status.
````


## B.4 — 00_Research_Question.md

Source: `project_sources/04-00_Research_Question.md`

````markdown
# Research Question

## Platform Question

How can a reproducible scientific data platform ingest, validate, model, and expose MOF structure and electronic-property data while preserving the provenance, dataset version, and scientific context of each property observation?

## First Analytical Question

Which MOFs can be filtered and compared by metal composition, structural context, and band gap without losing the source and calculation context required to interpret the comparison?

## Review Seed Question

What data-infrastructure, provenance, interoperability, and reproducibility problems limit the reliable reuse of MOF datasets, and how have existing databases and tools addressed them?

## Current Assumptions

- QMOF is the primary candidate source.
- Band gap is the first property.
- A property value without context is incomplete.
- The final grain has not yet been approved.

## Open Decisions

- [ ] Exact QMOF release/version for the MVP.
- [ ] Dataset access method.
- [ ] Structure identity strategy.
- [ ] Minimum calculation context available.
- [ ] Whether Materials Project is a source or only an integration reference.
````


## B.5 — 00_Sources_Master_Index.md

Source: `project_sources/05-00_Sources_Master_Index.md`

````markdown
---
type: source-index
project: MOF Scientific Data Platform
status: active
last_updated: 2026-07-30
---

# 00 — Sources Master Index

> This was the first project source index and its control point for sources.
> Do not use a source for a consequential scientific claim or engineering decision before registering it here.

## 1. Source Workflow

```text
Source discovered
→ registered here
→ source note created
→ evidence verified
→ claim extracted
→ claim linked to decision/specification
→ used in platform or paper
```

## 2. Classification Fields

### Authority Type
- `primary-research`
- `official-technical`
- `peer-reviewed-review`
- `academic-teaching`
- `professional-informal`
- `personal-record`

### Access Status
- `public-full-text`
- `restricted-full-text`
- `abstract-only`
- `currently-unavailable`

### Verification Status
- `fully-read`
- `partially-read`
- `metadata-checked`
- `second-hand-only`
- `not-checked`

### Permitted Use
- `scientific-claim`
- `engineering-decision`
- `background-explanation`
- `discovery-lead`
- `personal-traceability-only`

## 3. Reliability Rule

A load-bearing scientific claim must be supported by:
1. a primary research source or an official scientific source;
2. evidence that can be verified;
3. an exact evidence location when the source is read.

Unavailable or unverified sources may be preserved, but cannot independently support a central scientific claim.

## 4. Source Registry

| ID | Source | Type | Authority | Access | Verification | Primary Use | Status |
|---|---|---|---|---|---|---|---|
| SRC-001 | Materials Project API Documentation | Documentation | official-technical | public-full-text | metadata-checked | engineering-decision | queued |
| SRC-002 | Jain et al. (2013), The Materials Project | Journal article | primary-research | public-full-text | metadata-checked | scientific-claim | queued |
| SRC-003 | QMOF Database, Figshare/GitHub | Dataset | official-technical | public-full-text | metadata-checked | scientific-claim | queued |
| SRC-004 | Rosen et al. (2021), QMOF original paper | Journal article | primary-research | public-full-text | metadata-checked | scientific-claim | queued |
| SRC-005 | Rosen et al. (2022), QMOF electronic-properties expansion | Journal article | primary-research | public-full-text | metadata-checked | scientific-claim | queued |
| SRC-006 | Chung et al. (2014), CoRE MOF database | Journal article + dataset | primary-research | public/full supporting data | metadata-checked | scientific-claim | queued |
| SRC-007 | Wilkinson et al. (2016), FAIR Principles | Journal article | primary/consensus | public-full-text | metadata-checked | engineering-decision | queued |
| SRC-008 | Ong et al. (2013), pymatgen | Journal article + software | primary-research | public metadata | metadata-checked | engineering-decision | queued |

## 5. Seed Source Details

### SRC-001 — Materials Project API Documentation
- Official documentation: https://docs.materialsproject.org/downloading-data/using-the-api/getting-started
- Querying data: https://docs.materialsproject.org/downloading-data/using-the-api/querying-data
- Role in project:
  - API authentication
  - supported endpoints and fields
  - source contract
  - retrieval behavior
- Note: [[01_Research/06_Source_Notes/SRC-001_Materials_Project_API_Documentation]]

### SRC-002 — The Materials Project foundational paper
- Jain, A. et al. (2013).
- Title: *Commentary: The Materials Project: A materials genome approach to accelerating materials innovation*
- Journal: APL Materials, 1, 011002.
- DOI: 10.1063/1.4812323
- Role:
  - scientific and institutional rationale
  - origin and purpose of the Materials Project
- Note: [[01_Research/06_Source_Notes/SRC-002_Materials_Project_Foundational_Paper]]

### SRC-003 — QMOF Database
- Dataset: https://figshare.com/articles/dataset/QMOF_Database/13147324
- Repository: https://github.com/Andrew-S-Rosen/QMOF
- Role:
  - primary candidate dataset
  - versioned scientific records
  - electronic and structural MOF properties
- Note: [[01_Research/06_Source_Notes/SRC-003_QMOF_Database]]

### SRC-004 — QMOF original research paper
- Rosen, A. S. et al. (2021).
- Title: *Machine learning the quantum-chemical properties of metal–organic frameworks for accelerated materials discovery*
- Journal: Matter, 4, 1578–1597.
- DOI: 10.1016/j.matt.2021.02.015
- Role:
  - dataset construction
  - calculated properties
  - limitations and scientific context
- Note: [[01_Research/06_Source_Notes/SRC-004_QMOF_Original_Paper]]

### SRC-005 — QMOF expansion and electronic properties
- Rosen, A. S. et al. (2022).
- Title: *High-Throughput Predictions of Metal–Organic Framework Electronic Properties: Theoretical Challenges, Graph Neural Networks, and Data Exploration*
- Journal: npj Computational Materials, 8, 112.
- DOI: 10.1038/s41524-022-00796-6
- Role:
  - expanded dataset context
  - electronic-property methods
  - theoretical comparability risks
- Note: [[01_Research/06_Source_Notes/SRC-005_QMOF_Electronic_Properties]]

### SRC-006 — CoRE MOF
- Chung, Y. G. et al. (2014).
- Title: *Computation-Ready, Experimental Metal–Organic Frameworks: A Tool To Enable High-Throughput Screening of Nanoporous Crystals*
- Journal: Chemistry of Materials, 26, 6185–6192.
- DOI: 10.1021/cm502594j
- Role:
  - computation-ready structure preparation
  - structural-cleaning assumptions
  - comparison between experimentally sourced and computational datasets
- Note: [[01_Research/06_Source_Notes/SRC-006_CoRE_MOF]]

### SRC-007 — FAIR Guiding Principles
- Wilkinson, M. D. et al. (2016).
- Title: *The FAIR Guiding Principles for scientific data management and stewardship*
- Journal: Scientific Data, 3, 160018.
- DOI: 10.1038/sdata.2016.18
- Role:
  - findability
  - accessibility
  - interoperability
  - reusability
- Note: [[01_Research/06_Source_Notes/SRC-007_FAIR_Principles]]

### SRC-008 — pymatgen
- Ong, S. P. et al. (2013).
- Title: *Python Materials Genomics (pymatgen): A robust, open-source Python library for materials analysis*
- Journal: Computational Materials Science, 68, 314–319.
- DOI: 10.1016/j.commatsci.2012.10.028
- Role:
  - scientific parsing and representation
  - structure/composition tooling
  - dependency evaluation
- Note: [[01_Research/06_Source_Notes/SRC-008_pymatgen]]

## 6. Source Backlog

### Must read before Source Contract
- [ ] SRC-001
- [ ] SRC-003
- [ ] SRC-004
- [ ] SRC-005

### Must read before Scientific Core Model
- [ ] SRC-004
- [ ] SRC-005
- [ ] SRC-006
- [ ] SRC-008

### Must read before Reproducibility Policy
- [ ] SRC-007
- [ ] Materials Project versioning/citation guidance

## 7. Rules

- Never cite a source from memory when exact metadata can be checked.
- Never write `fully-read` unless the relevant full text was actually inspected.
- Every extracted claim must link to [[01_Research/03_Claims_Register]].
- Every engineering decision that depends on evidence must link to the relevant source note.
- A blog or video can explain; it cannot silently replace the original paper.
- A source that cannot be verified must be labelled explicitly.
````


## B.6 — 09_Project_Management_System.md

Source: `project_sources/06-09_Project_Management_System.md`

````markdown
---
type: control-policy
domain: project-management
status: active
---

# Project Management System

## Product Goal

Deliver a working vertical MVP of the MOF Scientific Data Platform that preserves scientific context and provenance from source to analytical result.

## Management Style

Use a lightweight hybrid system:

- product vision and controlled scope;
- milestone-based roadmap;
- small sprint execution;
- Kanban-style task status;
- decision and risk tracking;
- sprint review and retrospective.

Do not simulate a large Scrum team. Use only practices that improve delivery, visibility, or risk control.

## Work Hierarchy

```text
Product Goal
→ Milestone
→ Sprint
→ Feature
→ Task
→ Verifiable Artifact
```

## Task Status

- Backlog
- Ready
- In Progress
- Blocked
- Review
- Done

Only one major implementation task should be In Progress unless two tasks are genuinely independent.

## Definition of Ready

A task is Ready when:

- its purpose is clear;
- its user or platform value is clear;
- dependencies are available;
- task classification is known;
- acceptance criteria exist;
- required decisions and sources are available;
- the expected artifact is named;
- Codex permissions are defined where applicable.

## Definition of Done

Use [[04_Definition_of_Done]].

## Priority Rule

Prioritize work that:

1. unlocks the vertical MVP;
2. reduces major scientific risk;
3. reduces major data-loss or reproducibility risk;
4. removes a blocker;
5. produces reusable learning and evidence.

Do not prioritize work because it appears advanced, a course happens to teach it now, a tool is popular, or Codex can implement it quickly.

## Change Control

A scope-change proposal must state:

- requested change;
- reason;
- user or scientific value;
- estimated cost;
- affected sprint;
- dependencies;
- risks;
- what will be delayed, removed, or simplified.

No scope addition is free.

## Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation | Owner | Status |
|---|---|---:|---:|---|---|---|
| RSK-001 | Project becomes too broad | High | High | One domain, one primary source, one main property, one mart | Mohammed | Active |
| RSK-002 | Process overhead exceeds implementation | Medium | High | T/N/C task classification and proportional gates | Mohammed | Active |
| RSK-003 | Dataset semantics are misunderstood | Medium | High | Source contract, claims register, scientific review | Mohammed | Active |
| RSK-004 | Codex produces code I cannot explain | Medium | High | Plan, diff, tests, oral defense | Mohammed | Active |
| RSK-005 | Courses drive unnecessary architecture | High | Medium | Learning-to-project mapping and no-forced-application rule | Mohammed | Active |
| RSK-006 | Research work delays the functioning product | Medium | High | Product first; review paper remains secondary | Mohammed | Active |

## Milestone Rule

A milestone is complete only through observable artifacts, not hours studied.

Examples:

- source contract approved;
- raw snapshot is replayable;
- staging reconciliation passes;
- core grain is approved;
- first mart answers the use case.

## Sprint Planning

Each sprint defines:

- one sprint goal;
- deliverables;
- excluded work;
- risks;
- course concepts being applied;
- exit test.

## Sprint Review

Record:

- planned;
- completed with evidence;
- incomplete;
- blocked;
- risks discovered;
- decisions made;
- sources added;
- concepts transferred from courses;
- Codex work accepted or rejected;
- next sprint goal.

## Retrospective

Ask:

- What created value?
- What created overhead?
- Where did I misunderstand the science or engineering?
- What did Codex do well or poorly?
- Which rule should change?
- Which repeated failure should become a test, template, or instruction?
````


## B.7 — 08_Software_Engineering_Principles.md

Source: `project_sources/07-08_Software_Engineering_Principles.md`

````markdown
---
type: control-policy
domain: software-engineering
status: active
---

# Software Engineering Principles

## Purpose

Apply Software Engineering practices proportionally so the MOF Scientific Data Platform is:

- understandable;
- testable;
- maintainable;
- extensible;
- reproducible;
- reviewable.

Software Engineering is not decoration around Data Engineering. It controls how pipeline code, interfaces, tests, configuration, and changes remain safe as the project grows.

## 1. Separation of Concerns

Keep these responsibilities separate when a real boundary exists:

- source access;
- retrieval orchestration;
- raw persistence;
- parsing;
- validation;
- scientific transformation;
- database access;
- configuration;
- logging;
- analytical queries.

Do not split code into many files merely to imitate a large company.

## 2. Explicit Contracts

Every important component must define:

- inputs;
- outputs;
- assumptions;
- state changes;
- exceptions;
- failure behavior;
- retry behavior where relevant;
- test evidence.

## 3. Cohesion and Coupling

A component should have one clear responsibility and one clear reason to change.

Prefer high cohesion, explicit dependencies, narrow interfaces, and replaceable external adapters.

Avoid hidden global state, unrelated responsibilities in one function, and tight coupling between scientific rules and API/database code.

## 4. Dependency Control

A new dependency requires answers to:

1. What problem does it solve?
2. Can the standard library or current stack solve it?
3. What are the alternatives?
4. Is it maintained?
5. What is its license?
6. What security or supply-chain risk does it introduce?
7. How will its version be pinned and upgraded?
8. What is the cost of removing it later?

Codex may recommend a dependency but may not install it without approval.

## 5. Testability by Design

Design the system so:

- source calls can be replaced with fixtures;
- raw persistence can be tested without live APIs;
- transformations can be tested independently;
- failure conditions can be simulated;
- deterministic outputs can be asserted;
- database integration tests are separated from unit tests.

## 6. Error Handling

Errors must be:

- classified;
- surfaced clearly;
- logged with useful context;
- retried only when retry is valid;
- prevented from silently corrupting data;
- connected to recovery behavior.

A caught exception is not automatically a handled error.

## 7. Configuration and Secrets

- Configuration is separate from code.
- Secrets are never committed.
- `.env.example` contains names, never real values.
- Development and test settings are explicit.
- Default values must not hide unsafe assumptions.
- Configuration validation should fail early.

## 8. Version Control

- Specifications are approved before implementation.
- One meaningful change per branch.
- Commits are small and coherent.
- Diff is reviewed before merge.
- Generated noise is separated from meaningful changes.
- No direct unreviewed change to the main branch.

## 9. Documentation as Product Work

Document:

- why a decision exists;
- how to run the component;
- inputs and outputs;
- failure and recovery behavior;
- assumptions and limitations;
- related sources and decisions.

Documentation must change when behavior changes.

## 10. Refactoring Rule

Refactor when there is evidence of duplication, confusing responsibility boundaries, difficult testing, recurring defects, or excessive coupling.

Do not refactor merely because Codex proposes a more elegant abstraction.

## 11. Proportional Engineering

Do not add an abstraction, design pattern, service, framework, microservice, agent, or infrastructure layer unless it solves a demonstrated product or engineering problem.

## 12. Review Questions

For every non-trivial component:

- Why does it exist?
- Where should this responsibility live?
- What contract does it expose?
- How can it fail?
- How is it tested?
- What changes if it is removed?
- What alternative was rejected and why?
````


## B.8 — 00_Project_Charter(1).md

Source: `project_sources/08-00_Project_Charter-1-.md`

````markdown
---
type: project-charter
status: draft
domain: MOF
---

# Project Charter

## Official Name

**MOF Scientific Data Platform — Research, Review & Codex Engineering Lab**

## Priority Order

1. Build a functioning scientific data platform.
2. Apply and master Data Engineering principles.
3. Learn professional Codex-assisted engineering.
4. Produce a structured literature-review seed.
5. Prepare the basis for a possible Data/Methods paper.

The paper is a secondary outcome until the vertical MVP pipeline works.

## Primary User

A graduate student or researcher in computational materials science who needs to search, compare, and filter MOF structure/property data while tracing every value to its source, version, and calculation context.

## First Vertical Use Case

Filter and compare MOFs using:

- metal composition;
- crystal/structure context;
- band-gap values;
- source/version metadata;
- validation status.

## MVP Domain Decision

- Approved domain: MOF
- Future validation domain: Polymers
- The MVP does not support both domains.

## Product Boundary

The platform is not:
- a machine-learning model;
- a general-purpose materials database;
- a replacement for source databases;
- an autonomous scientific agent.

It is a reproducible data infrastructure layer between scientific sources and analysis.

## Engineering Disciplines

The platform deliberately integrates:

1. Scientific domain reasoning.
2. Data Engineering.
3. Software Engineering.
4. Lightweight Project Management.
5. Evidence-grounded research.
6. Bounded Codex-assisted implementation.

These disciplines support the product; none is added for appearance.
````


## B.9 — 11_Project_Handoff.md.md

Source: `project_sources/09-11_Project_Handoff.md.md`

````markdown
# Project Handoff

## Project

MOF Scientific Data Platform — Research, Review & Codex Engineering Lab

## Current Phase

Sprint 00A — Product Definition

## Current Status

The ChatGPT Project, Obsidian structure, source index, control documents, research files, engineering files, Codex policies, Software Engineering principles, Project Management system, and learning-to-project mapping system have been prepared.

No production code, Git repository, database schema, API ingestion, or Codex implementation has started.

## Approved Direction

- MVP scientific domain: MOF.
- Future validation domain: Polymers.
- The functioning scientific data platform is the primary product.
- Data Engineering, Software Engineering, Project Management, and Codex-assisted development are execution and learning systems.
- The literature review is a secondary research output until the vertical MVP works.
- The project must remain more than an API-to-database pipeline by preserving scientific context, provenance, versioning, validation, and reproducibility.
- Every course lesson must be mapped to a real project need or explicitly postponed/rejected.
- Codex is a bounded implementation engineer, not the scientific authority or architect.

## Current Draft Product Direction

Primary user:

A graduate student or researcher in computational materials science who needs to search, filter, and compare MOF structure and property data while tracing every value to its source, version, and calculation context.

Candidate first use case:

Filter and compare MOFs by metal composition, structural context, and band gap while preserving provenance and validation status.

Candidate primary source:

QMOF, subject to Source Contract evaluation in Sprint 01.

These are drafts until approved during Sprint 00A.

## Decisions to Approve in Order

1. Real problem.
2. Primary user.
3. First use case.
4. Platform value and differentiation.
5. MVP boundaries.
6. Initial research question.

Only one decision may be discussed at a time.

## Current Decision

A — The real problem.

The key question is:

What real problem prevents a researcher from simply downloading QMOF, opening it in a notebook, and completing the intended analysis reliably?

## Constraints

- No code.
- No Git repository.
- No Codex implementation.
- No database schema.
- No expansion outside MOF.
- No large literature search yet.
- No tool is adopted merely because a course teaches it.
- Do not rewrite complete documents before the underlying decisions are approved.

## Documentation Rule

After each approved decision, produce:

- a concise Session Record;
- a Decision Record;
- affected Obsidian files;
- future GitHub artifact;
- learning-to-project mapping where relevant.

Raw chat transcripts are not future GitHub artifacts.
````


---

# Appendix C — Earlier scientific research brief (English translation)

**Provisional descriptive title: An evidence-based research tool for selecting MOF-related materials**

**Historical status:** This brief predates the current decisions in sections 0–10. In particular, its first example requires experimental preparation and describes a narrow HER prototype. The current product also permits clearly labeled computational candidates and is intended to support other electrochemical questions. Use this brief for its workflow and evaluation ideas, subject to the current specification.

## 1. Project definition

A tool that helps a researcher turn a scientific question into a list of MOF candidates for study, showing the evidence that explains why each candidate appears, how it fits the question's constraints, and which missing information prevents a firm judgment.

The workflow starts with the **researcher's need**: the intended application, desired properties, laboratory limitations, and the type of novelty being investigated. It then helps locate relevant studies, link evidence to the correct material, and organize results so a person can review them.

The researcher and supervisor retain responsibility for choosing a material and interpreting the evidence.

## 2. Problem addressed

Choosing a material requires answering questions spread across multiple sources:

- Where was its synthesis method published?
- Do names used in two papers refer to the same material?
- Is the tested material a MOF, a MOF-containing composite, or a derivative produced from a MOF?
- Which applications have been investigated?
- Are the reported results actually relevant to the research question?
- What synthesis, characterization, and testing capabilities are required?
- Are useful structural or computational data available?
- What evidence points to a research opportunity, and what are the limits of that search?

The **hypothesis to evaluate** is that combining these steps in a documented workflow could reduce searching and rereading time, lower errors in linking materials to results, and help a researcher explain a choice. The size of any benefit must be measured.

## 3. First user and historical example

The initial user is a graduate student or researcher starting materials exploration for a defined project.

An earlier example of the owner's research question was:

> Find up to five MOF compounds worth investigating for electrochemical hydrogen production, with a published experimental synthesis route, assessable requirements for a local laboratory, and documented previous work on the application.

Five was a target for an initial shortlist; if the evidence supports fewer, show the smaller number and why. The experimental-synthesis requirement in this example is **not a global rule in the current specification**.

## 4. Tool inputs

| Input | Example |
|---|---|
| Research question | Search for MOFs to investigate for HER |
| Allowed material type | Pristine MOF, composite, or derivative, as selected by the researcher |
| Mandatory criteria for a particular query | Published experimental preparation, if that query explicitly requires it |
| Preferences | Accessible linker, fewer steps, or structural data |
| Laboratory capabilities | Available equipment/materials and unresolved facts |
| Meaning of novelty sought | New application, unresolved mechanistic question, or comparatively little-studied material |
| Starting sources | Article, DOI, lawfully available PDFs and supporting information, or a bibliography |

Separate a **mandatory condition**, **preference**, and **unknown**. If the availability of equipment is unknown, do not count it as either available or unavailable. Show the parsed question and conditions for correction before screening.

## 5. Research workflow

| Stage | Work | Output |
|---|---|---|
| Specify question | Make the request searchable and testable | Explicit query and criteria |
| Discover sources | Search terms, material names, references, and citation leads where accessible | Potentially relevant papers |
| Resolve material identity | Collect names, composition, constituents, and identifiers | Material/sample records with visible uncertainty |
| Extract information | Link preparation, application, and result claims to exact source locations | Attributed evidence |
| Check conditions | Compare evidence against researcher-defined criteria | Meets, does not meet, or requires more information |
| Researcher review | Correct extraction, identity, and relevance | Reviewed record |
| Present shortlist | Show candidates and the reasons and limits for each | Cards and comparison table |

A material might first be found in a paper on an application other than HER and then be traced to later electrochemical work. The workflow therefore allows both application-first and material-first searches.

## 6. Candidate card

| Field | Contents |
|---|---|
| Identity | Reported name and aliases, metal, linker, formula if available |
| Material category | MOF, composite, derivative, or unresolved |
| Reason for inclusion | Which criteria the evidence supports |
| Preparation reference | DOI and the exact Methods or supporting-information location |
| Preparation requirements | Reported reagents, equipment, and conditions |
| Published applications | Located uses with citations |
| Performance observations | Values, units, and measurement conditions when actually extracted |
| Structure/calculation | Availability and source of CIF or computational data |
| Prior-use search | Search strings, inspected sources, date, and limits |
| Missing evidence | What needs another source, verification, or author clarification |
| Researcher review | Corrections and reasons for keeping or excluding a candidate |

When sources conflict, display both claims and provenance; do not automatically choose one or average values.

## 7. Evidence rules

Display the epistemic status clearly:

- **Direct source report:** A specific fact with source location.
- **Author interpretation:** For example, an author's proposed explanation for improved activity.
- **Preliminary tool inference:** A possible link requiring researcher review.
- **Unknown:** Evidence is not yet available.
- **Conflicted:** Sources or records disagree.

Also record whether the source is original research, a review, or preliminary work, and whether its text was actually accessed. A published method does not establish feasibility in a particular laboratory. Appearing on a candidate list does not establish catalytic activity.

A controlled statement about novelty is:

> No directly relevant study was found within the specified sources and queries as of the recorded date.

Every number or rank needs an interpretable basis. If a numeric score is introduced later, disclose its rules and weights and examine sensitivity to their changes.

## 8. Potential role of AI

AI might help interpret the question and propose search synonyms for user review, extract information from permitted text, explain scientific language while retaining original terminology, summarize why a paper may be relevant, and suggest potential links between material names for human inspection.

Programmatic checks should validate identifiers, units, values, and fields where possible; ambiguous cases need review. Every extracted claim needs an evidence pointer. When the evidence is insufficient, say so. Do not treat text found inside a paper as an instruction to alter the tool's behavior.

## 9. Role of the data platform

The platform stores relations between the **question, paper, material, synthesis, observation, evidence, search run, and user review**. One paper may describe many materials; one material may appear in several papers; every experiment may have different conditions. Preserve these relations without merging different results under a generic label such as “Ni-MOF.”

QMOF or another dataset may supply structural or computational data when those data serve the chosen question. Select sources by scientific need, data availability, and permitted usage.

## 10. Earlier first-version proposal

An earlier proposal scoped a small version to **MOFs and a HER question** with a source set that could be checked manually. It suggested entering the research question, adding lawful reference files, helping fill candidate cards, permitting human review, searching saved records, and exporting results.

Paper access could be manual at first while the tool handles organization, traceability, and comparison. Any connection to an external source would follow its documented access rules. A local version could retain permitted references and notes for offline inspection; discovering new papers would require connectivity at update time.

This is a **proposal, not a committed first-version feature list**. The current implementation boundary remains to be determined through owner decisions and task 003 acceptance criteria.

## 11. How usefulness could be evaluated

Use questions and materials with reference answers checked by qualified reviewers.

| Evaluation dimension | Question to measure |
|---|---|
| Extraction accuracy | Do name, value, unit, and conditions match the source? |
| Identity accuracy | Are papers and observations linked to the correct sample? |
| Retrieval coverage | What share of relevant studies in a predefined reference set were found? |
| Result relevance | Which displayed outputs actually address the question? |
| Traceability | Can the researcher find evidence for every key claim? |
| Time and effort | Are steps and elapsed time lower than in a documented manual workflow? |
| Reproducibility of search | Can the inputs, queries, filters, and versions that generated the shortlist be reconstructed? |

Compare against a competent manual workflow using searches and references. Document errors and failures, not only successful examples.

## 12. Relation to a master's project and a software portfolio

As a software project, a working tool using real permitted data, documentation, tests, error handling, and a usable researcher workflow could demonstrate engineering ability.

As academic research, it would need a specific research question and contribution. One **unverified proposal for evaluation** is:

> Does an evidence-linked workflow for selecting MOF materials, retaining sample identity and search history, improve screening accuracy and auditability compared with an organized manual search?

Neither the novelty nor suitability of this question as a master's thesis has been established. A linked theoretical chemistry study would require its own chemical question, model, and validation. Extracting information from computational papers alone is not a new theoretical study.

## 13. Meaning of success for an initial stage

A researcher can enter a specific question, inspect candidates and why they appeared, open their evidence, correct records, save results, and resume the work later. Current paper-reading sessions can generate manually checked examples to understand and test the workflow. Ten hours of reading should not be mistaken for time sufficient to build or validate the entire product.

## 14. Decisions before implementation

The older brief asked the owner to settle the first exact question, allowed materials and mandatory/preferred conditions, usable sources and fields, the candidate-card evidence threshold, automated versus human-reviewed steps, and the method for evaluating success and limiting research claims.

**Start by understanding and documenting one material-selection process manually. Turn only its understood, repeated steps into testable software behavior.**
