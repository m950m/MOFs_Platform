"""Tested-sample identity: records, relations, and the merge policy (issue #8).

Implements the identity contract (plan §3, issue #1) as executable behavior:
- observations attach ONLY to samples — never to a framework name or a
  hypothesized operating phase (structural, via FKs);
- the comparison vocabulary is exactly: same reported sample / same parent
  framework / derived / composite / different / unresolved;
- a shared name, formula, DOI, MOFid, or CIF alone never merges samples —
  merge permission is 'within_source_after_review' at most, and cross-source
  identity is always unresolved/human-review;
- the same CIF with different activation histories = different samples.
"""

import json
import sqlite3
from dataclasses import dataclass

BASIS_KINDS = ("experimental", "computational", "hypothetical")
LINEAGE_KINDS = ("composite", "derived")
STAGES = ("before", "during", "after", "unknown")
OBSERVATION_KINDS = ("experimental", "computational", "hypothetical")
class IdentityValidationError(ValueError):
    """The proposed sample/state/observation/relation cannot be recorded."""


class IdentityPersistenceError(RuntimeError):
    """Saving failed; previously saved records are unchanged."""


@dataclass(frozen=True)
class Sample:
    id: int
    source_id: int
    designation: str
    parent_framework_name: str | None
    linker: str | None
    metal_node: str | None
    composition: str | None
    additions: str | None
    structure_ref: str | None
    activation: str | None
    lineage_kind: str | None
    derived_from_sample_id: int | None
    basis: str


@dataclass(frozen=True)
class OperatingState:
    id: int
    sample_id: int
    stage: str
    phase_assignment: str | None
    epistemic_type: str
    evidence_location: str | None


@dataclass(frozen=True)
class Observation:
    id: int
    sample_id: int
    source_id: int
    observation_kind: str
    value: str | None
    unit: str | None
    reaction: str | None
    medium: str | None
    reference_convention: str | None
    loading: str | None
    duration: str | None
    protocol: str | None
    evidence_location: str | None


def _row_to_sample(row: sqlite3.Row) -> Sample:
    return Sample(
        id=row["id"], source_id=row["source_id"], designation=row["designation"],
        parent_framework_name=row["parent_framework_name"], linker=row["linker"],
        metal_node=row["metal_node"], composition=row["composition"],
        additions=row["additions"], structure_ref=row["structure_ref"],
        activation=row["activation"], lineage_kind=row["lineage_kind"],
        derived_from_sample_id=row["derived_from_sample_id"], basis=row["basis"],
    )


def _row_to_state(row: sqlite3.Row) -> OperatingState:
    return OperatingState(
        id=row["id"], sample_id=row["sample_id"], stage=row["stage"],
        phase_assignment=row["phase_assignment"], epistemic_type=row["epistemic_type"],
        evidence_location=row["evidence_location"],
    )


def _row_to_obs(row: sqlite3.Row) -> Observation:
    return Observation(
        id=row["id"], sample_id=row["sample_id"], source_id=row["source_id"],
        observation_kind=row["observation_kind"], value=row["value"], unit=row["unit"],
        reaction=row["reaction"], medium=row["medium"],
        reference_convention=row["reference_convention"], loading=row["loading"],
        duration=row["duration"], protocol=row["protocol"],
        evidence_location=row["evidence_location"],
    )


def _opt(value: str | None) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _log(conn: sqlite3.Connection, action: str, entity_id: int, detail: dict) -> None:
    conn.execute(
        "INSERT INTO identity_event (action, entity_id, detail) VALUES (?, ?, ?)",
        (action, entity_id, json.dumps(detail)),
    )


def _require_source(conn: sqlite3.Connection, source_id) -> int:
    row = conn.execute("SELECT id FROM source WHERE id = ?", (source_id,)).fetchone()
    if row is None:
        raise IdentityValidationError(
            "Select a saved reference first — samples are recorded per source."
        )
    return int(row["id"])


def record_sample(
    conn: sqlite3.Connection,
    *,
    source_id: int,
    designation: str,
    parent_framework_name: str | None = None,
    linker: str | None = None,
    metal_node: str | None = None,
    composition: str | None = None,
    additions: str | None = None,
    structure_ref: str | None = None,
    activation: str | None = None,
    lineage_kind: str | None = None,
    derived_from_sample_id: int | None = None,
    basis: str = "experimental",
) -> Sample:
    clean_designation = _opt(designation)
    if not clean_designation:
        raise IdentityValidationError("Sample designation is empty — enter the reported name.")
    sid = _require_source(conn, source_id)
    clean_basis = basis if basis in BASIS_KINDS else None
    if clean_basis is None:
        raise IdentityValidationError(
            f"Basis must be one of {BASIS_KINDS!r} — got {basis!r}."
        )
    clean_lineage = _opt(lineage_kind)
    derived_from = int(derived_from_sample_id) if derived_from_sample_id else None
    if (clean_lineage is None) != (derived_from is None):
        raise IdentityValidationError(
            "A lineage link needs both the kind (composite/derived) and the parent sample."
        )
    if clean_lineage is not None and clean_lineage not in LINEAGE_KINDS:
        raise IdentityValidationError(
            f"Lineage kind must be one of {LINEAGE_KINDS!r} — got {clean_lineage!r}."
        )
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO sample_record (source_id, designation, parent_framework_name, "
                "linker, metal_node, composition, additions, structure_ref, activation, "
                "lineage_kind, derived_from_sample_id, basis) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (sid, clean_designation, _opt(parent_framework_name), _opt(linker),
                 _opt(metal_node), _opt(composition), _opt(additions),
                 _opt(structure_ref), _opt(activation), clean_lineage, derived_from,
                 clean_basis),
            )
            new_id = int(cur.lastrowid)
            _log(conn, "sample_recorded", new_id, {"designation": clean_designation, "source_id": sid})
    except sqlite3.Error as exc:
        raise IdentityPersistenceError(
            f"Saving failed; previously saved records are unchanged. ({exc})"
        ) from exc
    return get_sample(conn, new_id)


def get_sample(conn: sqlite3.Connection, sample_id: int) -> Sample | None:
    row = conn.execute("SELECT * FROM sample_record WHERE id = ?", (sample_id,)).fetchone()
    return None if row is None else _row_to_sample(row)


def list_samples(conn: sqlite3.Connection) -> list[Sample]:
    rows = conn.execute("SELECT * FROM sample_record ORDER BY id").fetchall()
    return [_row_to_sample(row) for row in rows]


def record_operating_state(
    conn: sqlite3.Connection,
    *,
    sample_id: int,
    stage: str,
    phase_assignment: str | None = None,
    epistemic_type: str = "unknown",
    evidence_location: str | None = None,
) -> OperatingState:
    if get_sample(conn, sample_id) is None:
        raise IdentityValidationError(f"Sample #{sample_id} does not exist.")
    if stage not in STAGES:
        raise IdentityValidationError(f"Stage must be one of {STAGES!r} — got {stage!r}.")
    if epistemic_type not in (
        "directly_reported", "author_interpretation", "tool_inference", "user_judgment", "unknown"
    ):
        raise IdentityValidationError(f"Unknown epistemic type {epistemic_type!r}.")
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO operating_state (sample_id, stage, phase_assignment, "
                "epistemic_type, evidence_location) VALUES (?, ?, ?, ?, ?)",
                (sample_id, stage, _opt(phase_assignment), epistemic_type,
                 _opt(evidence_location)),
            )
            new_id = int(cur.lastrowid)
            _log(conn, "state_recorded", new_id, {"sample_id": sample_id, "stage": stage})
    except sqlite3.Error as exc:
        raise IdentityPersistenceError(
            f"Saving failed; previously saved records are unchanged. ({exc})"
        ) from exc
    row = conn.execute("SELECT * FROM operating_state WHERE id = ?", (new_id,)).fetchone()
    return _row_to_state(row)


def record_observation(
    conn: sqlite3.Connection,
    *,
    sample_id: int,
    source_id: int,
    observation_kind: str,
    value: str | None = None,
    unit: str | None = None,
    reaction: str | None = None,
    medium: str | None = None,
    reference_convention: str | None = None,
    loading: str | None = None,
    duration: str | None = None,
    protocol: str | None = None,
    evidence_location: str | None = None,
) -> Observation:
    if get_sample(conn, sample_id) is None:
        raise IdentityValidationError(f"Sample #{sample_id} does not exist.")
    sid = _require_source(conn, source_id)
    if observation_kind not in OBSERVATION_KINDS:
        raise IdentityValidationError(
            f"Observation kind must be one of {OBSERVATION_KINDS!r} — got {observation_kind!r}."
        )
    clean_reaction = _opt(reaction)
    if clean_reaction is not None and clean_reaction not in ("HER", "OER", "other"):
        raise IdentityValidationError("Reaction must be HER, OER, other, or left unknown.")
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO observation (sample_id, source_id, observation_kind, value, "
                "unit, reaction, medium, reference_convention, loading, duration, "
                "protocol, evidence_location) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (sample_id, sid, observation_kind, _opt(value), _opt(unit),
                 clean_reaction, _opt(medium), _opt(reference_convention),
                 _opt(loading), _opt(duration), _opt(protocol), _opt(evidence_location)),
            )
            new_id = int(cur.lastrowid)
            _log(conn, "observation_recorded", new_id, {"sample_id": sample_id, "kind": observation_kind})
    except sqlite3.Error as exc:
        raise IdentityPersistenceError(
            f"Saving failed; previously saved records are unchanged. ({exc})"
        ) from exc
    row = conn.execute("SELECT * FROM observation WHERE id = ?", (new_id,)).fetchone()
    return _row_to_obs(row)


def list_observations(conn: sqlite3.Connection, sample_id: int | None = None) -> list[Observation]:
    if sample_id is None:
        rows = conn.execute("SELECT * FROM observation ORDER BY id").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM observation WHERE sample_id = ? ORDER BY id", (sample_id,)
        ).fetchall()
    return [_row_to_obs(row) for row in rows]


def list_states(conn: sqlite3.Connection, sample_id: int | None = None) -> list[OperatingState]:
    if sample_id is None:
        rows = conn.execute("SELECT * FROM operating_state ORDER BY id").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM operating_state WHERE sample_id = ? ORDER BY id", (sample_id,)
        ).fetchall()
    return [_row_to_state(row) for row in rows]


def _same(a: str | None, b: str | None) -> bool:
    return a is not None and b is not None and a.strip().lower() == b.strip().lower()


def _differ(a: str | None, b: str | None) -> bool:
    return a is not None and b is not None and a.strip().lower() != b.strip().lower()


def _save_relation(
    conn: sqlite3.Connection, left: int, right: int, level: str, relation: str,
    reason: str, evidence_location: str | None, merge_permission: str = "none",
    review_state: str = "needs_verification",
) -> dict:
    # Idempotent: re-running the same comparison must not stack duplicate rows.
    existing = conn.execute(
        "SELECT * FROM identity_relation WHERE left_sample_id = ? AND right_sample_id = ? "
        "AND level = ? AND relation = ? AND reason = ?",
        (left, right, level, relation, reason),
    ).fetchone()
    if existing is not None:
        return {
            "id": existing["id"], "left": existing["left_sample_id"],
            "right": existing["right_sample_id"], "level": existing["level"],
            "relation": existing["relation"], "reason": existing["reason"],
            "evidence_location": existing["evidence_location"],
            "review_state": existing["review_state"],
            "merge_permission": existing["merge_permission"],
        }
    with conn:
        cur = conn.execute(
            "INSERT INTO identity_relation (left_sample_id, right_sample_id, level, "
            "relation, reason, evidence_location, review_state, merge_permission) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (left, right, level, relation, reason, _opt(evidence_location),
             review_state, merge_permission),
        )
        rel_id = int(cur.lastrowid)
        _log(conn, "relation_recorded", rel_id, {"relation": relation, "level": level})
    return {
        "id": rel_id, "left": left, "right": right, "level": level,
        "relation": relation, "reason": reason,
        "evidence_location": _opt(evidence_location),
        "review_state": review_state, "merge_permission": merge_permission,
    }


def compare_samples(
    conn: sqlite3.Connection, a_id: int, b_id: int, evidence_location: str | None = None
) -> list[dict]:
    """Deterministic scoped comparison per the identity contract. Returns the
    relation(s) per level with reason, evidence location, and merge permission;
    never merges rows."""
    a = get_sample(conn, a_id)
    b = get_sample(conn, b_id)
    if a is None or b is None:
        raise IdentityValidationError("Both samples must exist to compare.")
    if a.id == b.id:
        raise IdentityValidationError("Compare two distinct sample records.")
    out: list[dict] = []
    same_source = a.source_id == b.source_id

    # Documented lineage is the researcher's explicit statement and wins first.
    if b.derived_from_sample_id == a.id and b.lineage_kind in LINEAGE_KINDS:
        out.append(_save_relation(
            conn, a.id, b.id, "sample", b.lineage_kind,
            f"Documented lineage: '{b.designation}' is recorded as {b.lineage_kind} "
            f"of '{a.designation}'" + (f" with additions: {b.additions}" if b.additions else "."),
            evidence_location,
        ))
        if _same(a.parent_framework_name, b.parent_framework_name) and a.parent_framework_name:
            out.append(_save_relation(
                conn, a.id, b.id, "framework", "same_parent_framework",
                f"Both cite the same parent framework '{a.parent_framework_name}'.",
                evidence_location,
            ))
        return out

    if _differ(a.linker, b.linker):
        reason = (
            f"Explicitly different linkers: '{a.linker}' vs '{b.linker}' "
            "(generic name similarity is not identity evidence)."
        )
        out.append(_save_relation(conn, a.id, b.id, "framework", "different", reason,
                                  evidence_location))
        out.append(_save_relation(conn, a.id, b.id, "sample", "different",
                                  "Framework differs, so the prepared samples differ.",
                                  evidence_location))
        return out

    if _differ(a.activation, b.activation):
        same_cif = _same(a.structure_ref, b.structure_ref)
        cif_note = (
            " Even a byte-identical CIF does not merge different activation histories."
            if same_cif else ""
        )
        reason = (
            f"Different activation protocols: '{a.activation}' vs '{b.activation}'.{cif_note}"
        )
        if same_cif:
            out.append(_save_relation(conn, a.id, b.id, "framework", "same_parent_framework",
                                      f"Same referenced structure model '{a.structure_ref}'.",
                                      evidence_location))
        out.append(_save_relation(conn, a.id, b.id, "sample", "different", reason,
                                  evidence_location))
        return out

    if same_source and _same(a.designation, b.designation):
        # Conflicting attribute values undermine designation sameness: expose
        # both values and block merging instead of silently absorbing them.
        conflicts = [
            (field, getattr(a, field), getattr(b, field))
            for field in ("composition", "metal_node", "parent_framework_name",
                          "activation", "structure_ref", "additions")
            if _differ(getattr(a, field), getattr(b, field))
        ]
        if conflicts:
            quoted = "; ".join(
                f"{f}: '{va}' vs '{vb}'" for f, va, vb in conflicts
            )
            out.append(_save_relation(
                conn, a.id, b.id, "sample", "unresolved",
                f"Same source and designation, but conflicting attributes — {quoted}. "
                "Both values stay visible; merging is blocked pending review.",
                evidence_location, review_state="conflicted",
            ))
            return out
        out.append(_save_relation(
            conn, a.id, b.id, "sample", "same_reported_sample",
            "Same source explicitly designates the same reported sample "
            "(designation-level sameness, not physical batch identity).",
            evidence_location, merge_permission="within_source_after_review",
        ))
        return out

    if _same(a.parent_framework_name, b.parent_framework_name) and a.parent_framework_name:
        out.append(_save_relation(
            conn, a.id, b.id, "framework", "same_parent_framework",
            f"Both cite the same parent framework '{a.parent_framework_name}'.",
            evidence_location,
        ))
        out.append(_save_relation(
            conn, a.id, b.id, "sample", "unresolved",
            "Shared parent alone never merges prepared samples — activation, "
            "additions, and designation history are not established here.",
            evidence_location,
        ))
        return out

    missing = []
    if not a.structure_ref and not b.structure_ref:
        missing.append("no structure reference (CIF/model) on either record")
    if a.source_id != b.source_id:
        missing.append("records come from different sources")
    if not _same(a.designation, b.designation):
        missing.append(f"designations differ ('{a.designation}' vs '{b.designation}')")
    reason = "Identity unresolved — " + "; ".join(missing) + ". No merge; human review required."
    out.append(_save_relation(conn, a.id, b.id, "sample", "unresolved", reason, evidence_location))
    out.append(_save_relation(conn, a.id, b.id, "framework", "unresolved",
                              "No cited structural evidence connects or distinguishes the frameworks.",
                              evidence_location))
    return out


def list_relations(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM identity_relation ORDER BY id").fetchall()
    return [
        {
            "id": r["id"], "left": r["left_sample_id"], "right": r["right_sample_id"],
            "level": r["level"], "relation": r["relation"], "reason": r["reason"],
            "evidence_location": r["evidence_location"], "review_state": r["review_state"],
            "merge_permission": r["merge_permission"],
        }
        for r in rows
    ]
