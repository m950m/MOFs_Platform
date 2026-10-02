"""Candidate card tests (issue #10) — domain behavior + UI inspection."""

import pytest

from conftest import all_text
from mofs_platform.db.connection import connect
from mofs_platform.domain.candidates import (
    CandidateValidationError,
    get_candidate_card,
    list_candidate_cards,
    retrieval_outcome_summary,
)
from mofs_platform.domain.evidence import record_assertion
from mofs_platform.domain.identity import (
    record_observation,
    record_operating_state,
    record_sample,
)
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import add_manual_reference


@pytest.fixture
def conn_with_fixture(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Which prepared MOF samples merit inspection?"))
    ref = add_manual_reference(
        conn, doi="10.9999/card", title="Card fixture paper", contributor="Mohammed (owner)"
    )
    sample = record_sample(conn, source_id=ref.id, designation="Sample-A (synthetic)",
                           parent_framework_name="Framework-F (synthetic)")
    record_assertion(conn, source_id=ref.id, claim_type="preparation",
                     claim_text="Activated at 200 C (synthetic)",
                     evidence_location="Methods §2", epistemic_type="directly_reported")
    record_observation(conn, sample_id=sample.id, source_id=ref.id,
                       observation_kind="experimental", value="180", unit="mV")
    record_operating_state(conn, sample_id=sample.id, stage="during",
                           phase_assignment="Phase-R (synthetic)",
                           epistemic_type="author_interpretation",
                           evidence_location="fig. 3")
    return conn, ref.id, sample.id


def test_empty_state_shows_no_invented_candidates_and_retrieval_outcomes(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    ref = add_manual_reference(conn, doi="10.9999/empty", title="Empty fixture")
    import mofs_platform.sources.crossref as cr
    from mofs_platform.domain.references import enrich_with_crossref
    from mofs_platform.sources import crossref
    original = cr.fetch_metadata
    cr.fetch_metadata = lambda *a, **k: crossref.CrossrefFailure("no_hit", "none")
    enrich_with_crossref(conn, ref.id, "owner@example.com")
    cr.fetch_metadata = original

    assert list_candidate_cards(conn) == []
    summary = retrieval_outcome_summary(conn)
    assert summary.get("no_hit") == 1  # recorded retrieval outcome, honestly
    conn.close()


def test_card_shows_reason_class_parent_modifications_status(conn_with_fixture):
    conn, _ref_id, sample_id = conn_with_fixture
    card = get_candidate_card(conn, sample_id)
    assert "Sample-A (synthetic)" in card.retrieval_reason
    assert "Framework-F (synthetic)" in card.retrieval_reason
    assert card.basis == "experimental"
    assert card.parent_relation == "Framework-F (synthetic)"
    assert card.source_inspected_level.startswith("`unknown`")  # metadata honest


def test_card_follows_claim_to_provenance_and_gap_fields(conn_with_fixture):
    conn, _ref_id, sample_id = conn_with_fixture
    card = get_candidate_card(conn, sample_id)
    assert len(card.assertions) == 1
    a = card.assertions[0]
    assert a["location"] == "Methods §2"  # exact location followable
    assert "directly reported" in a["epistemic"]
    assert a["review_state"] == "needs_verification"
    ob = card.observations[0]
    assert ob["value"] == "180"
    assert set(ob["gaps"]) == {"reaction", "medium", "reference/conversion",
                               "loading", "duration", "protocol"}  # gaps exposed
    stt = card.operating_states[0]
    assert "author interpretation" in stt["epistemic"]


def test_conflicting_assertions_individually_accessible_not_averaged(conn_with_fixture):
    conn, ref_id, sample_id = conn_with_fixture
    first = record_assertion(conn, source_id=ref_id, claim_type="property",
                             claim_text="180 mV (synthetic)", epistemic_type="directly_reported")
    record_assertion(conn, source_id=ref_id, claim_type="property",
                     claim_text="220 mV (synthetic)", conflicts_with=first.id)
    card = get_candidate_card(conn, sample_id)
    texts = [a["claim_text"] for a in card.assertions]
    assert "180 mV (synthetic)" in texts and "220 mV (synthetic)" in texts
    assert len(card.conflicts) == 2  # both sides flagged
    review_states = {a["review_state"] for a in card.assertions}
    assert "conflicted" in review_states
    assert "needs_verification" in review_states  # other assertions stay unreviewed


def test_get_card_validates_existence(db_path):
    conn = connect(db_path)
    with pytest.raises(CandidateValidationError):
        get_candidate_card(conn, 999)
    conn.close()


def test_card_survives_restart(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    ref = add_manual_reference(conn, doi="10.9999/durable-card", title="Durable card fixture")
    sample = record_sample(conn, source_id=ref.id, designation="Durable (synthetic)")
    record_assertion(conn, source_id=ref.id, claim_type="preparation",
                     claim_text="Durable claim (synthetic)", evidence_location="fig. 1")
    record_observation(conn, sample_id=sample.id, source_id=ref.id,
                       observation_kind="experimental", value="200", unit="mV")
    conn.close()

    reopened = connect(db_path)
    card = get_candidate_card(reopened, sample.id)
    assert card.designation == "Durable (synthetic)"
    assert card.assertions[0]["location"] == "fig. 1"
    assert card.observations[0]["value"] == "200"
    reopened.close()


# ---- UI ---------------------------------------------------------------------

def test_ui_empty_state_and_card_inspection(run_app, db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    ref = add_manual_reference(conn, doi="10.9999/ui-card", title="UI card fixture")
    sample = record_sample(conn, source_id=ref.id, designation="UI sample (synthetic)")
    record_assertion(conn, source_id=ref.id, claim_type="preparation",
                     claim_text="UI claim (synthetic)", evidence_location="fig. 2")
    conn.close()

    at = run_app()
    at.sidebar.radio[0].set_value("Candidates")
    at.run()
    text = all_text(at)
    assert "Saved candidates (1)" in text
    by_key = lambda elements, key: [e for e in elements if e.key == key]
    by_key(at.selectbox, "cand_select")[0].set_value(sample.id)
    at.run()
    matches = [b for b in at.button if getattr(b, "label", "") == "Inspect"]
    matches[0].click()
    at.run()
    text = all_text(at)
    assert "UI sample (synthetic)" in text
    assert "UI claim (synthetic)" in text
    assert "fig. 2" in text
    assert "needs verification" in text
    assert "no ranking" in text.lower()


def test_ui_empty_candidates_invents_nothing(run_app, db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    conn.close()
    at = run_app()
    at.sidebar.radio[0].set_value("Candidates")
    at.run()
    text = all_text(at)
    assert "No candidates saved for the question yet" in text
    assert "Sample-A" not in text
