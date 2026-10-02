"""UI tests for the sample-record correction form (issue #20)."""

import pytest

from conftest import all_text
from mofs_platform.db.connection import connect
from mofs_platform.domain.identity import record_sample
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import add_manual_reference
from mofs_platform.domain.review import list_review_events


def by_key(elements, key):
    matches = [e for e in elements if e.key == key]
    assert len(matches) == 1, f"expected exactly one element with key {key!r}"
    return matches[0]


@pytest.fixture
def app_with_sample(run_app, db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Which prepared MOF samples merit inspection?"))
    ref = add_manual_reference(conn, doi="10.9999/fix-ui", title="Correction UI fixture")
    record_sample(conn, source_id=ref.id, designation="Wrong basis (synthetic)",
                  basis="experimental")
    conn.close()
    return run_app()


def _open_review_page(at):
    at.sidebar.radio[0].set_value("Review")
    at.run()


def test_sample_correction_section_lists_samples(app_with_sample):
    at = app_with_sample
    _open_review_page(at)
    text = all_text(at)
    assert "Correct a sample record" in text
    # the picker's option label shows designation + current basis
    picker = by_key(at.selectbox, "rev_sample")
    assert len(picker.options) == 1
    assert "Wrong basis (synthetic)" in picker.options[0]
    assert "experimental" in picker.options[0]


def test_sample_correction_via_ui_updates_and_logs(app_with_sample, db_path):
    at = app_with_sample
    _open_review_page(at)
    by_key(at.selectbox, "rev_sample").set_value(1)
    by_key(at.selectbox, "rc_basis").set_value("computational")
    by_key(at.text_input, "rc_editor").set_value("Mohammed (owner)")
    by_key(at.text_area, "rc_reason").set_value("the study is computational (synthetic)")
    by_key(at.button, "save_sample_correction").click()
    at.run()
    text = all_text(at)
    assert "Sample #1 corrected (basis; old" in text
    row = connect(db_path).execute(
        "SELECT basis FROM sample_record WHERE id = 1").fetchone()
    assert row["basis"] == "computational"
    events = list_review_events(connect(db_path), "sample_record", 1)
    assert events and events[0].action == "corrected"


def test_rejected_sample_correction_keeps_values_and_shows_error(app_with_sample, db_path):
    """G6: a rejected correction must not wipe the typed values, and nothing
    is persisted."""
    at = app_with_sample
    _open_review_page(at)
    by_key(at.selectbox, "rev_sample").set_value(1)
    by_key(at.text_input, "rc_editor").set_value("Mohammed (owner)")
    by_key(at.text_area, "rc_reason").set_value("typo hunt")
    # no field provided -> nothing to change -> rejected
    by_key(at.button, "save_sample_correction").click()
    at.run()
    assert at.error and "nothing to change" in at.error[0].value.lower()
    # typed values survive the rejection (no clear_on_submit)
    assert at.session_state["rc_reason"] == "typo hunt"
    events = list_review_events(connect(db_path), "sample_record", 1)
    assert events == []
