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
    text = all_text(at).replace("\\", "")
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


def test_criteria_display_and_scope_caption(app_with_question, monkeypatch):
    """Plan step 3 deliverable (spec-compliance review finding): the UI shows
    per-criterion results, the unknown branch, and the pagination scope."""
    monkeypatch.setattr(
        "mofs_platform.domain.search.extract_criteria",
        lambda conn: {"conductive MOF": "hard_requirements"},
    )
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.search_works",
        lambda *a, **k: [
            crossref.SearchHit(doi="10.9999/m", title="A conductive MOF study",
                               issued_year=None, container=None, her_token=False,
                               oer_token=False),
            crossref.SearchHit(doi="10.9999/nt", title=None, issued_year=None,
                               container=None, her_token=False, oer_token=False),
        ],
    )
    at = app_with_question
    _open_sources_page(at)
    by_key(at.button, "run_search").click()
    at.run()
    text = all_text(at)
    assert "'conductive MOF': **matched in title**" in text
    assert "`unknown` (no title in the provider metadata)" in text
    assert "one polite page per run (8 hits, a single request" in text
    assert "auto-paging is deliberately out of scope" in text


def test_unknown_criteria_line_for_criteria_less_runs(run_app, db_path):
    """Legacy runs (criteria_json NULL) and criteria-less questions render the
    honest unknown line, not a false reason."""
    conn = connect(db_path)
    save_question(conn, Question(wording="Plain question without criteria"))
    conn.close()
    monkeypatched = False
    at = run_app()
    at.sidebar.radio[0].set_value("Sources")
    at.run()
    # simulate a pre-0012 run by inserting directly
    c = connect(db_path)
    c.execute(
        "INSERT INTO search_run (provider, query_text, scope, outcome, result_count) "
        "VALUES ('crossref', 'q', 'owner_edited', 'success', 1)"
    )
    run_id = c.execute("SELECT MAX(id) FROM search_run").fetchone()[0]
    c.execute(
        "INSERT INTO search_hit (run_id, provider, doi, title, issued_year, container, "
        "her_token, oer_token) VALUES (?, 'crossref', '10.9999/legacy', 'Legacy hit', "
        "NULL, NULL, 0, 0)",
        (run_id,),
    )
    c.commit()
    c.close()
    at.run()
    text = all_text(at)
    assert "Per-criterion check: `unknown`" in text
    assert "the run predates the per-criterion check" in text
    assert monkeypatched is False
