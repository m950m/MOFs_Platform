"""Compound profiles (issue #18) — the per-compound feature card.

A compound is a RESEARCHER-GROUPED aggregation record: grouping is manual,
attributed, and reasoned — never a merge, never an equivalence claim (D5),
and never automatic by formula. Same composition with a different arrangement
or morphology lives in a separate compound with a separate profile.

The profile aggregates ONLY per member: a sample's observations stay under
that sample (nothing climbs to the compound level — identity contract), and
structure-record properties stay provider-labeled metadata. Streams stay
separate per D11 (experimental ≠ computational ≠ provider-computed).
Conflicting values render side by side with provenance — never averaged.
Empty sections render `unknown` honestly: nothing enters from memory.
"""

import json
import sqlite3
from dataclasses import dataclass, field

PROVIDER_LABELS = {
    "core_mof_2019": "CoRE MOF 2019",
    "qmof": "QMOF (computed)",
    "digimof": "DigiMOF (text-mined synthesis)",
    "cod": "COD",
    "other": "other provider",
}


class CompoundValidationError(ValueError):
    """The compound operation cannot be applied (requirements listed)."""


class CompoundPersistenceError(RuntimeError):
    """Saving failed; previously saved records are unchanged."""


@dataclass(frozen=True)
class Compound:
    id: int
    canonical_name: str
    framework_key: str | None
    identity_note: str
    created_by: str
    created_at: str


@dataclass(frozen=True)
class MemberLink:
    id: int
    member_type: str
    member_id: int
    added_by: str
    reason: str


@dataclass(frozen=True)
class CompoundProfile:
    compound: Compound
    samples: list[dict] = field(default_factory=list)
    structures: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)


def _clean(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _event(conn: sqlite3.Connection, action: str, compound_id: int,
           actor: str | None, detail: dict) -> None:
    conn.execute(
        "INSERT INTO compound_event (action, compound_id, actor, detail) "
        "VALUES (?, ?, ?, ?)",
        (action, compound_id, actor, json.dumps(detail, ensure_ascii=False)),
    )


def create_compound(
    conn: sqlite3.Connection, *, canonical_name: str, identity_note: str,
    created_by: str | None, framework_key: str | None = None,
) -> Compound:
    clean_name = _clean(canonical_name)
    clean_note = _clean(identity_note)
    clean_by = _clean(created_by)
    missing = [n for n, v in (
        ("canonical name", clean_name), ("identity note", clean_note),
        ("who is creating", clean_by),
    ) if not v]
    if missing:
        raise CompoundValidationError(
            "Compound creation rejected — missing: " + "; ".join(missing) + "."
        )
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO compound (canonical_name, framework_key, identity_note, "
                "created_by) VALUES (?, ?, ?, ?)",
                (clean_name, _clean(framework_key), clean_note, clean_by),
            )
            compound_id = int(cur.lastrowid)
            _event(conn, "compound_created", compound_id, clean_by, {
                "canonical_name": clean_name,
                "framework_key": _clean(framework_key),
                "identity_note": clean_note,
            })
    except sqlite3.Error as exc:
        raise CompoundPersistenceError(
            f"Saving failed; no compound was created. ({exc})"
        ) from exc
    return get_compound(conn, compound_id)


def get_compound(conn: sqlite3.Connection, compound_id: int) -> Compound | None:
    row = conn.execute(
        "SELECT * FROM compound WHERE id = ?", (compound_id,)
    ).fetchone()
    if row is None:
        return None
    return Compound(
        id=row["id"], canonical_name=row["canonical_name"],
        framework_key=row["framework_key"], identity_note=row["identity_note"],
        created_by=row["created_by"], created_at=row["created_at"],
    )


def list_compounds(conn: sqlite3.Connection) -> list[Compound]:
    rows = conn.execute("SELECT * FROM compound ORDER BY id DESC").fetchall()
    return [
        Compound(id=r["id"], canonical_name=r["canonical_name"],
                 framework_key=r["framework_key"], identity_note=r["identity_note"],
                 created_by=r["created_by"], created_at=r["created_at"])
        for r in rows
    ]


def _member_exists(conn: sqlite3.Connection, member_type: str, member_id: int) -> bool:
    table = {"sample_record": "sample_record", "structure_index": "structure_index"}[member_type]
    return conn.execute(
        f"SELECT id FROM {table} WHERE id = ?", (member_id,)
    ).fetchone() is not None


def attach_member(
    conn: sqlite3.Connection, *, compound_id: int, member_type: str,
    member_id: int, added_by: str | None, reason: str | None,
) -> MemberLink:
    if get_compound(conn, compound_id) is None:
        raise CompoundValidationError(f"Compound #{compound_id} does not exist.")
    if member_type not in ("sample_record", "structure_index"):
        raise CompoundValidationError(
            "Member type must be 'sample_record' or 'structure_index' — "
            f"got {member_type!r}."
        )
    clean_by = _clean(added_by)
    clean_reason = _clean(reason)
    missing = [n for n, v in (
        ("who is attaching", clean_by), ("membership reason", clean_reason)
    ) if not v]
    if missing:
        raise CompoundValidationError(
            "Attach rejected — missing: " + "; ".join(missing) + "."
        )
    try:
        member_id = int(member_id)
    except (TypeError, ValueError):
        raise CompoundValidationError(
            f"Member id must be an integer — got {member_id!r}."
        ) from None
    if not _member_exists(conn, member_type, member_id):
        raise CompoundValidationError(
            f"{member_type} #{member_id} does not exist."
        )
    existing = conn.execute(
        "SELECT id FROM compound_member WHERE compound_id = ? AND member_type = ? "
        "AND member_id = ?",
        (compound_id, member_type, member_id),
    ).fetchone()
    if existing is not None:
        raise CompoundValidationError(
            f"{member_type} #{member_id} is already a member of compound "
            f"#{compound_id}."
        )
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO compound_member (compound_id, member_type, member_id, "
                "added_by, reason) VALUES (?, ?, ?, ?, ?)",
                (compound_id, member_type, member_id, clean_by, clean_reason),
            )
            link_id = int(cur.lastrowid)
            _event(conn, "member_attached", compound_id, clean_by, {
                "member_type": member_type, "member_id": member_id,
                "reason": clean_reason,
            })
    except sqlite3.Error as exc:
        raise CompoundPersistenceError(
            f"Saving failed; membership is unchanged. ({exc})"
        ) from exc
    return MemberLink(id=link_id, member_type=member_type, member_id=member_id,
                      added_by=clean_by, reason=clean_reason)


def detach_member(
    conn: sqlite3.Connection, *, link_id: int, actor: str | None, reason: str | None
) -> None:
    row = conn.execute(
        "SELECT * FROM compound_member WHERE id = ?", (link_id,)
    ).fetchone()
    if row is None:
        raise CompoundValidationError(f"Membership link #{link_id} does not exist.")
    clean_actor = _clean(actor)
    clean_reason = _clean(reason)
    missing = [n for n, v in (
        ("who is detaching", clean_actor), ("detachment reason", clean_reason)
    ) if not v]
    if missing:
        raise CompoundValidationError(
            "Detach rejected — missing: " + "; ".join(missing) + "."
        )
    try:
        with conn:
            conn.execute("DELETE FROM compound_member WHERE id = ?", (link_id,))
            _event(conn, "member_detached", row["compound_id"], clean_actor, {
                "member_type": row["member_type"], "member_id": row["member_id"],
                "reason": clean_reason,
            })
    except sqlite3.Error as exc:
        raise CompoundPersistenceError(
            f"Saving failed; membership is unchanged. ({exc})"
        ) from exc


def get_profile(conn: sqlite3.Connection, compound_id: int) -> CompoundProfile:
    """Aggregate the compound's members WITHOUT climbing: each sample's
    observations stay under that sample; each structure record's properties
    stay provider-labeled. Streams are separate per D11. Nothing is averaged
    or deduplicated — conflicts sit side by side with their provenance."""
    compound = get_compound(conn, compound_id)
    if compound is None:
        raise CompoundValidationError(f"Compound #{compound_id} does not exist.")
    links = conn.execute(
        "SELECT * FROM compound_member WHERE compound_id = ? ORDER BY id",
        (compound_id,),
    ).fetchall()
    samples: list[dict] = []
    structures: list[dict] = []
    for link in links:
        if link["member_type"] == "sample_record":
            srow = conn.execute(
                "SELECT * FROM sample_record WHERE id = ?", (link["member_id"],)
            ).fetchone()
            if srow is None:
                continue
            observations = [
                {
                    "id": o["id"], "kind": o["observation_kind"],
                    "value": o["value"], "unit": o["unit"], "reaction": o["reaction"],
                    "medium": o["medium"], "location": o["evidence_location"],
                    "source_id": o["source_id"],
                    "reference_convention": o["reference_convention"],
                    "loading": o["loading"], "duration": o["duration"],
                    "protocol": o["protocol"],
                }
                for o in conn.execute(
                    "SELECT * FROM observation WHERE sample_id = ? ORDER BY id",
                    (link["member_id"],),
                ).fetchall()
            ]
            samples.append({
                "link_id": link["id"], "reason": link["reason"], "added_by": link["added_by"],
                "id": srow["id"], "designation": srow["designation"],
                "basis": srow["basis"], "composition": srow["composition"],
                "observations": observations,
            })
        else:
            rrow = conn.execute(
                "SELECT * FROM structure_index WHERE id = ?", (link["member_id"],)
            ).fetchone()
            if rrow is None:
                continue
            extras = {}
            if rrow["extra_json"]:
                try:
                    extras = json.loads(rrow["extra_json"])
                except json.JSONDecodeError:
                    extras = {}
            structures.append({
                "link_id": link["id"], "reason": link["reason"], "added_by": link["added_by"],
                "id": rrow["id"], "name": rrow["name"], "provider": rrow["provider"],
                "formula": rrow["formula"], "doi": rrow["doi"],
                "properties": extras,
            })
    events = [
        {"action": e["action"], "actor": e["actor"], "detail": e["detail"],
         "changed_at": e["changed_at"]}
        for e in conn.execute(
            "SELECT * FROM compound_event WHERE compound_id = ? ORDER BY id",
            (compound_id,),
        ).fetchall()
    ]
    return CompoundProfile(
        compound=compound, samples=samples, structures=structures, events=events,
    )
