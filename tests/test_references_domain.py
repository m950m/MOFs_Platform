"""Domain tests for reference capture (issue #6)."""

import sqlite3

import pytest

from mofs_platform.db.connection import connect
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import (
    ReferencePersistenceError,
    ReferenceValidationError,
    add_manual_reference,
    count_captures,
    enrich_with_crossref,
    get_reference,
    list_references,
)
from mofs_platform.sources import crossref


@pytest.fixture
def conn_with_question(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Which prepared MOF samples merit inspection?"))
    return conn


def test_manual_reference_requires_a_saved_question(db_path):
    conn = connect(db_path)
    with pytest.raises(ReferenceValidationError):
        add_manual_reference(conn, title="Orphan reference")
    assert list_references(conn) == []


def test_manual_minimal_entry_is_a_lead_linked_to_the_question(conn_with_question):
    conn = conn_with_question
    ref = add_manual_reference(conn, title="Some cited paper (supplied)", contributor="Mohammed (owner)")
    assert ref.question_id == 1
    assert ref.entry_method == "manual"
    assert ref.inspected_level == "unknown"
    assert count_captures(conn) == 1


def test_manual_entry_requires_at_least_one_pointer(conn_with_question):
    conn = conn_with_question
    with pytest.raises(ReferenceValidationError):
        add_manual_reference(conn)  # nothing supplied
    assert list_references(conn) == []


def test_recapturing_same_doi_keeps_both_capture_contexts(conn_with_question):
    conn = conn_with_question
    add_manual_reference(conn, doi="10.9999/first-capture", title="First version")
    add_manual_reference(
        conn,
        doi="10.9999/first-capture",
        title="Second capture with corrected note",
        supplied_input="I read the methods section (attributed)",
        contributor="Mohammed (owner)",
    )
    refs = list_references(conn)
    assert len(refs) == 1  # one reference, not a duplicate
    assert refs[0].supplied_input == "I read the methods section (attributed)"
    assert count_captures(conn) == 2
    events = conn.execute(
        "SELECT previous_json, updated_json FROM source_capture_event ORDER BY id"
    ).fetchall()
    assert events[0]["previous_json"] is None  # first capture
    assert "First version" in events[1]["previous_json"]  # earlier context retained


def test_enrich_fills_only_missing_fields_and_records_context(conn_with_question, monkeypatch):
    conn = conn_with_question
    ref = add_manual_reference(
        conn,
        doi="10.1016/j.matt.2021.02.015",
        title="My own supplied title",
        inspected_level="user_passage",
    )
    metadata = crossref.CrossrefMetadata(
        doi=ref.doi,
        title="Publisher title (must NOT overwrite)",
        container="Matter",
        issued_year="2021",
        license_url="https://elsevier.example/license",
        url="https://doi.org/10.1016/j.matt.2021.02.015",
        indexed="2026-10-02T00:00:00",
    )
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.fetch_metadata", lambda *a, **k: metadata
    )
    updated, failure = enrich_with_crossref(conn, ref.id, "owner@example.com")
    assert failure is None
    assert updated.title == "My own supplied title"  # never overwritten
    assert updated.container == "Matter"  # filled
    assert updated.issued_year == "2021"
    assert updated.inspected_level == "user_passage"  # enrichment never raises inspection
    assert count_captures(conn) == 2  # captured + crossref_enriched
    event = conn.execute(
        "SELECT action, previous_json FROM source_capture_event ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert event["action"] == "crossref_enriched"
    assert "My own supplied title" in event["previous_json"]


def test_enrich_failure_leaves_reference_untouched(conn_with_question, monkeypatch):
    conn = conn_with_question
    ref = add_manual_reference(conn, doi="10.9999/does-not-exist", title="Typed citation")
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.fetch_metadata",
        lambda *a, **k: crossref.CrossrefFailure("no_hit", "No Crossref record."),
    )
    updated, failure = enrich_with_crossref(conn, ref.id, "owner@example.com")
    assert updated is None
    assert failure.kind == "no_hit"
    saved = get_reference(conn, ref.id)
    assert saved.title == "Typed citation"  # unchanged
    assert count_captures(conn) == 1  # no event for a failed capture


def test_enrich_requires_a_doi(conn_with_question):
    conn = conn_with_question
    ref = add_manual_reference(conn, title="No DOI anywhere")
    with pytest.raises(ReferenceValidationError):
        enrich_with_crossref(conn, ref.id, "owner@example.com")


def test_restart_persistence(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Which prepared MOF samples merit inspection?"))
    add_manual_reference(conn, doi="10.9999/survives", title="Persistent lead")
    conn.close()

    reopened = connect(db_path)
    refs = list_references(reopened)
    assert len(refs) == 1
    assert refs[0].doi == "10.9999/survives"
    assert refs[0].question_id == 1  # still linked to the saved question
    reopened.close()


def test_save_failure_preserves_references(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    add_manual_reference(conn, doi="10.9999/kept", title="Kept reference")
    conn.close()

    readonly = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    readonly.row_factory = sqlite3.Row
    with pytest.raises(ReferencePersistenceError):
        add_manual_reference(readonly, doi="10.9999/never", title="Never saved")
    refs = list_references(readonly)
    assert len(refs) == 1
    assert refs[0].doi == "10.9999/kept"
    readonly.close()
