"""Review & correction tests (issue #11) — D4 threshold + D5 refusal."""

import pytest

from mofs_platform.db.connection import connect
from mofs_platform.domain.evidence import get_assertion, record_assertion
from mofs_platform.domain.identity import compare_samples, record_sample
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import add_manual_reference
from mofs_platform.domain.review import (
    ReviewValidationError,
    correct_assertion,
    list_review_events,
    review_assertion,
    review_identity_relation,
)


@pytest.fixture
def conn_with_assertion(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    ref = add_manual_reference(conn, doi="10.9999/review", title="Review fixture paper")
    asm = record_assertion(conn, source_id=ref.id, claim_type="preparation",
                           claim_text="Activated at 200 C (synthetic)",
                           evidence_location="Methods §2")
    return conn, ref.id, asm.id


def test_correction_preserves_original_and_records_attribution(conn_with_assertion):
    conn, _ref_id, asm_id = conn_with_assertion
    result = correct_assertion(
        conn, assertion_id=asm_id, new_claim_text="Activated at 180 C (corrected)",
        new_evidence_location="Methods §3", editor="Mohammed (owner)",
        reason="misread temperature in first extraction",
    )
    assert result["review_state"] == "needs_verification"
    events = list_review_events(conn, "assertion", asm_id)
    assert events[0].action == "corrected"
    assert events[0].reviewer == "Mohammed (owner)"
    assert "misread" in events[0].reason
    assert "200 C" in events[0].previous_json  # original preserved
    assert "180 C" in events[0].updated_json
    asm = get_assertion(conn, asm_id)
    assert asm.claim_text == "Activated at 180 C (corrected)"  # changed content live


def test_correction_without_attribution_rejected_history_intact(conn_with_assertion):
    conn, _ref_id, asm_id = conn_with_assertion
    with pytest.raises(ReviewValidationError) as exc:
        correct_assertion(conn, assertion_id=asm_id, new_claim_text="X (synthetic)",
                          new_evidence_location=None, editor=None, reason=None)
    assert "missing" in str(exc.value).lower()
    assert "editor" in str(exc.value) and "reason" in str(exc.value)
    assert len(list_review_events(conn)) == 0  # history untouched
    assert get_assertion(conn, asm_id).claim_text == "Activated at 200 C (synthetic)"


def test_reviewed_transition_records_d4_requirements(conn_with_assertion):
    conn, _ref_id, asm_id = conn_with_assertion
    result = review_assertion(
        conn, assertion_id=asm_id, reviewer="Mohammed (owner)",
        supporting_location="Methods §2", reason="read the exact section; value matches",
    )
    assert result["review_state"] == "reviewed"
    events = list_review_events(conn, "assertion", asm_id)
    review_event = next(e for e in events if e.action == "reviewed")
    assert review_event.reviewer == "Mohammed (owner)"
    assert review_event.supporting_location == "Methods §2"
    assert "D4" in review_event.threshold_note
    assert review_event.created_at is not None


def test_insufficient_review_rejected_with_unmet_requirements_visible(conn_with_assertion):
    conn, _ref_id, asm_id = conn_with_assertion
    with pytest.raises(ReviewValidationError) as exc:
        review_assertion(conn, assertion_id=asm_id, reviewer=None,
                         supporting_location=None, reason=None)
    message = str(exc.value)
    assert "reviewer name" in message
    assert "supporting source location" in message
    assert "D4 threshold" in message
    # prior state preserved:
    assert get_assertion(conn, asm_id).review_state == "needs_verification"
    rejection = list_review_events(conn, "assertion", asm_id)[0]
    assert rejection.action == "review_rejected"
    assert "unmet:" in rejection.threshold_note


def test_correcting_reviewed_content_cannot_inherit_approval(conn_with_assertion):
    conn, _ref_id, asm_id = conn_with_assertion
    review_assertion(conn, assertion_id=asm_id, reviewer="Mohammed (owner)",
                     supporting_location="Methods §2", reason="verified against source")
    assert get_assertion(conn, asm_id).review_state == "reviewed"
    correct_assertion(conn, assertion_id=asm_id,
                      new_claim_text="Activated at 175 C (corrected after re-read)",
                      new_evidence_location="Methods §2", editor="Mohammed (owner)",
                      reason="re-checked: temperature differs")
    asm = get_assertion(conn, asm_id)
    assert asm.review_state == "needs_verification"  # old approval not inherited
    events = list_review_events(conn, "assertion", asm_id)
    assert any(e.action == "reviewed" for e in events)  # original review stays in history
    assert any(e.action == "corrected" and "175 C" in e.updated_json for e in events)


def test_reviewing_one_claim_leaves_others_untouched(conn_with_assertion):
    conn, ref_id, asm_id = conn_with_assertion
    other = record_assertion(conn, source_id=ref_id, claim_type="property",
                             claim_text="Other claim (synthetic)")
    review_assertion(conn, assertion_id=asm_id, reviewer="Mohammed (owner)",
                     supporting_location="Methods §2", reason="verified")
    assert get_assertion(conn, asm_id).review_state == "reviewed"
    assert get_assertion(conn, other.id).review_state == "needs_verification"


def test_conflicting_pair_correction_keeps_both_review_refused(conn_with_assertion):
    conn, ref_id, _asm_id = conn_with_assertion
    first = record_assertion(conn, source_id=ref_id, claim_type="property",
                             claim_text="180 mV (synthetic)")
    second = record_assertion(conn, source_id=ref_id, claim_type="property",
                              claim_text="220 mV (synthetic)", conflicts_with=first.id)
    # Correction keeps both source claims available:
    correct_assertion(conn, assertion_id=second.id, new_claim_text="220 mV (corrected)",
                      new_evidence_location="table 1", editor="Mohammed (owner)",
                      reason="value mis-extracted")
    assert get_assertion(conn, first.id).claim_text == "180 mV (synthetic)"
    assert get_assertion(conn, second.id).claim_text == "220 mV (corrected)"
    assert get_assertion(conn, second.id).review_state == "conflicted"  # pair stays flagged
    # Review of a conflicted assertion is refused until resolved:
    with pytest.raises(ReviewValidationError) as exc:
        review_assertion(conn, assertion_id=first.id, reviewer="Mohammed (owner)",
                         supporting_location="fig. 3", reason="verified")
    assert "conflict" in str(exc.value).lower()


def test_within_source_identity_review_allowed_cross_source_refused(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    ref1 = add_manual_reference(conn, doi="10.9999/ws-1", title="Within-source paper")
    a = record_sample(conn, source_id=ref1.id, designation="Sample-B")
    b = record_sample(conn, source_id=ref1.id, designation="Sample-B")
    rels = compare_samples(conn, a.id, b.id)
    within = next(r for r in rels if r["relation"] == "same_reported_sample")
    result = review_identity_relation(
        conn, relation_id=within["id"], reviewer="Mohammed (owner)",
        supporting_location="Methods §2 + fig. 1 designation",
        reason="explicit designation checked against D5 rule",
    )
    assert result["review_state"] == "reviewed"

    ref2 = add_manual_reference(conn, doi="10.9999/cs-1", title="Cross-source paper")
    c = record_sample(conn, source_id=ref2.id, designation="Sample-B")
    # Cross-source same designation → unresolved relation; D5 refuses its review:
    rels2 = compare_samples(conn, a.id, c.id)
    unresolved = next(r for r in rels2 if r["level"] == "sample")
    assert unresolved["relation"] == "unresolved" and unresolved["merge_permission"] == "none"
    with pytest.raises(ReviewValidationError) as exc:
        review_identity_relation(conn, relation_id=unresolved["id"], reviewer="Mohammed (owner)",
                                 supporting_location="both papers", reason="tried")
    assert "D5" in str(exc.value)
    # cross-source equivalence refusal does not prevent unrelated assertion review:
    asm = record_assertion(conn, source_id=ref2.id, claim_type="preparation",
                           claim_text="Unrelated assertion (synthetic)")
    review_assertion(conn, assertion_id=asm.id, reviewer="Mohammed (owner)",
                     supporting_location="Methods §1", reason="verified independently")
    assert get_assertion(conn, asm.id).review_state == "reviewed"
    conn.close()


def test_review_history_survives_restart(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    ref = add_manual_reference(conn, doi="10.9999/hist", title="History fixture")
    asm = record_assertion(conn, source_id=ref.id, claim_type="preparation",
                           claim_text="Original (synthetic)", evidence_location="fig. 1")
    review_assertion(conn, assertion_id=asm.id, reviewer="Mohammed (owner)",
                     supporting_location="fig. 1", reason="verified")
    correct_assertion(conn, assertion_id=asm.id, new_claim_text="Corrected (synthetic)",
                      new_evidence_location="fig. 1", editor="Mohammed (owner)",
                      reason="re-read")
    conn.close()

    reopened = connect(db_path)
    events = list_review_events(reopened, "assertion", asm.id)
    actions = [e.action for e in events]
    assert "reviewed" in actions and "corrected" in actions
    assert get_assertion(reopened, asm.id).claim_text == "Corrected (synthetic)"
    assert get_assertion(reopened, asm.id).review_state == "needs_verification"
    reopened.close()
