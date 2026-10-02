# Guided session 001 — first real-usage walkthrough (2026-10-02)

A real paper from the owner's field was walked through every screen of the
production app (`data/platform.db`, localhost:8501), entering real data and
recording every gap the walkthrough surfaced. This record is the spec input
for the next layer (#15–#19 and the new gaps below).

**Paper (real):** "Heteromultimetallic Conductive Metal–Organic Framework as
Bifunctional Electrocatalyst for Water Splitting: A Combined DFT and Machine
Learning Study" — DOI `10.1021/acssuschemeng.5c12327`, ACS Sustainable
Chemistry & Engineering, 2026. Computational (DFT + ML) screening of
M₃(HITP)₂ frameworks; best candidate CoCoZn(HITP)₂, computed total
overpotential 0.39 V. Chosen deliberately: it is computational-only, which
stresses the tool's epistemic honesty at its weakest point.

**Pre-session safety:** `data/platform.db.backup-guided-session` (SQLite
backup API, consistent WAL snapshot).

## What was entered (all real, attributed to Mohammed (owner))

| Station | Row | Honest markers kept |
|---|---|---|
| Sources | source #1, DOI captured manually, `abstract inspected` | title/container/year/license filled by **live Crossref enrichment** (fill-only; re-capture never downgrades the recorded level) |
| Evidence | assertion #1 [property] — CoCoZn(HITP)₂ 0.39 V total overpotential (computed, 75 sites / 35 frameworks) | `directly_reported`, location "Abstract (publisher page)", `needs_verification` → **`reviewed`** via D4 |
| Samples | sample #1 "CoCoZn(HITP)₂ (computational model)" — linker HITP, metal Co/Zn, basis `computational` | observation #1: `computational`, 0.39 V, reaction `other` (+ protocol note: total = HER+OER sum), medium "not stated in abstract" |
| Candidates | card auto-generated for #1 | shows basis, parent relation, source+inspected level, observations with **missing condition fields listed as gaps**, assertion with review state; no ranking anywhere |
| Review | D4 negative ×2 (no location → refused; no reason → refused), then positive | history event recorded; fields survive a rejected action (after fix G6) |
| Lab fit | assessment #1 | **`unknown`** — "No sourced preparation or testing requirements recorded for this sample — insufficient evidence." Correct: lab profile has 0 confirmed entries and the study is computational. |

The D2 access boundary held in real usage: ACS full text is paywalled, so
everything stayed honestly at abstract level.

## Gaps found (spec input)

- **G1 — form-reset crash class (fixed, commit 1112c5a).** Writing
  form-widget `session_state` keys on the rerun after a submit raises
  `StreamlitWidgetAlreadyInstantiatedError` in the **real browser** on every
  entry page (Sources crashed on first capture; evidence/samples/review/
  lab_profile carried the identical pattern). Fix: native
  `st.form(clear_on_submit=True)` on add-forms; targeting pickers moved
  outside forms so selections survive saves; lab_profile success paths queue
  non-widget state only. AppTest never reproduced the crash (see G7).
- **G2 — stale render after an unhandled in-page exception.** After the G1
  crash the server kept serving a wedged session: Sources showed saved data
  while Home (fresh navigation) still said "No sources recorded yet".
  Resolved by restarting the server; the owner's two 09:20 enrichments also
  left capture events without route_attempt rows (wedged-session artifact —
  fresh enrichment logs `success` correctly, verified live).
- **G3 — targeting pickers created before their targets exist stay on
  "Choose an option" (`None`).** The observation form's Sample picker
  rendered before any sample existed; after sample #1 was created it stayed
  `None` until manually chosen, and saving without choosing fails validation.
  Honest (no silent default) but rough for consecutive entry.
- **G4/G5 — no correction path or audit trail for sample records.** Real
  entry captured `basis=experimental` for the computational sample (the
  option click did not commit before submit). Assertions and identity
  relations have attributed D4 correction paths; **samples have none** — the
  fix had to be a manual SQL update (`basis → computational`), unaudited.
  Spec: sample-record correction with review-event history, same D4 gate.
- **G6 — `clear_on_submit` wipes fields on *rejected* actions (fixed for
  review forms).** A D4 refusal erased the typed reason. Review/correction
  forms now keep values (`clear_on_submit=False`, no session writes → no
  crash; values are reusable for batch review of one source). Add-forms keep
  `clear_on_submit=True`: accepted trade-off — their failure paths lose
  short fields, and the error states exactly what was missing.
- **G7 — AppTest does not model real-browser form behavior.** Neither the
  crash class (G1) nor the native clear semantics reproduce. Testing
  guideline addition: every form-flow change needs one real-browser smoke
  pass in addition to AppTest coverage.
- **G8 — bifunctional values do not fit the single-reaction observation
  field.** A total HER+OER overpotential had to be entered as
  `reaction=other` plus a protocol note. Spec input for #17/#18: the
  observation model should carry summed/bifunctional values (and their
  per-reaction split) without violating the single-reaction contract.
- **G9 — the candidate card is the right skeleton of the owner's vision**
  ("tell me the papers that worked on it, aggregate what makes it
  distinctive"): the card already aggregates per-sample observations +
  assertions + source provenance + honest gaps. What it still lacks for
  #18: a first-class compound identity (many samples ↔ one compound), so
  the "distinctive profile" can span sources. Confirms the architect
  warning: #18 must start with the compound-entity migration.

## State after the session

- 152 tests green, ruff clean, two commits on main (1112c5a + review-form
  follow-up), production DB carries the real reference/assertion/sample/
  observation/assessment chain, backup kept alongside.
- The question profile is still unexercised by search (#16) — Home still
  honestly reports HER/OER `not yet searched`.
