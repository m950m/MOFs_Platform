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


# --- number-row corrections (issue #17 edit path) ---------------------------


def _add_industry_row(conn):
    return add_number(
        conn, stream="industry_reference", label="DOE target", value="0.2-2",
        unit="A/cm2", reaction="HER", conditions_note="industrial scale",
        source_citation="DOE Hydrogen Program", source_year="2026",
        contributor="Mohammed (owner)",
    )


def test_correct_number_changes_fields_and_logs_history(conn_with_lab):
    from mofs_platform.domain.numbers import correct_number

    conn, _ref = conn_with_lab
    row = _add_industry_row(conn)
    result = correct_number(
        conn, row.id, editor="Mohammed (owner)",
        reason="year of the target revision", source_year="2027",
    )
    assert result["changed_fields"] == ["source_year"]
    events = conn.execute(
        "SELECT * FROM review_event WHERE entity_type = 'reference_number' "
        "AND entity_id = ?", (row.id,)
    ).fetchall()
    assert len(events) == 1 and events[0]["action"] == "corrected"
    assert '"2026"' in events[0]["previous_json"]
    assert '"2027"' in events[0]["updated_json"]
    updated = conn.execute(
        "SELECT source_year FROM reference_number WHERE id = ?", (row.id,)
    ).fetchone()["source_year"]
    assert updated == "2027"


def test_correct_number_blank_keeps_and_no_change_refused(conn_with_lab):
    from mofs_platform.domain.numbers import correct_number

    conn, _ref = conn_with_lab
    row = _add_industry_row(conn)
    with pytest.raises(NumberValidationError) as exc:
        correct_number(conn, row.id, editor="Mohammed (owner)", reason="noop",
                       label="DOE target")  # equals stored value
    assert "nothing to change" in str(exc.value).lower()
    kept = conn.execute(
        "SELECT value, unit, conditions_note FROM reference_number WHERE id = ?",
        (row.id,),
    ).fetchone()
    assert kept["value"] == "0.2-2" and kept["unit"] == "A/cm2"
    assert conn.execute(
        "SELECT COUNT(*) FROM review_event WHERE entity_type = 'reference_number'"
    ).fetchone()[0] == 0


def test_correct_number_validates_attribution_row_and_reaction(conn_with_lab):
    from mofs_platform.domain.numbers import correct_number

    conn, _ref = conn_with_lab
    row = _add_industry_row(conn)
    with pytest.raises(NumberValidationError) as e1:
        correct_number(conn, row.id, editor=None, reason=None, value="9")
    assert "editor" in str(e1.value)
    with pytest.raises(NumberValidationError) as e2:
        correct_number(conn, 999, editor="x", reason="y", value="9")
    assert "does not exist" in str(e2.value)
    with pytest.raises(NumberValidationError) as e3:
        correct_number(conn, row.id, editor="x", reason="y", reaction="NRR")
    assert "Reaction must be one of" in str(e3.value)
    assert conn.execute(
        "SELECT COUNT(*) FROM review_event WHERE entity_type = 'reference_number'"
    ).fetchone()[0] == 0


def test_correct_number_never_moves_stream_or_source(conn_with_lab):
    """The stream defines which D11 stream a row belongs to; correct_number
    offers no parameter to change it or the source pointer."""
    import inspect

    from mofs_platform.domain.numbers import correct_number

    conn, _ref = conn_with_lab
    row = _add_industry_row(conn)
    params = inspect.signature(correct_number).parameters
    assert "stream" not in params and "source_id" not in params
    correct_number(conn, row.id, editor="x", reason="typo", value="0.2-2.0")
    kept = conn.execute(
        "SELECT stream, source_id FROM reference_number WHERE id = ?", (row.id,)
    ).fetchone()
    assert kept["stream"] == "industry_reference" and kept["source_id"] is None


def test_migration_0017_preserves_history(db_path):
    import sqlite3

    from mofs_platform.db.connection import MIGRATIONS_DIR

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    pre = sorted(p for p in MIGRATIONS_DIR.glob("*.sql") if p.name < "0017")
    assert pre[-1].name == "0016_number_streams.sql"
    for path in pre:
        conn.executescript(path.read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO review_event (entity_type, entity_id, action, reviewer, "
        "updated_json, created_at) VALUES ('assertion', 3, 'corrected', "
        "'Mohammed (owner)', '{}', '2026-01-01 00:00:00')"
    )
    conn.commit()
    conn.executescript(
        (MIGRATIONS_DIR / "0017_number_corrections.sql").read_text(encoding="utf-8")
    )
    survived = conn.execute(
        "SELECT * FROM review_event WHERE entity_id = 3"
    ).fetchone()
    assert survived is not None and survived["created_at"] == "2026-01-01 00:00:00"
    conn.execute(
        "INSERT INTO review_event (entity_type, entity_id, action, updated_json) "
        "VALUES ('reference_number', 1, 'corrected', '{}')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO review_event (entity_type, entity_id, action, updated_json) "
            "VALUES ('junk', 1, 'corrected', '{}')"
        )
    conn.close()
