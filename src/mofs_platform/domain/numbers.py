"""Number streams (issue #17, D11) — laboratory vs industry_reference.

Two separate streams of recorded numbers; comparison is display-only:
both sides shown as recorded with their conditions, no unit conversion
(there are none recorded), no ranking, no meet/fail verdicts, and the
caveat rendered wherever a comparison appears. The table starts empty —
nothing enters from memory.
"""

import sqlite3
from dataclasses import dataclass

STREAMS = ("laboratory", "industry_reference")
REACTIONS = ("HER", "OER", "other")


class NumberValidationError(ValueError):
    """The number entry cannot be applied (requirements listed)."""


class NumberPersistenceError(RuntimeError):
    """Saving failed; previously saved records are unchanged."""


@dataclass(frozen=True)
class NumberRow:
    id: int
    stream: str
    label: str
    value: str
    unit: str | None
    reaction: str
    conditions_note: str | None
    source_id: int | None
    source_citation: str | None
    source_year: str | None
    contributor: str


def _row_to_number(row: sqlite3.Row) -> NumberRow:
    return NumberRow(
        id=row["id"], stream=row["stream"], label=row["label"], value=row["value"],
        unit=row["unit"], reaction=row["reaction"],
        conditions_note=row["conditions_note"], source_id=row["source_id"],
        source_citation=row["source_citation"], source_year=row["source_year"],
        contributor=row["contributor"],
    )


def _clean(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def add_number(
    conn: sqlite3.Connection, *, stream: str, label: str, value: str,
    reaction: str, unit: str | None = None, conditions_note: str | None = None,
    source_id: int | None = None, source_citation: str | None = None,
    source_year: str | None = None, contributor: str | None,
) -> NumberRow:
    clean = {
        "stream": _clean(stream), "label": _clean(label), "value": _clean(value),
        "reaction": _clean(reaction), "unit": _clean(unit),
        "conditions_note": _clean(conditions_note),
        "source_citation": _clean(source_citation), "source_year": _clean(source_year),
        "contributor": _clean(contributor),
    }
    missing = [n for n in ("stream", "label", "value", "reaction", "contributor")
               if not clean[n]]
    if missing:
        raise NumberValidationError(
            "Number entry rejected — missing: " + "; ".join(missing) + "."
        )
    if clean["stream"] not in STREAMS:
        raise NumberValidationError(
            f"Stream must be one of {STREAMS!r} — got {clean['stream']!r}."
        )
    if clean["reaction"] not in REACTIONS:
        raise NumberValidationError(
            f"Reaction must be one of {REACTIONS!r} — got {clean['reaction']!r}."
        )
    clean_source_id = source_id
    if clean_source_id is not None:
        try:
            clean_source_id = int(clean_source_id)
        except (TypeError, ValueError):
            raise NumberValidationError(
                f"Source pointer must be an integer reference id — got "
                f"{source_id!r}."
            ) from None
        if conn.execute(
            "SELECT id FROM source WHERE id = ?", (clean_source_id,)
        ).fetchone() is None:
            raise NumberValidationError(
                f"Source reference #{clean_source_id} does not exist."
            )
    if not clean["source_citation"] and clean_source_id is None:
        raise NumberValidationError(
            "Provenance required — name a source: an existing reference id "
            "or a source citation (with year). Nothing enters without "
            "provenance."
        )
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO reference_number (stream, label, value, unit, reaction, "
                "conditions_note, source_id, source_citation, source_year, contributor) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (clean["stream"], clean["label"], clean["value"], clean["unit"],
                 clean["reaction"], clean["conditions_note"], clean_source_id,
                 clean["source_citation"], clean["source_year"], clean["contributor"]),
            )
            row_id = int(cur.lastrowid)
    except sqlite3.Error as exc:
        raise NumberPersistenceError(
            f"Saving failed; nothing was recorded. ({exc})"
        ) from exc
    return get_number(conn, row_id)


def get_number(conn: sqlite3.Connection, number_id: int) -> NumberRow | None:
    row = conn.execute(
        "SELECT * FROM reference_number WHERE id = ?", (number_id,)
    ).fetchone()
    return None if row is None else _row_to_number(row)


def list_numbers(conn: sqlite3.Connection, stream: str) -> list[NumberRow]:
    if stream not in STREAMS:
        raise NumberValidationError(
            f"Stream must be one of {STREAMS!r} — got {stream!r}."
        )
    rows = conn.execute(
        "SELECT * FROM reference_number WHERE stream = ? ORDER BY id DESC",
        (stream,),
    ).fetchall()
    return [_row_to_number(row) for row in rows]


def build_comparison(conn: sqlite3.Connection) -> dict:
    """Pair recorded laboratory observations with industry_reference rows of
    the SAME reaction. Both sides come as recorded (value, unit, conditions),
    with full provenance. No conversion, no ranking, no verdicts — the
    researcher draws the conclusion. Reactions with only one side present
    are returned too, honestly marked."""
    lab = conn.execute(
        "SELECT o.id, o.value, o.unit, o.reaction, o.medium, o.reference_convention, "
        "o.loading, o.duration, o.protocol, o.evidence_location, "
        "s.designation AS sample_designation, o.sample_id "
        "FROM observation o JOIN sample_record s ON s.id = o.sample_id "
        "WHERE o.value IS NOT NULL AND o.reaction IN ('HER', 'OER') "
        "ORDER BY o.reaction, o.id"
    ).fetchall()
    industry = {
        "HER": [n for n in list_numbers(conn, "industry_reference") if n.reaction == "HER"],
        "OER": [n for n in list_numbers(conn, "industry_reference") if n.reaction == "OER"],
    }
    comparisons = []
    for row in lab:
        reaction = row["reaction"]
        comparisons.append({
            "reaction": reaction,
            "laboratory": {
                "sample": row["sample_designation"], "value": row["value"],
                "unit": row["unit"], "medium": row["medium"],
                "reference_convention": row["reference_convention"],
                "loading": row["loading"], "duration": row["duration"],
                "protocol": row["protocol"], "location": row["evidence_location"],
                "sample_id": row["sample_id"],
            },
            "industry_reference": [
                {
                    "label": n.label, "value": n.value, "unit": n.unit,
                    "conditions_note": n.conditions_note,
                    "source_citation": n.source_citation or (
                        f"reference #{n.source_id}" if n.source_id else None
                    ),
                    "source_year": n.source_year, "contributor": n.contributor,
                }
                for n in industry[reaction]
            ],
        })
    return {"comparisons": comparisons, "caveat": CAVEAT}


CAVEAT = (
    "This comparison DOES NOT establish feasibility, novelty, or suitability. "
    "Laboratory conditions and industrial conditions differ (scale, current "
    "density, electrolyte, duration) — differences are displayed, never "
    "hidden. Units are shown as recorded; no conversion exists in this "
    "tool. There is no ranking and no meet/fail verdict: the researcher "
    "draws the conclusion."
)


def correct_number(
    conn: sqlite3.Connection, number_id: int, *, editor: str | None,
    reason: str | None, label: str | None = None, value: str | None = None,
    unit: str | None = None, reaction: str | None = None,
    conditions_note: str | None = None, source_citation: str | None = None,
    source_year: str | None = None,
) -> dict:
    """Correct a recorded number row with full attribution (issue #17 edit
    path). Blank = keep: unprovided fields keep their stored values. The
    stream and source_id are NOT correctable — the stream defines which D11
    stream a row belongs to (moving rows between streams is not offered),
    and source_id is provenance. Every correction appends a review_event
    with previous/updated snapshots in one transaction."""
    import json as _json

    row = conn.execute(
        "SELECT * FROM reference_number WHERE id = ?", (number_id,)
    ).fetchone()
    if row is None:
        raise NumberValidationError(f"Number row #{number_id} does not exist.")
    clean_editor = _clean(editor)
    clean_reason = _clean(reason)
    missing = [n for n, v in (
        ("editor (who is correcting)", clean_editor),
        ("reason for the correction", clean_reason),
    ) if not v]
    if missing:
        raise NumberValidationError(
            "Correction rejected — missing: " + "; ".join(missing) + "."
            " The saved history is untouched."
        )
    provided = {
        "label": _clean(label), "value": _clean(value), "unit": _clean(unit),
        "reaction": _clean(reaction),
        "conditions_note": _clean(conditions_note),
        "source_citation": _clean(source_citation),
        "source_year": _clean(source_year),
    }
    if provided["reaction"] is not None and provided["reaction"] not in REACTIONS:
        raise NumberValidationError(
            f"Reaction must be one of {REACTIONS!r} — got {provided['reaction']!r}."
        )
    changes = {
        field: value for field, value in provided.items()
        if value is not None and value != row[field]
    }
    if not changes:
        raise NumberValidationError(
            "Correction rejected — nothing to change: every provided field "
            "equals the stored value (blank means keep). The saved history "
            "is untouched."
        )
    previous = {k: v for k, v in dict(row).items() if k != "created_at"}
    updated = {**previous, **changes}
    set_clause = ", ".join(f"{name} = ?" for name in changes)
    try:
        with conn:
            conn.execute(
                f"UPDATE reference_number SET {set_clause} WHERE id = ?",
                (*changes.values(), number_id),
            )
            conn.execute(
                "INSERT INTO review_event (entity_type, entity_id, action, "
                "reviewer, reason, previous_json, updated_json) "
                "VALUES ('reference_number', ?, 'corrected', ?, ?, ?, ?)",
                (number_id, clean_editor, clean_reason,
                 _json.dumps(previous, ensure_ascii=False),
                 _json.dumps(updated, ensure_ascii=False)),
            )
    except sqlite3.Error as exc:
        raise NumberPersistenceError(
            f"Saving failed; the row is unchanged. ({exc})"
        ) from exc
    return {
        "id": number_id, "changed_fields": sorted(changes),
        "original_preserved_in_history": True,
    }
