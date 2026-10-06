"""CONTRIBUTING.md doc-rot guard (issue #19 AC5).

The guide must always explain the three mandated topics: the evidence-
package format, how to run the offline test suite, and the PR rule that
identity invariants and provenance may not be weakened. If a future edit
drops any of them, this test fails.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_contributing_guide_covers_the_mandated_topics():
    text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    # AC topic 1: the package format
    assert "package-schema-v1.json" in text
    assert "needs_verification" in text
    assert "never anonymous" in text or "Packages are never anonymous" in text
    # AC topic 2: how to run the offline test suite
    assert ".venv/bin/pytest" in text
    assert "No live network in tests" in text
    # AC topic 3: the PR rules per ARCHITECTURE.md
    assert "Identity invariants are untouchable" in text
    assert "Provenance is untouchable" in text
    assert "ARCHITECTURE.md" in text


def test_contributing_guide_documents_the_submission_path():
    text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "attach" in text.lower()  # package JSON attached to an issue/PR
    assert "no upload endpoint" in text.lower()  # local-first, by decision
