"""Headless startup smoke check (issues #3 and #4).

Runs the Streamlit entry point in the AppTest runtime and asserts the
observable startup result: the app starts without an exception and the home
page renders its honest status line — the empty/ready marker when nothing is
saved, or the question-recorded marker once a question exists. A broken
entry point or failed startup produces a failing result and exit code 1 —
never an unconditional pass.

Usage: python -m mofs_platform.smoke
"""

import sys
from pathlib import Path

READY_MARKERS = (
    "Empty / ready",
    "Ready — research question recorded",
)

APP_PATH = Path(__file__).resolve().parent / "app.py"


def _rendered_text(at) -> str:
    parts: list[str] = []
    for group in (at.title, at.header, at.subheader, at.markdown, at.success, at.info):
        for element in group:
            value = getattr(element, "value", None)
            if value:
                parts.append(str(value))
    return "\n".join(parts)


def run_smoke(app_path: Path) -> tuple[bool, str]:
    """Run the entry point headlessly; return (passed, explanation)."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(app_path), default_timeout=20)
    at.run()
    if at.exception:
        return False, f"entry point raised an exception: {at.exception[0].value!r}"
    text = _rendered_text(at)
    if not any(marker in text for marker in READY_MARKERS):
        return False, f"none of the ready-state markers {READY_MARKERS!r} found in output"
    return True, "entry point started and rendered its status line"


def main() -> int:
    passed, message = run_smoke(APP_PATH)
    print(f"smoke: {'PASS' if passed else 'FAIL'} — {message}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
