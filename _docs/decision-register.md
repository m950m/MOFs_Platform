# Decision register — owner entries only

This file records the owner-held decisions of plan §5. **Only Mohammed writes in
the "Owner entry" column.** Agents may propose (see
[`proposals/proposed-implementation-spec.md`](proposals/proposed-implementation-spec.md) §1)
but never fill an entry, treat silence as approval, or edit a recorded decision.

---

## Pending decisions D1–D8 (prepared 2026-10-01 as proposals)

| ID | Decision | Proposal (summary — full text in the proposal §1) | Owner entry | Date |
|---|---|---|---|---|
| D1 | First exact research question, reaction(s), conditions, acceptance case | **Owner entry recorded 2026-10-01:** the owner will enter the first question himself through the app once issue #4's entry surface exists; until then no question exists and **every scientific field (reaction, material classes, conditions, hard requirements, preferences, meaning of improvement) starts intentionally unknown** — the implementer supplies none of their values. Tool acceptance case for the first slice: **proposal §2.1 approved as-is.** | **Approved** (owner selection via agent decision session) | 2026-10-01 |
| D2 | First source contract (route, permitted fields, rights, failure behavior) | Crossref REST polite pool (`mailto`) for DOI metadata enrichment; manual entry is the primary evidence path; no full-text retrieval. | **Approved — Crossref + manual entry** (owner selection via agent decision session; full contract per proposal §5) | 2026-10-01 |
| D3 | Local stack and interface | L2: Python 3.11+ / Streamlit local app / SQLite (stdlib `sqlite3`); deps `streamlit`, `httpx`; dev `pytest`, `ruff`. | **Approved — L2: Streamlit + SQLite** (owner selection via agent decision session) | 2026-10-01 |
| D4 | Threshold for an assertion to become `reviewed` | Named human records a ReviewEvent confirming inspection of the exact cited evidence location (who, when, verdict, reason). | **Approved — D4 proposal as-is** (owner selection via agent decision session) | 2026-10-02 |
| D5 | Cross-source sample equivalence rule | Human confirms both sources explicitly designate the same sample (shared batch ID or explicit citation); otherwise records stay separate; no automated merge. | **Approved — stricter variant: NO cross-source equivalence, ever.** Records stay separate permanently; the relation stays `unresolved`/documented; even a qualifying human review cannot merge (owner selection) | 2026-10-02 |
| D6 | Absence-of-testing filter | None in the first slice; per-reaction outcomes displayed without excluding candidates. | | |
| D7 | Laboratory capability profile | Seeded from prior statements (no glovebox/inert line; HHTP excluded) but every entry starts `unknown` until owner reconfirms. | **Approved as implemented:** no seeding at all — every entry is owner-entered at runtime with the four statuses (rule per plan §2.5; D6/D8 still open) | 2026-10-02 |
| D8 | Interactive mock prototype scope | Out of scope (plan §7 backlog boundary). | | |
| D9 | Permitted search sources for active search (#16) | Metadata-only scholarly search consistent with the D2 contract (no full text): **Crossref REST `/works` queries + OpenAlex `/works` queries**, both polite-pool (contact e-mail), typed failures, transport-injected adapters, every hit a lead. | **Approved — Crossref + OpenAlex** (owner selection via agent decision session; decided immediately after guided session 001) | 2026-10-02 |
| D10 | AI service for question refinement (#15) | Provider-agnostic adapter (same pattern as the Crossref adapter: injected transport, typed failures, offline tests); **first adapter: Z.ai GLM API** (OpenAI-compatible endpoint). The AI suggests question wording/reaction/condition refinements; the owner accepts or edits — the tool never silently rewrites the saved question. | **Approved — Z.ai GLM API first** (owner selection via agent decision session) | 2026-10-02 |

| D12 | Open data-source adoption order (post-scan 2026-10-03) | Adopt in order: **1) CoRE MOF 2019** (structures + source DOIs), **2) QMOF** (theory-stream computed properties), **3) DigiMOF** (text-mined synthesis context), **4) MOFid/MOFkey** (compound-identity keys for #18), **5) COD** (fallback lookup). Deferred: ODAC23 (DAC-scoped), hMOF/ARC (hypothetical), CSD (closed — separate licensing decision). All imported data keeps provider provenance and streams per D11. | **Owner approved** ("go" after the scan, 2026-10-03) | 2026-10-03 |
| D11 | Number-stream separation: laboratory vs industry/reference numbers | Laboratory-measured numbers and industry/reference numbers are **separate streams, never merged into one verdict** — same rule as HER/OER separation. Comparisons may display both side by side with provenance; may not collapse, average, or let one override the other. Binding on #17 and #18 aggregation. | **Owner mandate under full delegation** (2026-10-02; recorded during task-016-completion) | 2026-10-02 |

Gates: **D2 + D3 unblock issue #3**; D1 unblocks #4; D4–D7 are needed before their
corresponding issues (#11, #8, #4–#13, #12) — see `proposals/diagrams.md` §5.
**D9 unblocks #16** (active search); **D10 unblocks #15** (AI question refinement).
Register-D6 (absence-of-testing filter) remains open — it governs candidate
display/filtering, not search sources.

---

## Full decision record (plan §5 template — copy per final decision)

```text
Decision ID / date / owner: ... / ... / Mohammed
First precise research question, relevant reaction(s), and conditions: ...
Observable acceptance case for the first slice: ...
Any absence-of-testing selection rule (if approved): Not specified / ...
Selected first preparation/application evidence route, permitted input or API fields, rights, and failure behavior: ...
Selected local UI and persistence; repository: m950m/MOFs_Platform
Interactive mock prototype scope, if approved: Not specified / ...
Current / future / unknown laboratory capabilities: ...
Evidence-review threshold and cross-source sample equivalence rule: ...
Reason, supporting source, alternative, and implications for task 003: ...
```

---

## Owner architectural mandates (recorded 2026-10-02)

Recorded verbatim in intent by the owner; binding for all future implementation
(details and landing spots in `ARCHITECTURE.md` and issues #18, #19, and the
comment on #8):

1. **Stable architecture, open source:** the repository is an open-source
   project (Apache-2.0 added 2026-10-02) with fixed layers and documented
   extension points so contributors cannot destabilize provenance or identity.
2. **Contributor data entry:** "whoever registers or works on a compound
   enters precise data" — implemented as attributed evidence packages with
   mandatory review ([#19](https://github.com/m950m/MOFs_Platform/issues/19));
   a hosted multi-user server remains a separate future owner decision.
3. **Compound distinctness:** the same composition with a different atomic
   arrangement (structure/topology/CIF) or different morphology is a **different
   compound** — enforced in #8 and [#18](https://github.com/m950m/MOFs_Platform/issues/18).
4. **Unique property aggregation:** every compound aggregates its own property
   profile as a unique feature card ([#18](https://github.com/m950m/MOFs_Platform/issues/18));
   properties never transfer between compounds.
