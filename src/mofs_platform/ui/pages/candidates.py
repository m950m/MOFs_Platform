"""Candidates page (issue #10): inspect why a candidate appeared and follow
each claim to its recorded evidence. No ranking, no scoring, no invention.
"""

import streamlit as st

from mofs_platform.domain.candidates import (
    CandidateValidationError,
    get_candidate_card,
    list_candidate_cards,
    retrieval_outcome_summary,
)
from mofs_platform.domain.compounds import (
    PROVIDER_LABELS,
    CompoundPersistenceError,
    CompoundValidationError,
    attach_member,
    create_compound,
    detach_member,
    get_profile,
    list_compounds,
)
from mofs_platform.ui._widgets import esc

CANDIDATES_PAGE_TITLE = "Candidates"


def render_candidates_page(conn) -> None:
    st.header(CANDIDATES_PAGE_TITLE)
    flash = st.session_state.pop("flash", None)  # one-shot display notice
    if flash:
        st.success(flash)
    cards = list_candidate_cards(conn)

    if not cards:
        st.info(
            "No candidates saved for the question yet — record samples under "
            "**Samples & identity**. Nothing is invented here."
        )
        summary = retrieval_outcome_summary(conn)
        if summary:
            outcomes = ", ".join(f"`{k}`: {v}" for k, v in sorted(summary.items()))
            st.markdown(f"**Recorded retrieval outcomes:** {outcomes}")
        st.divider()
        _render_compounds_section(conn)
        return

    st.subheader(f"Saved candidates ({len(cards)})")
    candidate_options = {c.sample_id: f"#{c.sample_id} — {c.designation}" for c in cards}
    st.selectbox("Inspect candidate", list(candidate_options), key="cand_select",
                 format_func=lambda k: candidate_options[k])

    if st.button("Inspect", key="inspect_candidate", type="primary"):
        st.session_state["inspect_requested"] = st.session_state.get("cand_select")
    requested = st.session_state.get("inspect_requested")

    if requested is None:
        st.caption("Select a candidate and press Inspect to open its card.")
        st.divider()
        _render_compounds_section(conn)
        return
    try:
        card = get_candidate_card(conn, requested)
    except CandidateValidationError as exc:
        st.error(str(exc))
        return

    st.markdown(f"### Candidate #{card.sample_id}: {esc(card.designation)}")
    st.markdown(
        f"- Basis: `{card.basis}` — material class (composition as entered): "
        f"{esc(card.material_class) if card.material_class else '`unknown`'}\n"
        f"- Parent relation: {esc(card.parent_relation) if card.parent_relation else '`unknown`'}\n"
        f"- Modifications/additions: {esc(card.modifications) if card.modifications else '`unknown`'}\n"
        f"- Source: {esc(card.source_label)} — inspected level: {card.source_inspected_level}\n"
        f"- Route outcomes for this source: "
        + (", ".join(f"`{r['outcome']}`" for r in card.route_outcomes) or "`unknown`")
    )
    st.markdown(f"**Why it appeared:** {esc(card.retrieval_reason)}")

    st.subheader("Observations (per tested sample)")
    for ob in card.observations:
        gaps = ", ".join(ob["gaps"]) if ob["gaps"] else "none"
        st.markdown(
            f"- `{ob['kind']}` {(esc(ob['value']) if ob['value'] else '`unknown`')} "
            f"{esc(ob['unit']) if ob['unit'] else ''} — sample #{ob['sample_id']} — "
            f"location: {(esc(ob['evidence_location']) if ob['evidence_location'] else '`unknown`')}\n"
            f"  - missing condition fields: {gaps} — these are displayed as gaps, "
            "not compared or ranked."
        )
    if not card.observations:
        st.markdown("- `unknown` — no observation recorded.")

    st.subheader("Operating-state interpretations")
    for stt in card.operating_states:
        st.markdown(f"- ({stt['stage']}) phase '{(esc(stt['phase']) if stt['phase'] else '`unknown`')}' — {stt['epistemic']} "
                    f"— location: {(esc(stt['evidence_location']) if stt['evidence_location'] else '`unknown`')}")
    if not card.operating_states:
        st.markdown("- `unknown` — no operating state recorded.")

    st.subheader("Recorded assertions for this source (follow to evidence)")
    for a in card.assertions:
        conflict = (
            f" — **CONFLICT with #{a['conflicts_with']}**" if a["conflicts_with"] else ""
        )
        st.markdown(
            f"- Assertion #{a['id']} [{a['claim_type']}]: {esc(a['claim_text'])}\n"
            f"  - location: {esc(a['location'])} — {a['epistemic']} — "
            f"review: `{a['review_state']}`{conflict}"
        )
    if card.conflicts:
        st.warning(
            "This source has conflicting assertions: both claims stay individually "
            "accessible above; neither is averaged or replaced."
        )
    if any(a["review_state"] != "reviewed" for a in card.assertions) or not card.assertions:
        st.caption(
            "One reviewed assertion would not make the whole candidate reviewed; "
            "metadata-only records need verification. No ranking is shown anywhere "
            "on this card."
        )
    if not card.assertions:
        st.info("No assertions recorded for this source yet — record them under **Evidence**.")

    st.divider()
    _render_compounds_section(conn)


def _render_compounds_section(conn) -> None:
    """Compound feature cards (issue #18): researcher-grouped aggregation —
    manual, attributed, reasoned; never a merge, never an equivalence claim
    (D5); same composition with a different arrangement/morphology belongs
    in a separate compound. Streams stay separate per D11; sample properties
    stay under their sample (no climbing); conflicting values sit side by
    side; empty sections render `unknown` — nothing enters from memory."""
    st.subheader("Compounds (feature cards)")

    with st.form("compound_form"):
        st.text_input("Canonical compound name", key="cp_name")
        st.text_input(
            "Framework key (optional — MOFid/MOFkey or equivalent)",
            key="cp_key",
            help="A mechanical node+linker+topology key distinguishes "
            "arrangements a formula collapses. Its absence never blocks a "
            "profile.",
        )
        st.text_area(
            "Identity note (required — why this grouping exists)",
            key="cp_note",
            height=60,
        )
        st.text_input("Created by", value="Mohammed (owner)", key="cp_by")
        st.form_submit_button("Create compound", key="cp_create", type="primary")
    if st.session_state.get("cp_create"):
        try:
            c = create_compound(
                conn, canonical_name=st.session_state.get("cp_name"),
                identity_note=st.session_state.get("cp_note"),
                created_by=st.session_state.get("cp_by"),
                framework_key=st.session_state.get("cp_key"),
            )
            st.session_state["flash"] = (
                f"Compound #{c.id} '{esc(c.canonical_name)}' created — grouping is "
                "manual and reasoned, never a merge (D5)."
            )
            st.rerun()
        except CompoundValidationError as exc:
            st.error(str(exc))
        except CompoundPersistenceError as exc:
            st.error(str(exc))

    compounds = list_compounds(conn)
    if not compounds:
        st.info("No compounds yet — create one above, then attach samples and "
                "structure records as members.")
        return
    compound_options = {c.id: f"#{c.id} — {c.canonical_name}" for c in compounds}
    st.selectbox("Inspect compound", list(compound_options), key="cp_select",
                 format_func=lambda k: compound_options[k])
    if st.button("Open profile", key="cp_open"):
        st.session_state["cp_requested"] = st.session_state.get("cp_select")
    requested = st.session_state.get("cp_requested")
    if requested is None:
        st.caption("Select a compound and press Open profile.")
        return
    profile = get_profile(conn, requested)
    c = profile.compound
    st.markdown(
        f"**Compound #{c.id}: {esc(c.canonical_name)}**"
        + (f" — framework key: `{esc(c.framework_key)}`" if c.framework_key else "")
        + f"\n\nIdentity note: {esc(c.identity_note)} — created by {esc(c.created_by)}."
    )
    st.caption(
        "This grouping was made by the researcher with recorded reasons. "
        "Grouping is NOT sample equivalence and NEVER merges records (D5): "
        "same composition with a different arrangement/morphology belongs in "
        "a SEPARATE compound. Member properties never climb between members."
    )
    if profile.samples:
        st.markdown("**Sample members** (observations stay under their sample):")
        for s in profile.samples:
            st.markdown(
                f"- Sample #{s['id']} {esc(s['designation'])} (`{s['basis']}`) — "
                f"composition: {(esc(s['composition']) if s['composition'] else '`unknown`')} — attached: "
                f"{esc(s['reason'])}"
            )
            if s["observations"]:
                for o in s["observations"]:
                    st.markdown(
                        f"  - [{o['kind']}] {(esc(o['value']) if o['value'] else '`unknown`')} "
                        f"{(esc(o['unit']) if o['unit'] else '')} — reaction: {o['reaction'] or '`unknown`'}"
                        f" — medium: {(esc(o['medium']) if o['medium'] else '`unknown`')}"
                        f" — loc: {(esc(o['location']) if o['location'] else '`unknown`')}"
                    )
            else:
                st.markdown("  - observations: `unknown` — none recorded")
    else:
        st.markdown("- Sample members: `unknown` — none attached")
    if profile.structures:
        st.markdown("**Structure-record members** (provider-labeled metadata):")
        for r in profile.structures:
            st.markdown(
                f"- Record #{r['id']} {esc(r['name'])} — "
                f"{PROVIDER_LABELS.get(r['provider'], r['provider'])}"
                + (f" — formula: {esc(r['formula'])}" if r["formula"] else "")
                + (f" — DOI: {esc(r['doi'])}" if r["doi"] else "")
                + f" — attached: {esc(r['reason'])}"
            )
            if r["properties"]:
                for k, v in r["properties"].items():
                    st.markdown(f"  - {esc(k)}: {esc(v)} (provider metadata)")
            else:
                st.markdown("  - properties: `unknown` — none in the index")
    else:
        st.markdown("- Structure-record members: `unknown` — none attached")
    st.caption(
        "Values from different members sit side by side with their provenance "
        "— never averaged, never silently overwritten, never ranked. Empty "
        "sections are honest `unknown`s: literature values are never inserted "
        "from memory."
    )
    st.markdown("**Membership changes (attributed):**")
    with st.form("compound_attach_form"):
        st.selectbox(
            "Member type", ["sample_record", "structure_index"], key="cp_mtype"
        )
        st.text_input("Member id (the record's number)", key="cp_mid")
        st.text_input("Added by", value="Mohammed (owner)", key="cp_mby")
        st.text_area("Reason (required — why this record belongs here)",
                     key="cp_mreason", height=50)
        st.form_submit_button("Attach member", key="cp_attach")
    if st.session_state.get("cp_attach"):
        try:
            attach_member(
                conn, compound_id=requested,
                member_type=st.session_state.get("cp_mtype"),
                member_id=st.session_state.get("cp_mid"),
                added_by=st.session_state.get("cp_mby"),
                reason=st.session_state.get("cp_mreason"),
            )
            st.session_state["flash"] = "Member attached with a recorded reason."
            st.rerun()
        except CompoundValidationError as exc:
            st.error(str(exc))
        except CompoundPersistenceError as exc:
            st.error(str(exc))
    if profile.samples or profile.structures:
        links = [
            (s["link_id"], f"sample #{s['id']} {esc(s['designation'])}")
            for s in profile.samples
        ] + [
            (r["link_id"], f"structure #{r['id']} {esc(r['name'])}")
            for r in profile.structures
        ]
        link_options = {lid: label for lid, label in links}
        st.selectbox("Detach a member", list(link_options), key="cp_detach_sel",
                     format_func=lambda k: link_options[k])
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Detached by", value="Mohammed (owner)", key="cp_dby")
        with c2:
            st.text_input("Detachment reason (required)", key="cp_dreason")
        if st.button("Detach member", key="cp_detach"):
            try:
                detach_member(
                    conn, link_id=st.session_state.get("cp_detach_sel"),
                    actor=st.session_state.get("cp_dby"),
                    reason=st.session_state.get("cp_dreason"),
                )
                st.session_state["flash"] = (
                    "Member detached with a recorded reason — the event stays "
                    "audited."
                )
                st.rerun()
            except CompoundValidationError as exc:
                st.error(str(exc))
            except CompoundPersistenceError as exc:
                st.error(str(exc))
    if profile.events:
        st.caption("Audit: " + " · ".join(
            f"{e['action']} by {esc(e['actor']) or 'unknown'} at {e['changed_at']}"
            for e in profile.events
        ))
