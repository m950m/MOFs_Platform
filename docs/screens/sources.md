# Sources

The widest screen: **everything that brings outside material in** — reference
capture, active literature search, structure lookup, and offline evidence
packages. Every record created here is a **lead**.

## What enters

1. **Manual reference capture** (works fully offline): DOI, URL, title — all
   optional; the contributor name and *what was actually inspected* (metadata
   only / abstract / text, …) are recorded. A supplied passage note can record
   exactly what you read.
2. **Active search** (Crossref / OpenAlex): the query text
   defaults to your saved question **verbatim** — editable; the exact text
   sent is recorded. One polite page (8 hits) per run; no automatic retry.
3. **Crossref enrichment** (optional): fills missing
   bibliographic fields for a captured DOI. Add your contact e-mail to use the
   Crossref polite pool.
4. **Structure lookup**: you download the CoRE MOF 2019
   deposit from Zenodo yourself, export its summary spreadsheet as CSV, and
   import the file from your disk. The tool never downloads anything. Then
   search the index by name / formula / id.
5. **Evidence packages**: import a collaborator's package JSON
   from a local path (see [Evidence packages](../evidence-packages.md)).

## What comes out

- **Saved references** — each with origin (manual / captured-from-hit /
  structure), contributor, DOI, capture date, and inspected level.
- **Hits per search run** — provider retrieval order, never a ranking, each
  with HER / OER title-token flags, per-criterion checks against your
  question (`matched in title` / `not in title` / `unknown`), and status.
  Hits can be **captured as references** (with search provenance) or
  **dismissed** (a reason is required; the dismissal stays auditable).
- **Route attempts and search runs** — the "Route attempts" list covers the
  Crossref enrichment calls, and search runs get their own list under the
  search section; each entry shows its outcome and next step, and failed
  entries stay failed in the log.
- **Structure search results** — provider-labeled records with their DOI and
  any computed/context properties from the provider CSV; capturing a
  structure's DOI creates a reference lead.

## Honest markers

- **Every hit and reference is `needs verification`** — metadata alone never
  establishes experimental preparation or measured performance.
- **`no_hit` never means the material is unstudied.** A failed Crossref
  lookup on a DOI is a statement about that provider and query only.
- A shared DOI never means the same tested sample; a text link does not mean
  the text was inspected.
- HER and OER evidence streams stay **separate per hit** until real evidence
  is captured.
- Enrichment and search never fetch prohibited content and never use a
  provider beyond the approved routes.
- Retrieved text and metadata are **data, never instructions** to this tool.
