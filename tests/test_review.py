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
    correct_sample,
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


# --- sample-record corrections (issue #20) ---------------------------------


@pytest.fixture
def conn_with_sample(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    ref = add_manual_reference(conn, doi="10.9999/sample-fix", title="Sample fixture paper")
    sample = record_sample(
        conn, source_id=ref.id, designation="CoCoZn(HITP)2 (computational model)",
        linker="HITP", metal_node="Co, Zn", composition="CoCoZn(HITP)2",
        basis="experimental",  # the guided-session 001 mistake
    )
    return conn, ref.id, sample.id


def test_correct_sample_fixes_basis_and_logs_history(conn_with_sample):
    conn, _ref_id, sample_id = conn_with_sample
    result = correct_sample(
        conn, sample_id=sample_id, editor="Mohammed (owner)",
        reason="dropdown click did not commit — the study is computational",
        basis="computational",
    )
    assert result["changed_fields"] == ["basis"]
    assert result["original_preserved_in_history"] is True
    events = list_review_events(conn, "sample_record", sample_id)
    assert events[0].action == "corrected"
    assert events[0].reviewer == "Mohammed (owner)"
    assert '"basis": "experimental"' in events[0].previous_json
    assert '"basis": "computational"' in events[0].updated_json
    row = conn.execute("SELECT basis, designation, source_id FROM sample_record WHERE id = ?",
                       (sample_id,)).fetchone()
    assert row["basis"] == "computational"
    assert row["designation"] == "CoCoZn(HITP)2 (computational model)"  # untouched
    assert row["source_id"] == _ref_id  # provenance immutable


def test_correct_sample_requires_editor_and_reason(conn_with_sample):
    conn, _ref_id, sample_id = conn_with_sample
    with pytest.raises(ReviewValidationError) as exc:
        correct_sample(conn, sample_id=sample_id, editor=None, reason=None, basis="computational")
    assert "editor" in str(exc.value) and "reason" in str(exc.value)
    events = list_review_events(conn, "sample_record", sample_id)
    assert events == []
    row = conn.execute("SELECT basis FROM sample_record WHERE id = ?", (sample_id,)).fetchone()
    assert row["basis"] == "experimental"  # untouched


def test_correct_sample_rejects_no_change(conn_with_sample):
    conn, _ref_id, sample_id = conn_with_sample
    with pytest.raises(ReviewValidationError) as exc_nothing:
        correct_sample(conn, sample_id=sample_id, editor="Mohammed (owner)", reason="typo hunt")
    assert "nothing to change" in str(exc_nothing.value).lower()
    with pytest.raises(ReviewValidationError) as exc_same:
        correct_sample(conn, sample_id=sample_id, editor="Mohammed (owner)", reason="no-op",
                       linker="HITP")  # equals stored value
    assert "nothing to change" in str(exc_same.value).lower()
    assert list_review_events(conn, "sample_record", sample_id) == []


def test_correct_sample_rejects_unknown_sample_and_bad_basis(conn_with_sample):
    conn, _ref_id, _sample_id = conn_with_sample
    with pytest.raises(ReviewValidationError) as exc_missing:
        correct_sample(conn, sample_id=999, editor="Mohammed (owner)", reason="x", basis="computational")
    assert "does not exist" in str(exc_missing.value)
    with pytest.raises(ReviewValidationError) as exc_basis:
        correct_sample(conn, sample_id=_sample_id, editor="Mohammed (owner)", reason="x",
                       basis="simulated")
    assert "Basis must be one of" in str(exc_basis.value)
    assert list_review_events(conn, "sample_record", _sample_id) == []


def test_correct_sample_lineage_pair_rules(conn_with_sample, db_path):
    conn, ref_id, sample_id = conn_with_sample
    other = record_sample(conn, source_id=ref_id, designation="Sibling (synthetic)")
    with pytest.raises(ReviewValidationError) as exc_half:
        correct_sample(conn, sample_id=sample_id, editor="Mohammed (owner)", reason="x",
                       lineage_kind="derived")  # no parent provided, none stored
    assert "both the kind" in str(exc_half.value)
    with pytest.raises(ReviewValidationError) as exc_self:
        correct_sample(conn, sample_id=sample_id, editor="Mohammed (owner)", reason="x",
                       lineage_kind="derived", derived_from_sample_id=sample_id)
    assert "derive from itself" in str(exc_self.value)
    with pytest.raises(ReviewValidationError) as exc_ghost:
        correct_sample(conn, sample_id=sample_id, editor="Mohammed (owner)", reason="x",
                       lineage_kind="composite", derived_from_sample_id=4242)
    assert "#4242 does not exist" in str(exc_ghost.value)
    result = correct_sample(conn, sample_id=sample_id, editor="Mohammed (owner)", reason="x",
                            lineage_kind="composite", derived_from_sample_id=other.id)
    assert sorted(result["changed_fields"]) == ["derived_from_sample_id", "lineage_kind"]


def test_migration_0010_preserves_history_and_accepts_sample_events(db_path):
    """0010 rebuilds review_event with the 'sample_record' entity type; the
    append-only history must survive the rebuild."""
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    ref = add_manual_reference(conn, doi="10.9999/mig10", title="Migration fixture")
    asm = record_assertion(conn, source_id=ref.id, claim_type="preparation",
                           claim_text="Pre-0010 claim", evidence_location="loc")
    correct_assertion(conn, assertion_id=asm.id, new_claim_text="Post-0010 claim",
                      new_evidence_location=None, editor="Mohammed (owner)", reason="r")
    # force a fresh connection through apply_migrations (0010 already applied
    # at connect); the pre-0010 event must still be readable
    events_before = list_review_events(conn, "assertion", asm.id)
    assert events_before and "Pre-0010 claim" in events_before[0].previous_json
    sample = record_sample(conn, source_id=ref.id, designation="S (synthetic)")
    correct_sample(conn, sample_id=sample.id, editor="Mohammed (owner)", reason="r",
                   basis="computational")
    kinds = {e.entity_type for e in list_review_events(conn)}
    assert kinds == {"assertion", "sample_record"}


def test_migration_0010_survives_preexisting_events(db_path):
    """QA finding (issue #20): the survival demonstration must stage the real
    transition — build a pre-0010 database (0001-0009), insert a review_event
    row, THEN run the 0010 rebuild and assert the row survives intact."""
    import sqlite3

    from mofs_platform.db.connection import MIGRATIONS_DIR

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    pre = sorted(p for p in MIGRATIONS_DIR.glob("*.sql") if p.name < "0010")
    assert [p.name for p in pre][-1] == "0009_fit_assessment.sql"
    for path in pre:
        conn.executescript(path.read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO review_event (entity_type, entity_id, action, reviewer, reason, "
        "updated_json, created_at) VALUES ('assertion', 7, 'corrected', "
        "'Mohammed (owner)', 'pre-0010 reason', '{}', '2026-01-01 00:00:00')"
    )
    conn.commit()

    conn.executescript(
        (MIGRATIONS_DIR / "0010_sample_correction.sql").read_text(encoding="utf-8")
    )
    survived = conn.execute(
        "SELECT * FROM review_event WHERE entity_id = 7"
    ).fetchone()
    assert survived is not None
    assert survived["action"] == "corrected"
    assert survived["reviewer"] == "Mohammed (owner)"
    assert survived["reason"] == "pre-0010 reason"
    assert survived["created_at"] == "2026-01-01 00:00:00"
    # the rebuilt table accepts sample_record events and still refuses junk
    conn.execute(
        "INSERT INTO review_event (entity_type, entity_id, action, updated_json) "
        "VALUES ('sample_record', 1, 'corrected', '{}')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO review_event (entity_type, entity_id, action, updated_json) "
            "VALUES ('nonsense', 1, 'corrected', '{}')"
        )
    conn.close()


def test_correct_sample_rejects_nonnumeric_parent(conn_with_sample):
    conn, _ref_id, sample_id = conn_with_sample
    with pytest.raises(ReviewValidationError) as exc:
        correct_sample(conn, sample_id=sample_id, editor="Mohammed (owner)", reason="x",
                       derived_from_sample_id="not-a-number")  # type: ignore[arg-type]
    assert "must be an integer" in str(exc.value)
    assert list_review_events(conn, "sample_record", sample_id) == []


# --- conflict resolution (strict-audit BLOCKING fix, migration 0018) --------


def test_resolve_conflict_persists_event_and_resets_states(conn_with_assertion):
    """The strict audit found resolve_conflict wrote action
    'conflict_resolved', forbidden by the review_event CHECK since #11 —
    every resolution attempt failed at persist time. This test pins the
    working path end-to-end."""
    from mofs_platform.domain.review import resolve_conflict

    conn, _ref_id, asm_id = conn_with_assertion
    first = record_assertion(conn, source_id=_ref_id, claim_type="property",
                             claim_text="220 mV (synthetic)",
                             conflicts_with=asm_id)
    result = resolve_conflict(
        conn, assertion_id=asm_id, resolver="Mohammed (owner)",
        reason="double entry of the same claim",
    )
    assert result["resolved"] == sorted([asm_id, first.id])
    events = conn.execute(
        "SELECT action FROM review_event WHERE action = 'conflict_resolved'"
    ).fetchall()
    assert len(events) == 1
    states = conn.execute(
        "SELECT review_state FROM assertion ORDER BY id"
    ).fetchall()
    assert all(s["review_state"] == "needs_verification" for s in states)


def test_resolve_conflict_requires_resolver_and_reason(conn_with_assertion):
    from mofs_platform.domain.review import resolve_conflict

    conn, _ref_id, asm_id = conn_with_assertion
    record_assertion(conn, source_id=_ref_id, claim_type="property",
                     claim_text="220 mV (synthetic)", conflicts_with=asm_id)
    with pytest.raises(Exception) as exc:
        resolve_conflict(conn, assertion_id=asm_id, resolver=None, reason=None)
    assert "missing" in str(exc.value).lower()
    assert conn.execute(
        "SELECT COUNT(*) FROM review_event WHERE action = 'conflict_resolved'"
    ).fetchone()[0] == 0
