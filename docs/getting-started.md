# Getting started

From zero to your first reviewed piece of evidence — in five steps. Everything
runs on your machine; nothing is uploaded anywhere.

!!! note "What you need"

    Python 3.11 or newer. No API keys are required for searching — only for
    the optional AI question-refinement assistant.

## 1. Install and start the app

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/streamlit run src/mofs_platform/app.py
```

Your browser opens the app. All data is stored in one local file,
`data/platform.db` (you can move it with the `MOFS_DB_PATH` environment
variable). The sidebar lists the screens in the order you will use them.

## 2. Record your research question

Open **Research question** in the sidebar and write what you are looking for:
the reaction (for example HER or OER), the allowed material classes (MOF, ZIF,
composite, derived …), the relevant conditions, and — importantly — what
"improvement" means *for this question*.

- **Hard requirements** must be met by a candidate; **preferences** are nice to
  have. Keep them separate — the tool does.
- Fields you leave blank stay `unknown`. The tool never guesses a value.
- The optional AI assistant (Z.ai GLM) can suggest a clearer wording. It only
  works if you enable it for the session and paste a key; suggestions are
  labeled `tool inference` and are never applied until you press *Apply* and
  then *Save* yourself.

## 3. Run your first search

Open **Sources**. Your saved question wording becomes the default search query,
verbatim — you can edit it, and the exact text sent is what gets recorded.
Pick a provider (Crossref or OpenAlex) and press **Run search**.

Honest behavior to expect:

- Every hit is a **lead** (`needs_verification`) — never a verified candidate.
- One run fetches a single polite page (8 hits) to respect provider rate
  limits; run again with edited terms to widen the net.
- A run that finds nothing records `no_hit` — that is a statement about *this
  provider and query on this date*, **not** proof that a material is unstudied.
- Failed runs stay failed in the log; every retry is a manual action.

## 4. Capture your first reference and record evidence

In **Sources**, capture the reference: paste the DOI/URL/title yourself, or
press **Capture as reference** on a hit you want to keep. Add *what you
actually inspected* (metadata only? abstract? full text?) — that label stays
attached.

Then open **Evidence** and record an **assertion**: the claim exactly as
reported, the source it came from, the exact location in the source (or an
explicit `unknown`), who extracted it, and the **epistemic type** — was it
*directly reported*, an *author interpretation*, a *tool inference*, or your
own *user judgment*? Recording never marks anything reviewed.

## 5. Record the sample and review

Open **Samples & identity** and record the **reported tested sample** the claim
is about: designation, parent framework, linker, metal node, additions,
activation — exactly as the source reports them. Measurements (**observations**)
attach only to that sample, with value, unit, conditions, and evidence location.

Finally open **Review**. Every assertion and relation starts as
`needs verification`. When *you* have inspected the exact source location, mark
it `reviewed` — the tool records who reviewed it, where, and why (the review
threshold). Conflicting claims can be marked as conflicts and both stay
visible; nothing is ever averaged away.

That is the whole loop. The [Screens](screens/index.md) reference explains each
screen in depth, and [Workflows](workflows.md) shows how the loop repeats in
daily use.
