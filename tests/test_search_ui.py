"""UI tests for the active-search section (issue #16, D9)."""

import pytest

from conftest import all_text
from mofs_platform.db.connection import connect
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import list_references
from mofs_platform.sources import crossref
from mofs_platform.sources.search_common import SearchFailure


def by_key(elements, key):
    matches = [e for e in elements if e.key == key]
    assert len(matches) == 1, f"expected exactly one element with key {key!r}"
    return matches[0]


@pytest.fixture
def app_with_question(run_app, db_path):
    conn = connect(db_path)
    save_question(conn, Question(
        wording="Which conductive MOFs work for both HER and OER in water splitting?"
    ))
    conn.close()
    return run_app()


def _open_sources_page(at):
    at.sidebar.radio[0].set_value("Sources")
    at.run()


def test_search_section_derives_default_query_verbatim(app_with_question):
    at = app_with_question
    _open_sources_page(at)
    text = all_text(at)
    assert "Active search (D9: Crossref + OpenAlex)" in text
    assert "Query derivation is transparent" in text
    box = by_key(at.text_area, "search_query")
    assert box.value == "Which conductive MOFs work for both HER and OER in water splitting?"


def test_successful_search_lists_hits_and_captures(app_with_question, db_path, monkeypatch):
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.search_works",
        lambda *a, **k: [crossref.SearchHit(
            doi="10.9999/ui-hit", title="Bifunctional MOF paper (synthetic)",
            issued_year="2026", container="J", her_token=True, oer_token=True,
        )],
    )
    at = app_with_question
    _open_sources_page(at)
    by_key(at.button, "run_search").click()
    at.run()
    assert any("1 hit(s)" in s.value for s in at.success)
    text = all_text(at)
    assert "Bifunctional MOF paper (synthetic)" in text
    assert "HER token in title: yes" in text
    assert "the two evidence streams stay separate" in text

    matches = [b for b in at.button if getattr(b, "key", "") == "capture_hit_1"]
    assert len(matches) == 1
    matches[0].click()
    at.run()
    assert any("captured as reference #1" in s.value for s in at.success)
    refs = list_references(connect(db_path))
    assert len(refs) == 1 and refs[0].doi == "10.9999/ui-hit"
    assert "active search run #" in refs[0].supplied_input


def test_failed_search_shows_honest_no_hit_warning(app_with_question, monkeypatch):
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.search_works",
        lambda *a, **k: SearchFailure("no_hit", "none matched"),
    )
    at = app_with_question
    _open_sources_page(at)
    by_key(at.button, "run_search").click()
    at.run()
    assert at.warning, "typed failure must be surfaced"
    assert "no_hit" in at.warning[0].value
    assert "not evidence of novelty" in at.warning[0].value


def test_edited_query_runs_with_owner_edited_scope(app_with_question, monkeypatch):
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.search_works",
        lambda *a, **k: [crossref.SearchHit(
            doi="10.9999/e", title="E", issued_year=None, container=None,
            her_token=False, oer_token=False,
        )],
    )
    at = app_with_question
    _open_sources_page(at)
    by_key(at.text_area, "search_query").set_value("conductive MOF water splitting")
    by_key(at.button, "run_search").click()
    at.run()
    text = all_text(at)
    assert "owner_edited" in text
    assert "owner_question_verbatim" not in text  # only the edited scope ran
