"""UI tests for the Lab fit number-streams section (issue #17)."""

from conftest import all_text


def test_number_streams_empty_state_honest(run_app):
    at = run_app()
    at.sidebar.radio[0].set_value("Lab fit")
    at.run()
    text = all_text(at)
    assert "Number streams (D11: laboratory vs industry" in text
    assert "The reference table starts EMPTY" in text
    assert "DOE Hydrogen Program" in text


def test_add_row_and_comparison_render(run_app, db_path):
    at = run_app()
    at.sidebar.radio[0].set_value("Lab fit")
    at.run()

    def keyed(elements, key):
        matches = [e for e in elements if e.key == key]
        assert len(matches) == 1
        return matches[0]

    keyed(at.selectbox, "num_stream").set_value("industry_reference")
    keyed(at.text_input, "num_label").set_value("DOE 2026 target")
    keyed(at.text_input, "num_value").set_value("0.2-2")
    keyed(at.text_input, "num_unit").set_value("A/cm2")
    keyed(at.selectbox, "num_reaction").set_value("HER")
    keyed(at.text_area, "num_conditions").set_value("industrial scale")
    keyed(at.text_input, "num_citation").set_value("DOE Hydrogen Program targets")
    keyed(at.text_input, "num_year").set_value("2026")
    keyed(at.button, "num_save").click()
    at.run()
    assert any("industry_reference" in s.value for s in at.success)
    text = all_text(at).replace("\\", "")
    assert "Industry reference stream (1 rows)" in text
    assert "DOE 2026 target" in text
    assert any("the researcher draws the conclusion" in w.value
               for w in at.warning)  # caveat rendered as a warning
    # provenance enforcement: no citation AND no id → typed error
    keyed(at.text_input, "num_label").set_value("Bad row")
    keyed(at.text_input, "num_value").set_value("1")
    keyed(at.text_input, "num_citation").set_value("")
    keyed(at.button, "num_save").click()
    at.run()
    assert at.error and "Provenance required" in at.error[0].value
