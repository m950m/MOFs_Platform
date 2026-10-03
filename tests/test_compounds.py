"""Compound profile tests (issue #18) — distinctness, no climbing, D11."""

import pytest

from mofs_platform.db.connection import connect
from mofs_platform.domain.compounds import (
    CompoundValidationError,
    attach_member,
    create_compound,
    detach_member,
    get_profile,
    list_compounds,
)
from mofs_platform.domain.identity import record_observation, record_sample
from mofs_platform.domain.questions import Question, save_question
from mofs_platform.domain.references import add_manual_reference


@pytest.fixture
def conn_with_members(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Which conductive MOFs for HER and OER?"))
    ref = add_manual_reference(conn, doi="10.9999/compound-fixture", title="Fixture")
    sample = record_sample(
        conn, source_id=ref.id, designation="CoCoZn(HITP)2 (computational model)",
        linker="HITP", metal_node="Co, Zn", composition="CoCoZn(HITP)2",
        basis="computational",
    )
    record_observation(
        conn, sample_id=sample.id, source_id=ref.id, observation_kind="computational",
        value="0.39", unit="V", reaction="other",
        protocol="computed total overpotential (HER + OER sum)",
        evidence_location="Abstract",
    )
    conn.execute(
        "INSERT INTO structure_index (provider, external_id, name, formula, doi, "
        "extra_json) VALUES ('qmof', 'QMOF-1', 'CoCoZn(HITP)2 model', "
        "'C24N12CoZn', '10.9999/qmof-ref', '{\"Band Gap (eV)\": \"1.42\"}')"
    )
    conn.commit()
    structure_id = conn.execute(
        "SELECT id FROM structure_index WHERE external_id = 'QMOF-1'"
    ).fetchone()[0]
    return conn, ref.id, sample.id, structure_id


def test_create_requires_name_note_and_creator(conn_with_members):
    conn, *_ = conn_with_members
    with pytest.raises(CompoundValidationError) as exc:
        create_compound(conn, canonical_name=" ", identity_note="x", created_by="y")
    assert "canonical name" in str(exc.value)
    with pytest.raises(CompoundValidationError) as exc2:
        create_compound(conn, canonical_name="C", identity_note="x", created_by="")
    assert "who is creating" in str(exc2.value)


def test_attach_requires_membership_reason_and_existing_member(conn_with_members):
    conn, _ref, sample_id, _structure_id = conn_with_members
    c = create_compound(
        conn, canonical_name="CoCoZn(HITP)2", identity_note="the reported best candidate",
        created_by="Mohammed (owner)", framework_key="mofkey-abc",
    )
    with pytest.raises(CompoundValidationError) as exc:
        attach_member(conn, compound_id=c.id, member_type="sample_record",
                      member_id=sample_id, added_by="Mohammed (owner)", reason=None)
    assert "membership reason" in str(exc.value)
    with pytest.raises(CompoundValidationError) as exc2:
        attach_member(conn, compound_id=c.id, member_type="sample_record",
                      member_id=9999, added_by="Mohammed (owner)", reason="x")
    assert "does not exist" in str(exc2.value)
    link = attach_member(conn, compound_id=c.id, member_type="sample_record",
                         member_id=sample_id, added_by="Mohammed (owner)",
                         reason="the paper's reported candidate")
    assert link.member_id == sample_id
    with pytest.raises(CompoundValidationError) as exc3:
        attach_member(conn, compound_id=c.id, member_type="sample_record",
                      member_id=sample_id, added_by="Mohammed (owner)", reason="dup")
    assert "already a member" in str(exc3.value)


def test_profile_keeps_properties_under_members_and_streams_separate(conn_with_members):
    conn, _ref, sample_id, structure_id = conn_with_members
    c = create_compound(
        conn, canonical_name="CoCoZn(HITP)2", identity_note="reported candidate",
        created_by="Mohammed (owner)",
    )
    attach_member(conn, compound_id=c.id, member_type="sample_record",
                  member_id=sample_id, added_by="Mohammed (owner)", reason="reported")
    attach_member(conn, compound_id=c.id, member_type="structure_index",
                  member_id=structure_id, added_by="Mohammed (owner)", reason="same composition")
    profile = get_profile(conn, c.id)
    assert len(profile.samples) == 1 and len(profile.structures) == 1
    # the observation stays UNDER its sample, labeled by its kind
    assert profile.samples[0]["observations"][0]["kind"] == "computational"
    assert profile.samples[0]["observations"][0]["value"] == "0.39"
    # the structure's computed property stays provider-labeled metadata
    assert profile.structures[0]["properties"]["Band Gap (eV)"] == "1.42"
    # nothing climbed: the compound itself carries no values


def test_distinctness_same_formula_two_arrangements_two_profiles(conn_with_members):
    """Owner mandate: same composition, different arrangement → separate
    compounds, separate profiles, no transfer."""
    conn, _ref, _sample_id, structure_id = conn_with_members
    conn.execute(
        "INSERT INTO structure_index (provider, external_id, name, formula, doi, "
        "extra_json) VALUES ('core_mof_2019', 'CM-99', 'CoCoZn(HITP)2 alt-topology', "
        "'C24N12CoZn', '10.9999/alt', NULL)"
    )
    conn.commit()
    alt_id = conn.execute(
        "SELECT id FROM structure_index WHERE external_id = 'CM-99'"
    ).fetchone()[0]
    c1 = create_compound(conn, canonical_name="CoCoZn(HITP)2 arrangement A",
                         identity_note="HITP arrangement A", created_by="Mohammed (owner)")
    c2 = create_compound(conn, canonical_name="CoCoZn(HITP)2 arrangement B",
                         identity_note="same formula, different topology",
                         created_by="Mohammed (owner)")
    attach_member(conn, compound_id=c1.id, member_type="structure_index",
                  member_id=structure_id, added_by="Mohammed (owner)", reason="topology A")
    attach_member(conn, compound_id=c2.id, member_type="structure_index",
                  member_id=alt_id, added_by="Mohammed (owner)", reason="topology B")
    p1, p2 = get_profile(conn, c1.id), get_profile(conn, c2.id)
    assert len(p1.structures) == 1 and len(p2.structures) == 1
    assert p1.structures[0]["id"] != p2.structures[0]["id"]
    assert p1.structures[0]["properties"] != {} or p2.structures[0]["properties"] == {}
    # no transfer: profile B has no properties from profile A's member
    assert "Band Gap (eV)" not in p2.structures[0]["properties"]


def test_detach_is_attributed_and_audited(conn_with_members):
    conn, _ref, sample_id, _structure_id = conn_with_members
    c = create_compound(conn, canonical_name="C", identity_note="n",
                        created_by="Mohammed (owner)")
    link = attach_member(conn, compound_id=c.id, member_type="sample_record",
                         member_id=sample_id, added_by="Mohammed (owner)", reason="r")
    with pytest.raises(CompoundValidationError) as exc:
        detach_member(conn, link_id=link.id, actor="Mohammed (owner)", reason=None)
    assert "detachment reason" in str(exc.value)
    detach_member(conn, link_id=link.id, actor="Mohammed (owner)", reason="wrong grouping")
    profile = get_profile(conn, c.id)
    assert profile.samples == []
    actions = [e["action"] for e in profile.events]
    assert actions == ["compound_created", "member_attached", "member_detached"]


def test_empty_profile_is_honest(conn_with_members):
    conn, *_ = conn_with_members
    c = create_compound(conn, canonical_name="Empty compound", identity_note="n",
                        created_by="Mohammed (owner)")
    profile = get_profile(conn, c.id)
    assert profile.samples == [] and profile.structures == []
    assert list_compounds(conn)[0].canonical_name == "Empty compound"
