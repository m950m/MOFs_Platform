"""Attributed evidence assertions (issue #7).

Each assertion carries its own provenance: linked source, exact evidence
location (or explicit unknown), extraction author/method, epistemic type, and
its own review state. Recording never marks an assertion reviewed and never
turns an interpretation into a direct measurement. Conflicts keep both claims
side by side — no averaging, no overwriting. Claim text is source data, never
instructions to this tool.
"""

import json
import sqlite3
from dataclasses import dataclass

CLAIM_TYPES = ("preparation", "composition", "property", "application", "other")

EPISTEMIC_TYPES = (
    "directly_reported",
    "author_interpretation",
    "tool_inference",
    "user_judgment",
    "unknown",
)

EPISTEMIC_LABELS = {
    "directly_reported": "directly reported (stated/measured in the source)",
    "author_interpretation": "author interpretation (source's own reading)",
    "tool_inference": "tool inference (this tool suggested it — needs review)",
    "user_judgment": "user judgment (researcher-entered, not from the source)",
    "unknown": "`unknown` — epistemic type not yet determined",
}

REVIEW_STATES = ("needs_verification", "in_review", "reviewed", "conflicted")

REVIEW_LABELS = {
    "needs_verification": "`needs verification`",
    "in_review": "`in review`",
    "reviewed": "`reviewed`",
    "conflicted": "`conflicted`",
}


class EvidenceValidationError(ValueError):
    """The proposed assertion cannot be recorded."""


class EvidencePersistenceError(RuntimeError):
    """Saving failed; previously saved assertions are unchanged."""


@dataclass(frozen=True)
class Assertion:
    id: int
    source_id: int
    claim_type: str
    claim_text: str
    evidence_location: str | None
    extraction_author: str | None
    epistemic_type: str
    review_state: str
    conflicts_with: int | None
    created_at: str | None = None


def _row_to_assertion(row: sqlite3.Row) -> Assertion:
    return Assertion(
        id=row["id"],
        source_id=row["source_id"],
        claim_type=row["claim_type"],
        claim_text=row["claim_text"],
        evidence_location=row["evidence_location"],
        extraction_author=row["extraction_author"],
        epistemic_type=row["epistemic_type"],
        review_state=row["review_state"],
        conflicts_with=row["conflicts_with"],
        created_at=row["created_at"],
    )


def _row_to_dict(row: sqlite3.Row) -> dict:
    keys = (
        "id", "source_id", "claim_type", "claim_text", "evidence_location",
        "extraction_author", "epistemic_type", "review_state", "conflicts_with",
        "created_at",
    )
    return {key: row[key] for key in keys}


def _opt(value: str | None) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def record_assertion(
    conn: sqlite3.Connection,
    *,
    source_id: int,
    claim_type: str,
    claim_text: str,
    evidence_location: str | None = None,
    extraction_author: str | None = None,
    epistemic_type: str = "unknown",
    conflicts_with: int | None = None,
) -> Assertion:
    """Record one attributed assertion. Missing location/author stay unknown —
    a partial but valid assertion is never rejected or completed by guessing."""
    source = conn.execute("SELECT id FROM source WHERE id = ?", (source_id,)).fetchone()
    if source is None:
        raise EvidenceValidationError(
            "Select a saved reference first — assertions attach to a source."
        )
    clean_type = _opt(claim_type)
    if clean_type not in CLAIM_TYPES:
        raise EvidenceValidationError(
            f"Claim type must be one of {CLAIM_TYPES!r} — got {claim_type!r}."
        )
    clean_text = _opt(claim_text)
    if not clean_text:
        raise EvidenceValidationError(
            "Claim text is empty — enter the claim/value exactly as reported or judged."
        )
    if epistemic_type not in EPISTEMIC_TYPES:
        raise EvidenceValidationError(
            f"Epistemic type must be one of {EPISTEMIC_TYPES!r} — got {epistemic_type!r}."
        )
    clean_location = _opt(evidence_location)  # may stay unknown — never guessed
    clean_author = _opt(extraction_author)  # may stay unknown
    try:
        pair_id = None
        if conflicts_with is not None:
            pair = conn.execute(
                "SELECT id FROM assertion WHERE id = ?", (conflicts_with,)
            ).fetchone()
            if pair is None:
                raise EvidenceValidationError(
                    f"Conflicting assertion #{conflicts_with} does not exist."
                )
            pair_id = int(pair["id"])
        with conn:
            cur = conn.execute(
                "INSERT INTO assertion (source_id, claim_type, claim_text, "
                "evidence_location, extraction_author, epistemic_type, review_state, "
                "conflicts_with) VALUES (?, ?, ?, ?, ?, ?, 'needs_verification', ?)",
                (source_id, clean_type, clean_text, clean_location, clean_author,
                 epistemic_type, pair_id),
            )
            new_id = int(cur.lastrowid)
            saved = conn.execute(
                "SELECT * FROM assertion WHERE id = ?", (new_id,)
            ).fetchone()
            conn.execute(
                "INSERT INTO assertion_event (action, assertion_id, previous_json, "
                "updated_json) VALUES ('recorded', ?, NULL, ?)",
                (new_id, json.dumps(_row_to_dict(saved))),
            )
            if pair_id is not None:
                # Both sides of a recorded conflict stay visible, flagged,
                # mutually linked, and unaveraged.
                conn.execute(
                    "UPDATE assertion SET review_state = 'conflicted' WHERE id IN (?, ?)",
                    (new_id, pair_id),
                )
                conn.execute(
                    "UPDATE assertion SET conflicts_with = ? WHERE id = ?",
                    (new_id, pair_id),
                )
                saved = conn.execute(
                    "SELECT * FROM assertion WHERE id = ?", (new_id,)
                ).fetchone()
                conn.execute(
                    "INSERT INTO assertion_event (action, assertion_id, previous_json, "
                    "updated_json) VALUES ('flagged_conflict', ?, ?, ?)",
                    (new_id, json.dumps(_row_to_dict(saved)), json.dumps(_row_to_dict(saved))),
                )
    except EvidenceValidationError:
        raise
    except sqlite3.Error as exc:
        raise EvidencePersistenceError(
            f"Saving failed; previously saved assertions are unchanged. ({exc})"
        ) from exc
    return _row_to_assertion(saved)


def list_assertions(
    conn: sqlite3.Connection, source_id: int | None = None
) -> list[Assertion]:
    if source_id is None:
        rows = conn.execute("SELECT * FROM assertion ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM assertion WHERE source_id = ? ORDER BY id DESC", (source_id,)
        ).fetchall()
    return [_row_to_assertion(row) for row in rows]


def get_assertion(conn: sqlite3.Connection, assertion_id: int) -> Assertion | None:
    row = conn.execute(
        "SELECT * FROM assertion WHERE id = ?", (assertion_id,)
    ).fetchone()
    return None if row is None else _row_to_assertion(row)


def count_events(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM assertion_event").fetchone()[0])
