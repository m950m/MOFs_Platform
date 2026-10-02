"""UI tests for the laboratory capability profile page (issue #5)."""

from conftest import all_text
from mofs_platform.db.connection import connect
from mofs_platform.domain.labprofile import list_capabilities


def by_key(elements, key):
    matches = [e for e in elements if e.key == key]
    assert len(matches) == 1, f"expected exactly one element with key {key!r}"
    return matches[0]


def _open_lab_page(at):
    at.sidebar.radio[0].set_value("Laboratory profile")
    at.run()


def _button(at, prefix: str):
    matches = [b for b in at.button if (getattr(b, "label", "") or "").startswith(prefix)]
    assert len(matches) == 1, f"expected one button starting with {prefix!r}, got {len(matches)}"
    return matches[0]


def test_empty_profile_reports_nothing_recorded_and_invents_nothing(run_app):
    at = run_app()
    _open_lab_page(at)
    text = all_text(at)
    assert "No laboratory capability recorded yet." in text
    assert not at.exception
    # No invented equipment, restrictions, or defaults (e.g. no HHTP line).
    assert "glovebox" not in text.lower()
    assert "HHTP" not in text


def test_blank_name_shows_validation_and_saves_nothing(run_app, db_path):
    at = run_app()
    _open_lab_page(at)
    by_key(at.button, "save_capability").click()
    at.run()
    assert at.error, "blank name must show a validation message"
    assert "empty" in at.error[0].value.lower()
    assert list_capabilities(connect(db_path)) == []


def test_add_entries_with_distinct_statuses_displayed_distinctly(run_app, db_path):
    at = run_app()
    _open_lab_page(at)
    # current entry
    by_key(at.text_input, "cap_name").set_value("Synthetic furnace A")
    by_key(at.radio, "cap_status").set_value("current")
    by_key(at.button, "save_capability").click()
    at.run()
    assert any("Capability added" in s.value for s in at.success)

    # explicitly unavailable entry — must display distinctly from unknown
    by_key(at.text_input, "cap_name").set_value("Synthetic glovebox B")
    by_key(at.radio, "cap_status").set_value("unavailable")
    by_key(at.button, "save_capability").click()
    at.run()

    # future entry — must display as NOT currently available
    by_key(at.text_input, "cap_name").set_value("Synthetic potentiostat C")
    by_key(at.radio, "cap_status").set_value("future")
    by_key(at.button, "save_capability").click()
    at.run()

    text = all_text(at)
    assert "current — available now" in text
    assert "explicitly unavailable" in text
    assert "future — planned, NOT currently available" in text
    assert len(list_capabilities(connect(db_path))) == 3


def test_correction_via_correct_button_updates_in_place(run_app, db_path):
    at = run_app()
    _open_lab_page(at)
    by_key(at.text_input, "cap_name").set_value("Synthetic reflux setup")
    by_key(at.radio, "cap_status").set_value("future")
    by_key(at.button, "save_capability").click()
    at.run()

    _button(at, "Correct:").click()
    at.run()
    assert by_key(at.text_input, "cap_name").value == "Synthetic reflux setup"  # prefilled
    by_key(at.radio, "cap_status").set_value("current")
    by_key(at.button, "save_capability").click()
    at.run()

    entries = list_capabilities(connect(db_path))
    assert len(entries) == 1  # corrected in place, no duplicate
    assert entries[0].status == "current"
    assert any("Correction saved" in s.value for s in at.success)


def test_duplicate_name_rejected_in_ui(run_app):
    at = run_app()
    _open_lab_page(at)
    by_key(at.text_input, "cap_name").set_value("Synthetic tool D")
    by_key(at.button, "save_capability").click()
    at.run()
    by_key(at.text_input, "cap_name").set_value("synthetic tool D")
    by_key(at.button, "save_capability").click()
    at.run()
    assert at.error
    assert "already exists" in at.error[0].value.lower()


def test_reopen_in_fresh_session_shows_saved_profile(run_app, db_path):
    at = run_app()
    _open_lab_page(at)
    by_key(at.text_input, "cap_name").set_value("Synthetic durable entry")
    by_key(at.radio, "cap_status").set_value("unavailable")
    by_key(at.button, "save_capability").click()
    at.run()

    at2 = run_app()  # completely fresh application session
    _open_lab_page(at2)
    text = all_text(at2)
    assert "Synthetic durable entry" in text
    assert "explicitly unavailable" in text
    # The home status line also reflects the saved profile:
    at2.sidebar.radio[0].set_value("Home")
    at2.run()
    assert "Ready — data recorded" in all_text(at2)


def test_ui_persistence_failure_shows_error_not_success(run_app, db_path, monkeypatch):
    from mofs_platform.domain.labprofile import LabProfilePersistenceError

    def failing_update(conn, capability_id, name, description, status):
        raise LabProfilePersistenceError(
            "Saving failed; the previously saved profile is unchanged. (injected)"
        )

    at = run_app()
    _open_lab_page(at)
    by_key(at.text_input, "cap_name").set_value("Synthetic entry for failure test")
    by_key(at.radio, "cap_status").set_value("current")
    by_key(at.button, "save_capability").click()
    at.run()
    _button(at, "Correct:").click()
    at.run()
    by_key(at.radio, "cap_status").set_value("future")
    monkeypatch.setattr(
        "mofs_platform.ui.pages.lab_profile.update_capability", failing_update
    )
    by_key(at.button, "save_capability").click()
    at.run()
    assert at.error, "failure must be surfaced"
    assert "failed" in at.error[0].value.lower()
    assert not any("Correction saved" in s.value for s in at.success)
    entries = list_capabilities(connect(db_path))
    assert len(entries) == 1
    assert entries[0].status == "current"  # previous value intact


def test_unsaved_add_is_not_persisted(run_app, db_path):
    at = run_app()
    _open_lab_page(at)
    by_key(at.text_input, "cap_name").set_value("Typed but never saved")
    at.sidebar.radio[0].set_value("Home")
    at.run()
    at2 = run_app()
    assert "Typed but never saved" not in all_text(at2)
    assert list_capabilities(connect(db_path)) == []


def test_correction_save_exits_edit_mode(run_app, db_path):
    """Guided session 001: saving a correction exits edit mode and the form
    returns to 'Add capability' with cleared fields (clear_on_submit)."""
    at = run_app()
    _open_lab_page(at)
    by_key(at.text_input, "cap_name").set_value("Furnace (synthetic)")
    by_key(at.button, "save_capability").click()
    at.run()
    _button(at, "Correct:").click()
    at.run()
    assert any("Correcting entry" in w.value for w in at.warning)
    by_key(at.text_input, "cap_name").set_value("Furnace corrected (synthetic)")
    by_key(at.button, "save_capability").click()
    at.run()
    text = all_text(at)
    assert "Correction saved" in text
    assert "Correcting entry" not in text
    caps = list_capabilities(connect(db_path))
    assert len(caps) == 1 and caps[0].name == "Furnace corrected (synthetic)"
