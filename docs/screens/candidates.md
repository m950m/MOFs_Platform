# Candidates

The screen that answers "**why did this candidate appear**" — and lets you
follow every claim on its card back to the recorded evidence. No ranking, no
scoring, no invention.

## What enters

Nothing new — the card is assembled from what you already recorded: the
sample under [Samples & identity](samples-identity.md), its source, the
assertions under [Evidence](evidence.md), and the search outcomes under
[Sources](sources.md). Samples must exist first; nothing is invented here.

## What comes out

A **candidate card** per sample:

- Basis (`experimental` / `computational` / `hypothetical`), material class,
  parent relation, modifications/additions.
- The source with its inspected level and the route outcomes that brought it
  in.
- **"Why it appeared"** — the retrieval reason.
- **Observations** per tested sample, with missing condition fields shown as
  gaps — displayed, not compared or ranked.
- **Operating-state interpretations** with their epistemic types.
- **Recorded assertions for this source** — follow them to
  [Evidence](evidence.md); conflicts flagged.
- A reminder where review is still pending: one reviewed assertion would not
  make the whole candidate reviewed.

## Compounds (feature cards)

Below the candidate cards you can group records into **compounds**:

- Create a compound with a canonical name, an optional framework key
  (MOFid/MOFkey or equivalent), and a **required identity note** — why this
  grouping exists, and who created it.
- Attach sample records and structure-index records as members, each with a
  required reason; detach with a reason too. Every change is audited.
- The **compound profile** shows all members side by side: sample
  observations stay under their sample; structure properties stay
  provider-labeled metadata.

## Honest markers

- **Grouping is not equivalence and never merges**: same
  composition with a different arrangement or morphology belongs in a
  *separate* compound. Member properties never "climb" between members.
- Values from different members sit side by side with provenance — never
  averaged, silently overwritten, or ranked.
- Empty sections render `unknown` — literature values are never inserted from
  memory.
- Structure records on a profile are metadata about published structures;
  they never establish that a sample was made or tested.
