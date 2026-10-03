"""UI tests for the research-question page (issue #4, via streamlit.testing)."""

from conftest import all_text
from mofs_platform.db.connection import connect
from mofs_platform.domain.questions import count_events, get_question
from mofs_platform.domain.refinement import VAGUE_TERMS_DOCUMENTATION
from mofs_platform.sources import glm


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


# --- issue #15: refinement observations + optional assistant ----------------


def test_vague_question_shows_mechanical_observations(run_app):
    at = run_app()
    at.sidebar.radio[0].set_value("Research question")
    at.run()
    at.text_area[0].set_value("Find a low-cost MOF for HER")
    matches = [b for b in at.button if getattr(b, "label", "") == "Save question"]
    matches[0].click()
    at.run()
    text = all_text(at)
    assert "Mechanical observations" in text
    assert "'low-cost'" in text
    assert "tool inference" in text
    assert VAGUE_TERMS_DOCUMENTATION[:40] in text


def test_precise_complete_question_shows_no_observations(run_app):
    at = run_app()
    at.sidebar.radio[0].set_value("Research question")
    at.run()
    at.text_area[0].set_value(
        "Which conductive MOF compositions function as a single bifunctional "
        "electrode for the hydrogen evolution reaction and the oxygen "
        "evolution reaction in 1 M KOH at room temperature?"
    )
    at.text_input[0].set_value("HER, OER")
    at.text_input[1].set_value("MOF")
    areas = [t for t in at.text_area]
    areas[1].set_value("1 M KOH electrolyte, 25 C")   # conditions
    areas[2].set_value("overpotential below 300 mV")  # hard requirements
    areas[3].set_value("nickel based")                # preferences
    areas[4].set_value("lower total overpotential")   # meaning of improvement
    matches = [b for b in at.button if getattr(b, "label", "") == "Save question"]
    matches[0].click()
    at.run()
    text = all_text(at)
    assert "No mechanical observations" in text


def test_ai_suggestion_requires_enable_and_never_autosaves(run_app, db_path, monkeypatch):
    suggestion = glm.GLMRefinement(
        suggestions={"conditions": "1 M KOH electrolyte"},
        notes="adds the missing electrolyte.",
    )
    monkeypatch.setattr(
        "mofs_platform.sources.glm.suggest_refinement",
        lambda *a, **k: suggestion,
    )
    at = run_app()
    at.sidebar.radio[0].set_value("Research question")
    at.run()
    at.text_area[0].set_value("Which MOFs catalyze HER?")
    next(b for b in at.button if getattr(b, "label", "") == "Save question").click()
    at.run()
    # unchecked enable -> warning, nothing sent
    next(b for b in at.button if getattr(b, "label", "") == "Request suggestions").click()
    at.run()
    assert at.warning and "Enable the assistant first" in at.warning[0].value
    # enable + request -> suggestion rendered as tool inference
    at.checkbox[0].check()
    next(b for b in at.button if getattr(b, "label", "") == "Request suggestions").click()
    at.run()
    text = all_text(at)
    assert "tool inference" in text and "1 M KOH electrolyte" in text
    assert "never auto-applied" in text
    # the saved question is UNCHANGED until the owner applies AND saves
    q = get_question(connect(db_path))
    assert q.conditions is None
    # apply -> form prefilled, but still not saved
    next(b for b in at.button if getattr(b, "label", "") == "Apply suggestion to the form below").click()
    at.run()
    q = get_question(connect(db_path))
    assert q.conditions is None  # applying never saves
    # the owner's explicit save persists it as their own value
    next(b for b in at.button if getattr(b, "label", "") == "Save question").click()
    at.run()
    q = get_question(connect(db_path))
    assert q.conditions == "1 M KOH electrolyte"
    # every assistant call was audited
    conn = connect(db_path)
    rows = conn.execute(
        "SELECT outcome FROM route_attempt WHERE attempt_kind = 'ai_refinement'"
    ).fetchall()
    assert [r[0] for r in rows] == ["success"]
