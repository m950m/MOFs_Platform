"""UI tests for the Sources page (issue #6)."""

import pytest

from conftest import all_text
from mofs_platform.db.connection import connect
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import list_references
from mofs_platform.sources import crossref


def by_key(elements, key):
    matches = [e for e in elements if e.key == key]
    assert len(matches) == 1, f"expected exactly one element with key {key!r}"
    return matches[0]


def _open_sources_page(at):
    at.sidebar.radio[0].set_value("Sources")
    at.run()


@pytest.fixture
def app_with_question(run_app, db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Which prepared MOF samples merit inspection?"))
    conn.close()
    return run_app()


def test_sources_page_requires_saved_question_first(run_app):
    at = run_app()
    _open_sources_page(at)
    text = all_text(at)
    assert "No research question is saved yet" in text
    assert "Capture reference" not in text  # entry surface withheld


def test_manual_capture_creates_attributed_lead(app_with_question, db_path):
    at = app_with_question
    _open_sources_page(at)
    by_key(at.text_input, "ref_doi").set_value("10.9999/manual-lead")
    by_key(at.text_area, "ref_title").set_value("A paper the researcher supplies")
    by_key(at.text_input, "ref_contributor").set_value("Mohammed (owner)")
    by_key(at.button, "save_reference").click()
    at.run()
    assert any("Reference captured (lead)" in s.value for s in at.success)
    text = all_text(at)
    assert "Origin: `manual`" in text
    assert "Mohammed (owner)" in text
    refs = list_references(connect(db_path))
    assert len(refs) == 1 and refs[0].question_id == 1


def test_metadata_only_lead_is_labeled_needs_verification(app_with_question):
    at = app_with_question
    _open_sources_page(at)
    by_key(at.text_input, "ref_doi").set_value("10.9999/metadata-only")
    by_key(at.button, "save_reference").click()
    at.run()
    text = all_text(at)
    assert "needs verification" in text  # metadata-only lead labeled, not verified


def test_enrich_success_shows_metadata_and_stays_lead(app_with_question, db_path, monkeypatch):
    metadata = crossref.CrossrefMetadata(
        doi="10.9999/enrich-me",
        title="Publisher title from Crossref",
        container="Some Journal",
        issued_year="2024",
        license_url="https://example.com/license",
        url="https://doi.org/10.9999/enrich-me",
        indexed="2026-10-02T00:00:00",
    )
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.fetch_metadata", lambda *a, **k: metadata
    )
    at = app_with_question
    _open_sources_page(at)
    by_key(at.text_input, "ref_doi").set_value("10.9999/enrich-me")
    by_key(at.button, "save_reference").click()
    at.run()
    by_key(at.button, "enrich_1").click()
    at.run()
    text = all_text(at)
    assert "Publisher title from Crossref" in text
    assert "Some Journal" in text
    assert "the reference remains a lead" in text
    assert len(list_references(connect(db_path))) == 1


def test_enrich_no_hit_shows_honest_warning_not_novelty_claim(app_with_question, monkeypatch):
    monkeypatch.setattr(
        "mofs_platform.sources.crossref.fetch_metadata",
        lambda *a, **k: crossref.CrossrefFailure("no_hit", "No Crossref record."),
    )
    at = app_with_question
    _open_sources_page(at)
    by_key(at.text_input, "ref_doi").set_value("10.9999/not-there")
    by_key(at.button, "save_reference").click()
    at.run()
    by_key(at.button, "enrich_1").click()
    at.run()
    assert at.warning, "typed failure must be surfaced"
    assert "does NOT mean the material is unstudied" in at.warning[0].value


def test_successful_capture_survives_rerun_without_duplicate(app_with_question, db_path):
    """Guided session 001: post-submit reset is Streamlit's native
    clear_on_submit, never a manual session_state write for form widgets —
    manual writes raise StreamlitWidgetAlreadyInstantiatedError in the real
    browser. AppTest reproduces neither the crash nor the native clear, so
    this test pins what it can see: no exception, and reruns do not re-fire
    the capture."""
    at = app_with_question
    _open_sources_page(at)
    by_key(at.text_input, "ref_doi").set_value("10.9999/clears-after-save")
    by_key(at.button, "save_reference").click()
    at.run()
    assert any("Reference captured (lead)" in s.value for s in at.success)
    assert not at.exception
    at.run()
    at.run()
    assert not at.exception
    refs = list_references(connect(db_path))
    assert len(refs) == 1 and refs[0].doi == "10.9999/clears-after-save"


def test_restart_shows_saved_references_with_provenance(app_with_question, run_app, db_path):
    at = app_with_question
    _open_sources_page(at)
    by_key(at.text_input, "ref_doi").set_value("10.9999/durable")
    by_key(at.text_area, "ref_title").set_value("Durable lead")
    by_key(at.button, "save_reference").click()
    at.run()

    at2 = run_app()  # fresh application session
    _open_sources_page(at2)
    text = all_text(at2)
    assert "Durable lead" in text
    assert "10.9999/durable" in text
    assert "Origin: `manual`" in text


# --- structure lookup (issue #24, D12 slice 1) -------------------------------


def test_structure_section_shows_honest_empty_instructions(app_with_question):
    at = app_with_question
    _open_sources_page(at)
    text = all_text(at)
    assert "Structure lookup (D12: CoRE MOF 2019 first)" in text
    assert "The index is empty" in text
    assert "The tool never downloads anything itself" in text


def test_structure_import_search_and_capture(app_with_question, db_path, tmp_path):
    csv = tmp_path / "core.csv"
    csv.write_text(
        "MOF Name,DOI,Formula\n"
        "Zn-MOF-test,10.9999/zn-mof,C8H4O4Zn\n"
    )
    at = app_with_question
    _open_sources_page(at)
    by_key(at.selectbox, "struct_provider").set_value("core_mof_2019")
    by_key(at.text_input, "struct_csv_path").set_value(str(csv))
    by_key(at.button, "struct_import").click()
    at.run()
    assert any("[core_mof_2019]: 1 new" in s.value for s in at.success)

    by_key(at.text_input, "struct_query").set_value("Zn-MOF")
    by_key(at.button, "struct_search").click()
    at.run()
    text = all_text(at)
    assert "Zn-MOF-test" in text and "10.9999/zn-mof" in text
    assert "leads, not verified samples" in text

    by_key(at.button, "capture_struct_1").click()
    at.run()
    assert any("captured as reference #1" in s.value for s in at.success)
    refs = list_references(connect(db_path))
    assert len(refs) == 1
    assert "structure index [core_mof_2019]" in refs[0].supplied_input


def test_structure_extras_render_as_theory_metadata(app_with_question, db_path, tmp_path):
    """QMOF-style computed properties ride along from the provider CSV and
    render labeled to their provider — theory-stream metadata, never lab
    evidence (D11)."""
    csv = tmp_path / "qmof.csv"
    csv.write_text(
        "MOF Name,DOI,Band Gap (eV)\n"
        "QMOF-test,10.9999/qmof,1.42\n"
    )
    at = app_with_question
    _open_sources_page(at)
    by_key(at.selectbox, "struct_provider").set_value("qmof")
    by_key(at.text_input, "struct_csv_path").set_value(str(csv))
    by_key(at.button, "struct_import").click()
    at.run()
    by_key(at.text_input, "struct_query").set_value("QMOF-test")
    by_key(at.button, "struct_search").click()
    at.run()
    text = all_text(at)
    assert "record properties:" in text
    assert "Band Gap (eV)" in text
