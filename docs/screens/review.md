# Review

The honesty checkpoint. Recorded claims start at `needs verification`; here
**you** correct them, review them, and resolve conflicts — always attributed,
always with history.

## What enters

- **Corrections** to an assertion (new claim text / evidence location), an
  identity relation, or a sample record — each requires the editor's name and
  a **reason**. Blank fields on sample corrections mean "keep"; the source
  link itself is capture provenance and is not correctable here.
- **Reviews** — marking an assertion or relation `reviewed` requires:
    - the reviewer's name,
    - the **exact supporting source location** you personally inspected,
    - the reason it meets the review threshold (decision D4).
- **Conflict resolution** — for assertions marked `conflicted`: the resolver's
  name and a required reason (e.g. double entry, or one side was corrected).

## What comes out

- Updated claims and records, each with its **full history**: old → new
  values, who changed them, when, and why. Originals live in each event's
  snapshot.
- The **review & correction history** — every action with its actor, reason,
  and supporting location.

## Honest markers

- **Reviewing one claim never reviews the others** — and no whole material is
  ever labeled `reviewed`. Review applies to a particular assertion or
  relation.
- **Correcting a reviewed claim strips the approval** — it returns to
  re-review, so an old `reviewed` badge can never hide a newer correction.
- **Resolving a conflict is an explicit human decision**; afterwards both
  assertions return to `needs verification` (re-review required).
- Rejected actions (missing reason, missing location) keep everything you
  typed — nothing is silently discarded.
