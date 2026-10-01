"""Shared fixtures: a temporary migrated database and an AppTest runner."""

from pathlib import Path

import pytest

APP_PATH = Path(__file__).resolve().parents[1] / "src" / "mofs_platform" / "app.py"


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "platform.db"


@pytest.fixture
def run_app(db_path, monkeypatch):
    """Run the app headlessly against a temp database; returns the AppTest."""

    def _run() -> "object":
        from streamlit.testing.v1 import AppTest

        monkeypatch.setenv("MOFS_DB_PATH", str(db_path))
        at = AppTest.from_file(str(APP_PATH), default_timeout=20)
        at.run()
        return at

    return _run


def all_text(at) -> str:
    parts: list[str] = []
    for group in (
        at.title,
        at.header,
        at.subheader,
        at.markdown,
        at.success,
        at.info,
        at.error,
        at.caption,
    ):
        for element in group:
            value = getattr(element, "value", None)
            if value:
                parts.append(str(value))
    return "\n".join(parts)
