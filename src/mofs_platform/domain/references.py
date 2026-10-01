"""Reference capture and storage (issue #6).

References are leads linked to the saved research question. Manual entry is
attributed; Crossref enrichment (D2 contract) fills bibliographic metadata
only and never raises what was inspected. Re-captures append events so every
capture context remains visible; a shared DOI never implies sample equivalence.
"""

import json
import sqlite3
from dataclasses import dataclass

from mofs_platform.sources import crossref

INSPECTED_LEVELS = ("unknown", "metadata", "abstract", "full_text", "user_passage")

_LEVEL_LABELS = {
    "unknown": "`unknown` — inspection level not recorded (needs verification)",
    "metadata": "metadata only (needs verification)",
    "abstract": "abstract inspected",
    "full_text": "full text inspected",
    "user_passage": "user-supplied passage (attributed)",
}


class ReferenceValidationError(ValueError):
    """The proposed reference cannot be saved."""


class ReferencePersistenceError(RuntimeError):
    """Saving failed; the previously saved references are unchanged."""


@dataclass(frozen=True)
class Reference:
    id: int
    question_id: int
    doi: str | None
    url: str | None
    title: str | None
    container: str | None
    issued_year: str | None
    license_url: str | None
    entry_method: str
    supplied_input: str | None
    retrieval_date: str
    inspected_level: str
    contributor: str | None
    rights_note: str | None
    indexed_at: str | None = None


def _row_to_ref(row: sqlite3.Row) -> Reference:
    return Reference(
        id=row["id"],
        question_id=row["question_id"],
        doi=row["doi"],
        url=row["url"],
        title=row["title"],
        container=row["container"],
        issued_year=row["issued_year"],
        license_url=row["license_url"],
        entry_method=row["entry_method"],
        supplied_input=row["supplied_input"],
        retrieval_date=row["retrieval_date"],
        inspected_level=row["inspected_level"],
        contributor=row["contributor"],
        rights_note=row["rights_note"],
        indexed_at=row["indexed_at"],
    )


def _row_to_dict(row: sqlite3.Row) -> dict:
    keys = (
        "id", "question_id", "doi", "url", "title", "container", "issued_year",
        "license_url", "entry_method", "supplied_input", "retrieval_date",
        "inspected_level", "contributor", "rights_note", "indexed_at",
    )
    return {key: row[key] for key in keys}


def _opt(value: str | None) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _require_question(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT id FROM question WHERE id = 1").fetchone()
    if row is None:
        raise ReferenceValidationError(
            "Save a research question first — references attach to it."
        )
    return int(row["id"])


def add_manual_reference(
    conn: sqlite3.Connection,
    *,
    doi: str | None = None,
    url: str | None = None,
    title: str | None = None,
    supplied_input: str | None = None,
    contributor: str | None = None,
    inspected_level: str = "unknown",
    rights_note: str | None = None,
) -> Reference:
    """Capture a reference by manual attribution; re-capturing the same DOI
    updates the row and appends an event so both capture contexts remain."""
    question_id = _require_question(conn)
    clean_doi = _opt(doi)
    clean_url = _opt(url)
    clean_title = _opt(title)
    clean_input = _opt(supplied_input)
    clean_contributor = _opt(contributor)
    clean_rights = _opt(rights_note)
    if inspected_level not in INSPECTED_LEVELS:
        raise ReferenceValidationError(
            f"Inspected level must be one of {INSPECTED_LEVELS!r} — got {inspected_level!r}."
        )
    if not (clean_doi or clean_url or clean_title or clean_input):
        raise ReferenceValidationError(
            "Enter at least one pointer: a DOI, a URL, a title/citation, or a supplied passage."
        )
    try:
        existing = None
        if clean_doi:
            existing = conn.execute(
                "SELECT * FROM source WHERE lower(doi) = lower(?)", (clean_doi,)
            ).fetchone()
        with conn:
            if existing is not None:
                conn.execute(
                    "UPDATE source SET url = COALESCE(?, url), title = COALESCE(?, title), "
                    "supplied_input = COALESCE(?, supplied_input), contributor = COALESCE(?, contributor), "
                    "inspected_level = CASE WHEN ? = 'unknown' THEN inspected_level "
                    "ELSE ? END, rights_note = COALESCE(?, rights_note), "
                    "retrieval_date = CURRENT_TIMESTAMP WHERE id = ?",
                    (clean_url, clean_title, clean_input, clean_contributor,
                     inspected_level, inspected_level, clean_rights, existing["id"]),
                )
                ref_id = int(existing["id"])
                action = "captured"
            else:
                cur = conn.execute(
                    "INSERT INTO source (question_id, doi, url, title, supplied_input, "
                    "entry_method, inspected_level, contributor, rights_note) "
                    "VALUES (?, ?, ?, ?, ?, 'manual', ?, ?, ?)",
                    (question_id, clean_doi, clean_url, clean_title, clean_input,
                     inspected_level, clean_contributor, clean_rights),
                )
                ref_id = int(cur.lastrowid)
                action = "captured"
            saved = conn.execute("SELECT * FROM source WHERE id = ?", (ref_id,)).fetchone()
            conn.execute(
                "INSERT INTO source_capture_event "
                "(action, source_id, previous_json, updated_json) VALUES (?, ?, ?, ?)",
                (action, ref_id,
                 json.dumps(_row_to_dict(existing)) if existing is not None else None,
                 json.dumps(_row_to_dict(saved))),
            )
    except ReferenceValidationError:
        raise
    except sqlite3.Error as exc:
        raise ReferencePersistenceError(
            f"Saving failed; the previously saved references are unchanged. ({exc})"
        ) from exc
    return _row_to_ref(saved)


def enrich_with_crossref(
    conn: sqlite3.Connection, reference_id: int, mailto: str | None
) -> tuple[Reference | None, crossref.CrossrefFailure | None]:
    """Fill missing bibliographic fields from Crossref; fill-only, never erase.
    On typed failure the reference row is left untouched."""
    existing = conn.execute(
        "SELECT * FROM source WHERE id = ?", (reference_id,)
    ).fetchone()
    if existing is None:
        raise ReferenceValidationError(f"Reference #{reference_id} does not exist.")
    if not existing["doi"]:
        raise ReferenceValidationError(
            "This reference has no DOI to enrich — add its DOI first."
        )
    result = crossref.fetch_metadata(existing["doi"], mailto)
    if isinstance(result, crossref.CrossrefFailure):
        return None, result
    try:
        with conn:
            conn.execute(
                "UPDATE source SET title = COALESCE(title, ?), container = COALESCE(container, ?), "
                "issued_year = COALESCE(issued_year, ?), license_url = COALESCE(license_url, ?), "
                "url = COALESCE(url, ?), indexed_at = ?, retrieval_date = CURRENT_TIMESTAMP "
                "WHERE id = ?",
                (result.title, result.container, result.issued_year,
                 result.license_url, result.url, result.indexed, reference_id),
            )
            saved = conn.execute(
                "SELECT * FROM source WHERE id = ?", (reference_id,)
            ).fetchone()
            conn.execute(
                "INSERT INTO source_capture_event "
                "(action, source_id, previous_json, updated_json) "
                "VALUES ('crossref_enriched', ?, ?, ?)",
                (reference_id, json.dumps(_row_to_dict(existing)), json.dumps(_row_to_dict(saved))),
            )
    except sqlite3.Error as exc:
        raise ReferencePersistenceError(
            f"Saving failed; the previously saved references are unchanged. ({exc})"
        ) from exc
    return _row_to_ref(saved), None


def list_references(conn: sqlite3.Connection) -> list[Reference]:
    rows = conn.execute("SELECT * FROM source ORDER BY id DESC").fetchall()
    return [_row_to_ref(row) for row in rows]


def get_reference(conn: sqlite3.Connection, reference_id: int) -> Reference | None:
    row = conn.execute("SELECT * FROM source WHERE id = ?", (reference_id,)).fetchone()
    return None if row is None else _row_to_ref(row)


def count_captures(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM source_capture_event").fetchone()[0])


def level_label(inspected_level: str) -> str:
    return _LEVEL_LABELS.get(inspected_level, "`unknown` — inspection level not yet recorded")
