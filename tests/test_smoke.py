"""Issue #3/#4 smoke tests: positive startup checks plus negative controls.

The negative controls prove the smoke check can actually fail (never an
unconditional pass)."""

from pathlib import Path

from mofs_platform.smoke import run_smoke

APP_PATH = Path(__file__).resolve().parents[1] / "src" / "mofs_platform" / "app.py"


def test_entry_point_starts_and_renders_ready_state(tmp_path, monkeypatch):
    monkeypatch.setenv("MOFS_DB_PATH", str(tmp_path / "smoke.db"))
    passed, message = run_smoke(APP_PATH)
    assert passed, message


def test_smoke_passes_after_a_question_is_saved(tmp_path, monkeypatch):
    from mofs_platform.db.connection import connect
    from mofs_platform.domain.questions import Question, save_question

    db = tmp_path / "with_question.db"
    monkeypatch.setenv("MOFS_DB_PATH", str(db))
    conn = connect(db)
    save_question(conn, Question(wording="Owner-entered question"))
    conn.close()
    passed, message = run_smoke(APP_PATH)
    assert passed, message


def test_smoke_fails_when_entry_point_is_broken(tmp_path, monkeypatch):
    monkeypatch.setenv("MOFS_DB_PATH", str(tmp_path / "unused.db"))
    broken = tmp_path / "broken_app.py"
    broken.write_text("raise RuntimeError('broken entry point')")
    passed, message = run_smoke(broken)
    assert not passed, f"smoke must fail on a broken entry point (got: {message})"


def test_smoke_fails_when_no_status_marker_is_present(tmp_path, monkeypatch):
    monkeypatch.setenv("MOFS_DB_PATH", str(tmp_path / "unused2.db"))
    silent = tmp_path / "silent_app.py"
    silent.write_text("import streamlit as st\n\nst.title('Some other app')\n")
    passed, message = run_smoke(silent)
    assert not passed, f"smoke must fail without a status marker (got: {message})"
