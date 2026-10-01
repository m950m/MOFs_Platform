# Design system (local review UI)

Draft established 2026-10-01 to satisfy the issue #3 guidance requirement
("read `_docs/design-system.md` before UI work"). Mohammed may amend at any
time; these rules bind agent-authored UI.

## Principles

The interface exists to make evidence inspection and correction easy and to make
uncertainty impossible to miss. It never suggests scientific certainty the data
does not carry.

## Controlled vocabulary (rendered exactly, never paraphrased)

| Concept | Exact label |
|---|---|
| Assertion review states | `needs verification` · `in review` · `reviewed` · `conflicted` |
| Epistemic types | `directly reported` · `author interpretation` · `tool inference` · `user judgment` · `unknown` |
| Per-reaction search outcome | `not yet searched` · `no experimental test found within the documented search scope` · positive evidence |
| Modification proposals | always tagged `untested hypothesis` |
| 3D structure (future) | `crystal structure model`; illustrative renderings `schematic` |
| Missing values | `unknown` — never blank, never guessed |

## Layout rules

1. **HER and OER are separate.** Distinct columns/sections with independent
   outcomes; never a combined "tested: yes/no".
2. **Evidence-first rows.** Every claim line shows: source pointer, evidence
   location (or explicit `unknown`), epistemic type, review state. Provenance is
   visible without navigation.
3. **Conflicts show both.** Contradicting assertions render side by side, each
   with provenance; no averaging, no silent winner, no auto-resolution.
4. **Labels, not colors alone.** Status is always text (color may accompany,
   never replace).
5. **Identity is always visible.** A record shows what level it is (framework /
   reported sample / operating state / observation) and its parent links;
   nothing is ever collapsed under a generic name.
6. **Explicit saves.** Edits persist to SQLite on explicit action; the UI never
   implies `session_state` is storage. Corrections display old → new with reason.
7. **Honest empty state.** The empty/ready state names what is absent
   ("no questions recorded yet") and never invents example candidates.
8. **No dark patterns toward certainty.** No ranking that implies validated
   activity; search-rank order is labeled as retrieval order, nothing more.
