# MOFs_Platform — research with the evidence attached

MOFs_Platform is a **local desktop tool** for researchers working on
MOF-related electrochemistry (HER, OER, and similar reactions). It helps you
answer one question honestly:

> *Which materials have documented experimental preparation, have any of them
> been tested for my reaction, and **how do I know**?*

Every claim in the tool keeps its source. Every measurement stays tied to the
exact reported sample that was tested — not to a generic material name. And
when something is unknown, the tool says **unknown** instead of guessing.

## What the tool does

- **Ask a research question** and record what it means: the reaction, allowed
  material classes, hard requirements, and your laboratory's capabilities.
- **Search real literature databases** (Crossref, OpenAlex) for preparation
  reports and reaction-testing evidence — only when you click Search.
- **Capture and review evidence** with a source for every claim, keeping what
  was *directly reported* separate from what an author *interpreted* or the
  tool *inferred*.
- **Preserve tested-sample identity**: the parent framework, the prepared
  sample, its modifications, and the operating state during the reaction are
  related but never collapsed into one thing.
- **Compare your laboratory profile** against what a candidate's preparation
  and testing would require — possible now, needs future capabilities, or
  unknown, each with reasons.

## Honest boundaries

These limits are deliberate — they are what makes the tool trustworthy:

- **It never ranks or recommends materials.** It organizes evidence and shows
  shortfalls; *you* write the scientific conclusion and pick the materials.
- **Metadata is not measurement.** A database hit, a title, or a DOI never
  proves that a sample was prepared or that performance was measured.
- **"No result found" proves nothing.** It does not mean a material is novel,
  unstudied, or unsuitable — only that this search, on this date, found
  nothing within its documented scope.
- **Conflicting claims stay side by side.** Sources that disagree are both
  retained — never averaged, merged, or overwritten.
- **No server, no cloud.** Your evidence store lives in one local file
  (`data/platform.db`) on your machine. The network is used only for the
  searches you trigger, and the AI question-refinement assistant is optional
  with a key you supply per session (never stored).

## Where to go next

- **New here?** Follow [Getting started](getting-started.md) from install to
  your first review.
- **Want to know what a screen does?** Browse the [Screens](screens/index.md)
  reference — one page per screen, in the order the app shows them.
- **Using it daily?** The [Workflows](workflows.md) page walks the full loop:
  ask → search → capture → record → review → assess fit → compare streams.
- **Contributing a colleague's data?** Read [Evidence packages](evidence-packages.md).
- **Curious how the pieces fit?** See [How it fits together](internals.md).
- **Skeptical?** Good. The [FAQ](faq.md) states the honesty rules as plain
  questions.
