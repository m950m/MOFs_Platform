"""CI protection for the acceptance workflow (issue #13).

Runs the acceptance script in-process and fails if any step regresses. The
generated Markdown record is produced by scripts/acceptance_run.py.
"""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "acceptance_run.py"


def test_acceptance_workflow_all_steps_pass():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=120,
        cwd=str(SCRIPT.parents[1]),
    )
    assert result.returncode == 0, f"acceptance run failed:\n{result.stdout}\n{result.stderr}"
    assert "ALL CHECKS PASS" in result.stdout
    for step in ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S10"):
        assert f"| {step} " in result.stdout, f"missing step {step}"
