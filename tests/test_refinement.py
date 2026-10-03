"""Mechanical refinement observations (issue #15, Part A)."""

from mofs_platform.domain.questions import Question
from mofs_platform.domain.refinement import (
    VAGUE_TERMS,
    VAGUE_TERMS_DOCUMENTATION,
    mechanical_observations,
)


def test_vague_terms_are_flagged_with_reasons():
    q = Question(wording="Find a low-cost and efficient MOF for HER")
    obs = mechanical_observations(q)
    vague = [o for o in obs if o["kind"] == "vague_term"]
    details = {o["detail"] for o in vague}
    assert "low-cost" in details and "efficient" in details
    assert all("state what it means" in o["message"] for o in vague)


def test_unknown_fields_are_flagged():
    q = Question(wording="Which MOFs catalyze HER?")
    obs = mechanical_observations(q)
    unknown = [o for o in obs if o["kind"] == "unknown_field"]
    fields = {o["detail"] for o in unknown}
    assert {"reactions", "conditions", "hard_requirements"} <= fields


def test_hint_rules_are_reused_verbatim():
    # R1: wording mentions HER but the reactions field is unknown
    q = Question(wording="Which MOFs catalyze the HER?")
    obs = mechanical_observations(q)
    hints = [o for o in obs if o["kind"] == "hint"]
    assert any(o["detail"] == "R1" for o in hints)


def test_precise_complete_question_yields_zero_observations():
    """The issue's negative test: a precise, complete question must produce
    NO observations — no false alarms."""
    q = Question(
        wording=(
            "Which conductive MOF compositions function as a single "
            "bifunctional electrode for the hydrogen evolution reaction and "
            "the oxygen evolution reaction in 1 M KOH at room temperature?"
        ),
        reactions="HER, OER",
        material_classes="MOF",
        conditions="1 M KOH electrolyte, 25 C",
        hard_requirements="overpotential below 300 mV at 10 mA/cm2 for each reaction",
        preferences="nickel based",
        meaning_of_improvement="lower total overpotential than the reference set",
    )
    assert mechanical_observations(q) == []


def test_vague_term_list_is_documented_and_visible():
    assert len(VAGUE_TERMS) >= 10
    assert all(t in VAGUE_TERMS_DOCUMENTATION for t in VAGUE_TERMS)
    assert "complete visible set" in VAGUE_TERMS_DOCUMENTATION
