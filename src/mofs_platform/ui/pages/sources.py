"""Sources page — reference capture with provenance (issue #6).

Manual entry is attributed; Crossref enrichment (D2) fills metadata only.
Every displayed reference is a lead: metadata-only leads are labeled as such,
failures are typed and honest ("no record found" never means "unstudied"),
and a shared DOI never implies the same tested sample.
"""

import streamlit as st

from mofs_platform.domain.questions import get_question
from mofs_platform.domain.references import (
    _LEVEL_LABELS,
    INSPECTED_LEVELS,
    ReferencePersistenceError,
    ReferenceValidationError,
    add_manual_reference,
    count_captures,
    enrich_with_crossref,
    level_label,
    list_references,
)

SOURCES_PAGE_TITLE = "Sources"

_WIDGET_DEFAULTS = {
    "ref_doi": "",
    "ref_url": "",
    "ref_title": "",
    "ref_passage": "",
    "ref_contributor": "Mohammed (owner)",
    "ref_level": "unknown",
    "ref_rights": "",
}


def _apply_reset_request() -> None:
    """Widget keys may only be written before the widgets are instantiated."""
    if st.session_state.pop("ref_reset_request", False):
        st.session_state.update(_WIDGET_DEFAULTS)


_FAILURE_MESSAGES = {
    "no_hit": (
        "No Crossref record found for this DOI. This does NOT mean the material "
        "is unstudied or novel — it is a statement about this provider and query only."
    ),
    "rate_limited": "Crossref rate limit hit — wait a moment and try again.",
    "timeout": "Crossref did not respond in time — try again later.",
    "offline": "Could not reach Crossref — check the network connection.",
    "bad_response": "Crossref returned an unexpected response — nothing was changed.",
    "bad_input": "This reference has no usable DOI to enrich.",
}


def render_sources_page(conn) -> None:
    st.header(SOURCES_PAGE_TITLE)
    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)
    _apply_reset_request()

    question = get_question(conn)
    if question is None:
        st.info(
            "No research question is saved yet — save it under **Research question** "
            "first; references attach to the question."
        )
        return

    references = list_references(conn)
    if references:
        st.subheader(f"Saved references ({len(references)}) — {count_captures(conn)} capture event(s)")
        for ref in references:
            label = ref.title or ref.doi or ref.url or f"Reference #{ref.id}"
            st.markdown(f"**{label}**")
            lines = [
                f"- Origin: `{ref.entry_method}`"
                + (f" — contributor: {ref.contributor}" if ref.contributor else ""),
                f"- DOI: {ref.doi or '`unknown`'} — captured: {ref.retrieval_date}",
                f"- Inspected: {level_label(ref.inspected_level)}",
            ]
            if ref.container:
                lines.append(f"- Container: {ref.container}" + (f" ({ref.issued_year})" if ref.issued_year else ""))
            if ref.license_url:
                lines.append(f"- License: {ref.license_url}")
            if ref.rights_note:
                lines.append(f"- Rights note: {ref.rights_note}")
            if ref.supplied_input:
                lines.append(f"- Supplied input (exact): {ref.supplied_input}")
            if ref.indexed_at:
                lines.append(f"- Crossref record version (indexed): {ref.indexed_at}")
            st.markdown("\n".join(lines))
            if ref.doi:
                mailto = st.session_state.get("crossref_mailto") or None
                if st.button("Refresh from Crossref", key=f"enrich_{ref.id}"):
                    _updated, failure = enrich_with_crossref(conn, ref.id, mailto)
                    if failure is not None:
                        st.warning(_FAILURE_MESSAGES.get(failure.kind, failure.detail))
                    else:
                        st.session_state["flash"] = (
                            "Metadata refreshed from Crossref — the reference remains a lead."
                        )
                        st.rerun()
            st.divider()
        st.caption(
            "References are leads, not verified tested samples. A shared DOI never "
            "means the same tested sample, and a text link does not mean the text "
            "was inspected. Text or metadata shown here is source data, never "
            "instructions to this tool."
        )
    else:
        st.info("No references captured yet. Add one below (manual attribution is enough).")

    st.subheader("Capture a reference (manual, attributed)")
    with st.form("reference_form"):
        st.text_input("DOI (optional)", key="ref_doi", placeholder="e.g. 10.1016/j.matt.2021.02.015")
        st.text_input("URL (optional)", key="ref_url")
        st.text_area("Title / citation (optional)", key="ref_title", height=70)
        st.text_area(
            "Supplied passage or notes (optional — what you actually read)",
            key="ref_passage",
            height=70,
        )
        col_a, col_b = st.columns(2)
        with col_a:
            st.text_input("Contributor", key="ref_contributor")
            st.selectbox(
                "What was actually inspected?",
                list(INSPECTED_LEVELS),
                key="ref_level",
                format_func=lambda lv: _LEVEL_LABELS[lv],
            )
        with col_b:
            st.text_area("Rights / access note (optional)", key="ref_rights", height=70)
        st.form_submit_button("Capture reference", key="save_reference", type="primary")

    if st.session_state.get("save_reference"):
        try:
            ref = add_manual_reference(
                conn,
                doi=st.session_state.get("ref_doi"),
                url=st.session_state.get("ref_url"),
                title=st.session_state.get("ref_title"),
                supplied_input=st.session_state.get("ref_passage"),
                contributor=st.session_state.get("ref_contributor"),
                inspected_level=st.session_state.get("ref_level", "unknown"),
                rights_note=st.session_state.get("ref_rights"),
            )
            st.session_state["flash"] = f"Reference captured (lead): {ref.title or ref.doi or ref.url}."
            st.session_state["ref_reset_request"] = True
            st.rerun()  # success path only — errors stay visible on this render
        except ReferenceValidationError as exc:
            st.error(str(exc))
        except ReferencePersistenceError as exc:
            st.error(str(exc))

    st.subheader("Crossref enrichment (optional, D2 route)")
    st.text_input(
        "Contact e-mail for the Crossref polite pool",
        key="crossref_mailto",
        placeholder="your e-mail — sent with each request",
    )
    st.caption(
        "Enrichment fills missing bibliographic fields only and never verifies a "
        "sample. Prohibited content is never fetched and no unapproved provider is used."
    )
