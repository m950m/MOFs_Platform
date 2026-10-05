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
