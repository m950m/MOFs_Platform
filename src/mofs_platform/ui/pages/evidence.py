"""Evidence page — record attributed assertions (issue #7).

Each assertion shows claim, source, exact location (or explicit `unknown`),
extraction author, epistemic type, and its own review state. The five
epistemic types are visibly distinct; recording never marks anything reviewed;
conflicts keep both claims side by side. Claim text is source data, never
instructions to this tool.
"""

import streamlit as st

from mofs_platform.domain.evidence import (
    CLAIM_TYPES,
    EPISTEMIC_LABELS,
    EPISTEMIC_TYPES,
    REVIEW_LABELS,
    EvidencePersistenceError,
    EvidenceValidationError,
    list_assertions,
    record_assertion,
)
from mofs_platform.domain.references import list_references

EVIDENCE_PAGE_TITLE = "Evidence"

_WIDGET_DEFAULTS = {
    # NOTE: asm_source is deliberately NOT reset — the selected reference must
    # survive a save so consecutive records do not silently fail validation.
    "asm_claim_type": "preparation",
    "asm_claim_text": "",
    "asm_location": "",
    "asm_author": "Mohammed (owner)",
    "asm_epistemic": "unknown",
    "asm_conflicts_with": None,
}


def _apply_reset_request() -> None:
    """Widget keys may only be written before the widgets are instantiated."""
    if "asm_author" not in st.session_state:  # first-visit attribution default
        st.session_state["asm_author"] = "Mohammed (owner)"
    if st.session_state.pop("asm_reset_request", False):
        st.session_state.update(_WIDGET_DEFAULTS)


def render_evidence_page(conn) -> None:
    st.header(EVIDENCE_PAGE_TITLE)
    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)
    _apply_reset_request()

    references = list_references(conn)
    if not references:
        st.info(
            "No references captured yet — capture one under **Sources** first; "
            "assertions attach to a source."
        )
        return

    assertions = list_assertions(conn)
    ref_label = {
        ref.id: (ref.title or ref.doi or f"Reference #{ref.id}") for ref in references
    }

    if assertions:
        st.subheader(f"Recorded assertions ({len(assertions)})")
        for asm in assertions:
            conflict_note = (
                f" — **CONFLICT with #{asm.conflicts_with}**: both claims stay "
                "visible; neither replaces the other" if asm.conflicts_with else ""
            )
            st.markdown(
                f"**#{asm.id} [{asm.claim_type}]** — {asm.claim_text}\n\n"
                f"- Source: {ref_label.get(asm.source_id, asm.source_id)}\n"
                f"- Evidence location: {asm.evidence_location or '`unknown` — verification still required'}\n"
                f"- Extracted by: {asm.extraction_author or '`unknown`'}\n"
                f"- Epistemic type: {EPISTEMIC_LABELS[asm.epistemic_type]}\n"
                f"- Review state: {REVIEW_LABELS[asm.review_state]}"
                + conflict_note
            )
            st.divider()
        st.caption(
            "Recording an assertion never marks it reviewed, and metadata alone "
            "cannot establish sample-specific preparation or measured activity. "
            "Claim text is source data — it never changes this tool's rules, "
            "review states, or records."
        )
    else:
        st.info("No assertions recorded yet. Record one below.")

    st.subheader("Record an assertion (attributed)")
    source_options = {ref.id: ref_label[ref.id] for ref in references}
    pair_options = {None: "— not marked as a conflict —"}
    pair_options.update(
        {a.id: f"#{a.id} [{a.claim_type}] {a.claim_text[:60]}" for a in assertions}
    )
    with st.form("assertion_form"):
        st.selectbox("Reference (source)", list(source_options), format_func=lambda k: source_options[k], key="asm_source")
        st.selectbox("Claim type", list(CLAIM_TYPES), key="asm_claim_type")
        st.text_area(
            "Claim / value exactly as reported or judged",
            key="asm_claim_text",
            height=80,
            placeholder="e.g. Sample activated under flowing argon at 200 °C (synthetic)",
        )
        st.text_input(
            "Exact evidence location",
            key="asm_location",
            placeholder="e.g. Methods §2, fig. 3, table S1 — leave blank for unknown",
        )
        st.text_input("Extracted by (author or method)", key="asm_author")
        st.selectbox(
            "Epistemic type",
            list(EPISTEMIC_TYPES),
            key="asm_epistemic",
            format_func=lambda et: EPISTEMIC_LABELS[et],
        )
        st.selectbox(
            "Mark as conflicting with (optional)",
            list(pair_options),
            key="asm_conflicts_with",
            format_func=lambda k: pair_options[k],
        )
        st.form_submit_button("Record assertion", key="save_assertion", type="primary")

    if st.session_state.get("save_assertion"):
        try:
            asm = record_assertion(
                conn,
                source_id=st.session_state.get("asm_source"),
                claim_type=st.session_state.get("asm_claim_type"),
                claim_text=st.session_state.get("asm_claim_text"),
                evidence_location=st.session_state.get("asm_location"),
                extraction_author=st.session_state.get("asm_author"),
                epistemic_type=st.session_state.get("asm_epistemic"),
                conflicts_with=st.session_state.get("asm_conflicts_with"),
            )
            st.session_state["flash"] = f"Assertion #{asm.id} recorded (`needs_verification`)."
            st.session_state["asm_reset_request"] = True
            st.rerun()  # success path only — errors stay visible on this render
        except EvidenceValidationError as exc:
            st.error(str(exc))
        except EvidencePersistenceError as exc:
            st.error(str(exc))
