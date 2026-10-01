"""UI tests for the research-question page (issue #4, via streamlit.testing)."""

from conftest import all_text
from mofs_platform.db.connection import connect
from mofs_platform.domain.questions import count_events, get_question


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
    assert "Ready — data recorded" in text
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


def test_ui_correction_second_save_updates_in_place(run_app, db_path):
    at = run_app()
    _open_question_page(at)
    at.text_area[0].set_value("First wording")
    at.button[0].click()
    at.run()
    _open_question_page(at)
    # The form is prefilled with the saved state; correct only the wording.
    assert at.text_area[0].value == "First wording"
    at.text_area[0].set_value("Corrected wording")
    at.button[0].click()
    at.run()
    _open_question_page(at)
    assert at.text_area[0].value == "Corrected wording"
    conn = connect(db_path)
    saved = get_question(conn)
    assert saved is not None
    assert saved.wording == "Corrected wording"
    rows = conn.execute("SELECT COUNT(*) FROM question").fetchone()[0]
    assert rows == 1  # still one saved question, not a duplicate
    assert count_events(conn) == 2  # created + corrected


def test_ui_persistence_failure_shows_error_not_success(run_app, db_path, monkeypatch):
    from mofs_platform.domain.questions import QuestionPersistenceError

    def failing_save(conn, question):
        raise QuestionPersistenceError(
            "Saving the question failed; the previously saved question is "
            "unchanged. (injected)"
        )

    at = run_app()
    _open_question_page(at)
    at.text_area[0].set_value("This save must fail")
    monkeypatch.setattr(
        "mofs_platform.ui.pages.question_page.save_question", failing_save
    )
    at.button[0].click()
    at.run()
    assert at.error, "failure must be surfaced"
    assert "failed" in at.error[0].value.lower()
    assert not any("Question saved." in s.value for s in at.success)
    conn = connect(db_path)
    assert get_question(conn) is None  # nothing partially written


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
