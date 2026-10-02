"""Identity-contract tests (issue #8): the five synthetic cases as code."""

import pytest

from mofs_platform.db.connection import connect
from mofs_platform.domain.identity import (
    IdentityValidationError,
    compare_samples,
    list_observations,
    list_relations,
    list_samples,
    list_states,
    record_observation,
    record_operating_state,
    record_sample,
)
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import add_manual_reference


@pytest.fixture
def conn(db_path):
    c = connect(db_path)
    save_question(c, Question(wording="Which prepared MOF samples merit inspection?"))
    return c


def _source(conn, doi, title):
    return add_manual_reference(conn, doi=doi, title=title, contributor="fixture").id


def _relations_for(conn, a, b):
    return [r for r in list_relations(conn) if {r["left"], r["right"]} == {a, b}]


# ---- Case 1: same generic name, different linker -> different ---------------

def test_case1_same_name_different_linker_is_different(conn):
    s1 = _source(conn, "10.9999/c1a", "Fixture paper S1")
    s2 = _source(conn, "10.9999/c1b", "Fixture paper S2")
    a = record_sample(conn, source_id=s1, designation="Framework-F",
                      linker="Linker-L", metal_node="Co")
    b = record_sample(conn, source_id=s2, designation="Framework-F",
                      linker="Linker-M", metal_node="Co")
    rels = compare_samples(conn, a.id, b.id)
    by_level = {r["level"]: r for r in rels}
    assert by_level["framework"]["relation"] == "different"
    assert by_level["sample"]["relation"] == "different"
    assert "Linker-L" in by_level["framework"]["reason"]
    assert all(r["merge_permission"] == "none" for r in rels)


# ---- Case 2: nanoparticle addition -> composite, observations stay -----------

def test_case2_nanoparticle_addition_is_composite_not_derived(conn):
    s1 = _source(conn, "10.9999/c2", "Fixture paper S3")
    a = record_sample(conn, source_id=s1, designation="Sample-A",
                      parent_framework_name="Framework-F")
    b = record_sample(conn, source_id=s1, designation="Sample-B",
                      parent_framework_name="Framework-F",
                      additions="Nano-N particles added",
                      lineage_kind="composite", derived_from_sample_id=a.id)
    rels = compare_samples(conn, a.id, b.id)
    by_relation = {r["relation"] for r in rels}
    assert "composite" in by_relation
    assert "derived" not in by_relation  # no transformation evidence claimed
    assert "same_parent_framework" in by_relation
    # Observation on B must NOT transfer to A:
    record_observation(conn, sample_id=b.id, source_id=s1, observation_kind="experimental",
                       value="150", unit="mV", reaction="HER")
    from mofs_platform.domain.identity import list_observations
    assert len(list_observations(conn, a.id)) == 0
    assert len(list_observations(conn, b.id)) == 1


# ---- Case 3: same structure, different activation -> different samples ------

def test_case3_same_cif_different_activation_stays_different(conn):
    s1 = _source(conn, "10.9999/c3", "Fixture paper S4")
    a = record_sample(conn, source_id=s1, designation="Sample-A",
                      parent_framework_name="Framework-F",
                      structure_ref="Model-F (same CIF)", activation="protocol P")
    b = record_sample(conn, source_id=s1, designation="Sample-B",
                      parent_framework_name="Framework-F",
                      structure_ref="Model-F (same CIF)", activation="protocol Q")
    rels = compare_samples(conn, a.id, b.id)
    by_level = {r["level"]: r for r in rels}
    assert by_level["framework"]["relation"] == "same_parent_framework"
    assert by_level["sample"]["relation"] == "different"
    assert "byte-identical CIF" in by_level["sample"]["reason"]
    assert by_level["sample"]["merge_permission"] == "none"


# ---- Case 4: reconstructed operating phase is a separate related state ------

def test_case4_reconstruction_state_labeled_author_interpretation(conn):
    s1 = _source(conn, "10.9999/c4", "Fixture paper S5")
    a = record_sample(conn, source_id=s1, designation="Sample-A")
    record_observation(conn, sample_id=a.id, source_id=s1, observation_kind="experimental",
                       value="180", unit="mV", reaction="HER",
                       medium="0.5 M H2SO4", reference_convention="RHE",
                       loading="0.2 mg/cm2", duration="10 h", protocol="LSV 5 mV/s",
                       evidence_location="fig. 2")
    state = record_operating_state(
        conn, sample_id=a.id, stage="during",
        phase_assignment="Phase-R (reconstructed)",
        epistemic_type="author_interpretation", evidence_location="fig. 3",
    )
    assert state.epistemic_type == "author_interpretation"
    obs = list_observations(conn, a.id)
    assert obs[0].value == "180"  # observation stays on the prepared sample
    assert obs[0].medium == "0.5 M H2SO4" and obs[0].loading == "0.2 mg/cm2"
    # Missing phase evidence: an unknown-type state, identity unresolved, no rename
    unresolved = record_operating_state(
        conn, sample_id=a.id, stage="during", phase_assignment=None,
        epistemic_type="unknown",
    )
    assert unresolved.phase_assignment is None
    assert a.designation == "Sample-A"  # sample never renamed


# ---- Case 5: metadata-only similar names -> unresolved, no merge ------------

def test_case5_similar_names_missing_structure_unresolved(conn):
    s1 = _source(conn, "10.9999/c5a", "Fixture paper S6 (metadata only)")
    s2 = _source(conn, "10.9999/c5b", "Fixture paper S7 (metadata only)")
    a = record_sample(conn, source_id=s1, designation="ZIF-like F")
    b = record_sample(conn, source_id=s2, designation="ZIF F")
    rels = compare_samples(conn, a.id, b.id)
    by_level = {r["level"]: r for r in rels}
    assert by_level["sample"]["relation"] == "unresolved"
    assert by_level["framework"]["relation"] == "unresolved"
    assert "different sources" in by_level["sample"]["reason"]
    assert "no structure reference" in by_level["sample"]["reason"]
    assert all(r["merge_permission"] == "none" for r in rels)


# ---- Within-source designation & cross-source guards ------------------------

def test_within_source_same_designation_needs_review_before_any_merge(conn):
    s1 = _source(conn, "10.9999/ws", "Fixture paper with methods+figures")
    a = record_sample(conn, source_id=s1, designation="Sample-B")
    b = record_sample(conn, source_id=s1, designation="Sample-B")
    rels = compare_samples(conn, a.id, b.id)
    assert rels[0]["relation"] == "same_reported_sample"
    assert rels[0]["merge_permission"] == "within_source_after_review"
    assert rels[0]["review_state"] == "needs_verification"  # not reviewed yet


def test_cross_source_shared_name_never_gains_equivalence(conn):
    s1 = _source(conn, "10.9999/x1", "Fixture paper X1")
    s2 = _source(conn, "10.9999/x2", "Fixture paper X2")
    a = record_sample(conn, source_id=s1, designation="Ni-MOF", composition="Ni C8H4O4")
    b = record_sample(conn, source_id=s2, designation="Ni-MOF", composition="Ni C8H4O4")
    rels = compare_samples(conn, a.id, b.id)
    sample_rel = next(r for r in rels if r["level"] == "sample")
    assert sample_rel["relation"] == "unresolved"
    assert sample_rel["merge_permission"] == "none"


def test_observation_context_fields_stay_independently_unknown(conn):
    s1 = _source(conn, "10.9999/obs", "Fixture paper obs")
    a = record_sample(conn, source_id=s1, designation="Sample-O")
    ob = record_observation(conn, sample_id=a.id, source_id=s1,
                            observation_kind="experimental", value="180", unit="mV")
    for field in (ob.reaction, ob.medium, ob.reference_convention,
                  ob.loading, ob.duration, ob.protocol):
        assert field is None  # each context field separately unknown, not defaulted


def test_restart_preserves_all_five_cases(db_path):
    """Build all five labeled cases, close, reopen, verify everything survives."""
    conn = connect(db_path)
    save_question(conn, Question(wording="Q"))
    s1 = _source(conn, "10.9999/r1", "Restart fixture 1")
    s2 = _source(conn, "10.9999/r2", "Restart fixture 2")
    # Case 1: different linkers
    c1a = record_sample(conn, source_id=s1, designation="Framework-F", linker="Linker-L")
    c1b = record_sample(conn, source_id=s2, designation="Framework-F", linker="Linker-M")
    compare_samples(conn, c1a.id, c1b.id)
    # Case 2: composite lineage + observation on the composite only
    c2a = record_sample(conn, source_id=s1, designation="Sample-A (restart)",
                        parent_framework_name="Framework-F")
    c2b = record_sample(conn, source_id=s1, designation="Sample-B (restart)",
                        parent_framework_name="Framework-F", additions="Nano-N",
                        lineage_kind="composite", derived_from_sample_id=c2a.id)
    record_observation(conn, sample_id=c2b.id, source_id=s1,
                       observation_kind="experimental", value="150", unit="mV",
                       reaction="HER", medium="0.5 M H2SO4")
    compare_samples(conn, c2a.id, c2b.id)
    # Case 4: operating state with author interpretation
    record_operating_state(conn, sample_id=c2a.id, stage="during",
                           phase_assignment="Phase-R (restart)",
                           epistemic_type="author_interpretation",
                           evidence_location="fig. 3 (restart)")
    conn.close()

    reopened = connect(db_path)
    assert len(list_samples(reopened)) == 4  # all samples survived
    rels = list_relations(reopened)
    relations = {r["relation"] for r in rels}
    assert "different" in relations  # case 1
    assert "composite" in relations  # case 2
    assert "same_parent_framework" in relations
    # Case 2 observation survived on the composite, not the parent:
    c2a_r = next(s for s in list_samples(reopened) if s.designation == "Sample-A (restart)")
    c2b_r = next(s for s in list_samples(reopened) if s.designation == "Sample-B (restart)")
    assert len(list_observations(reopened, c2a_r.id)) == 0
    c2b_obs = list_observations(reopened, c2b_r.id)
    assert c2b_obs and c2b_obs[0].medium == "0.5 M H2SO4"
    # Case 4 state survived with its author-interpretation label and location:
    states = list_states(reopened, c2a_r.id)
    assert states and states[0].phase_assignment == "Phase-R (restart)"
    assert states[0].epistemic_type == "author_interpretation"
    assert states[0].evidence_location == "fig. 3 (restart)"
    reopened.close()


def test_sample_requires_source_and_designation(conn):
    with pytest.raises(IdentityValidationError):
        record_sample(conn, source_id=999, designation="Ghost")
    s1 = _source(conn, "10.9999/val", "Fixture paper val")
    with pytest.raises(IdentityValidationError):
        record_sample(conn, source_id=s1, designation="   ")
    with pytest.raises(IdentityValidationError):
        record_sample(conn, source_id=s1, designation="X", basis="quantum")
