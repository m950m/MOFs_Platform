"""Laboratory capability profile persistence (issue #5).

A set of named capability entries, each with one of four distinct statuses:
current (available now), future (planned, not available yet), explicitly
unavailable, and unknown (not yet confirmed). The tool never seeds equipment,
never infers candidate suitability or synthesis success, and never converts an
unknown into a yes or a no (plan §2.5; design-system rule 7).
"""

import json
import sqlite3
from dataclasses import dataclass

STATUSES = ("current", "future", "unavailable", "unknown")

STATUS_LABELS = {
    "current": "current — available now",
    "future": "future — planned, NOT currently available",
    "unavailable": "explicitly unavailable",
    "unknown": "unknown — not yet confirmed",
}


class LabProfileValidationError(ValueError):
    """The proposed capability entry cannot be saved."""


class LabProfilePersistenceError(RuntimeError):
    """Saving failed; the previously saved profile is unchanged."""


@dataclass(frozen=True)
class LabCapability:
    id: int
    name: str
    description: str | None
    status: str
    updated_at: str | None = None


def _row_to_cap(row: sqlite3.Row) -> LabCapability:
    return LabCapability(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        status=row["status"],
        updated_at=row["updated_at"],
    )


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in ("id", "name", "description", "status", "updated_at")}


def _validate(name: str | None, status: str) -> tuple[str, str]:
    if name is None or not name.strip():
        raise LabProfileValidationError(
            "Capability name is empty — enter a name before saving."
        )
    if status not in STATUSES:
        raise LabProfileValidationError(
            f"Status must be one of {STATUSES!r} — got {status!r}."
        )
    return name.strip(), status


def add_capability(
    conn: sqlite3.Connection, name: str | None, description: str | None, status: str
) -> LabCapability:
    clean_name, clean_status = _validate(name, status)
    desc = description.strip() if isinstance(description, str) and description.strip() else None
    try:
        dup = conn.execute(
            "SELECT id FROM lab_capability WHERE lower(name) = lower(?)", (clean_name,)
        ).fetchone()
        if dup is not None:
            raise LabProfileValidationError(
                "A capability with this name already exists — correct the existing "
                "entry instead of adding a duplicate."
            )
        with conn:
            cur = conn.execute(
                "INSERT INTO lab_capability (name, description, status) VALUES (?, ?, ?)",
                (clean_name, desc, clean_status),
            )
            new_id = int(cur.lastrowid)
            saved = conn.execute(
                "SELECT * FROM lab_capability WHERE id = ?", (new_id,)
            ).fetchone()
            conn.execute(
                "INSERT INTO lab_profile_event "
                "(action, capability_id, previous_json, updated_json) "
                "VALUES ('added', ?, NULL, ?)",
                (new_id, json.dumps(_row_to_dict(saved))),
            )
    except LabProfileValidationError:
        raise
    except sqlite3.Error as exc:
        raise LabProfilePersistenceError(
            f"Saving failed; the previously saved profile is unchanged. ({exc})"
        ) from exc
    return _row_to_cap(saved)


def update_capability(
    conn: sqlite3.Connection,
    capability_id: int,
    name: str | None,
    description: str | None,
    status: str,
) -> LabCapability:
    clean_name, clean_status = _validate(name, status)
    desc = description.strip() if isinstance(description, str) and description.strip() else None
    try:
        existing = conn.execute(
            "SELECT * FROM lab_capability WHERE id = ?", (capability_id,)
        ).fetchone()
        if existing is None:
            raise LabProfileValidationError(
                f"Capability #{capability_id} does not exist — nothing to correct."
            )
        dup = conn.execute(
            "SELECT id FROM lab_capability WHERE lower(name) = lower(?) AND id != ?",
            (clean_name, capability_id),
        ).fetchone()
        if dup is not None:
            raise LabProfileValidationError(
                "Another capability already uses this name — choose a distinct name."
            )
        with conn:
            conn.execute(
                "UPDATE lab_capability SET name = ?, description = ?, status = ?, "
                "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (clean_name, desc, clean_status, capability_id),
            )
            saved = conn.execute(
                "SELECT * FROM lab_capability WHERE id = ?", (capability_id,)
            ).fetchone()
            conn.execute(
                "INSERT INTO lab_profile_event "
                "(action, capability_id, previous_json, updated_json) "
                "VALUES ('corrected', ?, ?, ?)",
                (capability_id, json.dumps(_row_to_dict(existing)), json.dumps(_row_to_dict(saved))),
            )
    except LabProfileValidationError:
        raise
    except sqlite3.Error as exc:
        raise LabProfilePersistenceError(
            f"Saving failed; the previously saved profile is unchanged. ({exc})"
        ) from exc
    return _row_to_cap(saved)


def list_capabilities(conn: sqlite3.Connection) -> list[LabCapability]:
    rows = conn.execute(
        "SELECT * FROM lab_capability ORDER BY name COLLATE NOCASE"
    ).fetchall()
    return [_row_to_cap(row) for row in rows]


def count_events(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM lab_profile_event").fetchone()[0])
