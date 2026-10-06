"""Docs-site doc-rot guard (issue #36, plan item 6).

The MkDocs Material site must keep rendering every page its navigation
promises, the nine app screens must keep their pages under names that still
match the app's own titles, and the honesty markers must stay present on the
landing / screens-overview / FAQ pages. The docs extra must also stay
optional: mkdocs may never become a runtime dependency. Same pattern as
test_contributing_guide.py — pure file checks, no mkdocs import needed, so
the guard runs in the normal suite without the [docs] extra installed.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MKDOCS_YML = ROOT / "mkdocs.yml"

EXPECTED_NAV_PAGES = (
    "index.md",
    "getting-started.md",
    "workflows.md",
    "evidence-packages.md",
    "internals.md",
    "faq.md",
    "screens/index.md",
)

EXPECTED_SCREEN_PAGES = (
    "screens/home.md",
    "screens/research-question.md",
    "screens/laboratory-profile.md",
    "screens/sources.md",
    "screens/evidence.md",
    "screens/samples-identity.md",
    "screens/candidates.md",
    "screens/review.md",
    "screens/lab-fit.md",
)

# The app's own screen titles (ui/pages/*.py) — docs pages must keep matching.
SCREEN_TITLES = {
    "screens/home.md": "# Home",
    "screens/research-question.md": "# Research question",
    "screens/laboratory-profile.md": "# Laboratory profile",
    "screens/sources.md": "# Sources",
    "screens/evidence.md": "# Evidence",
    "screens/samples-identity.md": "# Samples & identity",
    "screens/candidates.md": "# Candidates",
    "screens/review.md": "# Review",
    "screens/lab-fit.md": "# Lab fit",
}


def _nav_md_paths() -> list[str]:
    """Extract the .md paths from mkdocs.yml nav without a yaml dependency.

    Handles both entry forms used by the file: ``- Label: page.md`` and
    ``- page.md`` (nested section items)."""
    text = MKDOCS_YML.read_text(encoding="utf-8")
    nav_block = text.split("nav:", 1)[1]
    paths = []
    for line in nav_block.splitlines():
        match = re.search(r"-\s+(?:[^:]+:\s*)?(\S+\.md)\s*$", line)
        if match:
            paths.append(match.group(1))
    return paths


@pytest.mark.parametrize("page", EXPECTED_NAV_PAGES + EXPECTED_SCREEN_PAGES)
def test_nav_page_exists(page):
    assert page in _nav_md_paths(), f"{page} is missing from mkdocs.yml nav"
    assert (DOCS / page).is_file(), f"{page} is in the nav but the file is gone"


@pytest.mark.parametrize("page,title", sorted(SCREEN_TITLES.items()))
def test_screen_page_title_matches_app(page, title):
    text = (DOCS / page).read_text(encoding="utf-8")
    assert text.lstrip().startswith(title), (
        f"{page} must keep the H1 title '{title}' matching the app screen"
    )


def test_honesty_markers_stay_on_the_landing_page():
    text = (DOCS / "index.md").read_text(encoding="utf-8").lower()
    assert "never ranks or recommends" in text
    assert "metadata is not measurement" in text
    assert "no server, no cloud" in text
    assert "conflicting claims stay side by side" in text


def test_marker_glossary_stays_on_the_screens_overview():
    text = (DOCS / "screens" / "index.md").read_text(encoding="utf-8")
    for marker in ("`unknown`", "`needs verification`", "`no_hit`",
                   "`not yet searched`", "`reviewed`", "`conflicted`"):
        assert marker in text, f"marker glossary lost {marker}"


def test_faq_keeps_the_honesty_questions():
    text = (DOCS / "faq.md").read_text(encoding="utf-8")
    assert "studies" in text or "unstudied" in text
    assert "never" in text.lower()
    # the table of markers must survive edits
    for marker in ("`unknown`", "`needs verification`", "`conflicted`",
                   "`no_hit`", "`not yet searched`"):
        assert marker in text, f"FAQ marker table lost {marker}"


def test_internals_embeds_the_existing_mermaid_diagrams():
    text = (DOCS / "internals.md").read_text(encoding="utf-8")
    source = (ROOT / "_docs" / "proposals" / "diagrams.md").read_text(
        encoding="utf-8"
    )
    assert text.count("```mermaid") == 4
    # each embedded diagram must be a verbatim block from the source of record
    for block in [b.strip() for b in text.split("```mermaid")[1:]]:
        diagram = block.split("```", 1)[0].strip()
        assert diagram in source, "internals.md diagram drifted from the source file"
    assert "_docs/proposals/diagrams.md" in text  # source pointer present


def test_evidence_packages_page_links_contributing_without_duplicating_it():
    text = (DOCS / "evidence-packages.md").read_text(encoding="utf-8")
    assert "CONTRIBUTING.md" in text
    # no duplication: the schema file and run commands stay owned by CONTRIBUTING
    assert "package-schema-v1" in text  # named, not explained in depth
    assert ".venv/bin/pytest" not in text
    assert "Identity invariants are untouchable" not in text


def test_mkdocs_never_becomes_a_runtime_dependency():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    main_deps = pyproject.split("dependencies = [", 1)[1].split("]", 1)[0]
    assert "mkdocs" not in main_deps.lower()
    docs_extra = pyproject.split("docs = [", 1)[1].split("]", 1)[0]
    assert "mkdocs-material" in docs_extra


def test_publish_workflow_deploys_the_strict_build():
    text = (ROOT / ".github" / "workflows" / "docs.yml").read_text(
        encoding="utf-8"
    )
    assert "mkdocs build --strict" in text
    assert 'pip install -e ".[docs]"' in text
    assert "workflow_dispatch" in text
