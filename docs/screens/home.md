# Home

The Home screen is the app's status line. It answers one question honestly:
**what is recorded right now, and what is not.**

## What enters

Nothing — you do not input anything here. Home reads what the other screens
recorded.

## What comes out

- **Status line:**
    - `Empty / ready` — a fresh database: no question, no laboratory profile,
      no sources yet. The screen lists exactly what is missing.
    - `Ready — data recorded` — with a summary of what exists: the saved
      question, how many laboratory profile entries, how many reference leads.
- **Saved question** (if any), quoted verbatim.
- **Latest active-search outcome** for each provider (Crossref and OpenAlex):
  `not yet searched`, or the run outcome with hit count, timestamp, and run
  number.

## Honest markers

- The word `Empty / ready` proves only that the entry point works — the screen
  itself says so: *startup validates the entry point only. It does not
  validate provider access, chemistry, or any scientific claim.*
- Search outcomes are shown exactly as recorded — a failed run is not hidden.
