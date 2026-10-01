"""Headless startup smoke check (issue #3).

Runs the Streamlit entry point in the AppTest runtime and asserts the
observable startup result (the empty/ready state marker). A broken entry
point or failed startup produces a failing result and exit code 1 —
never an unconditional pass.

Usage: python -m mofs_platform.smoke
"""

import sys
from pathlib import Path

READY_MARKER = "Empty / ready"

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
    if READY_MARKER not in _rendered_text(at):
        return False, f"ready-state marker {READY_MARKER!r} missing from rendered output"
    return True, "entry point started and rendered the empty/ready state"


def main() -> int:
    passed, message = run_smoke(APP_PATH)
    print(f"smoke: {'PASS' if passed else 'FAIL'} — {message}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
