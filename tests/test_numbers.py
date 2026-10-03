"""Number streams tests (issue #17, D11) — separate streams, display-only."""

import pytest

from mofs_platform.db.connection import connect
from mofs_platform.domain.identity import record_observation, record_sample
from mofs_platform.domain.numbers import (
    CAVEAT,
    NumberValidationError,
    add_number,
    build_comparison,
    list_numbers,
)
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import add_manual_reference


@pytest.fixture
def conn_with_lab(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Which conductive MOFs for HER and OER?"))
    ref = add_manual_reference(conn, doi="10.9999/lab-num", title="Lab fixture")
    sample = record_sample(conn, source_id=ref.id, designation="My MOF (synthetic)")
    record_observation(
        conn, sample_id=sample.id, source_id=ref.id, observation_kind="experimental",
        value="180", unit="mV", reaction="HER", medium="0.5 M H2SO4",
    )
    return conn, ref.id


def test_add_requires_provenance_and_attribution(conn_with_lab):
    conn, _ref_id = conn_with_lab
    with pytest.raises(NumberValidationError) as exc:
        add_number(conn, stream="industry_reference", label="DOE target",
                   value="0.2-2 A/cm2", reaction="HER", contributor="Mohammed (owner)")
    assert "Provenance required" in str(exc.value)
    with pytest.raises(NumberValidationError) as exc2:
        add_number(conn, stream="industry_reference", label="L", value="1",
                   reaction="HER", source_citation="DOE", contributor="")
    assert "contributor" in str(exc2.value)


def test_streams_stay_separate(conn_with_lab):
    conn, _ref_id = conn_with_lab
    add_number(conn, stream="industry_reference", label="DOE 2026 target",
               value="0.2-2", unit="A/cm2", reaction="HER",
               conditions_note="industrial scale, alkaline electrolyzer",
               source_citation="DOE Hydrogen Program targets", source_year="2026",
               contributor="Mohammed (owner)")
    lab = list_numbers(conn, "laboratory")
    industry = list_numbers(conn, "industry_reference")
    assert all(n.stream == "laboratory" for n in lab)
    assert all(n.stream == "industry_reference" for n in industry)
    assert len(industry) == 1 and len(lab) == 0  # the observation is not a row


def test_comparison_pairs_same_reaction_and_shows_conditions(conn_with_lab):
    conn, _ref_id = conn_with_lab
    add_number(conn, stream="industry_reference", label="DOE target",
               value="0.2-2", unit="A/cm2", reaction="HER",
               conditions_note="industrial scale", source_citation="DOE",
               source_year="2026", contributor="Mohammed (owner)")
    add_number(conn, stream="industry_reference", label="OER target",
               value="300", unit="mV", reaction="OER",
               source_citation="DOE", contributor="Mohammed (owner)")
    result = build_comparison(conn)
    assert CAVEAT == result["caveat"]
    her = [c for c in result["comparisons"] if c["reaction"] == "HER"]
    assert len(her) == 1
    assert her[0]["laboratory"]["value"] == "180"
    assert her[0]["laboratory"]["medium"] == "0.5 M H2SO4"  # conditions displayed
    assert her[0]["industry_reference"][0]["conditions_note"] == "industrial scale"
    assert [c["reaction"] for c in result["comparisons"]] == ["HER"]  # OER lab absent


def test_missing_sides_render_honestly(conn_with_lab):
    conn, _ref_id = conn_with_lab
    result = build_comparison(conn)
    assert result["comparisons"][0]["industry_reference"] == []  # no rows yet
    assert list_numbers(conn, "laboratory") == []  # observations are not rows


def test_invalid_stream_reaction_and_source(conn_with_lab):
    conn, _ref_id = conn_with_lab
    with pytest.raises(NumberValidationError):
        add_number(conn, stream="marketing", label="L", value="1", reaction="HER",
                   source_citation="s", contributor="c")
    with pytest.raises(NumberValidationError):
        add_number(conn, stream="laboratory", label="L", value="1", reaction="NRR",
                   source_citation="s", contributor="c")
    with pytest.raises(NumberValidationError):
        add_number(conn, stream="laboratory", label="L", value="1", reaction="HER",
                   source_id=999, contributor="c")


def test_injection_style_values_stored_as_data(conn_with_lab):
    conn, _ref_id = conn_with_lab
    n = add_number(conn, stream="industry_reference",
                   label="'; DROP TABLE reference_number; --", value="**1**",
                   reaction="HER", source_citation="[x](http://e)",
                   contributor="Mohammed (owner)")
    assert "DROP TABLE" in n.label  # stored verbatim as data
    assert conn.execute(
        "SELECT COUNT(*) FROM reference_number"
    ).fetchone()[0] == 1
