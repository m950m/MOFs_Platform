"""Evidence packages (issue #19, ACs 1–4): attributed offline collaboration.

Export produces a schema-v1 package from selected sources and their
dependents. Import validates STRICTLY and collects EVERY reason before
deciding: schema drift, version mismatch, missing provenance, review-state
overwrite attempts, and merge attempts (any row carrying local-linking
keys such as existing_local_id or merge_into) are all rejected. Accepted imports create NEW separate rows attributed to the
package contributor, every row entering as `needs_verification` — the
import never auto-promotes review states, never merges, and never attaches
to local records (identity invariants, D5).
"""

import json
import sqlite3
from dataclasses import dataclass, field

FORMAT = "mofs-evidence-package"
SUPPORTED_VERSION = 1

_TOP_KEYS = {
    "package_format", "schema_version", "exported_at", "contributor",
    "sources", "samples", "observations", "assertions", "compounds",
}
_CONTRIBUTOR_KEYS = {"name"}
_SOURCE_KEYS = {
    "package_id", "doi", "url", "title", "supplied_input", "inspected_level",
    "rights_note", "container", "issued_year",
}
_SAMPLE_KEYS = {
    "package_id", "source_package_id", "designation", "basis",
    "parent_framework_name", "linker", "metal_node", "composition",
    "additions", "structure_ref", "activation", "lineage_kind",
    "lineage_parent_package_id",
}
_OBSERVATION_KEYS = {
    "package_id", "sample_package_id", "source_package_id", "observation_kind",
    "value", "unit", "reaction", "medium", "reference_convention", "loading",
    "duration", "protocol", "evidence_location",
}
_ASSERTION_KEYS = {
    "package_id", "source_package_id", "claim_type", "claim_text",
    "evidence_location", "epistemic_type", "conflicts_with_package_id",
}
_COMPOUND_KEYS = {
    "package_id", "canonical_name", "framework_key", "identity_note",
    "member_package_ids",
}
_MEMBER_KEYS = {"member_type", "member_package_id"}

_SOURCE_LEVELS = {"unknown", "metadata", "abstract", "full_text", "user_passage"}
_SAMPLE_BASES = {"experimental", "computational", "hypothetical"}
_OBSERVATION_KINDS = {"experimental", "computational", "hypothetical"}
_REACTIONS = {None, "HER", "OER", "other"}
_CLAIM_TYPES = {"preparation", "composition", "property", "application", "other"}
_EPISTEMIC = {
    "directly_reported", "author_interpretation", "tool_inference",
    "user_judgment", "unknown",
}
_LINEAGE = {None, "composite", "derived"}
_MEMBER_TYPES = {"sample_record", "structure_index"}


class PackageValidationError(ValueError):
    """The package is rejected — `.reasons` lists EVERY reason."""

    def __init__(self, reasons: list[str]):
        self.reasons = reasons
        super().__init__(
            "Package rejected — " + str(len(reasons)) + " reason(s): "
            + " | ".join(reasons)
        )


class PackagePersistenceError(RuntimeError):
    """Saving failed; previously saved records are unchanged."""


@dataclass(frozen=True)
class ImportReport:
    sources: int
    samples: int
    observations: int
    assertions: int
    compounds: int
    contributor: str
    review_state: str = "needs_verification"
    notes: list = field(default_factory=list)


def export_package(conn: sqlite3.Connection, source_ids: list[int]) -> dict:
    """Build a schema-v1 package from the selected sources and their
    dependents (assertions, samples, observations), plus compounds whose
    members all fall inside the selection. Rows keep their local ids as
    package_ids — import never reuses them."""
    from datetime import UTC, datetime

    if not source_ids:
        raise PackageValidationError(
            ["Export rejected — select at least one source to export."]
        )
    ids = [int(s) for s in source_ids]
    sources = conn.execute(
        f"SELECT * FROM source WHERE id IN ({','.join('?' * len(ids))})", ids
    ).fetchall()
    if len(sources) != len(set(ids)):
        raise PackageValidationError(
            ["Export rejected — one or more selected sources do not exist."]
        )
    package = {
        "package_format": FORMAT,
        "schema_version": SUPPORTED_VERSION,
        "exported_at": datetime.now(UTC).isoformat(),
        "contributor": {"name": "Mohammed (owner)"},
        "sources": [], "samples": [], "observations": [], "assertions": [],
        "compounds": [],
    }
    for row in sources:
        package["sources"].append({
            "package_id": row["id"],
            "doi": row["doi"], "url": row["url"], "title": row["title"],
            "supplied_input": row["supplied_input"],
            "inspected_level": row["inspected_level"],
            "rights_note": row["rights_note"], "container": row["container"],
            "issued_year": row["issued_year"],
        })
    exported_sample_ids: set[int] = set()
    for row in conn.execute(
        f"SELECT * FROM sample_record WHERE source_id IN ({','.join('?' * len(ids))})", ids
    ):
        exported_sample_ids.add(row["id"])
        package["samples"].append({
            "package_id": row["id"], "source_package_id": row["source_id"],
            "designation": row["designation"], "basis": row["basis"],
            "parent_framework_name": row["parent_framework_name"],
            "linker": row["linker"], "metal_node": row["metal_node"],
            "composition": row["composition"], "additions": row["additions"],
            "structure_ref": row["structure_ref"], "activation": row["activation"],
            # a lineage parent OUTSIDE the selection is a local fact — the
            # pair is neutralized together so the package stays importable
            "lineage_kind": row["lineage_kind"]
            if row["derived_from_sample_id"] in exported_sample_ids else None,
            "lineage_parent_package_id": row["derived_from_sample_id"]
            if row["derived_from_sample_id"] in exported_sample_ids else None,
        })
    for row in conn.execute(
        f"SELECT * FROM observation WHERE source_id IN ({','.join('?' * len(ids))})", ids
    ):
        package["observations"].append({
            "package_id": row["id"], "sample_package_id": row["sample_id"],
            "source_package_id": row["source_id"],
            "observation_kind": row["observation_kind"], "value": row["value"],
            "unit": row["unit"], "reaction": row["reaction"],
            "medium": row["medium"],
            "reference_convention": row["reference_convention"],
            "loading": row["loading"], "duration": row["duration"],
            "protocol": row["protocol"],
            "evidence_location": row["evidence_location"],
        })
    exported_assertion_ids: set[int] = set()
    for row in conn.execute(
        f"SELECT * FROM assertion WHERE source_id IN ({','.join('?' * len(ids))})", ids
    ):
        exported_assertion_ids.add(row["id"])
        package["assertions"].append({
            "package_id": row["id"], "source_package_id": row["source_id"],
            "claim_type": row["claim_type"], "claim_text": row["claim_text"],
            "evidence_location": row["evidence_location"],
            "epistemic_type": row["epistemic_type"],
            "conflicts_with_package_id": row["conflicts_with"]
            if row["conflicts_with"] in exported_assertion_ids else None,
        })
    # compounds: exported ONLY when every sample member is inside the
    # selection (v1 members are samples; structure members never export —
    # they cannot be re-created outside this machine)
    for row in conn.execute("SELECT * FROM compound ORDER BY id"):
        members = conn.execute(
            "SELECT * FROM compound_member WHERE compound_id = ? ORDER BY id",
            (row["id"],),
        ).fetchall()
        if not members or any(
            m["member_type"] != "sample_record" or m["member_id"] not in exported_sample_ids
            for m in members
        ):
            continue
        package["compounds"].append({
            "package_id": row["id"], "canonical_name": row["canonical_name"],
            "framework_key": row["framework_key"],
            "identity_note": row["identity_note"],
            "member_package_ids": [
                {"member_type": m["member_type"], "member_package_id": m["member_id"]}
                for m in members
            ],
        })
    return package


def _validate_row_keys(kind: str, row: dict, allowed: set, reasons: list) -> None:
    unknown = set(row) - allowed
    if unknown:
        reasons.append(
            f"schema drift in {kind} package_id={row.get('package_id')}: unknown "
            f"keys {sorted(unknown)} (the schema is strict — see "
            "_docs/package-schema-v1.json)"
        )


def import_package(
    conn: sqlite3.Connection, raw: str | bytes | dict,
    contributor_override: str | None = None,
) -> ImportReport:
    """Validate strictly (every reason collected) then import in one
    transaction. Raises PackageValidationError (with the full reason list)
    when anything fails."""
    reasons: list[str] = []
    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        if isinstance(raw, str):
            package = json.loads(raw)
        else:
            package = raw
    except UnicodeDecodeError as exc:
        raise PackageValidationError(
            [f"the payload is not valid UTF-8 text. ({exc})"]
        ) from exc
    except json.JSONDecodeError as exc:
        raise PackageValidationError(
            [f"the payload is not valid JSON. ({exc})"]
        ) from exc
    if not isinstance(package, dict):
        raise PackageValidationError(["the payload must be a JSON object."])

    unknown_top = set(package) - _TOP_KEYS
    if unknown_top:
        reasons.append(
            f"schema drift: unknown top-level keys {sorted(unknown_top)}"
        )
    if package.get("package_format") != FORMAT:
        reasons.append(
            f"package_format must be '{FORMAT}' — got "
            f"{package.get('package_format')!r}."
        )
    if package.get("schema_version") != SUPPORTED_VERSION:
        reasons.append(
            f"schema_version must be {SUPPORTED_VERSION} — got "
            f"{package.get('schema_version')!r}. A different version needs a "
            "format migration, never a silent import."
        )
    if not package.get("exported_at"):
        reasons.append("exported_at is missing — provenance requires the export time.")
    if conn.execute("SELECT COUNT(*) FROM question").fetchone()[0] == 0:
        reasons.append(
            "no research question exists locally — save one first; sources "
            "attach to the question."
        )

    contributor_raw = package.get("contributor")
    if not isinstance(contributor_raw, dict):
        reasons.append("contributor object is missing — packages are never anonymous.")
        contributor_name = None
    else:
        unknown_contrib = set(contributor_raw) - _CONTRIBUTOR_KEYS
        if unknown_contrib:
            reasons.append(
                f"schema drift in contributor: unknown keys {sorted(unknown_contrib)}"
            )
        contributor_name = _clean(contributor_raw.get("name"))
        if not contributor_name:
            reasons.append(
                "contributor.name is empty — packages are never anonymous."
            )
    contributor = contributor_override or contributor_name
    if contributor and not _clean(contributor):
        reasons.append("the overriding contributor name is empty.")

    sources = package.get("sources") or []
    samples = package.get("samples") or []
    observations = package.get("observations") or []
    assertions = package.get("assertions") or []
    compounds = package.get("compounds") or []
    for name, rows, allowed in (
        ("sources", sources, _SOURCE_KEYS),
        ("samples", samples, _SAMPLE_KEYS),
        ("observations", observations, _OBSERVATION_KEYS),
        ("assertions", assertions, _ASSERTION_KEYS),
        ("compounds", compounds, _COMPOUND_KEYS),
    ):
        if not isinstance(rows, list):
            reasons.append(f"{name} must be a list.")
            continue
        for row in rows:
            if not isinstance(row, dict):
                reasons.append(f"{name} contains a non-object row.")
                continue
            _validate_row_keys(name, row, allowed, reasons)

    # provenance + vocabulary per source
    source_ids = set()
    for row in sources:
        pid = row.get("package_id")
        if not isinstance(pid, int):
            reasons.append(f"source with missing/invalid package_id: {row}.")
            continue
        if pid in source_ids:
            reasons.append(f"duplicate source package_id {pid}.")
        source_ids.add(pid)
        if row.get("inspected_level") not in _SOURCE_LEVELS:
            reasons.append(
                f"source {pid}: inspected_level must be one of "
                f"{sorted(_SOURCE_LEVELS)} — got {row.get('inspected_level')!r}."
            )
        if not any(_clean(row.get(k)) for k in ("doi", "url", "title", "supplied_input")):
            reasons.append(
                f"source {pid}: at least one pointer (doi/url/title/supplied_input) "
                "is required — provenance needs something that was actually read."
            )
        for field_name, pattern in (("doi", "10."),):
            value = _clean(row.get(field_name))
            if value and not value.startswith(pattern):
                reasons.append(f"source {pid}: {field_name} '{value}' does not look like a DOI.")

    # samples: source refs resolve in-package; vocabularies; lineage
    sample_ids = set()
    for row in samples:
        pid = row.get("package_id")
        if not isinstance(pid, int):
            reasons.append(f"sample with missing/invalid package_id: {row}.")
            continue
        if pid in sample_ids:
            reasons.append(f"duplicate sample package_id {pid}.")
        sample_ids.add(pid)
        if row.get("source_package_id") not in source_ids:
            reasons.append(
                f"sample {pid}: source_package_id {row.get('source_package_id')!r} "
                "does not resolve inside this package (local-id references are "
                "rejected)."
            )
        if not _clean(row.get("designation")):
            reasons.append(f"sample {pid}: designation is required.")
        if row.get("basis") not in _SAMPLE_BASES:
            reasons.append(
                f"sample {pid}: basis must be one of {sorted(_SAMPLE_BASES)}."
            )
        if (row.get("lineage_kind") is None) != (row.get("lineage_parent_package_id") is None):
            reasons.append(
                f"sample {pid}: lineage needs BOTH lineage_kind and "
                "lineage_parent_package_id (or neither)."
            )
        if row.get("lineage_parent_package_id") not in ({None} | sample_ids):
            reasons.append(
                f"sample {pid}: lineage_parent_package_id does not resolve inside "
                "this package."
            )
        state = row.get("review_state")
        if state is not None and state != "needs_verification":
            reasons.append(
                f"sample {pid}: review-state overwrite attempt ({state!r}) — "
                "imports always enter as needs_verification."
            )

    obs_ids = set()
    for row in observations:
        pid = row.get("package_id")
        if not isinstance(pid, int):
            reasons.append(f"observation with missing/invalid package_id: {row}.")
            continue
        obs_ids.add(pid)
        if row.get("sample_package_id") not in sample_ids:
            reasons.append(
                f"observation {pid}: sample_package_id does not resolve inside "
                "this package."
            )
        if row.get("source_package_id") not in source_ids:
            reasons.append(
                f"observation {pid}: source_package_id does not resolve inside "
                "this package."
            )
        if row.get("observation_kind") not in _OBSERVATION_KINDS:
            reasons.append(
                f"observation {pid}: observation_kind must be one of "
                f"{sorted(_OBSERVATION_KINDS)}."
            )
        if row.get("reaction") not in _REACTIONS:
            reasons.append(
                f"observation {pid}: reaction must be one of {sorted(_REACTIONS)}."
            )
        state = row.get("review_state")
        if state is not None and state != "needs_verification":
            reasons.append(
                f"observation {pid}: review-state overwrite attempt ({state!r})."
            )

    assertion_ids = set()
    for row in assertions:
        pid = row.get("package_id")
        if not isinstance(pid, int):
            reasons.append(f"assertion with missing/invalid package_id: {row}.")
            continue
        assertion_ids.add(pid)
        if row.get("source_package_id") not in source_ids:
            reasons.append(
                f"assertion {pid}: source_package_id does not resolve inside this "
                "package."
            )
        if row.get("claim_type") not in _CLAIM_TYPES:
            reasons.append(
                f"assertion {pid}: claim_type must be one of {sorted(_CLAIM_TYPES)}."
            )
        if not _clean(row.get("claim_text")):
            reasons.append(f"assertion {pid}: claim_text is required.")
        if row.get("epistemic_type") not in _EPISTEMIC:
            reasons.append(
                f"assertion {pid}: epistemic_type must be one of {sorted(_EPISTEMIC)}."
            )
        conflict = row.get("conflicts_with_package_id")
        if conflict is not None and conflict not in assertion_ids:
            reasons.append(
                f"assertion {pid}: conflicts_with_package_id must reference an "
                "assertion that appears EARLIER in this package."
            )
        state = row.get("review_state")
        if state is not None and state != "needs_verification":
            reasons.append(
                f"assertion {pid}: review-state overwrite attempt ({state!r})."
            )

    for row in compounds:
        pid = row.get("package_id")
        if not isinstance(pid, int):
            reasons.append(f"compound with missing/invalid package_id: {row}.")
            continue
        if not _clean(row.get("canonical_name")):
            reasons.append(f"compound {pid}: canonical_name is required.")
        if not _clean(row.get("identity_note")):
            reasons.append(f"compound {pid}: identity_note is required.")
        members = row.get("member_package_ids") or []
        for member in members:
            if not isinstance(member, dict):
                reasons.append(f"compound {pid}: a member is not an object.")
                continue
            unknown = set(member) - _MEMBER_KEYS
            if unknown:
                reasons.append(
                    f"compound {pid}: unknown member keys {sorted(unknown)}."
                )
            if member.get("member_type") not in _MEMBER_TYPES:
                reasons.append(
                    f"compound {pid}: member_type must be one of "
                    f"{sorted(_MEMBER_TYPES)}."
                )
                continue
            member_key = member.get("member_package_id")
            pool = sample_ids if member.get("member_type") == "sample_record" else None
            if member.get("member_type") == "structure_index":
                reasons.append(
                    f"compound {pid}: v1 packages cannot attach structure_index "
                    "members (no local or package structure store is imported)."
                )
            elif member_key not in pool:
                reasons.append(
                    f"compound {pid}: member sample {member_key!r} does not resolve "
                    "inside this package."
                )

    # merge attempts: any key that tries to link/overwrite LOCAL records.
    # The import itself can never merge (everything becomes new separate
    # rows — AC4 coexistence), so a merge attempt is structural and is
    # rejected with a named reason.
    _MERGE_ATTEMPT_KEYS = ("existing_local_id", "merge_into", "local_id",
                           "overwrite", "replace_local")
    for kind, rows_set in (("sample", samples), ("observation", observations),
                           ("assertion", assertions), ("compound", compounds)):
        for row in rows_set:
            if not isinstance(row, dict):
                continue
            hit_keys = [k for k in row if any(m in str(k).lower() for m in _MERGE_ATTEMPT_KEYS)]
            if hit_keys:
                reasons.append(
                    f"merge attempt: {kind} package_id="
                    f"{row.get('package_id')} carries local-linking keys "
                    f"{sorted(hit_keys)} — packages never merge into or "
                    "overwrite local records; imported data coexists as "
                    "separate rows."
                )

    if reasons:
        raise PackageValidationError(reasons)

    # ---------- import: one transaction, attributed, needs_verification ------
    contributor_final = _clean(contributor)
    id_map: dict[tuple[str, int], int] = {}
    try:
        with conn:
            for row in sources:
                cur = conn.execute(
                    "INSERT INTO source (question_id, doi, url, title, supplied_input, "
                    "inspected_level, contributor, rights_note, container, "
                    "issued_year, entry_method) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (row.get("doi"), row.get("url"), row.get("title"),
                     row.get("supplied_input"), row.get("inspected_level"),
                     contributor_final, row.get("rights_note"),
                     row.get("container"), row.get("issued_year"),
                     'package'),
                )
                id_map[("source", row["package_id"])] = int(cur.lastrowid)
                conn.execute(
                    "INSERT INTO source_capture_event (action, source_id, "
                    "previous_json, updated_json) VALUES ('captured', ?, NULL, ?)",
                    (int(cur.lastrowid), _snapshot(conn, int(cur.lastrowid), "source")),
                )
            for row in samples:
                cur = conn.execute(
                    "INSERT INTO sample_record (source_id, designation, "
                    "parent_framework_name, linker, metal_node, composition, "
                    "additions, structure_ref, activation, lineage_kind, "
                    "derived_from_sample_id, basis) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (id_map[("source", row["source_package_id"])],
                     row.get("designation"), row.get("parent_framework_name"),
                     row.get("linker"), row.get("metal_node"),
                     row.get("composition"), row.get("additions"),
                     row.get("structure_ref"), row.get("activation"),
                     row.get("lineage_kind"),
                     id_map.get(("sample", row.get("lineage_parent_package_id"))),
                     row.get("basis")),
                )
                id_map[("sample", row["package_id"])] = int(cur.lastrowid)
            for row in observations:
                cur = conn.execute(
                    "INSERT INTO observation (sample_id, source_id, "
                    "observation_kind, value, unit, reaction, medium, "
                    "reference_convention, loading, duration, protocol, "
                    "evidence_location) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (id_map[("sample", row["sample_package_id"])],
                     id_map[("source", row["source_package_id"])],
                     row.get("observation_kind"), row.get("value"),
                     row.get("unit"), row.get("reaction"), row.get("medium"),
                     row.get("reference_convention"), row.get("loading"),
                     row.get("duration"), row.get("protocol"),
                     row.get("evidence_location")),
                )
                id_map[("observation", row["package_id"])] = int(cur.lastrowid)
            for row in assertions:
                conflict_local = id_map.get(
                    ("assertion", row.get("conflicts_with_package_id"))
                )
                cur = conn.execute(
                    "INSERT INTO assertion (source_id, claim_type, claim_text, "
                    "evidence_location, extraction_author, epistemic_type, "
                    "review_state, conflicts_with) VALUES (?, ?, ?, ?, ?, ?, "
                    "'needs_verification', ?)",
                    (id_map[("source", row["source_package_id"])],
                     row.get("claim_type"), row.get("claim_text"),
                     row.get("evidence_location"),
                     f"package contributor: {contributor_final}",
                     row.get("epistemic_type"), conflict_local),
                )
                id_map[("assertion", row["package_id"])] = int(cur.lastrowid)
            for row in compounds:
                cur = conn.execute(
                    "INSERT INTO compound (canonical_name, framework_key, "
                    "identity_note, created_by) VALUES (?, ?, ?, ?)",
                    (row.get("canonical_name"), row.get("framework_key"),
                     row.get("identity_note"), contributor_final),
                )
                compound_id = int(cur.lastrowid)
                for member in row.get("member_package_ids") or []:
                    member_type = member.get("member_type")
                    local_key = "sample" if member_type == "sample_record" else member_type
                    local_id = id_map.get(
                        (local_key, member.get("member_package_id"))
                    )
                    conn.execute(
                        "INSERT INTO compound_member (compound_id, member_type, "
                        "member_id, added_by, reason) VALUES (?, ?, ?, ?, ?)",
                        (compound_id, member.get("member_type"), local_id,
                         contributor_final,
                         "member of an imported evidence package"),
                    )
                id_map[("compound", row["package_id"])] = compound_id
    except sqlite3.Error as exc:
        raise PackagePersistenceError(
            f"Import failed; nothing was recorded. ({exc})"
        ) from exc
    return ImportReport(
        sources=len(sources), samples=len(samples),
        observations=len(observations), assertions=len(assertions),
        compounds=len(compounds), contributor=contributor_final,
    )


def _snapshot(conn: sqlite3.Connection, source_id: int, table: str) -> str:
    row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (source_id,)).fetchone()
    return json.dumps({k: row[k] for k in dict(row)}, ensure_ascii=False)


def _clean(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
