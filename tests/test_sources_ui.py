"""UI tests for the Sources page (issue #6)."""

import pytest

from conftest import all_text
from mofs_platform.db.connection import connect
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import list_references
from mofs_platform.sources import crossref


def by_key(elements, key):
    matches = [e for e in elements if e.key == key]
    assert len(matches) == 1, f"expected exactly one element with key {key!r}"
    return matches[0]


def _open_sources_page(at):
    at.sidebar.radio[0].set_value("Sources")
    at.run()


@pytest.fixture
def app_with_question(run_app, db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Which prepared MOF samples merit inspection?"))
    conn.close()
    return run_app()


def test_sources_page_requires_saved_question_first(run_app):
    at = run_app()
    _open_sources_page(at)
    text = all_text(at)
    assert "No research question is saved yet" in text
    assert "Capture reference" not in text  # entry surface withheld


def test_manual_capture_creates_attributed_lead(app_with_question, db_path):
    at = app_with_question
    _open_sources_page(at)
    by_key(at.text_input, "ref_doi").set_value("10.9999/manual-lead")
    by_key(at.text_area, "ref_title").set_value("A paper the researcher supplies")
    by_key(at.text_input, "ref_contributor").set_value("Mohammed (owner)")
    by_key(at.button, "save_reference").click()
    at.run()
    assert any("Reference captured (lead)" in s.value for s in at.success)
    text = all_text(at)
    assert "Origin: `manual`" in text
    assert "Mohammed (owner)" in text
    refs = list_references(connect(db_path))
    assert len(refs) == 1 and refs[0].question_id == 1


def test_metadata_only_lead_is_labeled_needs_verification(app_with_question):
    at = app_with_question
    _open_sources_page(at)
    by_key(at.text_input, "ref_doi").set_value("10.9999/metadata-only")
    by_key(at.button, "save_reference").click()
    at.run()
    text = all_text(at)
    assert "needs verification" in text  # metadata-only lead labeled, not verified


def test_enrich_success_shows_metadata_and_stays_lead(app_with_question, db_path, monkeypatch):
    metadata = crossref.CrossrefMetadata(
        doi="10.9999/enrich-me",
        title="Publisher title from Crossref",
        container="Some Journal",
        issued_year="2024",
        license_url="https://example.com/license",
        url="https://doi.org/10.9999/enrich-me",
        indexed="2026-10-02T00:00:00",
    )
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.fetch_metadata", lambda *a, **k: metadata
    )
    at = app_with_question
    _open_sources_page(at)
    by_key(at.text_input, "ref_doi").set_value("10.9999/enrich-me")
    by_key(at.button, "save_reference").click()
    at.run()
    by_key(at.button, "enrich_1").click()
    at.run()
    text = all_text(at)
    assert "Publisher title from Crossref" in text
    assert "Some Journal" in text
    assert "the reference remains a lead" in text
    assert len(list_references(connect(db_path))) == 1


def test_enrich_no_hit_shows_honest_warning_not_novelty_claim(app_with_question, monkeypatch):
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.fetch_metadata",
        lambda *a, **k: crossref.CrossrefFailure("no_hit", "No Crossref record."),
    )
    at = app_with_question
    _open_sources_page(at)
    by_key(at.text_input, "ref_doi").set_value("10.9999/not-there")
    by_key(at.button, "save_reference").click()
    at.run()
    by_key(at.button, "enrich_1").click()
    at.run()
    assert at.warning, "typed failure must be surfaced"
    assert "does NOT mean the material is unstudied" in at.warning[0].value


def test_restart_shows_saved_references_with_provenance(app_with_question, run_app, db_path):
    at = app_with_question
    _open_sources_page(at)
    by_key(at.text_input, "ref_doi").set_value("10.9999/durable")
    by_key(at.text_area, "ref_title").set_value("Durable lead")
    by_key(at.button, "save_reference").click()
    at.run()

    at2 = run_app()  # fresh application session
    _open_sources_page(at2)
    text = all_text(at2)
    assert "Durable lead" in text
    assert "10.9999/durable" in text
    assert "Origin: `manual`" in text
