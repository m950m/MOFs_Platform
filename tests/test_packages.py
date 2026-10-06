"""Evidence-package tests (issue #19, ACs 1-4) — unit tier."""

import json
from pathlib import Path

import pytest

from mofs_platform.db.connection import connect
from mofs_platform.domain.identity import record_observation, record_sample
from mofs_platform.domain.packages import (
    PackageValidationError,
    export_package,
    import_package,
)
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import add_manual_reference


@pytest.fixture
def conn_with_data(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Which conductive MOFs for HER and OER?"))
    ref = add_manual_reference(
        conn, doi="10.9999/export-me", title="Export fixture paper",
        inspected_level="abstract", contributor="Mohammed (owner)",
    )
    sample = record_sample(
        conn, source_id=ref.id, designation="CoCoZn(HITP)2 (computational model)",
        linker="HITP", composition="CoCoZn(HITP)2", basis="computational",
    )
    record_observation(
        conn, sample_id=sample.id, source_id=ref.id, observation_kind="computational",
        value="0.39", unit="V", reaction="other", evidence_location="Abstract",
    )
    return conn, ref.id


def test_export_builds_schema_v1_package(conn_with_data):
    conn, ref_id = conn_with_data
    package = export_package(conn, [ref_id])
    assert package["package_format"] == "mofs-evidence-package"
    assert package["schema_version"] == 1
    assert package["contributor"]["name"] == "Mohammed (owner)"
    assert package["sources"][0]["doi"] == "10.9999/export-me"
    assert package["samples"][0]["designation"] == "CoCoZn(HITP)2 (computational model)"
    assert package["observations"][0]["value"] == "0.39"
    # the package must validate against the documented schema's key sets
    schema = json.loads(Path("_docs/package-schema-v1.json").read_text(encoding="utf-8"))
    top_allowed = set(schema["properties"])
    assert set(package) <= top_allowed
    # row-level conformance: every exported row's keys ⊆ the schema's row keys
    row_map = {
        "sources": set(schema["properties"]["sources"]["items"]["properties"]),
        "samples": set(schema["properties"]["samples"]["items"]["properties"]),
        "observations": set(schema["properties"]["observations"]["items"]["properties"]),
        "assertions": set(schema["properties"]["assertions"]["items"]["properties"]),
    }
    for section, allowed in row_map.items():
        for row in package[section]:
            assert set(row) <= allowed, f"{section} row drift: {set(row) - allowed}"
    assert json.dumps(package)  # JSON-serializable


def test_round_trip_export_import_creates_separate_coexisting_rows(conn_with_data):
    conn, ref_id = conn_with_data
    package = export_package(conn, [ref_id])
    package["contributor"]["name"] = "A. Contributor"
    report = import_package(conn, package)
    assert (report.sources, report.samples, report.observations) == (1, 1, 1)
    assert report.contributor == "A. Contributor"
    # coexistence: separate rows, nothing merged
    import sqlite3
    conn.row_factory = sqlite3.Row
    sources = conn.execute("SELECT id, doi, contributor, entry_method FROM source ORDER BY id").fetchall()
    assert len(sources) == 2
    assert sources[0]["doi"] == sources[1]["doi"] == "10.9999/export-me"
    assert sources[1]["contributor"] == "A. Contributor"
    assert sources[1]["entry_method"] == "package"
    samples = conn.execute("SELECT designation FROM sample_record ORDER BY id").fetchall()
    assert len(samples) == 2  # both exist — no merge
    assert conn.execute("SELECT COUNT(*) FROM observation").fetchone()[0] == 2


def test_import_forces_needs_verification_and_never_promotes(conn_with_data):
    conn, ref_id = conn_with_data
    package = export_package(conn, [ref_id])
    package["assertions"] = [
        {
            "package_id": 900, "source_package_id": ref_id,
            "claim_type": "property", "claim_text": "contributed claim",
            "evidence_location": "Abstract",
            "epistemic_type": "directly_reported",
            "review_state": "reviewed",  # overwrite attempt
        }
    ]
    with pytest.raises(PackageValidationError) as exc:
        import_package(conn, package)
    assert any("review-state overwrite" in r for r in exc.value.reasons)
    # a clean version imports as needs_verification
    del package["assertions"][0]["review_state"]
    package["assertions"][0]["package_id"] = 901
    import_package(conn, package)
    row = conn.execute(
        "SELECT review_state, extraction_author FROM assertion ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert row["review_state"] == "needs_verification"
    assert "package contributor" in row["extraction_author"]


def test_rejections_list_every_reason(conn_with_data):
    conn, _ref_id = conn_with_data
    bad = {
        "package_format": "wrong-format", "schema_version": 99,
        "sources": [{"package_id": 1, "inspected_level": "tabloid", "extra_key": 1}],
        "samples": [
            {"package_id": 1, "source_package_id": 42, "designation": "", "basis": "magic"},
        ],
        "observations": [],
        "assertions": [],
        "contributor": {},
        "rogue_top_key": True,
    }
    with pytest.raises(PackageValidationError) as exc:
        import_package(conn, bad)
    reasons = exc.value.reasons
    for fragment in (
        "wrong-format", "schema_version", "rogue_top_key", "extra_key",
        "tabloid", "does not resolve inside this package", "designation is required",
        "basis must be one of", "never anonymous",
    ):
        assert any(fragment in r for r in reasons), f"missing reason: {fragment}"


def test_round_trip_reimport_coexists_not_rejects(conn_with_data):
    """AC4: an identical re-submission does not merge — it coexists as new
    separate rows attributed to its contributor."""
    conn, ref_id = conn_with_data
    package = export_package(conn, [ref_id])
    package["contributor"]["name"] = "A. Contributor"
    import_package(conn, package)
    package2 = export_package(conn, [ref_id])
    package2["contributor"]["name"] = "B. Contributor"
    report = import_package(conn, package2)
    assert report.sources == 1  # accepted again, as separate rows
    import sqlite3
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT contributor, entry_method FROM source ORDER BY id").fetchall()
    assert [r["contributor"] for r in rows] == [
        "Mohammed (owner)", "A. Contributor", "B. Contributor"]
    assert all(r["entry_method"] == "package" for r in rows[1:])
    assert conn.execute("SELECT COUNT(*) FROM sample_record").fetchone()[0] == 3


def test_merge_attempt_keys_rejected(conn_with_data):
    """AC2: a package that structurally tries to link/overwrite local
    records is rejected, with the merge reason in the list."""
    conn, ref_id = conn_with_data
    package = export_package(conn, [ref_id])
    package["samples"][0]["merge_into_local_id"] = ref_id
    with pytest.raises(PackageValidationError) as exc:
        import_package(conn, package)
    assert any("merge attempt" in r for r in exc.value.reasons)
    assert conn.execute("SELECT COUNT(*) FROM sample_record").fetchone()[0] == 1


def test_missing_provenance_rejected(conn_with_data):
    conn, _ref = conn_with_data
    with pytest.raises(PackageValidationError) as exc:
        import_package(conn, {"package_format": "mofs-evidence-package",
                              "schema_version": 1, "contributor": {"name": ""},
                              "exported_at": "2026-10-04"})
    assert any("never anonymous" in r for r in exc.value.reasons)


def test_local_id_reference_rejected(conn_with_data):
    conn, ref_id = conn_with_data
    package = {
        "package_format": "mofs-evidence-package", "schema_version": 1,
        "exported_at": "2026-10-04T00:00:00",
        "contributor": {"name": "A. Contributor"},
        "sources": [], "samples": [
            {"package_id": 1, "source_package_id": ref_id, "designation": "X",
             "basis": "experimental"},
        ],
        "observations": [], "assertions": [], "compounds": [],
    }
    with pytest.raises(PackageValidationError) as exc:
        import_package(conn, package)
    assert any("does not resolve inside this package" in r for r in exc.value.reasons)


def test_export_requires_selection(conn_with_data):
    conn, _ref = conn_with_data
    with pytest.raises(PackageValidationError):
        export_package(conn, [])


def test_compound_round_trip_with_within_package_member(conn_with_data):
    """Gate HIGH finding: compounds must export AND import (member key
    mismatch made every compound import crash)."""
    conn, ref_id = conn_with_data
    package = export_package(conn, [ref_id])
    # a local compound attached to the selected sample
    compound = conn.execute(
        "INSERT INTO compound (canonical_name, framework_key, identity_note, "
        "created_by) VALUES ('CoCoZn(HITP)2', 'mofkey-x', 'reported candidate', "
        "'Mohammed (owner)')"
    )
    compound_id = compound.lastrowid
    sample_row = conn.execute(
        "SELECT id FROM sample_record WHERE source_id = ?", (ref_id,)
    ).fetchone()
    conn.execute(
        "INSERT INTO compound_member (compound_id, member_type, member_id, "
        "added_by, reason) VALUES (?, 'sample_record', ?, 'Mohammed (owner)', "
        "'reported')",
        (compound_id, sample_row["id"]),
    )
    conn.commit()
    package = export_package(conn, [ref_id])
    assert len(package["compounds"]) == 1  # exported now, was silently empty

    package["contributor"]["name"] = "A. Contributor"
    report = import_package(conn, package)
    assert report.compounds == 1
    imported = conn.execute(
        "SELECT c.canonical_name, cm.member_id FROM compound c "
        "JOIN compound_member cm ON cm.compound_id = c.id "
        "WHERE c.canonical_name = 'CoCoZn(HITP)2' AND c.created_by = 'A. Contributor'"
    ).fetchone()
    assert imported is not None
    # the imported member is the IMPORTED sample, never the local one
    local_sample_id = sample_row["id"]
    assert imported["member_id"] != local_sample_id
    assert imported["member_id"] > local_sample_id


def test_export_id_spaces_do_not_coincide(conn_with_data):
    """Gate HIGH: membership/lineage/conflict must be tested against the
    EXPORTED sample/assertion id sets, never the selected source ids. This
    layout forces sample/assertion ids to differ from source ids."""
    conn, ref_id = conn_with_data
    # a SECOND source (id 2) so source-id and sample-id spaces diverge
    ref2 = add_manual_reference(conn, doi="10.9999/other-source", title="Other")
    sample = conn.execute(
        "SELECT id FROM sample_record WHERE source_id = ?", (ref_id,)
    ).fetchone()
    sample_id = sample["id"]  # created AFTER ref_id → ids may coincide; force drift:
    # add a sample under the SECOND source so the next sample id skips away
    drift = record_sample(conn, source_id=ref2.id, designation="Drift sample")
    # compound: member is sample_id (under ref_id) — sample id ≠ ref2.id likely;
    # the assertion below holds regardless of coincidence because we assert
    # against behavior, not ids.
    conn.execute(
        "INSERT INTO compound (canonical_name, framework_key, identity_note, created_by) "
        "VALUES ('CoCoZn(HITP)2', NULL, 'reported candidate', 'Mohammed (owner)')"
    )
    conn.execute(
        "INSERT INTO compound_member (compound_id, member_type, member_id, added_by, "
        "reason) VALUES ((SELECT MAX(id) FROM compound), 'sample_record', ?, "
        "'Mohammed (owner)', 'reported')", (sample_id,))
    # two conflicting assertions under ref_id
    first = conn.execute(
        "INSERT INTO assertion (source_id, claim_type, claim_text, epistemic_type, "
        "review_state) VALUES (?, 'property', 'Claim A', 'directly_reported', "
        "'conflicted')", (ref_id,)).lastrowid
    second = conn.execute(
        "INSERT INTO assertion (source_id, claim_type, claim_text, epistemic_type, "
        "review_state, conflicts_with) VALUES (?, 'property', 'Claim B', "
        "'directly_reported', 'conflicted', ?)", (ref_id, first)).lastrowid
    # lineage: drift sample DERIVES from sample_id (parent in selection)
    conn.execute(
        "UPDATE sample_record SET lineage_kind = 'derived', "
        "derived_from_sample_id = ? WHERE id = ?", (sample_id, drift.id))
    conn.commit()

    # export BOTH sources: both samples inside, ids non-coinciding with sources
    package = export_package(conn, [ref_id, ref2.id])
    exported_sample_ids = {s["package_id"] for s in package["samples"]}
    assert sample_id in exported_sample_ids and drift.id in exported_sample_ids
    # compound with an in-selection member exports WITH its member
    assert len(package["compounds"]) == 1
    assert package["compounds"][0]["member_package_ids"][0]["member_package_id"] == sample_id
    # lineage whose parent IS in the package stays (drift derives from sample_id)
    lineages = [(s["lineage_kind"], s["lineage_parent_package_id"]) for s in package["samples"]]
    assert ("derived", sample_id) in lineages
    # conflict links between two exported assertions stay
    conflicts = {a["package_id"]: a["conflicts_with_package_id"] for a in package["assertions"]}
    assert conflicts.get(second) == first

    # S5/S8: importing the exported package must SUCCEED (self-importable)
    package["contributor"]["name"] = "A. Contributor"
    report = import_package(conn, package)
    assert report.compounds == 1 and report.assertions == 2


def test_export_neutralizes_and_excludes_out_of_selection(conn_with_data):
    """S2/S3/S6-style: lineage parent and compound members OUTSIDE the
    selection are dropped/excluded — never exported as dangling references."""
    conn, ref_id = conn_with_data
    ref2 = add_manual_reference(conn, doi="10.9999/out-source", title="Out")
    outside = record_sample(conn, source_id=ref2.id, designation="Outside sample")
    inside = conn.execute(
        "SELECT id FROM sample_record WHERE source_id = ?", (ref_id,)
    ).fetchone()["id"]
    # lineage points OUTSIDE the selection
    conn.execute(
        "UPDATE sample_record SET lineage_kind = 'derived', "
        "derived_from_sample_id = ? WHERE id = ?", (outside.id, inside))
    # compound with an OUT-of-selection member
    conn.execute(
        "INSERT INTO compound (canonical_name, identity_note, created_by) "
        "VALUES ('Mixed compound', 'n', 'Mohammed (owner)')")
    conn.execute(
        "INSERT INTO compound_member (compound_id, member_type, member_id, added_by, "
        "reason) VALUES ((SELECT MAX(id) FROM compound), 'sample_record', ?, 'o', 'r')",
        (outside.id,))
    conn.execute(
        "INSERT INTO compound_member (compound_id, member_type, member_id, added_by, "
        "reason) VALUES ((SELECT MAX(id) FROM compound), 'sample_record', ?, 'o', 'r')",
        (inside,))
    conn.commit()
    package = export_package(conn, [ref_id])
    # the lineage pair is neutralized together (importable)
    assert package["samples"][0]["lineage_kind"] is None
    assert package["samples"][0]["lineage_parent_package_id"] is None
    # the mixed compound is EXCLUDED (a member is outside the selection)
    assert package["compounds"] == []
    # and the package self-imports
    package["contributor"]["name"] = "A. Contributor"
    report = import_package(conn, package)
    assert report.samples == 1
