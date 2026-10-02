"""Active-search domain tests (issue #16, D9)."""

import pytest

from mofs_platform.db.connection import connect
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import list_references
from mofs_platform.domain.search import (
    SearchValidationError,
    capture_hit,
    derive_query,
    dismiss_hit,
    get_hit,
    list_hits,
    run_active_search,
)
from mofs_platform.sources import crossref
from mofs_platform.sources.search_common import SearchFailure


@pytest.fixture
def conn_with_question(db_path):
    conn = connect(db_path)
    save_question(conn, Question(
        wording="Which conductive MOFs work for both HER and OER in water splitting?",
    ))
    return conn


def test_derive_query_is_the_verbatim_wording(conn_with_question):
    q = conn_with_question.execute("SELECT wording FROM question").fetchone()[0]
    derived = derive_query(q)
    assert derived["query"] == q
    assert derived["scope"] == "owner_question_verbatim"
    with pytest.raises(SearchValidationError):
        derive_query("   ")


def test_successful_run_records_run_and_hits(conn_with_question, monkeypatch):
    hits = [
        crossref.SearchHit(doi="10.9999/a", title="MOF for HER", issued_year="2026",
                           container="J", her_token=True, oer_token=False),
        crossref.SearchHit(doi="10.9999/b", title="Plain MOF paper", issued_year=None,
                           container=None, her_token=False, oer_token=False),
    ]
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.search_works", lambda *a, **k: hits
    )
    run, failure = run_active_search(
        conn_with_question, "crossref", "Which conductive MOFs work?", "owner_question_verbatim"
    )
    assert failure is None and run.outcome == "success" and run.result_count == 2
    stored = list_hits(conn_with_question, run.id)
    assert [h.doi for h in stored] == ["10.9999/a", "10.9999/b"]
    assert stored[0].her_token and not stored[0].oer_token  # streams stay separate
    assert all(h.status == "needs_verification" for h in stored)
    assert "verbatim" in run.scope


def test_failed_run_is_recorded_typed_with_next_step(conn_with_question, monkeypatch):
    monkeypatch.setattr(
        "mofs_platform.sources.openalex.search_works",
        lambda *a, **k: SearchFailure("no_hit", "none matched"),
    )
    run, failure = run_active_search(
        conn_with_question, "openalex", "obscure", "owner_edited"
    )
    assert failure.kind == "no_hit"
    assert run.outcome == "no_hit" and run.result_count == 0
    assert "not evidence of novelty" in run.next_step
    assert list_hits(conn_with_question, run.id) == []


def test_run_validates_provider_query_and_scope(conn_with_question):
    with pytest.raises(SearchValidationError):
        run_active_search(conn_with_question, "google", "q", "owner_edited")
    with pytest.raises(SearchValidationError):
        run_active_search(conn_with_question, "crossref", "   ", "owner_edited")
    with pytest.raises(SearchValidationError):
        run_active_search(conn_with_question, "crossref", "q", "auto")


def test_dismissal_is_attributed_and_auditable(conn_with_question, monkeypatch):
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.search_works",
        lambda *a, **k: [crossref.SearchHit(doi="10.9999/x", title="T", issued_year=None,
                                            container=None, her_token=False, oer_token=False)],
    )
    run, _ = run_active_search(conn_with_question, "crossref", "q", "owner_edited")
    hit = list_hits(conn_with_question, run.id)[0]
    with pytest.raises(SearchValidationError) as exc:
        dismiss_hit(conn_with_question, hit.id, None, None)
    assert "who is dismissing" in str(exc.value)
    dismissed = dismiss_hit(conn_with_question, hit.id, "Mohammed (owner)", "off-topic")
    assert dismissed.status == "dismissed" and dismissed.dismiss_reason == "off-topic"
    # still auditable: the row remains
    assert get_hit(conn_with_question, hit.id).status == "dismissed"


def test_capture_creates_attributed_reference_with_provenance(conn_with_question, monkeypatch):
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.search_works",
        lambda *a, **k: [crossref.SearchHit(doi="10.9999/cap", title="Captured title",
                                            issued_year="2025", container="J",
                                            her_token=False, oer_token=False)],
    )
    run, _ = run_active_search(conn_with_question, "crossref", "q", "owner_edited")
    hit = list_hits(conn_with_question, run.id)[0]
    with pytest.raises(SearchValidationError) as exc:
        capture_hit(conn_with_question, hit.id, "  ")
    assert "who is capturing" in str(exc.value)

    hit, source_id = capture_hit(conn_with_question, hit.id, "Mohammed (owner)")
    assert hit.status == "captured" and hit.captured_source_id == source_id
    refs = list_references(conn_with_question)
    assert len(refs) == 1
    assert refs[0].entry_method == "manual"
    assert refs[0].inspected_level == "metadata"
    assert "active search run #" in refs[0].supplied_input
    # idempotent: capturing again returns the same source
    _hit2, source_id2 = capture_hit(conn_with_question, hit.id, "Mohammed (owner)")
    assert source_id2 == source_id
    assert len(list_references(conn_with_question)) == 1

    # dismissed hits refuse capture
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.search_works",
        lambda *a, **k: [crossref.SearchHit(doi="10.9999/d", title="D", issued_year=None,
                                            container=None, her_token=False, oer_token=False)],
    )
    run2, _ = run_active_search(conn_with_question, "crossref", "q2", "owner_edited")
    hit2 = list_hits(conn_with_question, run2.id)[0]
    dismiss_hit(conn_with_question, hit2.id, "Mohammed (owner)", "off-topic")
    with pytest.raises(SearchValidationError) as exc_dis:
        capture_hit(conn_with_question, hit2.id, "Mohammed (owner)")
    assert "dismissed" in str(exc_dis.value)


def test_openalex_wildcards_stripped_and_recorded_as_sent(conn_with_question, monkeypatch):
    """Live finding (issue #16 smoke): OpenAlex rejects '?' as a wildcard.
    prepare_query strips it for openalex only; the run records the exact
    text that was sent."""
    from mofs_platform.domain.search import prepare_query

    q = "Which conductive MOFs work for both HER and OER?"
    assert prepare_query("crossref", q) == q  # crossref is untouched
    stripped = prepare_query("openalex", q)
    assert stripped == "Which conductive MOFs work for both HER and OER"
    assert "?" not in stripped

    sent = {}
    monkeypatch.setattr(
        "mofs_platform.sources.openalex.search_works",
        lambda query, mailto, **k: sent.update(sent_query=query)
        or SearchFailure("no_hit", "x"),
    )
    run, failure = run_active_search(conn_with_question, "openalex", q, "owner_edited")
    assert sent["sent_query"] == stripped  # adapter got the normalized text
    assert run.query_text == stripped  # run recorded the sent text, verbatim
    assert failure.kind == "no_hit"
