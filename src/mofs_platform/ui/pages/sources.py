"""Sources page — reference capture with provenance (issue #6).

Manual entry is attributed; Crossref enrichment (D2) fills metadata only.
Every displayed reference is a lead: metadata-only leads are labeled as such,
failures are typed and honest ("no record found" never means "unstudied"),
and a shared DOI never implies the same tested sample.
"""

import json
from pathlib import Path

import streamlit as st

from mofs_platform.domain.attempts import list_attempts
from mofs_platform.domain.packages import (
    FORMAT as PACKAGE_FORMAT,
)
from mofs_platform.domain.packages import (
    PackagePersistenceError,
    PackageValidationError,
    export_package,
    import_package,
)
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
    source_dependency_warning,
)
from mofs_platform.domain.search import (
    NEXT_STEPS as SEARCH_NEXT_STEPS,
)
from mofs_platform.domain.search import (
    SearchValidationError,
    capture_hit,
    derive_query,
    dismiss_hit,
    list_hits,
    list_runs,
    run_active_search,
)
from mofs_platform.domain.structures import (
    PROVIDERS as STRUCTURE_PROVIDERS,
)
from mofs_platform.domain.structures import (
    StructureValidationError,
    capture_structure_reference,
    count_structures,
    import_structure_csv,
    search_structures,
)
from mofs_platform.ui._widgets import esc

SOURCES_PAGE_TITLE = "Sources"

_OWNER_DEFAULT_CONTRIBUTOR = "Mohammed (owner)"


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
            st.markdown(f"**{esc(label)}**")
            lines = [
                f"- Origin: `{ref.entry_method}`"
                + (f" — contributor: {esc(ref.contributor)}" if ref.contributor else ""),
                f"- DOI: {esc(ref.doi) if ref.doi else '`unknown`'} — captured: {ref.retrieval_date}",
                f"- Inspected: {level_label(ref.inspected_level)}",
            ]
            if ref.container:
                lines.append(f"- Container: {esc(ref.container) if ref.container else '`unknown`'}" + (f" ({ref.issued_year})" if ref.issued_year else ""))
            if ref.license_url:
                lines.append(f"- License: {esc(ref.license_url)}")
            if ref.rights_note:
                lines.append(f"- Rights note: {esc(ref.rights_note)}")
            if ref.supplied_input:
                lines.append(f"- Supplied input (exact): {esc(ref.supplied_input)}")
            if ref.indexed_at:
                lines.append(f"- Crossref record version (indexed): {ref.indexed_at}")
            st.markdown("\n".join(lines))
            if ref.doi:
                mailto = st.session_state.get("crossref_mailto") or None
                if st.button("Refresh from Crossref", key=f"enrich_{ref.id}"):
                    _updated, failure = enrich_with_crossref(conn, ref.id, mailto)
                    if failure is not None:
                        from mofs_platform.domain.attempts import NEXT_STEPS
                        st.warning(
                            _FAILURE_MESSAGES.get(failure.kind, failure.detail)
                            + " Next step: " + NEXT_STEPS.get(failure.kind, "none.")
                        )
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
    # clear_on_submit resets the fields natively; manually resetting form-widget
    # session_state keys after a submit crashes the real browser (guided
    # session 001), even though AppTest does not reproduce it.
    with st.form("reference_form", clear_on_submit=True):
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
            st.text_input(
                "Contributor", value=_OWNER_DEFAULT_CONTRIBUTOR, key="ref_contributor"
            )
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
        existing_context = None
        if _opt := st.session_state.get("ref_doi"):
            existing_context = _opt.strip() or None
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
            warning = source_dependency_warning(conn, ref.id) if existing_context else None
            st.session_state["flash"] = (
                f"Reference captured (lead): {esc(ref.title or ref.doi or ref.url)}."
                + (f" — {warning}" if warning else "")
            )
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
    attempts = list_attempts(conn)
    if attempts:
        st.subheader(f"Route attempts ({len(attempts)}) — Crossref (D2)")
        for at_row in attempts:
            icon = "✅" if at_row.outcome == "success" else "⚠️"
            st.markdown(
                f"- {icon} `{at_row.outcome}` — {at_row.target} — {at_row.created_at}"
                + (f"\n  Next step: {esc(at_row.next_step)}" if at_row.next_step else "")
                + (f"\n  Detail: {esc(at_row.note)}" if at_row.note else "")
            )
    st.caption(
        "Manual capture is an offline route: network failure kinds cannot apply "
        "to it. No automatic retry exists — every retry is a manual action. "
        "Failed attempts stay failed in this log even when a later attempt succeeds."
    )
    st.caption(
        "Enrichment fills missing bibliographic fields only and never verifies a "
        "sample. Prohibited content is never fetched and no unapproved provider is used."
    )

    st.subheader("Active search (D9: Crossref + OpenAlex)")
    if question is None:  # pragma: no cover - early return above already guards
        st.info("Save the research question first — queries derive from it.")
    else:
        derived = derive_query(question.wording)
        st.caption(
            "Query derivation is transparent: the default query is the saved "
            "question's wording, verbatim. You can edit it below — the exact "
            "text sent is what gets recorded. Hit order is provider retrieval "
            "order, never a ranking. Every hit is a lead "
            "(`needs_verification`); HER and OER evidence streams stay "
            "separate per hit and metadata never claims measured performance."
        )
        query_text = st.text_area(
            "Search query (the exact text that will be sent)",
            value=derived["query"],
            key="search_query",
            height=80,
        )
        scope = (
            "owner_question_verbatim"
            if query_text.strip() == question.wording.strip()
            else "owner_edited"
        )
        col_p, col_r = st.columns([1, 3])
        with col_p:
            provider = st.radio("Provider", ["crossref", "openalex"], key="search_provider",
                                horizontal=True)
        with col_r:
            st.caption(
                "Runs hit the live polite-pool APIs (D9). No automatic retry "
                "exists; failed runs stay failed in the log."
            )
        if st.button("Run search", key="run_search", type="primary"):
            try:
                run, failure = run_active_search(
                    conn, provider, query_text, scope,
                    st.session_state.get("crossref_mailto") or None,
                )
                if failure is not None:
                    st.warning(
                        f"`{failure.kind}` — {failure.detail} Next step: "
                        f"{SEARCH_NEXT_STEPS[failure.kind]}"
                    )
                else:
                    st.session_state["flash"] = (
                        f"Search run #{run.id} recorded: {run.result_count} hit(s) "
                        f"({provider}) — every hit is a lead."
                    )
                    st.rerun()
            except SearchValidationError as exc:
                st.error(str(exc))

        runs = list_runs(conn)
        if runs:
            st.subheader(f"Search runs ({len(runs)})")
            latest = runs[0]
            for run in runs:
                icon = "✅" if run.outcome == "success" else "⚠️"
                st.markdown(
                    f"- {icon} run #{run.id} `{run.provider}` `{run.outcome}` — "
                    f"{run.result_count} hit(s) — scope: `{run.scope}` — {run.created_at}"
                    + (f"\n\n  Query: {esc(run.query_text)}" if run.outcome == "success" else "")
                    + (f"\n  Next step: {run.next_step}" if run.next_step else "")
                )
            hits = list_hits(conn, latest.id)
            if latest.outcome == "success" and hits:
                st.subheader(f"Hits from run #{latest.id} — leads, not verified candidates")
                for hit in hits:
                    her = "yes" if hit.her_token else "no"
                    oer = "yes" if hit.oer_token else "no"
                    label = hit.title or hit.doi or f"Hit #{hit.id}"
                    lines = [
                        f"**{esc(label)}**" + (f" ({hit.issued_year})" if hit.issued_year else ""),
                        (
                            f"- DOI: {(esc(hit.doi) if hit.doi else '`unknown`')} — container: "
                            f"{(esc(hit.container) if hit.container else '`unknown`')} — provider: `{hit.provider}`"
                        ),
                        (
                            f"- HER token in title: {her} — OER token in title: {oer} — "
                            "the two evidence streams stay separate until real evidence "
                            "is captured (metadata alone never verifies either)."
                        ),
                        f"- Status: `{hit.status}`",
                    ]
                    if hit.criteria:
                        for phrase, matched in hit.criteria.items():
                            if matched is None:
                                lines.append(
                                    f"- Criterion from your question — "
                                    f"'{esc(phrase)}': `unknown` (no title in "
                                    "the provider metadata)"
                                )
                            else:
                                lines.append(
                                    f"- Criterion from your question — "
                                    f"'{esc(phrase)}': "
                                    + ("**matched in title**" if matched
                                       else "not in title (a metadata miss is "
                                       "not a failure)")
                                )
                    else:
                        lines.append(
                            "- Per-criterion check: `unknown` — the run predates "
                            "the per-criterion check or the saved question has no "
                            "hard requirements / preferences recorded."
                        )
                    st.markdown("\n".join(lines))
                    c_cap, c_dis = st.columns(2)
                    with c_cap:
                        if hit.status == "needs_verification" and st.button(
                            "Capture as reference", key=f"capture_hit_{hit.id}"
                        ):
                            try:
                                _hit, source_id = capture_hit(
                                    conn, hit.id,
                                    st.session_state.get("ref_contributor")
                                    or "Mohammed (owner)",
                                )
                                st.session_state["flash"] = (
                                    f"Hit #{hit.id} captured as reference #{source_id} "
                                    "with search provenance — a lead like any other."
                                )
                                st.rerun()
                            except SearchValidationError as exc:
                                st.error(str(exc))
                    with c_dis:
                        if hit.status == "captured":
                            st.caption(
                                f"Captured as reference #{hit.captured_source_id} — "
                                "dismissal is not available."
                            )
                        else:
                            with st.form(f"dismiss_hit_{hit.id}"):
                                st.text_input("Dismissed by", key=f"dis_by_{hit.id}")
                                st.text_input(
                                    "Dismissal reason (required)",
                                    key=f"dis_reason_{hit.id}",
                                )
                                if st.form_submit_button(
                                    "Dismiss lead", key=f"dis_btn_{hit.id}"
                                ):
                                    try:
                                        dismiss_hit(
                                            conn, hit.id,
                                            st.session_state.get(f"dis_by_{hit.id}"),
                                            st.session_state.get(f"dis_reason_{hit.id}"),
                                        )
                                        st.session_state["flash"] = (
                                            f"Hit #{hit.id} dismissed with a recorded "
                                            "reason — it stays auditable in the log."
                                        )
                                        st.rerun()
                                    except SearchValidationError as exc:
                                        st.error(str(exc))
                    st.divider()
        else:
            st.info("No search runs yet — run one above.")
        st.caption(
            "`no_hit` never means the material is unstudied. A metadata hit never "
            "claims experimental preparation or measured performance. Prohibited "
            "content is never fetched and no provider beyond D9 is used."
        )
        st.caption(
            "Search scope: one polite page per run (8 hits, a single request — "
            "auto-paging is deliberately out of scope; run again with edited "
            "terms to widen). This respects provider rate limits (issue #16 "
            "failure taxonomy)."
        )

    st.subheader("Evidence packages (offline collaboration — issue #19)")
    _render_packages_section(conn)

    st.subheader("Structure lookup (D12: CoRE MOF 2019 first)")
    _render_structure_section(conn)


def _render_structure_section(conn) -> None:
    """Structure lookup (issue #24, D12 slice 1): a provider-attributed
    index imported from files the researcher supplies — no fetch route.
    Capturing a structure's DOI goes through the attributed reference flow."""
    total = count_structures(conn)
    if total:
        st.caption(
            f"Index: {total} structure record(s) across providers: "
            + ", ".join(
                f"{p} ({count_structures(conn, p)})"
                for p in STRUCTURE_PROVIDERS
                if count_structures(conn, p)
            )
        )
    else:
        st.caption(
            "The index is empty. Download the CoRE MOF 2019 deposit from "
            "https://zenodo.org/records/4086443 , export its summary "
            "spreadsheet as CSV, and import it below. Expected CSV columns "
            "(flexible matching, first hit wins): a name column (name / "
            "MOF Name / title / compound), DOI, Formula, an id column "
            "(Refcode / MOFid / id), an optional file column; any other "
            "columns are preserved as extra data. The tool never downloads "
            "anything itself — the file comes from you, and the import is "
            "attributed."
        )
    provider = st.selectbox(
        "Provider of the CSV", list(STRUCTURE_PROVIDERS), key="struct_provider"
    )
    csv_path = st.text_input(
        "Path to the CSV file (local — no upload needed)",
        key="struct_csv_path",
        placeholder="e.g. data/imports/core_mof_2019.csv",
    )
    if st.button("Import CSV into the index", key="struct_import"):
        try:
            report = import_structure_csv(
                conn, csv_path, provider,
                st.session_state.get("ref_contributor") or "Mohammed (owner)",
            )
            st.session_state["flash"] = (
                f"Imported [{provider}]: {report['inserted']} new, "
                f"{report['updated']} updated — attributed to "
                f"{report['contributor']}."
            )
            st.rerun()
        except StructureValidationError as exc:
            st.error(str(exc))

    query = st.text_input(
        "Search the structure index (name / formula / external id)",
        key="struct_query",
        placeholder="e.g. Zn, CoCoZn, IRMOF — at least 2 characters",
    )
    if st.button("Search structures", key="struct_search"):
        try:
            results = search_structures(conn, query)
            st.session_state["struct_results"] = [
                {
                    "id": r.id, "provider": r.provider, "name": r.name,
                    "formula": r.formula, "doi": r.doi, "external_id": r.external_id,
                    "extra": r.extra_json,
                }
                for r in results
            ]
        except StructureValidationError as exc:
            st.error(str(exc))
    results = st.session_state.get("struct_results") or []
    if results:
        st.markdown(f"**{len(results)} structure record(s)** — leads, not verified samples")
        for r in results:
            st.markdown(
                f"- **{esc(r['name'])}**"
                + (f" ({esc(r['formula'])})" if r["formula"] else "")
                + f" — `{r['provider']}`"
                + (f" — id: {esc(r['external_id'])}" if r["external_id"] else "")
                + (f" — DOI: {esc(r['doi'])}" if r["doi"] else " — DOI: `unknown`")
            )
            if r.get("extra"):
                # Computed/context properties ride along from the provider CSV
                # (e.g. QMOF band gaps). They are theory-stream metadata about
                # a structure record — never measured lab evidence (D11).
                st.markdown(f"  - `{r['provider']}` computed/context properties: {esc(r['extra'])}")
            if r["doi"] and st.button(
                "Capture as reference", key=f"capture_struct_{r['id']}"
            ):
                try:
                    _rec, source_id = capture_structure_reference(
                        conn, r["id"],
                        st.session_state.get("ref_contributor") or "Mohammed (owner)",
                    )
                    st.session_state["flash"] = (
                        f"Structure #{r['id']} captured as reference #{source_id} "
                        "with structure provenance — a lead like any other."
                    )
                    st.rerun()
                except StructureValidationError as exc:
                    st.error(str(exc))
        st.caption(
            "A structure record is metadata about a published structure — it "
            "never establishes that a sample was made, or that it was tested. "
            "The reference remains a lead; identity questions belong to the "
            "Samples & identity relations."
        )


def _render_packages_section(conn) -> None:
    """Evidence packages (issue #19): attributed offline collaboration.
    Export selected sources + dependents as schema-v1 JSON; import validates
    strictly and lists EVERY rejection reason. Imported rows enter as
    needs_verification attributed to the package contributor — never
    auto-promoted, never merged."""
    st.caption(
        f"Format: `{PACKAGE_FORMAT}` schema v1 "
        "(_docs/package-schema-v1.json). Export selects sources and their "
        "dependents; import validates strictly — schema drift, missing "
        "provenance, review-state overwrites, and merge attempts are "
        "rejected with the full reason list. Imported rows enter as "
        "`needs_verification` attributed to the package contributor and "
        "coexist as separate records (never merged)."
    )
    refs = list_references(conn)
    if refs:
        selected = st.multiselect(
            "Export sources (and their dependents)",
            options=[r.id for r in refs],
            format_func=lambda k: next(
                f"#{r.id} — {r.title or r.doi}" for r in refs if r.id == k
            ),
            key="pkg_export_ids",
        )
        if st.button("Export package (JSON)", key="pkg_export"):
            try:
                package = export_package(conn, selected)
                st.download_button(
                    "Download package JSON",
                    data=json.dumps(package, indent=2, ensure_ascii=False),
                    file_name=f"evidence-package-v1-{selected}.json",
                    mime="application/json",
                    key="pkg_download",
                )
            except PackageValidationError as exc:
                st.error(str(exc))
    st.text_input(
        "Path to a package JSON file (local)", key="pkg_import_path",
        placeholder="e.g. data/imports/evidence-package.json",
    )
    if st.button("Import package", key="pkg_import_btn"):
        try:
            raw = Path(st.session_state.get("pkg_import_path") or "").read_text(
                encoding="utf-8"
            )
        except (OSError, UnicodeDecodeError) as exc:
            st.error(f"Could not read the package file. ({exc})")
        else:
            try:
                report = import_package(conn, raw)
                st.session_state["flash"] = (
                    f"Package imported: {report.sources} source(s), "
                    f"{report.samples} sample(s), {report.observations} "
                    f"observation(s), {report.assertions} assertion(s), "
                    f"{report.compounds} compound(s) — attributed to "
                    f"{report.contributor}, all `needs_verification`, all "
                    "separate records."
                )
                st.rerun()
            except PackageValidationError as exc:
                st.error("PACKAGE REJECTED — every reason:")
                for reason in exc.reasons:
                    st.markdown(f"- {esc(reason)}")
            except PackagePersistenceError as exc:
                st.error(str(exc))
            except json.JSONDecodeError as exc:
                st.error(f"The file is not valid JSON. ({exc})")
