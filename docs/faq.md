# FAQ — the honesty rules, as questions

The tool's behavior follows a small set of honesty rules. Here they are as the
questions you will actually ask.

## Does "no result found" mean my material is unstudied or novel?

**No.** A search that finds nothing (`no_hit`) is a statement about *one
provider, one query, one date, one page of results* — nothing more. It is not
evidence of novelty, of absence of prior use, or of suitability (or
unsuitability) for a reaction. The tool never lets a no-hit become a claim.

## A database has an entry for this MOF — doesn't that mean it was made and tested?

**No.** A database record is **metadata**. Metadata alone never proves that a
sample was experimentally prepared, and it never proves that performance was
measured. That is why every hit and reference in the tool is a
*lead* (`needs verification`) until a human inspects the actual source and
records attributed evidence.

## Two sources use the same name (or formula, DOI, MOFid, CIF) — same sample?

**Not necessarily — and the tool will not assume it.** A shared name, formula,
DOI, MOFid, or CIF alone never proves the same *tested sample*. Preparation
differences, added particles, and different activation make distinct samples.
If you judge two records to describe the same reported sample, record the
relation with its reason and evidence location — the relation **links** the
records, it never merges them. There is no automatic cross-source merge.

## The authors say the material "transformed into phase X" during the reaction — is the sample now X?

The tool keeps them separate on purpose: the **prepared sample** (as
synthesized and pretreated) and the **operating state** (what it was during or
after the reaction) are distinct records. An author's interpretation of the
active phase is recorded with its own epistemic type — it never silently
renames the sample you tested or read about.

## Can the tool rank candidates and tell me which is best?

**No — by design.** Hit order is provider retrieval order, not a ranking;
candidate cards show *why a candidate appeared* and what evidence exists; the
comparison view displays values side by side with provenance. Missing
condition fields are shown as gaps, never interpolated. The scientific
conclusion — and the choice of material — stays with you.

## It marked my assertion `needs verification`. Why can't I just say it's confirmed?

Because *reviewed* is an evidentiary state, not a feeling. Marking a claim
`reviewed` requires the reviewer's name, the **exact supporting source
location** you personally inspected, and a recorded reason. That is the
review threshold, and it is what makes a *reviewed* label worth trusting
later. One reviewed claim also never makes the whole material "reviewed" —
review applies to a particular assertion, not to a material.

## What do `unknown` and the other markers mean?

| Marker | Meaning |
|---|---|
| `unknown` | Nobody has recorded this — the tool will not invent a value. |
| `needs verification` | A lead recorded from metadata or unverified input; human inspection still required. |
| `in review` | A human is actively checking this claim. |
| `reviewed` | A named reviewer inspected an exact source location and approved the claim. |
| `conflicted` | Two recorded claims disagree — both stay visible until you resolve the conflict explicitly. |
| `no_hit` | This search (provider/query/date) found nothing — proves nothing about the material. |
| `not yet searched` | No search has been run for this reaction/provider yet. |

## Where does my data go?

Nowhere. The evidence store is one local file (`data/platform.db`) on your
machine; there is no server and no account. Outbound network happens only when
you trigger a Crossref/OpenAlex search or enrichment, or (optionally) an AI
question-refinement call — for which you supply the key per session and only
the question's own saved fields are sent. Publishing the *documentation site*
you are reading is static Markdown; it contains no evidence data.

## Can my collaborator send me their records?

Yes — as an **evidence package**: one attributed JSON file, exported from the
Sources screen and imported there. Import validates strictly, lists every
rejection reason, enters everything as `needs_verification` attributed to the
package's contributor, and keeps imported rows as separate records. See
[Evidence packages](evidence-packages.md).

## The tool suggested something — can I trust it?

Suggestions (AI wording refinements, mechanical observations) are labeled
`tool inference` and are **review suggestions only** — nothing changes until
you apply and save it yourself. Retrieved paper text is treated as *data*
about the paper, never as instructions to the tool.

## Can I run it as a shared web server for my group?

Not in this version — local-first is a deliberate design decision, and public
multi-user hosting (which would need authentication and change the evidence
model) is a deferred decision, not a hidden roadmap item.
