"""Home page: an honest status line (design-system rule 7)."""

import streamlit as st

from mofs_platform.domain.labprofile import list_capabilities
from mofs_platform.domain.questions import get_question
from mofs_platform.domain.references import list_references
from mofs_platform.domain.search import list_runs

EMPTY_MARKER = "Empty / ready"
READY_MARKER = "Ready — data recorded"

NOT_RECORDED = {
    "question": "No research question saved yet.",
    "profile": "No laboratory capability profile recorded yet.",
    "sources": "No sources recorded yet.",
    "candidates": "No candidates, samples, or evidence assertions recorded yet.",
}


def _search_outcome_lines(conn) -> str:
    """Latest active-search outcome per D9 provider — honest when empty."""
    runs = list_runs(conn, limit=10)
    lines = []
    for provider in ("crossref", "openalex"):
        latest = next((r for r in runs if r.provider == provider), None)
        if latest is None:
            lines.append(f"- Active search ({provider}): `not yet searched`")
        else:
            icon = "✅" if latest.outcome == "success" else "⚠️"
            lines.append(
                f"- Active search ({provider}): {icon} `{latest.outcome}` "
                f"({latest.result_count} hit(s), {latest.created_at}) — run "
                f"#{latest.id}"
            )
    return "\n".join(lines)


def render_home(conn) -> None:
    question = get_question(conn)
    capabilities = list_capabilities(conn)
    references = list_references(conn)

    if question is None and not capabilities and not references:
        st.success(f"{EMPTY_MARKER} — no data recorded yet.")
        st.markdown(
            f"- {NOT_RECORDED['question']}\n"
            f"- {NOT_RECORDED['profile']}\n"
            f"- {NOT_RECORDED['sources']}\n"
            f"- {NOT_RECORDED['candidates']}\n"
            + _search_outcome_lines(conn)
        )
    else:
        recorded = []
        if question is not None:
            recorded.append("research question")
        if capabilities:
            recorded.append(f"laboratory profile ({len(capabilities)} entries)")
        if references:
            recorded.append(f"references ({len(references)} leads)")
        st.success(f"{READY_MARKER} — " + ", ".join(recorded) + ".")
        st.markdown(
            (
                f"**Saved question:**\n\n> {question.wording}\n\n"
                "Edit it under **Research question** in the sidebar.\n\n"
            )
            if question is not None
            else f"- {NOT_RECORDED['question']}\n"
        )
        st.markdown(
            (
                f"**Laboratory capability profile:** {len(capabilities)} entries — "
                "inspect under **Laboratory profile** in the sidebar.\n"
            )
            if capabilities
            else f"- {NOT_RECORDED['profile']}\n"
        )
        st.markdown(
            (
                f"**Sources:** {len(references)} reference leads — inspect under "
                "**Sources** in the sidebar.\n"
            )
            if references
            else f"- {NOT_RECORDED['sources']}\n"
        )
        st.markdown(
            f"- {NOT_RECORDED['candidates']}\n" + _search_outcome_lines(conn)
        )
    st.caption(
        "This startup validates the entry point only. "
        "It does not validate provider access, chemistry, or any scientific claim."
    )
