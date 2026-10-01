"""Domain tests for attributed evidence assertions (issue #7)."""

import sqlite3

import pytest

from mofs_platform.db.connection import connect
from mofs_platform.domain.evidence import (
    EvidencePersistenceError,
    EvidenceValidationError,
    count_events,
    get_assertion,
    list_assertions,
    record_assertion,
)
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import add_manual_reference


@pytest.fixture
def conn_with_source(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Which prepared MOF samples merit inspection?"))
    ref = add_manual_reference(
        conn, doi="10.9999/fixture", title="Synthetic fixture paper", contributor="Mohammed (owner)"
    )
    return conn, ref.id


def test_assertion_requires_a_saved_source(db_path):
    conn = connect(db_path)
    with pytest.raises(EvidenceValidationError):
        record_assertion(conn, source_id=99, claim_type="preparation", claim_text="x")
    assert list_assertions(conn) == []


def test_blank_claim_rejected_and_invalid_type_rejected(conn_with_source):
    conn, source_id = conn_with_source
    for blank in ("", "   "):
        with pytest.raises(EvidenceValidationError):
            record_assertion(conn, source_id=source_id, claim_type="preparation", claim_text=blank)
    with pytest.raises(EvidenceValidationError):
        record_assertion(
            conn, source_id=source_id, claim_type="recipe", claim_text="x"
        )  # not a valid claim type
    with pytest.raises(EvidenceValidationError):
        record_assertion(
            conn, source_id=source_id, claim_type="preparation", claim_text="x",
            epistemic_type="magic",
        )
    assert list_assertions(conn) == []


def test_partial_assertion_saved_with_unknown_location_and_author(conn_with_source):
    conn, source_id = conn_with_source
    asm = record_assertion(
        conn, source_id=source_id, claim_type="preparation",
        claim_text="Sample activated under argon at 200 C (synthetic)",
    )
    assert asm.evidence_location is None  # stays unknown, not guessed
    assert asm.extraction_author is None
    assert asm.review_state == "needs_verification"  # recording never marks reviewed


def test_epistemic_types_stay_distinct_and_review_starts_unverified(conn_with_source):
    conn, source_id = conn_with_source
    for i, etype in enumerate(
        ("directly_reported", "author_interpretation", "tool_inference", "user_judgment", "unknown")
    ):
        asm = record_assertion(
            conn, source_id=source_id, claim_type="property",
            claim_text=f"Claim variant {i} (synthetic)", epistemic_type=etype,
        )
        assert asm.epistemic_type == etype  # stored verbatim, never transformed
        assert asm.review_state == "needs_verification"


def test_conflicting_pair_keeps_both_claims_flagged(conn_with_source):
    conn, source_id = conn_with_source
    first = record_assertion(
        conn, source_id=source_id, claim_type="property",
        claim_text="Overpotential 180 mV at 10 mA/cm2 (synthetic)",
        evidence_location="fig. 3", epistemic_type="directly_reported",
    )
    second = record_assertion(
        conn, source_id=source_id, claim_type="property",
        claim_text="Overpotential 220 mV at 10 mA/cm2 (synthetic)",
        evidence_location="table 1", epistemic_type="directly_reported",
        conflicts_with=first.id,
    )
    a, b = get_assertion(conn, first.id), get_assertion(conn, second.id)
    assert a.review_state == "conflicted" and b.review_state == "conflicted"
    assert a.claim_text != b.claim_text  # both originals retained — no averaging
    assert a.conflicts_with == second.id and b.id == second.id
    assert count_events(conn) == 3  # 2 recorded + 1 flagged_conflict


def test_relink_guard_rejects_conflict_with_already_paired_assertion(conn_with_source):
    conn, source_id = conn_with_source
    a = record_assertion(conn, source_id=source_id, claim_type="property", claim_text="A (synthetic)")
    b = record_assertion(
        conn, source_id=source_id, claim_type="property", claim_text="B (synthetic)",
        conflicts_with=a.id,
    )
    with pytest.raises(EvidenceValidationError):
        record_assertion(
            conn, source_id=source_id, claim_type="property", claim_text="C (synthetic)",
            conflicts_with=a.id,  # a is already paired with b — no silent severing
        )
    a_row, b_row = get_assertion(conn, a.id), get_assertion(conn, b.id)
    assert a_row.conflicts_with == b.id and b_row.conflicts_with == a.id  # pair intact


def test_conflict_with_missing_assertion_rejected(conn_with_source):
    conn, source_id = conn_with_source
    with pytest.raises(EvidenceValidationError):
        record_assertion(
            conn, source_id=source_id, claim_type="property",
            claim_text="x", conflicts_with=4242,
        )


def test_restart_keeps_located_missing_location_and_conflict(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    ref = add_manual_reference(conn, doi="10.9999/durable", title="Durable fixture")
    located = record_assertion(
        conn, source_id=ref.id, claim_type="preparation",
        claim_text="Located claim (synthetic)", evidence_location="Methods §2",
    )
    missing = record_assertion(
        conn, source_id=ref.id, claim_type="composition", claim_text="Missing-location claim (synthetic)"
    )
    record_assertion(
        conn, source_id=ref.id, claim_type="property",
        claim_text="Conflicting claim B (synthetic)", conflicts_with=located.id,
    )
    conn.close()

    reopened = connect(db_path)
    located_r = get_assertion(reopened, located.id)
    missing_r = get_assertion(reopened, missing.id)
    assert located_r.evidence_location == "Methods §2"  # located pointer retained
    assert missing_r.evidence_location is None  # unknown stays unknown
    assert located_r.review_state == "conflicted"  # conflict pair survived restart
    assert reopened.execute("SELECT COUNT(*) FROM assertion").fetchone()[0] == 3
    reopened.close()


def test_save_failure_preserves_assertions(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    ref = add_manual_reference(conn, doi="10.9999/kept", title="Kept fixture")
    record_assertion(conn, source_id=ref.id, claim_type="preparation", claim_text="Kept claim")
    conn.close()

    readonly = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    readonly.row_factory = sqlite3.Row
    with pytest.raises(EvidencePersistenceError):
        record_assertion(readonly, source_id=ref.id, claim_type="preparation", claim_text="Never saved")
    assert len(list_assertions(readonly)) == 1
    readonly.close()
