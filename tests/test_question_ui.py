"""UI tests for the research-question page (issue #4, via streamlit.testing)."""

from conftest import all_text
from mofs_platform.db.connection import connect
from mofs_platform.domain.questions import get_question


def _open_question_page(at):
    at.sidebar.radio[0].set_value("Research question")
    at.run()


def test_home_shows_no_saved_question_and_invents_none(run_app):
    at = run_app()
    assert not at.exception
    text = all_text(at)
    assert "No research question saved yet." in text
    # Nothing is presented as if the researcher supplied it.
    assert "Saved question" not in text


def test_blank_save_shows_validation_and_saves_nothing(run_app, db_path):
    at = run_app()
    _open_question_page(at)
    assert at.text_area[0].value == ""  # no sample wording populated
    at.text_area[0].set_value("   ")
    at.button[0].click()
    at.run()
    assert at.error, "blank save must show a validation message"
    assert "empty" in at.error[0].value.lower()
    conn = connect(db_path)
    assert get_question(conn) is None  # nothing persisted


def test_save_then_reopen_in_fresh_session(run_app, db_path):
    at = run_app()
    _open_question_page(at)
    at.text_area[0].set_value("Which prepared MOF samples merit inspection for HER?")
    at.text_input[0].set_value("HER")  # reactions
    at.text_area[1].set_value("Aqueous, ambient")  # conditions
    at.text_area[2].set_value("Documented experimental preparation")  # hard
    at.text_area[3].set_value("Accessible linker")  # preferences
    at.button[0].click()
    at.run()
    assert not at.exception
    assert any("Question saved." in s.value for s in at.success)

    # A completely fresh application session must show the saved work.
    at2 = run_app()
    text = all_text(at2)
    assert "Ready — research question recorded" in text
    assert "Which prepared MOF samples merit inspection for HER?" in text
    _open_question_page(at2)
    assert at2.text_area[0].value == "Which prepared MOF samples merit inspection for HER?"
    assert at2.text_input[0].value == "HER"


def test_saved_display_distinguishes_hard_vs_preference_and_unknowns(run_app):
    at = run_app()
    _open_question_page(at)
    at.text_area[0].set_value("Q wording only")  # everything else left blank
    at.button[0].click()
    at.run()
    _open_question_page(at)
    text = all_text(at)
    assert "Hard requirements" in text
    assert "Preferences" in text
    assert "unknown" in text  # unset fields visibly unknown, not hidden


def test_unsaved_edit_is_not_presented_as_persisted(run_app, db_path):
    at = run_app()
    _open_question_page(at)
    at.text_area[0].set_value("Typed but never saved")
    # Navigate away without saving, then reopen fresh.
    at.sidebar.radio[0].set_value("Home")
    at.run()
    at2 = run_app()
    text = all_text(at2)
    assert "Typed but never saved" not in text
    conn = connect(db_path)
    assert get_question(conn) is None
