"""Home page: an honest status line (design-system rule 7)."""

import streamlit as st

from mofs_platform.domain.labprofile import list_capabilities
from mofs_platform.domain.questions import get_question

EMPTY_MARKER = "Empty / ready"
READY_MARKER = "Ready — data recorded"

NOT_RECORDED = {
    "question": "No research question saved yet.",
    "profile": "No laboratory capability profile recorded yet.",
    "sources": "No sources recorded yet.",
    "candidates": "No candidates, samples, or evidence assertions recorded yet.",
}


def render_home(conn) -> None:
    question = get_question(conn)
    capabilities = list_capabilities(conn)

    if question is None and not capabilities:
        st.success(f"{EMPTY_MARKER} — no data recorded yet.")
        st.markdown(
            f"- {NOT_RECORDED['question']}\n"
            f"- {NOT_RECORDED['profile']}\n"
            f"- {NOT_RECORDED['sources']}\n"
            f"- {NOT_RECORDED['candidates']}\n"
            "- HER search outcome: `not yet searched`\n"
            "- OER search outcome: `not yet searched`"
        )
    else:
        recorded = []
        if question is not None:
            recorded.append("research question")
        if capabilities:
            recorded.append(f"laboratory profile ({len(capabilities)} entries)")
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
            f"- {NOT_RECORDED['sources']}\n"
            f"- {NOT_RECORDED['candidates']}\n"
            "- HER search outcome: `not yet searched`\n"
            "- OER search outcome: `not yet searched`"
        )
    st.caption(
        "This startup validates the entry point only. "
        "It does not validate provider access, chemistry, or any scientific claim."
    )
