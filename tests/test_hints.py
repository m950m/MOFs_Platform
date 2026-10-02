"""Consistency-hint tests (issue #14) — every rule: positive + negative."""

from mofs_platform.db.connection import connect
from mofs_platform.domain.hints import question_hints
from mofs_platform.domain.questions import Question, save_question


def _q(wording, reactions=None, classes=None, conditions=None,
       hard=None, improvement=None):
    return Question(wording=wording, reactions=reactions,
                    material_classes=classes, conditions=conditions,
                    hard_requirements=hard, meaning_of_improvement=improvement)


# ---- R1: wording reaction missing from the field ----------------------------

def test_r1_positive_wording_mentions_oer_field_says_her_only():
    hints = question_hints(_q(
        wording="Which MOFs work for HER and the oxygen evolution reaction?",
        reactions="HER",
    ))
    r1 = [h for h in hints if h["rule"] == "R1"]
    assert len(r1) == 1 and "OER" in r1[0]["message"]
    assert "review" in r1[0]["message"].lower()


def test_r1_negative_consistent_reactions_no_hint():
    hints = question_hints(_q(
        wording="Which MOFs work for HER and OER?", reactions="HER, OER",
    ))
    assert not [h for h in hints if h["rule"] == "R1"]


def test_r1_word_boundary_her_does_not_match_where():
    hints = question_hints(_q(
        wording="Where are the conductive MOFs?", reactions="HER",
    ))
    # "Where" must not trigger HER-in-wording; field HER matches field itself.
    assert not [h for h in hints if h["rule"] == "R1"]


# ---- R2: field reaction missing from the wording ----------------------------

def test_r2_positive_field_lists_reaction_wording_omits():
    hints = question_hints(_q(
        wording="Which MOFs work for HER?", reactions="HER, OER",
    ))
    r2 = [h for h in hints if h["rule"] == "R2"]
    assert len(r2) == 1 and "OER" in r2[0]["message"]


def test_r2_negative_field_fully_covered_by_wording():
    hints = question_hints(_q(
        wording="Bifunctional HER and OER screening?", reactions="HER, OER",
    ))
    assert not [h for h in hints if h["rule"] == "R2"]


# ---- R3: material classes, both directions ---------------------------------

def test_r3_positive_wording_mentions_zif_field_omits():
    hints = question_hints(_q(
        wording="Which ZIFs and MOFs merit inspection?", classes="MOF",
    ))
    r3 = [h for h in hints if h["rule"] == "R3"]
    assert any("ZIF" in h["message"] for h in r3)


def test_r3_positive_field_lists_class_wording_omits():
    hints = question_hints(_q(
        wording="Which frameworks merit inspection?", classes="MOF, composite",
    ))
    r3 = [h for h in hints if h["rule"] == "R3"]
    assert any("composite" in h["message"] for h in r3)


def test_r3_negative_consistent_classes_no_hint():
    hints = question_hints(_q(
        wording="Which ZIFs merit inspection?", classes="ZIF",
    ))
    assert not [h for h in hints if h["rule"] == "R3"]


# ---- R4: benchmark cited while conditions unknown ---------------------------

def test_r4_positive_benchmark_with_unknown_conditions():
    hints = question_hints(_q(
        wording="Which MOFs merit inspection?",
        hard="Lower overpotential at the 10 mA/cm2 benchmark",
        improvement=None,
    ))
    r4 = [h for h in hints if h["rule"] == "R4"]
    assert len(r4) == 1 and "conditions" in r4[0]["message"].lower()


def test_r4_negative_conditions_recorded_no_hint():
    hints = question_hints(_q(
        wording="Which MOFs merit inspection?",
        conditions="0.5 M H2SO4, room temperature",
        hard="Lower overpotential at the 10 mA/cm2 benchmark",
    ))
    assert not [h for h in hints if h["rule"] == "R4"]


def test_r4_negative_no_benchmark_no_hint():
    hints = question_hints(_q(
        wording="Which MOFs merit inspection?", hard="Documented preparation",
    ))
    assert not [h for h in hints if h["rule"] == "R4"]


# ---- Cross-cutting criteria -------------------------------------------------

def test_fully_consistent_question_has_no_hints_at_all():
    hints = question_hints(_q(
        wording="Bifunctional HER and OER screening of MOFs",
        reactions="HER, OER", classes="MOF",
        conditions="0.5 M H2SO4, room temperature",
        hard="Documented experimental preparation",
    ))
    assert hints == []


def test_hints_never_persisted_and_save_unaffected(db_path):
    conn = connect(db_path)
    save_question(conn, _q(
        wording="HER and OER question (synthetic)", reactions="HER",
    ))
    from mofs_platform.domain.questions import count_events
    assert count_events(conn) == 1  # one save = one event; hints add nothing
    # hints computed live, twice, add nothing:
    q = conn.execute("SELECT wording, reactions FROM question WHERE id=1").fetchone()
    question = Question(wording=q["wording"], reactions=q["reactions"])
    first = question_hints(question)
    second = question_hints(question)
    assert first == second and first  # deterministic, recomputed
    assert count_events(conn) == 1  # hints added no history entries


def test_hints_recompute_after_reopen(db_path):
    conn = connect(db_path)
    save_question(conn, _q(wording="HER and OER question (synthetic)",
                           reactions="HER"))
    conn.close()
    reopened = connect(db_path)
    q = reopened.execute("SELECT wording, reactions FROM question WHERE id=1").fetchone()
    hints = question_hints(Question(wording=q["wording"], reactions=q["reactions"]))
    assert any(h["rule"] == "R1" for h in hints)  # recomputed from saved values
    reopened.close()


def test_r1_plural_acronyms_recognized():
    hints = question_hints(_q(wording="Screen HERs and OERs.", reactions="HER"))
    r1 = [h for h in hints if h["rule"] == "R1"]
    assert any("OER" in h["message"] for h in r1)


def test_r1_english_pronoun_her_never_fires():
    hints = question_hints(_q(wording="Summarize what her experiments showed.",
                              reactions="HER"))
    assert not [h for h in hints if h["rule"] == "R1"]
