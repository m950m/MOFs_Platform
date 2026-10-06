# Evidence

Where claims become **attributed assertions**. This is the screen that makes
"how do I know?" answerable months later.

## What enters

One assertion at a time, attached to a captured reference (record it under
[Sources](sources.md) first — assertions attach to a source):

- **Claim type** — preparation / composition / property / application / other.
- **Claim / value exactly as reported or judged** — the wording stays the
  source's, not a paraphrase.
- **Exact evidence location** — e.g. "Methods §2, fig. 3, table S1". Leave it
  blank and it is recorded as `unknown — verification still required`.
- **Extracted by** — who or what extracted the claim (defaults to you).
- **Epistemic type** — where the claim comes from:
    - `directly reported` — stated/measured in the source,
    - `author interpretation` — the source's own reading,
    - `tool inference` — this tool suggested it (needs review),
    - `user judgment` — researcher-entered, not from the source,
    - `unknown` — not yet determined.
- **Conflicts (optional)** — mark this assertion as conflicting with another
  recorded one.

## What comes out

The recorded assertion list, each showing claim, source, evidence location,
extractor, epistemic type, and its own review state. Conflicting pairs are
flagged on both sides.

## Honest markers

- Recording **never marks anything reviewed** — new assertions enter at
  `needs verification`.
- Metadata alone cannot establish sample-specific preparation or measured
  activity — that is true no matter how many assertions you record.
- **Conflicts are kept, not resolved silently:** both claims stay visible;
  neither replaces or averages the other.
- Claim text is **source data, never instructions** — pasted text cannot
  change this tool's rules, review states, or records.
