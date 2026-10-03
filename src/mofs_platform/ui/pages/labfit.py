"""Lab-fit page (issue #12): explain whether a sample's sourced requirements
fit the confirmed laboratory profile. Outcomes: possible with current
capabilities / requires future capabilities / unknown — with reasons, basis,
and outdated marking. No success promises, no historical restrictions.
"""

import streamlit as st

from mofs_platform.domain.identity import list_samples
from mofs_platform.domain.labfit import (
    LabFitValidationError,
    assess_fit,
    latest_assessment,
)
from mofs_platform.domain.labprofile import list_capabilities
from mofs_platform.domain.numbers import (
    CAVEAT,
    NumberValidationError,
    add_number,
    build_comparison,
    list_numbers,
)
from mofs_platform.ui._widgets import esc

LABFIT_PAGE_TITLE = "Lab fit"

_ASSESSMENT_LABELS = {
    "possible_with_current_capabilities": "**possible with current capabilities**",
    "requires_future_capabilities": "**requires future capabilities**",
    "unknown": "**`unknown`**",
}


def render_labfit_page(conn) -> None:
    st.header(LABFIT_PAGE_TITLE)
    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)

    samples = list_samples(conn)
    capabilities = list_capabilities(conn)
    if not samples:
        st.info("No samples recorded yet — record one under **Samples & identity**.")
        return
    st.caption(
        f"Assessments run against the confirmed laboratory profile "
        f"({len(capabilities)} entries) and the sample's sourced requirement "
        "assertions. No synthesis success, catalytic performance, or universal "
        "suitability is ever claimed, and no historical restriction is applied "
        "unless confirmed in the current profile."
    )

    sample_options = {s.id: f"#{s.id} — {s.designation}" for s in samples}
    st.selectbox("Candidate / tested sample", list(sample_options), key="fit_sample",
                 format_func=lambda k: sample_options[k])

    if st.button("Assess fit", key="run_fit", type="primary"):
        try:
            a = assess_fit(conn, st.session_state.get("fit_sample"),
                           _source_of(conn, st.session_state.get("fit_sample")))
            st.session_state["flash"] = (
                f"Assessment #{a.id} recorded: {a.assessment}."
            )
            st.rerun()
        except LabFitValidationError as exc:
            st.error(str(exc))
            return

    latest = latest_assessment(conn, st.session_state.get("fit_sample"))
    if latest is None:
        st.info("No assessment recorded for this sample yet — press **Assess fit**.")
        return

    if latest.outdated:
        st.warning(
            "⚠️ **Outdated assessment** — the question, profile, or requirement "
            "assertions changed after this assessment was recorded. The old "
            "result cannot appear current; re-run **Assess fit** from the "
            "current recorded basis."
        )
    st.markdown(f"Assessment #{latest.id} (recorded {latest.created_at}): "
                f"{_ASSESSMENT_LABELS[latest.assessment]}")
    for r in latest.reasons:
        st.markdown(
            f"- [{r.get('kind', 'summary')}] {r.get('requirement', '')}"
            f"{r.get('match', '') + ' — ' if r.get('match') else ''}"
            f"effect: **{r['effect']}**\n  - {r['reason']}"
            + (f" — location: {r['evidence_location']}" if r.get("evidence_location") else "")
        )

    st.divider()
    _render_number_streams(conn)


def _render_number_streams(conn) -> None:
    """Number streams (issue #17, D11): laboratory and industry_reference
    numbers are SEPARATE streams — rows are never merged into one verdict.
    Comparison is display-only with the caveat rendered; the table starts
    empty (nothing enters from memory — the initial reference set is the
    owner's decision, entered with provenance)."""
    st.subheader("Number streams (D11: laboratory vs industry — separate, never merged)")
    st.caption(
        "The reference table starts EMPTY: the initial industry reference set "
        "is the owner's decision (e.g. DOE Hydrogen Program electrolyzer "
        "targets) — every row must carry its source and year. Nothing is "
        "seeded from memory."
    )
    with st.form("number_form", clear_on_submit=False):
        st.selectbox("Stream", ["laboratory", "industry_reference"], key="num_stream")
        st.text_input("Label (what this number is)", key="num_label",
                      placeholder="e.g. overpotential at 10 mA/cm2 / DOE 2026 target")
        st.text_input("Value (as reported)", key="num_value")
        st.text_input("Unit (as reported)", key="num_unit")
        st.selectbox("Reaction", ["HER", "OER", "other"], key="num_reaction")
        st.text_area("Conditions note (scale, electrolyte, temperature — differences "
                     "are displayed, never hidden)", key="num_conditions", height=50)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.text_input("Source reference id (optional)", key="num_src_id")
        with c2:
            st.text_input("Source citation (required if no id)", key="num_citation")
        with c3:
            st.text_input("Source year (optional)", key="num_year")
        st.text_input("Contributor", value="Mohammed (owner)", key="num_by")
        st.form_submit_button("Record number", key="num_save", type="primary")
    if st.session_state.get("num_save"):
        try:
            n = add_number(
                conn, stream=st.session_state.get("num_stream"),
                label=st.session_state.get("num_label"),
                value=st.session_state.get("num_value"),
                reaction=st.session_state.get("num_reaction"),
                unit=st.session_state.get("num_unit"),
                conditions_note=st.session_state.get("num_conditions"),
                source_id=st.session_state.get("num_src_id") or None,
                source_citation=st.session_state.get("num_citation"),
                source_year=st.session_state.get("num_year"),
                contributor=st.session_state.get("num_by"),
            )
            st.session_state["flash"] = (
                f"Number recorded in the `{n.stream}` stream (as reported, "
                "with provenance)."
            )
            st.rerun()
        except NumberValidationError as exc:
            st.error(str(exc))

    comparison = build_comparison(conn)
    lab_rows = list_numbers(conn, "laboratory")
    industry_rows = list_numbers(conn, "industry_reference")
    if not lab_rows and not industry_rows and not comparison["comparisons"]:
        st.info(
            "Both streams are empty. Record laboratory numbers from your "
            "measurements and industry reference numbers from the source you "
            "approve — the comparison view appears when either side exists."
        )
        return
    if comparison["comparisons"]:
        st.markdown("**Comparison view (display only — see the caveat):**")
        for comp in comparison["comparisons"]:
            lab = comp["laboratory"]
            st.markdown(
                f"**Reaction: {comp['reaction']}** — laboratory: sample "
                f"{esc(lab['sample'])}: {esc(lab['value'])} {(esc(lab['unit']) if lab['unit'] else '')} "
                f"({(esc(lab['protocol']) if lab['protocol'] else 'protocol `unknown`')})"
            )
            st.markdown(
                f"- Laboratory conditions: medium {esc(lab['medium']) or '`unknown`'} "
                f"— reference {(esc(lab['reference_convention']) if lab['reference_convention'] else '`unknown`')} — "
                f"loading {(esc(lab['loading']) if lab['loading'] else '`unknown`')} — duration "
                f"{(esc(lab['duration']) if lab['duration'] else '`unknown`')} — loc {(esc(lab['location']) if lab['location'] else '`unknown`')}"
            )
            if comp["industry_reference"]:
                for ref in comp["industry_reference"]:
                    st.markdown(
                        f"- Industry reference: {esc(ref['label'])} — "
                        f"{esc(ref['value'])} {(esc(ref['unit']) if ref['unit'] else '')} — "
                        f"conditions: {(esc(ref['conditions_note']) if ref['conditions_note'] else '`unknown`')} — "
                        f"source: {(esc(ref['source_citation']) if ref['source_citation'] else '`unknown`')} "
                        f"({(esc(ref['source_year']) if ref['source_year'] else 'year `unknown`')})"
                    )
            else:
                st.markdown(
                    "- Industry reference: `unknown` — no reference row for "
                    "this reaction yet (nothing inferred from similar values)."
                )
    else:
        st.info(
            "No recorded laboratory observations with HER/OER values yet — "
            "record samples and observations under **Samples & identity**; "
            "the comparison view pairs them with the reference stream."
        )
    if lab_rows:
        st.markdown(f"**Laboratory stream ({len(lab_rows)} rows):**")
        for n in lab_rows:
            st.markdown(
                f"- {esc(n.label)}: {esc(n.value)} {(esc(n.unit) if n.unit else '')} "
                f"({n.reaction}) — {(esc(n.conditions_note) if n.conditions_note else 'conditions `unknown`')} "
                f"— by {esc(n.contributor)}"
            )
    if industry_rows:
        st.markdown(f"**Industry reference stream ({len(industry_rows)} rows):**")
        for n in industry_rows:
            st.markdown(
                f"- {esc(n.label)}: {esc(n.value)} {(esc(n.unit) if n.unit else '')} "
                f"({n.reaction}) — {(esc(n.conditions_note) if n.conditions_note else 'conditions `unknown`')} "
                f"— source: {(esc(n.source_citation) if n.source_citation else 'see reference')} "
                f"({(esc(n.source_year) if n.source_year else 'year `unknown`')}) — by {esc(n.contributor)}"
            )
    st.warning(CAVEAT)


def _source_of(conn, sample_id) -> int:
    samples = {s.id: s.source_id for s in list_samples(conn)}
    return samples.get(sample_id, 0)
