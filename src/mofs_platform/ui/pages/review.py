"""Review page (issue #11): correct and review assertions & relations with
full attribution (D4), durable rejection logging, and visible history.
Design-system rule 6: corrections display old → new with reason.
"""

import streamlit as st

from mofs_platform.domain.evidence import list_assertions
from mofs_platform.domain.identity import list_relations
from mofs_platform.domain.review import (
    ReviewPersistenceError,
    ReviewValidationError,
    correct_assertion,
    correct_identity_relation,
    list_review_events,
    resolve_conflict,
    review_assertion,
    review_identity_relation,
)
from mofs_platform.ui._widgets import esc

REVIEW_PAGE_TITLE = "Review"

_OWNER_DEFAULT_REVIEWER = "Mohammed (owner)"


def render_review_page(conn) -> None:
    st.header(REVIEW_PAGE_TITLE)
    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)

    assertions = list_assertions(conn)
    relations = list_relations(conn)

    if not assertions and not relations:
        st.info("Nothing to review yet — record assertions under **Evidence** and "
                "samples/relations under **Samples & identity**.")
        return

    st.subheader("Correct an assertion")
    asm_options = {
        a.id: f"#{a.id} [{a.claim_type}] {a.claim_text[:60]}" for a in assertions
    }
    if asm_options:
        # Target pickers stay OUTSIDE the forms so the corrected/reviewed
        # target survives an action (correct now, review next — same target).
        st.selectbox("Assertion", list(asm_options), key="rev_asm",
                     format_func=lambda k: asm_options[k])
        with st.form("correct_assertion_form", clear_on_submit=True):
            st.text_area("Corrected claim text", key="rev_claim_text", height=70)
            st.text_input("Corrected evidence location", key="rev_location")
            st.text_input("Editor (who is correcting)",
                          value=_OWNER_DEFAULT_REVIEWER, key="rev_editor")
            st.text_area("Reason for the correction (required)", key="rev_reason", height=60)
            st.form_submit_button("Save correction", key="save_correction", type="primary")
        if st.session_state.get("save_correction"):
            try:
                result = correct_assertion(
                    conn, assertion_id=st.session_state.get("rev_asm"),
                    new_claim_text=st.session_state.get("rev_claim_text"),
                    new_evidence_location=st.session_state.get("rev_location"),
                    editor=st.session_state.get("rev_editor"),
                    reason=st.session_state.get("rev_reason"),
                )
                note = (" The reviewed approval was stripped — re-review required."
                        if result["awaiting_re_review"] else "")
                st.session_state["flash"] = (
                    f"Assertion #{result['id']} corrected (old → new kept in history).{note}"
                )
                st.rerun()
            except (ReviewValidationError, ReviewPersistenceError) as exc:
                st.error(str(exc))

    st.subheader("Review an assertion (D4 threshold)")
    if asm_options:
        st.selectbox("Assertion", list(asm_options), key="rev_review_asm",
                     format_func=lambda k: asm_options[k])
        with st.form("review_assertion_form", clear_on_submit=True):
            st.text_input("Reviewer", value=_OWNER_DEFAULT_REVIEWER, key="rev_reviewer")
            st.text_input("Supporting source location (exact)", key="rev_support",
                          placeholder="e.g. Methods §2 — you inspected this exact location")
            st.text_area("Reason: how it meets the D4 threshold (required)",
                         key="rev_review_reason", height=60)
            st.form_submit_button("Mark reviewed", key="mark_reviewed", type="primary")
        if st.session_state.get("mark_reviewed"):
            try:
                result = review_assertion(
                    conn, assertion_id=st.session_state.get("rev_review_asm"),
                    reviewer=st.session_state.get("rev_reviewer"),
                    supporting_location=st.session_state.get("rev_support"),
                    reason=st.session_state.get("rev_review_reason"),
                )
                st.session_state["flash"] = (
                    f"Assertion #{result['id']} marked `reviewed` by "
                    f"{result['reviewer']} (D4 recorded)."
                )
                st.rerun()
            except (ReviewValidationError, ReviewPersistenceError) as exc:
                st.error(str(exc))

    conflicted = [a for a in assertions if a.review_state == "conflicted"]
    if conflicted:
        st.subheader("Resolve a recorded conflict (explicit human decision)")
        pair_options = {
            a.id: f"#{a.id} {a.claim_text[:60]} ↔ pair #{a.conflicts_with}"
            for a in conflicted
        }
        st.selectbox("Conflicted assertion", list(pair_options), key="res_asm",
                     format_func=lambda k: pair_options[k])
        with st.form("resolve_form", clear_on_submit=True):
            st.text_input("Resolver", value=_OWNER_DEFAULT_REVIEWER, key="res_resolver")
            st.text_area(
                "Resolution reason (required) — e.g. the pair was a double entry, "
                "or one side was corrected and no longer conflicts",
                key="res_reason", height=60,
            )
            st.form_submit_button("Resolve conflict", key="resolve_conflict", type="primary")
        if st.session_state.get("resolve_conflict"):
            try:
                result = resolve_conflict(
                    conn, assertion_id=st.session_state.get("res_asm"),
                    resolver=st.session_state.get("res_resolver"),
                    reason=st.session_state.get("res_reason"),
                )
                st.session_state["flash"] = (
                    f"Conflict resolved: assertions {result['resolved']} returned to "
                    "`needs_verification` (re-review required)."
                )
                st.rerun()
            except (ReviewValidationError, ReviewPersistenceError) as exc:
                st.error(str(exc))

    st.subheader("Correct / review an identity relation")
    if relations:
        rel_options = {
            r["id"]: f"#{r['left']} ↔ #{r['right']}: {r['relation']} ({r['level']})"
            for r in relations
        }
        st.selectbox("Relation", list(rel_options), key="rev_rel",
                     format_func=lambda k: rel_options[k])
        with st.form("relation_form", clear_on_submit=True):
            st.text_input("Corrected evidence location (optional)", key="rev_rel_location")
            st.text_input("Editor / reviewer",
                          value=_OWNER_DEFAULT_REVIEWER, key="rev_rel_editor")
            st.text_area("Reason (required)", key="rev_rel_reason", height=60)
            st.radio("Action", ["Save correction", "Mark reviewed (D4)"],
                     key="rev_rel_action", horizontal=True)
            st.form_submit_button("Apply", key="apply_relation", type="primary")
        if st.session_state.get("apply_relation"):
            try:
                if st.session_state.get("rev_rel_action") == "Save correction":
                    result = correct_identity_relation(
                        conn, relation_id=st.session_state.get("rev_rel"),
                        new_evidence_location=st.session_state.get("rev_rel_location"),
                        editor=st.session_state.get("rev_rel_editor"),
                        reason=st.session_state.get("rev_rel_reason"),
                    )
                    st.session_state["flash"] = (
                        f"Relation #{result['id']} corrected"
                        + (" — re-review required." if result["awaiting_re_review"] else ".")
                    )
                else:
                    result = review_identity_relation(
                        conn, relation_id=st.session_state.get("rev_rel"),
                        reviewer=st.session_state.get("rev_rel_editor"),
                        supporting_location=st.session_state.get("rev_rel_location"),
                        reason=st.session_state.get("rev_rel_reason"),
                    )
                    st.session_state["flash"] = (
                        f"Relation #{result['id']} marked `reviewed` (D4 recorded)."
                    )
                st.rerun()
            except (ReviewValidationError, ReviewPersistenceError) as exc:
                st.error(str(exc))

    st.subheader("Review & correction history")
    events = list_review_events(conn)
    if events:
        for e in events:
            st.markdown(
                f"- {e.created_at} — **{e.action}** {e.entity_type} #{e.entity_id}"
                + (f" — by {esc(e.reviewer)}" if e.reviewer else "")
                + (f" — reason: {esc(e.reason)}" if e.reason else "")
                + (f" — location: {esc(e.supporting_location)}" if e.supporting_location else "")
            )
        st.caption(
            "Originals live in each event's previous snapshot; reviewing one claim "
            "never reviews the others, and no whole material is ever labeled reviewed."
        )
    else:
        st.info("No review or correction events yet.")
