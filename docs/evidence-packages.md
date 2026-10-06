# Evidence packages

Exchange evidence with a collaborator **offline, as a file** — no server, no
upload endpoint, no cloud. This page explains what packages are for and how
the exchange behaves; the full format specification and the contributor rules
live in [`CONTRIBUTING.md`](https://github.com/m950m/MOFs_Platform/blob/main/CONTRIBUTING.md)
(the tool's [Sources](screens/sources.md) screen links the same rules — this
page deliberately does not duplicate them).

## The idea

You select the sources you want to share; the tool exports them **and their
dependents** (samples, observations, assertions, compound links — whatever
hangs off those sources) as one JSON file in the `package-schema-v1` format.
Your colleague imports the file from their local disk. That is the whole
transport: a file you hand over yourself.

## What export does

- Packages your **selected sources + their dependents** into one attributed
  JSON file you download.
- The package carries each record's provenance: contributor, entry method,
  review state, evidence locations.

## What import does

- **Validates strictly.** Schema drift, missing provenance, review-state
  overwrites, and merge attempts are all rejected — and the rejection lists
  **every** reason, not just the first.
- **Enters everything as `needs_verification`, attributed to the package's
  contributor.** Nothing arrives pre-approved, and nothing is auto-promoted.
- **Keeps imported rows as separate records** — imported claims coexist with
  yours; they are never merged into your records. Identity questions between
  imported and local records belong to the
  [Samples & identity](screens/samples-identity.md) relations.

## Why it behaves this way

An evidence package is a *claim delivery*, not a truth transfer. The
reviewer on the receiving side is you: after import, records sit at
`needs verification` until someone inspects the cited locations and reviews
them under the [Review](screens/review.md) threshold. Attribution travels
with every record, so credit and responsibility stay attached to the data.
