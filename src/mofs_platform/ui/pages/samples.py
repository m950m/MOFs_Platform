"""Samples & identity page (issue #8) — records, observations, comparison.

Observations attach only to samples; comparison returns scoped relations with
reasons and merge permissions and never merges rows.
"""

import streamlit as st

from mofs_platform.domain.identity import (
    BASIS_KINDS,
    LINEAGE_KINDS,
    OBSERVATION_KINDS,
    IdentityPersistenceError,
    IdentityValidationError,
    compare_samples,
    list_observations,
    list_relations,
    list_samples,
    list_states,
    record_observation,
    record_sample,
)
from mofs_platform.domain.references import list_references
from mofs_platform.ui._widgets import esc

SAMPLES_PAGE_TITLE = "Samples & identity"


def render_samples_page(conn) -> None:
    st.header(SAMPLES_PAGE_TITLE)
    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)

    references = list_references(conn)
    if not references:
        st.info("No references captured yet — record one under **Sources** first; "
                "samples are recorded per source.")
        return
    ref_options = {ref.id: f"#{ref.id} — {ref.title or ref.doi}" for ref in references}
    samples = list_samples(conn)
    sample_options = {s.id: f"#{s.id} — {s.designation}" for s in samples}

    if samples:
        st.subheader(f"Recorded samples ({len(samples)})")
        for s in samples:
            lineage = ""
            if s.derived_from_sample_id:
                lineage = f" — {s.lineage_kind} of sample #{s.derived_from_sample_id}"
            st.markdown(
                f"- **#{s.id} {esc(s.designation)}** (`{s.basis}`){lineage}\n"
                f"  - parent framework: {esc(s.parent_framework_name) if s.parent_framework_name else '`unknown`'} — "
                f"linker: {esc(s.linker) if s.linker else '`unknown`'} — metal: {esc(s.metal_node) if s.metal_node else '`unknown`'}\n"
                f"  - additions: {esc(s.additions) if s.additions else '`unknown`'} — activation: "
                f"{esc(s.activation) if s.activation else '`unknown`'} — structure ref: {esc(s.structure_ref) if s.structure_ref else '`unknown`'}"
            )
            for ob in list_observations(conn, s.id):
                fields = ", ".join(
                    f"{k}={esc(v) if v else ''}" for k, v in {
                        "reaction": ob.reaction, "medium": ob.medium,
                        "ref": ob.reference_convention, "loading": ob.loading,
                        "duration": ob.duration, "protocol": ob.protocol,
                    }.items() if v
                ) or "context `unknown`"
                st.markdown(
                    f"  - 🔬 observation ({ob.observation_kind}): {esc(ob.value) if ob.value else '`unknown`'} "
                    f"{ob.unit or ''} — {fields} — loc: {(esc(ob.evidence_location) if ob.evidence_location else '`unknown`')}"
                )
            for stt in list_states(conn, s.id):
                st.markdown(
                    f"  - ⚙️ operating state ({stt.stage}): phase '{(esc(stt.phase_assignment) if stt.phase_assignment else '`unknown`')}' "
                    f"— {stt.epistemic_type.replace('_', ' ')} — loc: {(esc(stt.evidence_location) if stt.evidence_location else '`unknown`')}"
                )
        st.caption(
            "Observations belong to their sample only — they never appear on a "
            "parent framework or a hypothesized phase. No relation merges records."
        )
    else:
        st.info("No samples recorded yet. Record one below (per source).")

    st.subheader("Record a reported sample")
    # Targeting pickers stay OUTSIDE the forms: they must survive saves so
    # consecutive entries do not silently re-target another source or sample.
    st.selectbox("Source", list(ref_options), key="smp_source",
                 format_func=lambda k: ref_options[k])
    with st.form("sample_form", clear_on_submit=True):
        st.text_input("Designation (reported name)", key="smp_designation")
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Parent framework (as cited)", key="smp_parent")
            st.text_input("Linker", key="smp_linker")
            st.text_input("Metal node", key="smp_metal")
            st.text_input("Composition", key="smp_composition")
        with c2:
            st.text_input("Additions (e.g. nanoparticles)", key="smp_additions")
            st.text_input("Structure ref (CIF/model as cited)", key="smp_structure")
            st.text_input("Activation / pretreatment", key="smp_activation")
            st.selectbox("Basis", list(BASIS_KINDS), key="smp_basis")
        st.selectbox(
            "Lineage (only if documented)",
            ["— none —"] + list(LINEAGE_KINDS),
            key="smp_lineage_sel",
        )
        st.selectbox("Derived/composite from sample (if lineage chosen)",
                     ["— none —"] + list(sample_options),
                     key="smp_lineage_parent",
                     format_func=lambda k: sample_options[k] if isinstance(k, int) else k)
        st.form_submit_button("Record sample", key="save_sample", type="primary")

    if st.session_state.get("save_sample"):
        try:
            lineage_sel = st.session_state.get("smp_lineage_sel")
            parent_sel = st.session_state.get("smp_lineage_parent")
            s = record_sample(
                conn,
                source_id=st.session_state.get("smp_source"),
                designation=st.session_state.get("smp_designation"),
                parent_framework_name=st.session_state.get("smp_parent"),
                linker=st.session_state.get("smp_linker"),
                metal_node=st.session_state.get("smp_metal"),
                composition=st.session_state.get("smp_composition"),
                additions=st.session_state.get("smp_additions"),
                structure_ref=st.session_state.get("smp_structure"),
                activation=st.session_state.get("smp_activation"),
                lineage_kind=None if lineage_sel == "— none —" else lineage_sel,
                derived_from_sample_id=parent_sel if isinstance(parent_sel, int) else None,
                basis=st.session_state.get("smp_basis"),
            )
            st.session_state["flash"] = f"Sample recorded: #{s.id} {esc(s.designation)}."
            st.rerun()
        except IdentityValidationError as exc:
            st.error(str(exc))
        except IdentityPersistenceError as exc:
            st.error(str(exc))

    st.subheader("Record an observation (attaches to a sample only)")
    st.selectbox("Sample", list(sample_options), key="obs_sample",
                 format_func=lambda k: sample_options[k])
    st.selectbox("Source it was read from", list(ref_options), key="obs_source",
                 format_func=lambda k: ref_options[k])
    with st.form("observation_form", clear_on_submit=True):
        st.selectbox("Kind", list(OBSERVATION_KINDS), key="obs_kind")
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Value", key="obs_value")
            st.text_input("Unit", key="obs_unit")
            st.selectbox("Reaction", ["unknown", "HER", "OER", "other"], key="obs_reaction")
            st.text_input("Medium / electrolyte", key="obs_medium")
        with c2:
            st.text_input("Reference / conversion", key="obs_ref_conv")
            st.text_input("Loading", key="obs_loading")
            st.text_input("Duration", key="obs_duration")
            st.text_input("Protocol", key="obs_protocol")
        st.text_input("Evidence location", key="obs_location",
                      placeholder="e.g. fig. 3 — leave blank for unknown")
        st.form_submit_button("Record observation", key="save_observation", type="primary")

    if st.session_state.get("save_observation"):
        try:
            ob = record_observation(
                conn,
                sample_id=st.session_state.get("obs_sample"),
                source_id=st.session_state.get("obs_source"),
                observation_kind=st.session_state.get("obs_kind"),
                value=st.session_state.get("obs_value"),
                unit=st.session_state.get("obs_unit"),
                reaction=None if st.session_state.get("obs_reaction") == "unknown"
                else st.session_state.get("obs_reaction"),
                medium=st.session_state.get("obs_medium"),
                reference_convention=st.session_state.get("obs_ref_conv"),
                loading=st.session_state.get("obs_loading"),
                duration=st.session_state.get("obs_duration"),
                protocol=st.session_state.get("obs_protocol"),
                evidence_location=st.session_state.get("obs_location"),
            )
            st.session_state["flash"] = f"Observation #{ob.id} recorded on sample #{ob.sample_id}."
            st.rerun()
        except IdentityValidationError as exc:
            st.error(str(exc))
        except IdentityPersistenceError as exc:
            st.error(str(exc))

    if len(samples) >= 2:
        st.subheader("Compare two samples (identity contract)")
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Sample A", list(sample_options), key="cmp_a",
                         format_func=lambda k: sample_options[k])
        with c2:
            st.selectbox("Sample B", list(sample_options), key="cmp_b",
                         format_func=lambda k: sample_options[k])
        st.text_input("Evidence location for this comparison (optional)",
                      key="cmp_location",
                      placeholder="e.g. Methods \u00a72, fig. 1 \u2014 leave blank for unknown")
        if st.button("Compare", key="run_compare"):
            try:
                rels = compare_samples(conn, st.session_state.get("cmp_a"),
                                       st.session_state.get("cmp_b"),
                                       st.session_state.get("cmp_location"))
                for r in rels:
                    st.markdown(
                        f"- **{r['relation']}** at `{r['level']}` level — "
                        f"merge permission: `{r['merge_permission']}` — "
                        f"review: `{r['review_state']}` — "
                        f"evidence location: {r['evidence_location'] or '`unknown`'}"
                        f"\n\n  {esc(r['reason'])}"
                    )
            except IdentityValidationError as exc:
                st.error(str(exc))

    relations = list_relations(conn)
    if relations:
        st.subheader(f"Recorded relations ({len(relations)})")
        for r in relations:
            st.markdown(
                f"- #{r['left']} ↔ #{r['right']}: **{r['relation']}** (`{r['level']}`) — "
                f"merge: `{r['merge_permission']}` — review: `{r['review_state']}` — "
                f"evidence location: {r['evidence_location'] or '`unknown`'}"
            )
