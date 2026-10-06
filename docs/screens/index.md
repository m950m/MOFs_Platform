# Screens

The app has nine screens, listed in the sidebar in the order you usually meet
them. Each page below answers three questions: **what enters** the screen,
**what comes out** of it, and **what the honest markers mean** when they
appear.

| Screen | One-line role |
|---|---|
| [Home](home.md) | Status line: what is recorded, what is not, latest search outcomes. |
| [Research question](research-question.md) | Record what you are looking for; the question drives searches and fit checks. |
| [Laboratory profile](laboratory-profile.md) | What your lab can do now, plans to do, cannot do, or unknown. |
| [Sources](sources.md) | Capture references, run searches, import structures, exchange packages. |
| [Evidence](evidence.md) | Record attributed assertions — the claims behind every candidate. |
| [Samples & identity](samples-identity.md) | The reported tested samples, their observations, and their relations. |
| [Candidates](candidates.md) | Why a candidate appeared, and follow every claim to its evidence. |
| [Review](review.md) | Correct and review claims; resolve conflicts — all attributed. |
| [Lab fit](lab-fit.md) | Does a candidate's documented requirements fit your recorded profile? Plus the number streams. |

## The markers you will see

These markers appear across all screens — they are the tool's honesty
vocabulary:

- **`unknown`** — nothing was recorded; the tool invents no value.
- **`needs verification`** — a lead (from metadata or unverified input);
  human inspection still required. Every search hit starts here.
- **`in review` / `reviewed` / `conflicted`** — review states of individual
  assertions and relations; see [Review](review.md).
- **`no_hit`** — this search found nothing. It is a statement about the
  provider, query, and date — it does **not** mean the material is unstudied,
  novel, or unsuitable.
- **`not yet searched`** — no search has been run yet for this provider.

Epistemic types label *where a claim came from*: `directly reported`,
`author interpretation`, `tool inference`, `user judgment`, or `unknown`.
Review suggestions from the tool are always `tool inference` and are never
applied on their own.
