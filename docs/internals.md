# How it fits together

A look under the hood for contributors and the curious: the layers, the data
model, the review lifecycle, and the identity comparison logic.

**Source of record:** these diagrams live in
[`_docs/proposals/diagrams.md`](https://github.com/m950m/MOFs_Platform/blob/main/_docs/proposals/diagrams.md)
in the repository; that file wins if the copies below ever drift. The four
diagrams shown here describe behavior the tool implements today. The proposal
file also contains a first-slice sequence diagram and a task-roadmap diagram —
historical proposal artifacts (issues #3–#13 are all delivered), so they are
not reproduced here to avoid presenting completed work as future plans.

## System context and layering

The app is a **local process**: a Streamlit UI talks to a pure-Python domain
core, which is the only writer of the SQLite evidence file. The single
external route is the Crossref REST API — a metadata lead that never verifies
a sample. In tests, recorded fixtures replace the network entirely.

```mermaid
flowchart TB
    subgraph OWNER["Mohammed (owner)"]
        DEC["Decision register\n(D1–D8, plan §5 template)"]
    end

    subgraph USER["Researcher (single local user)"]
        UI["Streamlit local app\n(pages: question · sources ·\nevidence · review · lab-fit)"]
    end

    subgraph CORE["mofs_platform — local process"]
        subgraph DOMAIN["domain/ — pure Python, no UI/network imports"]
            ID["identity.py\nscoped comparison + merge policy"]
            RV["review.py\nstate transitions + ReviewEvent log"]
            EV["evidence.py\nassertions + epistemic types"]
            LF["labfit.py\ncurrent/future/unknown + reasons"]
            MD["models.py\nfrozen dataclasses"]
        end
        subgraph ADAPTERS["adapters"]
            UIA["ui/ cards + pages"]
            SRC["sources/crossref.py\npolite client · typed failures"]
            SMK["smoke.py (headless)"]
        end
        DB[("SQLite file\nschema_version + migrations\nWAL · foreign_keys=ON")]
        FX["sources/fixtures/\nrecorded JSON — tests never go live"]
    end

    subgraph EXT["External (only permitted route)"]
        CR["Crossref REST\n/works/{doi}?mailto=\nmetadata lead — never verifies a sample"]
    end

    UIA --> MD
    UIA --> RV
    SRC --> MD
    SRC -->|"permitted fields / typed failure"| CR
    DOMAIN --> DB
    FX -.->|"replaces network in tests"| SRC
    DEC -.->|"gates issue readiness"| CORE
    UI --- UIA
```

**Reading rules:** arrows from `domain/` never point into `ui/`, `sources/`,
or Streamlit — the domain core is testable without a browser or network.
`session_state` is never evidence storage; all evidence flows through
`domain/` into SQLite.

## Core data model (the identity contract, as schema)

```mermaid
erDiagram
    SOURCE {
        text doi "UNIQUE or null"
        text url
        text title
        text license_url
        text access_date
        text entry_method "manual | crossref"
    }
    FRAMEWORK {
        text name
        text aliases
        text metal_node
        text linker
        text cif_ref
        text structure_status "experimental | computational | unknown"
    }
    SAMPLE {
        text designation
        text constituents
        text prep_history
        text activation
        text basis "experimental | computational | hypothetical"
    }
    OPERATING_STATE {
        text stage "before | during | after | unknown"
        text phase_assignment
        text epistemic_type
    }
    OBSERVATION {
        text reaction "HER | OER | other"
        real value "null = unknown"
        text unit
        text electrolyte
        text reference_convention
        text loading
        text duration
    }
    ASSERTION {
        text subject_type
        text relation
        text object_type
        text evidence_location "or explicit unknown"
        text epistemic_type "directly_reported | author_interpretation | tool_inference | user_judgment | unknown"
        text review_state "needs_verification | in_review | reviewed | conflicted"
    }
    REVIEW_EVENT {
        text actor
        text verdict "confirm | correct | conflict"
        text old_value
        text new_value
        text reason
    }
    SEARCH_RUN {
        text provider
        text query
        text outcome "no_hit | rate_limited | timeout | offline | restricted | contradictory | results"
    }
    QUESTION {
        text text
        int version "append-only"
    }
    LAB_CAPABILITY {
        text name
        text status "current | future | unknown"
        text reconfirmed_by "null until owner reconfirms"
    }
    MODIFICATION_HYPOTHESIS {
        text change
        text rationale
        text label "invariant: untested hypothesis"
    }

    SOURCE ||--o{ SAMPLE : "designates"
    FRAMEWORK ||--o{ SAMPLE : "parent of"
    SAMPLE ||--o{ OPERATING_STATE : "states of"
    SAMPLE ||--o{ OBSERVATION : "tested by"
    SOURCE ||--o{ OBSERVATION : "reported in"
    SOURCE ||--o{ ASSERTION : "cited by"
    ASSERTION ||--o{ REVIEW_EVENT : "audited by"
    SAMPLE ||--o{ MODIFICATION_HYPOTHESIS : "proposed modification of"
    SAMPLE ||--o{ SAMPLE : "derived/composite lineage (directional, never merged)"
```

**Identity invariants encoded:** an observation points at exactly one
`SAMPLE` (never directly at a framework or an operating state); lineage
between samples is a directional *link*, never a merge; assertions carry
their own review state, so a status never spreads automatically to a whole
material.

## Assertion review lifecycle

```mermaid
stateDiagram-v2
    [*] --> needs_verification : assertion recorded (metadata-only / location missing / source uninspected)
    needs_verification --> in_review : human begins inspecting cited evidence
    in_review --> reviewed : ReviewEvent(confirm) — D4: named human inspected exact location
    in_review --> needs_verification : inspection incomplete (evidence still missing)
    needs_verification --> conflicted : contradicting assertion retained
    in_review --> conflicted : contradicting assertion retained
    reviewed --> conflicted : later contradicting assertion
    conflicted --> in_review : re-review requested\n(both claims stay visible)
    reviewed --> [*]
    note right of conflicted
        Terminal-preserve: both claims
        and their provenance are kept;
        nothing is overwritten or averaged.
    end note
    note right of reviewed
        Applies to THIS assertion only,
        never automatically to the
        whole material (plan §3).
    end note
```

## Identity comparison decision flow

The comparison logic behind
[Samples & identity](screens/samples-identity.md): **no path reaches "merge"
except the human-confirmed within-source, explicit-designation path** — a
shared name, formula, DOI, MOFid, or CIF alone can never arrive there.

```mermaid
flowchart TD
    Q["compare(record A, record B, level)"] --> L{"Level?
    framework | sample | state"}
    L -->|"sample"| CS{"Same source AND explicit
    same-sample designation
    confirmed by human (D5)?"}
    CS -->|yes| RS["same reported sample
    (designation only — not
    physical batch identity)"]
    CS -->|no| CP{"Cited shared
    parent framework?"}
    CP -->|yes| RP["same parent framework
    + derived/composite if cited
    samples NEVER merge"]
    CP -->|no| CD{"Cited discriminating
    difference (linker /
    activation / constituents)?"}
    CD -->|yes| RD["different (at this level)"]
    CD -->|no| RU["unresolved — no merge,
    list missing evidence,
    request review"]
    L -->|"framework"| CF{"Cited structural
    evidence (CIF, linker+node)
    or explicit parent designation?"}
    CF -->|yes| RF["same parent framework"]
    CF -->|no| RU
    RS --> M["merge: within-source duplicates only,
    after review — observations preserved"]
    RP --> NM["no merge"]
    RD --> NM
    RU --> NM
    RF --> NM2["no sample merge; parent link may be shared"]
```
