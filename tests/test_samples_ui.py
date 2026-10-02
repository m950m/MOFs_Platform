"""UI tests for the Samples & identity page (issue #8)."""

import pytest

from conftest import all_text
from mofs_platform.db.connection import connect
from mofs_platform.domain.identity import list_observations, list_relations, list_samples
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import add_manual_reference


def by_key(elements, key):
    matches = [e for e in elements if e.key == key]
    assert len(matches) == 1, f"expected exactly one element with key {key!r}"
    return matches[0]


@pytest.fixture
def app_with_reference(run_app, db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Which prepared MOF samples merit inspection?"))
    add_manual_reference(conn, doi="10.9999/fixture-a", title="Fixture paper A",
                         contributor="Mohammed (owner)")
    add_manual_reference(conn, doi="10.9999/fixture-b", title="Fixture paper B",
                         contributor="Mohammed (owner)")
    conn.close()
    return run_app()


def _open_samples_page(at):
    at.sidebar.radio[0].set_value("Samples & identity")
    at.run()


def test_record_sample_via_ui_with_correct_source(app_with_reference, db_path):
    at = app_with_reference
    _open_samples_page(at)
    by_key(at.selectbox, "smp_source").set_value(1)
    by_key(at.text_input, "smp_designation").set_value("Sample-A (synthetic)")
    by_key(at.text_input, "smp_linker").set_value("Linker-L (synthetic)")
    by_key(at.button, "save_sample").click()
    at.run()
    assert any("Sample recorded" in s.value for s in at.success)
    samples = list_samples(connect(db_path))
    assert len(samples) == 1
    assert samples[0].source_id == 1  # the selected source, not a hardcoded one


def test_record_observation_uses_selected_source_and_unknown_reaction(
    app_with_reference, db_path
):
    at = app_with_reference
    _open_samples_page(at)
    by_key(at.selectbox, "smp_source").set_value(2)  # sample from source 2
    by_key(at.text_input, "smp_designation").set_value("Sample-B (synthetic)")
    by_key(at.button, "save_sample").click()
    at.run()
    by_key(at.selectbox, "obs_sample").set_value(1)
    by_key(at.selectbox, "obs_source").set_value(2)  # read from paper B
    by_key(at.text_input, "obs_value").set_value("180")
    by_key(at.text_input, "obs_unit").set_value("mV")
    by_key(at.button, "save_observation").click()
    at.run()
    obs = list_observations(connect(db_path))
    assert len(obs) == 1
    assert obs[0].source_id == 2  # the selected source — no silent misattribution
    assert obs[0].reaction is None  # reaction stays unknown unless explicitly chosen


def test_compare_shows_relation_with_merge_permission_and_location(
    app_with_reference, db_path
):
    at = app_with_reference
    _open_samples_page(at)
    by_key(at.selectbox, "smp_source").set_value(1)
    by_key(at.text_input, "smp_designation").set_value("Sample-A (synthetic)")
    by_key(at.button, "save_sample").click()
    at.run()
    by_key(at.selectbox, "smp_source").set_value(2)
    by_key(at.text_input, "smp_designation").set_value("Sample-A (synthetic)")
    by_key(at.button, "save_sample").click()
    at.run()
    # Same designation but different sources → unresolved, never equivalence
    by_key(at.selectbox, "cmp_a").set_value(1)
    by_key(at.selectbox, "cmp_b").set_value(2)
    by_key(at.text_input, "cmp_location").set_value("Methods §2 (fixture)")
    matches = [b for b in at.button if getattr(b, "label", "") == "Compare"]
    assert len(matches) == 1
    matches[0].click()
    at.run()
    text = all_text(at)
    assert "**unresolved**" in text
    assert "`none`" in text  # merge blocked
    assert "Methods §2 (fixture)" in text  # evidence location rendered
    assert "different sources" in text


def test_conflicting_attributes_block_merge_and_show_both_values(
    app_with_reference, db_path
):
    at = app_with_reference
    _open_samples_page(at)
    by_key(at.selectbox, "smp_source").set_value(1)
    by_key(at.text_input, "smp_designation").set_value("Same name (synthetic)")
    by_key(at.text_input, "smp_composition").set_value("Ni C8H4O4")
    by_key(at.button, "save_sample").click()
    at.run()
    by_key(at.selectbox, "smp_source").set_value(1)
    by_key(at.text_input, "smp_designation").set_value("Same name (synthetic)")
    by_key(at.text_input, "smp_composition").set_value("Zn C8H4O4")
    by_key(at.button, "save_sample").click()
    at.run()
    by_key(at.selectbox, "cmp_a").set_value(1)
    by_key(at.selectbox, "cmp_b").set_value(2)
    matches = [b for b in at.button if getattr(b, "label", "") == "Compare"]
    matches[0].click()
    at.run()
    text = all_text(at)
    assert "**unresolved**" in text
    assert "Ni C8H4O4" in text and "Zn C8H4O4" in text  # both values exposed
    assert "`conflicted`" in text  # review state flags the conflict
    relations = list_relations(connect(db_path))
    assert all(r["merge_permission"] == "none" for r in relations)


def test_composite_lineage_recorded_via_ui(app_with_reference, db_path):
    at = app_with_reference
    _open_samples_page(at)
    by_key(at.selectbox, "smp_source").set_value(1)
    by_key(at.text_input, "smp_designation").set_value("Parent sample (synthetic)")
    by_key(at.button, "save_sample").click()
    at.run()
    by_key(at.selectbox, "smp_source").set_value(1)
    by_key(at.text_input, "smp_designation").set_value("Composite sample (synthetic)")
    by_key(at.text_input, "smp_additions").set_value("Nano-N (synthetic)")
    by_key(at.selectbox, "smp_lineage_sel").set_value("composite")
    by_key(at.selectbox, "smp_lineage_parent").set_value(1)
    by_key(at.button, "save_sample").click()
    at.run()
    by_key(at.selectbox, "cmp_a").set_value(1)
    by_key(at.selectbox, "cmp_b").set_value(2)
    matches = [b for b in at.button if getattr(b, "label", "") == "Compare"]
    matches[0].click()
    at.run()
    text = all_text(at)
    assert "**composite**" in text
    assert "derived" not in text.replace("derived/composite", "")  # no derivation claim
    relations = list_relations(connect(db_path))
    assert any(r["relation"] == "composite" for r in relations)


def test_targeting_pickers_survive_sample_save(app_with_reference, db_path):
    """Guided session 001: source/sample pickers live outside the forms so
    they survive saves — consecutive entries must not silently re-target."""
    at = app_with_reference
    at.sidebar.radio[0].set_value("Samples & identity")
    at.run()
    by_key(at.selectbox, "smp_source").set_value(2)  # default (newest first)
    by_key(at.text_input, "smp_designation").set_value("Survival check (synthetic)")
    by_key(at.button, "save_sample").click()
    at.run()
    assert at.session_state["smp_source"] == 2  # picker kept its selection
    samples = list_samples(connect(db_path))
    assert len(samples) == 1 and samples[0].source_id == 2
    assert not at.exception
