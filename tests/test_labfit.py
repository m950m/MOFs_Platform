"""Lab-fit assessment tests (issue #12)."""

import pytest

from mofs_platform.db.connection import connect
from mofs_platform.domain.evidence import record_assertion
from mofs_platform.domain.identity import record_sample
from mofs_platform.domain.labfit import (
    LabFitValidationError,
    assess_fit,
    latest_assessment,
)
from mofs_platform.domain.labprofile import add_capability, update_capability
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import add_manual_reference
from mofs_platform.domain.review import review_assertion


def _reviewed(conn, source_id, text):
    """Record a requirement assertion and apply the D4 review to it."""
    asm = record_assertion(conn, source_id=source_id, claim_type="preparation",
                           claim_text=text, evidence_location="Methods §2",
                           epistemic_type="directly_reported")
    review_assertion(conn, assertion_id=asm.id, reviewer="Mohammed (owner)",
                     supporting_location="Methods §2", reason="verified against source")
    return asm


@pytest.fixture
def conn(db_path):
    c = connect(db_path)
    save_question(c, Question(wording="Which prepared MOF samples merit inspection?"))
    ref = add_manual_reference(c, doi="10.9999/fit", title="Fit fixture paper")
    sample = record_sample(c, source_id=ref.id, designation="Fit sample (synthetic)")
    return c, ref.id, sample.id


def test_current_capability_yields_possible(conn):
    conn, ref_id, sample_id = conn
    _reviewed(conn, ref_id, "synthesized using Furnace-X (synthetic)")
    add_capability(conn, "Furnace-X (synthetic)", None, "current")
    a = assess_fit(conn, sample_id, ref_id)
    assert a.assessment == "possible_with_current_capabilities"
    reasons = {r["effect"] for r in a.reasons}
    assert "possible" in reasons


def test_future_requirement_named_and_never_current(conn):
    conn, ref_id, sample_id = conn
    _reviewed(conn, ref_id, "requires inert Glovebox-M (synthetic)")
    add_capability(conn, "Glovebox-M (synthetic)", None, "future")
    a = assess_fit(conn, sample_id, ref_id)
    assert a.assessment == "requires_future_capabilities"
    matched = next(r for r in a.reasons if r.get("effect") == "requires future")
    assert "Glovebox-M" in matched["match"]
    assert "NOT currently available" in matched["reason"]


def test_unavailable_blocks_and_is_not_relabeled_future(conn):
    conn, ref_id, sample_id = conn
    _reviewed(conn, ref_id, "pressed with Press-P (synthetic)")
    add_capability(conn, "Press-P (synthetic)", None, "unavailable")
    a = assess_fit(conn, sample_id, ref_id)
    assert a.assessment == "unknown"
    blocked = next(r for r in a.reasons if r.get("effect") == "blocked")
    assert "not silently relabeled as future" in blocked["reason"]


def test_unmatched_requirement_is_unknown_with_missing_fact_named(conn):
    conn, ref_id, sample_id = conn
    _reviewed(conn, ref_id, "electrodeposited (synthetic)")
    a = assess_fit(conn, sample_id, ref_id)
    assert a.assessment == "unknown"
    unmatched = next(r for r in a.reasons if r.get("match") == "no confirmed capability entry")
    assert "unknown" in unmatched["effect"]


def test_unreviewed_requirement_prevents_positive_assessment(conn):
    conn, ref_id, sample_id = conn
    record_assertion(conn, source_id=ref_id, claim_type="preparation",
                     claim_text="synthesized using Furnace-X (synthetic)",
                     epistemic_type="directly_reported")  # stays needs_verification
    add_capability(conn, "Furnace-X (synthetic)", None, "current")
    a = assess_fit(conn, sample_id, ref_id)
    assert a.assessment == "unknown"  # unreviewed requirement cannot ground a positive


def test_no_requirements_at_all_is_unknown(conn):
    conn, ref_id, sample_id = conn
    a = assess_fit(conn, sample_id, ref_id)
    assert a.assessment == "unknown"
    assert "insufficient evidence" in a.reasons[-1]["reason"]


def test_outdated_marking_after_capability_change_and_rerun(conn):
    conn, ref_id, sample_id = conn
    _reviewed(conn, ref_id, "synthesized using Furnace-X (synthetic)")
    cap = add_capability(conn, "Furnace-X (synthetic)", None, "future")
    first = assess_fit(conn, sample_id, ref_id)
    assert first.assessment == "requires_future_capabilities"
    assert first.outdated is False

    update_capability(conn, cap.id, cap.name, None, "current")  # profile changed
    later = latest_assessment(conn, sample_id)
    assert later.outdated is True  # old result can no longer appear current

    rerun = assess_fit(conn, sample_id, ref_id)
    assert rerun.assessment == "possible_with_current_capabilities"
    assert rerun.outdated is False


def test_missing_sample_rejected(db_path):
    conn = connect(db_path)
    with pytest.raises(LabFitValidationError):
        assess_fit(conn, 999, 1)
    conn.close()


def test_assessment_basis_and_reasons_survive_restart(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    ref = add_manual_reference(conn, doi="10.9999/durable-fit", title="Durable fit fixture")
    sample = record_sample(conn, source_id=ref.id, designation="Durable fit sample")
    _reviewed(conn, ref.id, "synthesized using Furnace-X (synthetic)")
    add_capability(conn, "Furnace-X (synthetic)", None, "current")
    assess_fit(conn, sample.id, ref.id)
    conn.close()

    reopened = connect(db_path)
    latest = latest_assessment(reopened, sample.id)
    assert latest is not None
    assert latest.assessment == "possible_with_current_capabilities"
    assert latest.outdated is False
    assert any("Furnace-X" in str(r) for r in latest.reasons)
    reopened.close()
