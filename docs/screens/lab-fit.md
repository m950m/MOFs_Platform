# Lab fit

Two things live here: the **fit assessment** (does a candidate's documented
requirements fit your recorded laboratory profile?) and the **number streams**
(laboratory vs industry reference — separate, never merged).

## Number streams

- **What enters:** number rows, each tagged `laboratory` or
  `industry_reference`, with label, value, unit, reaction (HER / OER /
  other), conditions note, and provenance — a source reference id or citation
  (required if no id) and year. The reference table starts **empty**: the
  initial industry reference set is your decision (e.g. DOE electrolyzer
  targets); nothing is seeded from memory.
- **What comes out:** the two stream lists and a **comparison view** —
  display only: laboratory results paired with industry references for the
  same reaction, side by side, each with its conditions and source.
- **Corrections:** attributed and reasoned; the old values stay in history.
  Blank means keep; the stream and the source pointer are not correctable
  here.
- **Honest markers:** laboratory-measured numbers and industry/reference
  numbers are **separate streams — never merged into one verdict**. A
  permanent caveat is rendered with the comparison; conditions differences
  are displayed, never hidden. No reference row for a reaction is shown as
  `unknown` — nothing is inferred from similar values.

## Fit assessment

- **What enters:** a candidate / tested sample (from
  [Samples & identity](samples-identity.md)), the confirmed
  [Laboratory profile](laboratory-profile.md), and the sample's sourced
  requirement assertions.
- **What comes out:** one of three recorded outcomes, with per-requirement
  reasons and evidence locations:
    - **possible with current capabilities**
    - **requires future capabilities**
    - **`unknown`**
- **Honest markers:**
    - Assessments compare *documented requirements* with the *documented
      profile* — no synthesis success, no catalytic performance, and no
      universal suitability is ever claimed.
    - No historical restriction is applied unless confirmed in the current
      profile.
    - If the question, profile, or requirement assertions changed after an
      assessment was recorded, it is marked **outdated**: the old result
      cannot appear current — re-run the assessment from the current recorded
      basis.
