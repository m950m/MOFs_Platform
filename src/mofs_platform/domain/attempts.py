"""Route-attempt audit log (issue #9).

Every attempt against the selected source route is recorded with its outcome
and the contract-permitted next step. Failures are never shown as successes,
a later success never relabels an earlier failure, and no automatic retry
exists — retrying is always a manual researcher action.
"""

import sqlite3
from dataclasses import dataclass

PROVIDER_CROSSREF = "crossref"
PROVIDER_AI = "zai-glm"

# Reserved vocabulary (migration CHECK constraint, not yet produced):
#   outcome 'restricted' and kind 'manual_capture' land with issue #16
#   (active search) and #19 (contributor packages) respectively.
NEXT_STEPS = {
    "success": "Metadata filled where missing; the reference remains a lead.",
    "no_hit": "Verify the DOI spelling or capture the reference manually — "
              "absence of a provider record is not evidence of novelty.",
    "rate_limited": "Wait and retry later (Crossref polite-pool limits apply).",
    "timeout": "Retry manually when the network is stable.",
    "offline": "Restore connectivity; capture the reference manually meanwhile.",
    "bad_response": "Retry later; nothing was changed.",
    "bad_input": "Correct the DOI and try again.",
    "restricted": "Use the permitted access route shown with the reference.",
    "no_key": "Configure the session API key first — nothing was sent.",
}


@dataclass(frozen=True)
class RouteAttempt:
    id: int
    provider: str
    target: str
    attempt_kind: str
    outcome: str
    next_step: str | None
    note: str | None
    created_at: str


def record_attempt(
    conn: sqlite3.Connection,
    *,
    provider: str,
    target: str,
    attempt_kind: str,
    outcome: str,
    note: str | None = None,
) -> RouteAttempt:
    if outcome not in NEXT_STEPS:
        raise ValueError(f"Unknown attempt outcome {outcome!r}.")
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO route_attempt (provider, target, attempt_kind, outcome, "
                "next_step, note) VALUES (?, ?, ?, ?, ?, ?)",
                (provider, target.strip(), attempt_kind, outcome,
                 NEXT_STEPS[outcome], note.strip() if isinstance(note, str) and note.strip() else None),
            )
            new_id = int(cur.lastrowid)
    except sqlite3.Error as exc:
        raise RuntimeError(f"Recording the attempt failed. ({exc})") from exc
    row = conn.execute("SELECT * FROM route_attempt WHERE id = ?", (new_id,)).fetchone()
    return _row_to_attempt(row)


def _row_to_attempt(row: sqlite3.Row) -> RouteAttempt:
    return RouteAttempt(
        id=row["id"], provider=row["provider"], target=row["target"],
        attempt_kind=row["attempt_kind"], outcome=row["outcome"],
        next_step=row["next_step"], note=row["note"], created_at=row["created_at"],
    )


def list_attempts(
    conn: sqlite3.Connection, provider: str | None = None, limit: int = 50
) -> list[RouteAttempt]:
    if provider is None:
        rows = conn.execute(
            "SELECT * FROM route_attempt ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM route_attempt WHERE provider = ? ORDER BY id DESC LIMIT ?",
            (provider, limit),
        ).fetchall()
    return [_row_to_attempt(row) for row in rows]


def count_attempts(conn: sqlite3.Connection, outcome: str | None = None) -> int:
    if outcome is None:
        row = conn.execute("SELECT COUNT(*) FROM route_attempt").fetchone()
    else:
        row = conn.execute(
            "SELECT COUNT(*) FROM route_attempt WHERE outcome = ?", (outcome,)
        ).fetchone()
    return int(row[0])
