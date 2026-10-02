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


def _source_of(conn, sample_id) -> int:
    samples = {s.id: s.source_id for s in list_samples(conn)}
    return samples.get(sample_id, 0)
