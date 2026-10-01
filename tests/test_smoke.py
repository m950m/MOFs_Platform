"""Issue #3 smoke tests: positive startup check plus negative controls.

The negative controls prove the smoke check can actually fail (issue #3:
'never an unconditional pass')."""

from pathlib import Path

from mofs_platform.smoke import run_smoke

APP_PATH = Path(__file__).resolve().parents[1] / "src" / "mofs_platform" / "app.py"


def test_entry_point_starts_and_renders_ready_state():
    passed, message = run_smoke(APP_PATH)
    assert passed, message


def test_smoke_fails_when_entry_point_is_broken(tmp_path):
    broken = tmp_path / "broken_app.py"
    broken.write_text("raise RuntimeError('broken entry point')")
    passed, message = run_smoke(broken)
    assert not passed, f"smoke must fail on a broken entry point (got: {message})"


def test_smoke_fails_when_ready_marker_is_missing(tmp_path):
    silent = tmp_path / "silent_app.py"
    silent.write_text("import streamlit as st\n\nst.title('Some other app')\n")
    passed, message = run_smoke(silent)
    assert not passed, f"smoke must fail without the ready-state marker (got: {message})"
