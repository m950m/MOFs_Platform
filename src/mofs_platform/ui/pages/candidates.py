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

CANDIDATES_PAGE_TITLE = "Candidates"


def render_candidates_page(conn) -> None:
    st.header(CANDIDATES_PAGE_TITLE)
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
        return
    try:
        card = get_candidate_card(conn, requested)
    except CandidateValidationError as exc:
        st.error(str(exc))
        return

    st.markdown(f"### Candidate #{card.sample_id}: {card.designation}")
    st.markdown(
        f"- Basis: `{card.basis}` — material class (composition as entered): "
        f"{card.material_class or '`unknown`'}\n"
        f"- Parent relation: {card.parent_relation or '`unknown`'}\n"
        f"- Modifications/additions: {card.modifications or '`unknown`'}\n"
        f"- Source: {card.source_label} — inspected level: {card.source_inspected_level}\n"
        f"- Route outcomes for this source: "
        + (", ".join(f"`{r['outcome']}`" for r in card.route_outcomes) or "`unknown`")
    )
    st.markdown(f"**Why it appeared:** {card.retrieval_reason}")

    st.subheader("Observations (per tested sample)")
    for ob in card.observations:
        gaps = ", ".join(ob["gaps"]) if ob["gaps"] else "none"
        st.markdown(
            f"- `{ob['kind']}` {ob['value']} {ob['unit']} — sample #{ob['sample_id']} — "
            f"location: {ob['evidence_location']}\n"
            f"  - missing condition fields: {gaps} — these are displayed as gaps, "
            "not compared or ranked."
        )
    if not card.observations:
        st.markdown("- `unknown` — no observation recorded.")

    st.subheader("Operating-state interpretations")
    for stt in card.operating_states:
        st.markdown(f"- ({stt['stage']}) phase '{stt['phase']}' — {stt['epistemic']} "
                    f"— location: {stt['evidence_location']}")
    if not card.operating_states:
        st.markdown("- `unknown` — no operating state recorded.")

    st.subheader("Recorded assertions for this source (follow to evidence)")
    for a in card.assertions:
        conflict = (
            f" — **CONFLICT with #{a['conflicts_with']}**" if a["conflicts_with"] else ""
        )
        st.markdown(
            f"- Assertion #{a['id']} [{a['claim_type']}]: {a['claim_text']}\n"
            f"  - location: {a['location']} — {a['epistemic']} — "
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
