"""Attributed review and correction (issue #11).

Implements the owner's recorded threshold (D4): an assertion or relation
becomes `reviewed` only when a named human confirms they inspected the exact
cited evidence location — reviewer, date, supporting location, and reason are
recorded. Corrections preserve the original content in history and return
reviewed content to `needs_verification` (no inherited approvals). Per D5,
cross-source sample-equivalence review is refused unconditionally.
"""

import json
import sqlite3
from dataclasses import dataclass

from mofs_platform.domain.evidence import _row_to_dict as _assertion_to_dict
from mofs_platform.domain.evidence import get_assertion
from mofs_platform.domain.identity import BASIS_KINDS, LINEAGE_KINDS


class ReviewValidationError(ValueError):
    """The proposed correction/review cannot be applied (requirements listed)."""


class ReviewPersistenceError(RuntimeError):
    """Saving failed; previously saved records are unchanged."""


@dataclass(frozen=True)
class ReviewRecord:
    id: int
    entity_type: str
    entity_id: int
    action: str
    reviewer: str | None
    reason: str | None
    supporting_location: str | None
    threshold_note: str | None
    previous_json: str | None
    updated_json: str
    created_at: str


def _row_to_record(row: sqlite3.Row) -> ReviewRecord:
    return ReviewRecord(
        id=row["id"], entity_type=row["entity_type"], entity_id=row["entity_id"],
        action=row["action"], reviewer=row["reviewer"], reason=row["reason"],
        supporting_location=row["supporting_location"],
        threshold_note=row["threshold_note"], previous_json=row["previous_json"],
        updated_json=row["updated_json"], created_at=row["created_at"],
    )


def _opt(value: str | None) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _review_event(
    conn: sqlite3.Connection, *, entity_type: str, entity_id: int, action: str,
    reviewer: str | None, reason: str | None, supporting_location: str | None,
    threshold_note: str | None, previous: dict | None, updated: dict,
) -> int:
    cur = conn.execute(
        "INSERT INTO review_event (entity_type, entity_id, action, reviewer, reason, "
        "supporting_location, threshold_note, previous_json, updated_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (entity_type, entity_id, action, reviewer, reason, supporting_location,
         threshold_note, json.dumps(previous) if previous else None,
         json.dumps(updated)),
    )
    return int(cur.lastrowid)


def correct_identity_relation(
    conn: sqlite3.Connection, *, relation_id: int, new_evidence_location: str | None,
    editor: str | None, reason: str | None,
) -> dict:
    """Correct a relation's evidence location with full attribution. A reviewed
    relation returns to needs_verification — approvals never cover changes."""
    rel = conn.execute(
        "SELECT * FROM identity_relation WHERE id = ?", (relation_id,)
    ).fetchone()
    if rel is None:
        raise ReviewValidationError(f"Relation #{relation_id} does not exist.")
    missing = [
        name for name, value in (("editor (who is correcting)", editor),
                                 ("reason for the correction", reason))
        if not _opt(value)
    ]
    if missing:
        raise ReviewValidationError(
            "Correction rejected — missing: " + "; ".join(missing) + "."
            " The saved history is untouched."
        )
    was_reviewed = rel["review_state"] == "reviewed"
    new_state = "needs_verification" if was_reviewed else rel["review_state"]
    try:
        with conn:
            conn.execute(
                "UPDATE identity_relation SET evidence_location = ?, review_state = ? "
                "WHERE id = ?",
                (_opt(new_evidence_location), new_state, relation_id),
            )
            updated = conn.execute(
                "SELECT * FROM identity_relation WHERE id = ?", (relation_id,)
            ).fetchone()
            _review_event(
                conn, entity_type="identity_relation", entity_id=relation_id,
                action="corrected", reviewer=_opt(editor), reason=_opt(reason),
                supporting_location=None, threshold_note=None,
                previous=dict(rel), updated=dict(updated),
            )
    except sqlite3.Error as exc:
        raise ReviewPersistenceError(
            f"Saving failed; previously saved records are unchanged. ({exc})"
        ) from exc
    return {"id": relation_id, "review_state": new_state,
            "evidence_location": _opt(new_evidence_location),
            "awaiting_re_review": was_reviewed}


def resolve_conflict(
    conn: sqlite3.Connection, *, assertion_id: int, resolver: str | None,
    reason: str | None,
) -> dict:
    """Resolve a recorded conflict pair by explicit human decision (M1 fix):
    both assertions return to `needs_verification` (re-review required), the
    pair links are cleared, and the resolution is attributed in history.
    Refused without resolver + reason."""
    a_row = _assertion_row(conn, assertion_id)
    partner_id = a_row["conflicts_with"]
    if a_row["review_state"] != "conflicted" or partner_id is None:
        raise ReviewValidationError(
            f"Assertion #{assertion_id} is not part of a recorded conflict."
        )
    missing = [
        name for name, value in (("resolver (who resolved it)", resolver),
                                 ("resolution reason", reason))
        if not _opt(value)
    ]
    if missing:
        raise ReviewValidationError(
            "Resolution rejected — missing: " + "; ".join(missing) + "."
            " The conflict stays flagged; the saved history is untouched."
        )
    try:
        with conn:
            rows = conn.execute(
                "SELECT * FROM assertion WHERE id IN (?, ?)",
                (assertion_id, partner_id),
            ).fetchall()
            previous = [_assertion_to_dict(r) for r in rows]
            conn.execute(
                "UPDATE assertion SET review_state = 'needs_verification', "
                "conflicts_with = NULL WHERE id IN (?, ?)",
                (assertion_id, partner_id),
            )
            updated = [_assertion_to_dict(r) for r in conn.execute(
                "SELECT * FROM assertion WHERE id IN (?, ?)",
                (assertion_id, partner_id),
            ).fetchall()]
            _review_event(
                conn, entity_type="assertion", entity_id=assertion_id,
                action="conflict_resolved", reviewer=_opt(resolver),
                reason=_opt(reason), supporting_location=None, threshold_note=None,
                previous={"pair": previous}, updated={"pair": updated},
            )
    except sqlite3.Error as exc:
        raise ReviewPersistenceError(
            f"Saving failed; previously saved records are unchanged. ({exc})"
        ) from exc
    return {"resolved": [assertion_id, partner_id],
            "state": "needs_verification", "by": _opt(resolver)}


def list_review_events(conn: sqlite3.Connection, entity_type: str | None = None,
                       entity_id: int | None = None) -> list[ReviewRecord]:
    if entity_type and entity_id:
        rows = conn.execute(
            "SELECT * FROM review_event WHERE entity_type = ? AND entity_id = ? ORDER BY id",
            (entity_type, entity_id),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM review_event ORDER BY id").fetchall()
    return [_row_to_record(row) for row in rows]


def correct_assertion(
    conn: sqlite3.Connection, *, assertion_id: int, new_claim_text: str | None,
    new_evidence_location: str | None, editor: str | None, reason: str | None,
) -> dict:
    """Correct an assertion's content with full attribution. Reviewed content
    returns to needs_verification — the old approval does not cover the change."""
    original = get_assertion(conn, assertion_id)
    if original is None:
        raise ReviewValidationError(f"Assertion #{assertion_id} does not exist.")
    missing = [
        name for name, value in (("editor (who is correcting)", editor),
                                 ("reason for the correction", reason))
        if not _opt(value)
    ]
    new_text = _opt(new_claim_text)
    if not new_text:
        missing.append("corrected claim text")
    if missing:
        raise ReviewValidationError(
            "Correction rejected — missing: " + "; ".join(missing) + "."
            " The saved history is untouched."
        )
    was_reviewed = original.review_state == "reviewed"
    new_state = "needs_verification" if was_reviewed else original.review_state
    previous_row = _assertion_row(conn, assertion_id)
    updated_row = {**_assertion_to_dict(previous_row), "claim_text": new_text,
                   "evidence_location": _opt(new_evidence_location)}
    try:
        with conn:
            conn.execute(
                "UPDATE assertion SET claim_text = ?, evidence_location = ?, "
                "review_state = ? WHERE id = ?",
                (new_text, _opt(new_evidence_location), new_state, assertion_id),
            )
            _review_event(
                conn, entity_type="assertion", entity_id=assertion_id,
                action="corrected", reviewer=_opt(editor), reason=_opt(reason),
                supporting_location=None, threshold_note=None,
                previous=_assertion_to_dict(previous_row),
                updated={**updated_row, "review_state": new_state},
            )
    except sqlite3.Error as exc:
        raise ReviewPersistenceError(
            f"Saving failed; previously saved records are unchanged. ({exc})"
        ) from exc
    result = {
        "id": assertion_id, "review_state": new_state,
        "claim_text": new_text,
        "awaiting_re_review": was_reviewed,
        "original_preserved_in_history": True,
    }
    return result


def correct_sample(
    conn: sqlite3.Connection, *, sample_id: int, editor: str | None,
    reason: str | None, designation: str | None = None,
    parent_framework_name: str | None = None, linker: str | None = None,
    metal_node: str | None = None, composition: str | None = None,
    additions: str | None = None, structure_ref: str | None = None,
    activation: str | None = None, basis: str | None = None,
    lineage_kind: str | None = None, derived_from_sample_id: int | None = None,
) -> dict:
    """Correct a sample record's entered fields with full attribution
    (issue #20, guided-session G4/G5).

    Unprovided (None) fields keep their stored values — the UI passes blank
    inputs as unprovided, so blanking a field to empty is out of scope.
    `source_id` is capture provenance and is not correctable here; identity
    questions belong to the relation system. Attached assertions,
    observations, and their review states are untouched. Every correction
    appends a review_event with both snapshots — history is never overwritten.
    """
    row = conn.execute(
        "SELECT * FROM sample_record WHERE id = ?", (sample_id,)
    ).fetchone()
    if row is None:
        raise ReviewValidationError(f"Sample #{sample_id} does not exist.")
    missing = [
        name for name, value in (("editor (who is correcting)", editor),
                                 ("reason for the correction", reason))
        if not _opt(value)
    ]
    if missing:
        raise ReviewValidationError(
            "Correction rejected — missing: " + "; ".join(missing) + "."
            " The saved history is untouched."
        )

    provided: dict = {
        "designation": _opt(designation),
        "parent_framework_name": _opt(parent_framework_name),
        "linker": _opt(linker),
        "metal_node": _opt(metal_node),
        "composition": _opt(composition),
        "additions": _opt(additions),
        "structure_ref": _opt(structure_ref),
        "activation": _opt(activation),
    }
    clean_basis = basis.strip() if isinstance(basis, str) and basis.strip() else None
    if clean_basis is not None and clean_basis not in BASIS_KINDS:
        raise ReviewValidationError(
            f"Basis must be one of {BASIS_KINDS!r} — got {clean_basis!r}."
        )
    provided["basis"] = clean_basis
    clean_lineage = _opt(lineage_kind)
    if clean_lineage is not None and clean_lineage not in LINEAGE_KINDS:
        raise ReviewValidationError(
            f"Lineage kind must be one of {LINEAGE_KINDS!r} — got {clean_lineage!r}."
        )
    provided["lineage_kind"] = clean_lineage
    try:
        provided["derived_from_sample_id"] = (
            int(derived_from_sample_id) if derived_from_sample_id else None
        )
    except (TypeError, ValueError):
        raise ReviewValidationError(
            f"Parent sample id must be an integer — got {derived_from_sample_id!r}."
        ) from None

    changes = {
        name: value for name, value in provided.items()
        if value is not None and value != row[name]
    }
    if not changes:
        raise ReviewValidationError(
            "Correction rejected — nothing to change: every provided field "
            "equals the stored value (blank means keep). The saved history "
            "is untouched."
        )

    new_lineage = changes.get("lineage_kind", row["lineage_kind"])
    new_derived = changes.get("derived_from_sample_id", row["derived_from_sample_id"])
    if (new_lineage is None) != (new_derived is None):
        raise ReviewValidationError(
            "A lineage link needs both the kind (composite/derived) and the "
            "parent sample — provide both or neither."
        )
    if new_derived is not None:
        if new_derived == sample_id:
            raise ReviewValidationError("A sample cannot derive from itself.")
        if conn.execute(
            "SELECT id FROM sample_record WHERE id = ?", (new_derived,)
        ).fetchone() is None:
            raise ReviewValidationError(
                f"Parent sample #{new_derived} does not exist."
            )

    previous = dict(row)
    updated = {**previous, **changes}
    set_clause = ", ".join(f"{name} = ?" for name in changes)
    try:
        with conn:
            conn.execute(
                f"UPDATE sample_record SET {set_clause} WHERE id = ?",
                (*changes.values(), sample_id),
            )
            _review_event(
                conn, entity_type="sample_record", entity_id=sample_id,
                action="corrected", reviewer=_opt(editor), reason=_opt(reason),
                supporting_location=None, threshold_note=None,
                previous=previous, updated=updated,
            )
    except sqlite3.Error as exc:
        raise ReviewPersistenceError(
            f"Saving failed; previously saved records are unchanged. ({exc})"
        ) from exc
    return {
        "id": sample_id,
        "changed_fields": sorted(changes),
        "original_preserved_in_history": True,
    }


def _assertion_row(conn: sqlite3.Connection, assertion_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM assertion WHERE id = ?", (assertion_id,)).fetchone()
    if row is None:
        raise ReviewValidationError(f"Assertion #{assertion_id} does not exist.")
    return row


def review_assertion(
    conn: sqlite3.Connection, *, assertion_id: int, reviewer: str | None,
    supporting_location: str | None, reason: str | None,
) -> dict:
    """Apply the D4 threshold: mark one assertion reviewed. Conflicted
    assertions are refused until their recorded conflict is resolved."""
    row = _assertion_row(conn, assertion_id)
    original = get_assertion(conn, assertion_id)
    if original.review_state == "conflicted":
        raise ReviewValidationError(
            f"Assertion #{assertion_id} is in a recorded conflict — resolve it by "
            "correcting the claim or its pair before review."
        )
    if original.review_state == "reviewed":
        raise ReviewValidationError(
            f"Assertion #{assertion_id} is already reviewed — correct it instead "
            "if the content changed."
        )
    missing = []
    if not _opt(reviewer):
        missing.append("reviewer name")
    if not _opt(supporting_location):
        missing.append("supporting source location (D4: the exact cited evidence location)")
    if not _opt(reason):
        missing.append("reason stating how this assertion meets the D4 threshold")
    if missing:
        try:
            with conn:
                _review_event(
                    conn, entity_type="assertion", entity_id=assertion_id,
                    action="review_rejected", reviewer=_opt(reviewer), reason=_opt(reason),
                    supporting_location=_opt(supporting_location),
                    threshold_note="unmet: " + "; ".join(missing),
                    previous=_assertion_to_dict(row),
                    updated={**_assertion_to_dict(row), "review_state": original.review_state},
                )
        except sqlite3.Error:
            pass  # the rejection log is best-effort; state preservation is certain
        raise ReviewValidationError(
            "Review rejected — unmet D4 requirements: " + "; ".join(missing) + "."
        )
    try:
        with conn:
            conn.execute(
                "UPDATE assertion SET review_state = 'reviewed' WHERE id = ?",
                (assertion_id,),
            )
            _review_event(
                conn, entity_type="assertion", entity_id=assertion_id,
                action="reviewed", reviewer=_opt(reviewer),
                reason=_opt(reason), supporting_location=_opt(supporting_location),
                threshold_note="D4: named human inspected the exact cited evidence location.",
                previous=_assertion_to_dict(row),
                updated={**_assertion_to_dict(row), "review_state": "reviewed"},
            )
    except sqlite3.Error as exc:
        raise ReviewPersistenceError(
            f"Saving failed; previously saved records are unchanged. ({exc})"
        ) from exc
    return {"id": assertion_id, "review_state": "reviewed", "reviewer": _opt(reviewer)}


def review_identity_relation(
    conn: sqlite3.Connection, *, relation_id: int, reviewer: str | None,
    supporting_location: str | None, reason: str | None,
) -> dict:
    """Review a scoped identity relation. Per D5, cross-source sample
    equivalence is refused unconditionally — records stay separate forever."""
    rel = conn.execute(
        "SELECT * FROM identity_relation WHERE id = ?", (relation_id,)
    ).fetchone()
    if rel is None:
        raise ReviewValidationError(f"Relation #{relation_id} does not exist.")
    if rel["review_state"] == "conflicted":
        raise ReviewValidationError(
            f"Relation #{relation_id} is conflicted — resolve it before review."
        )
    left = conn.execute(
        "SELECT source_id FROM sample_record WHERE id = ?", (rel["left_sample_id"],)
    ).fetchone()
    right = conn.execute(
        "SELECT source_id FROM sample_record WHERE id = ?", (rel["right_sample_id"],)
    ).fetchone()
    cross_source = left["source_id"] != right["source_id"]
    if rel["relation"] in ("same_reported_sample", "unresolved") and (
        rel["level"] == "sample" and cross_source
    ):
        _reason = (
            "D5: cross-source sample equivalence is never approved — the records "
            "stay separate with their documented unresolved relation; this does "
            "not prevent reviewing unrelated assertions."
        )
        try:
            with conn:
                _review_event(
                    conn, entity_type="identity_relation", entity_id=relation_id,
                    action="review_rejected", reviewer=_opt(reviewer), reason=_opt(reason),
                    supporting_location=_opt(supporting_location),
                    threshold_note=_reason,
                    previous=dict(rel), updated={**dict(rel), "review_state": rel["review_state"]},
                )
        except sqlite3.Error:
            pass
        raise ReviewValidationError(_reason)
    missing = []
    if not _opt(reviewer):
        missing.append("reviewer name")
    if not _opt(supporting_location):
        missing.append("supporting source location")
    if not _opt(reason):
        missing.append("reason stating how this relation meets the D4 threshold")
    if missing:
        try:
            with conn:
                _review_event(
                    conn, entity_type="identity_relation", entity_id=relation_id,
                    action="review_rejected", reviewer=_opt(reviewer), reason=_opt(reason),
                    supporting_location=_opt(supporting_location),
                    threshold_note="unmet: " + "; ".join(missing),
                    previous=dict(rel), updated={**dict(rel), "review_state": rel["review_state"]},
                )
        except sqlite3.Error:
            pass
        raise ReviewValidationError(
            "Review rejected — unmet D4 requirements: " + "; ".join(missing) + "."
        )
    try:
        with conn:
            conn.execute(
                "UPDATE identity_relation SET review_state = 'reviewed' WHERE id = ?",
                (relation_id,),
            )
            _review_event(
                conn, entity_type="identity_relation", entity_id=relation_id,
                action="reviewed", reviewer=_opt(reviewer), reason=_opt(reason),
                supporting_location=_opt(supporting_location),
                threshold_note="D4: named human inspected the cited designation evidence.",
                previous=dict(rel),
                updated={**dict(rel), "review_state": "reviewed"},
            )
    except sqlite3.Error as exc:
        raise ReviewPersistenceError(
            f"Saving failed; previously saved records are unchanged. ({exc})"
        ) from exc
    return {"id": relation_id, "review_state": "reviewed", "reviewer": _opt(reviewer)}
