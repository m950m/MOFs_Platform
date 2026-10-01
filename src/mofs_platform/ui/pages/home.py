"""Home page: an honest status line (design-system rule 7)."""

import streamlit as st

from mofs_platform.domain.questions import get_question

UNKNOWN = "unknown"

NOT_RECORDED_YET = (
    "No laboratory capability profile recorded yet.",
    "No sources recorded yet.",
    "No candidates, samples, or evidence assertions recorded yet.",
)

EMPTY_MARKER = "Empty / ready"
QUESTION_MARKER = "Ready — research question recorded"


def render_home(conn) -> None:
    question = get_question(conn)
    if question is None:
        st.success(f"{EMPTY_MARKER} — no data recorded yet.")
        st.markdown(
            "- No research question saved yet.\n"
            + "\n".join(f"- {line}" for line in NOT_RECORDED_YET)
            + "\n- HER search outcome: `not yet searched`"
            "\n- OER search outcome: `not yet searched`"
        )
    else:
        st.success(f"{QUESTION_MARKER}.")
        st.markdown(
            "**Saved question:**\n\n"
            f"> {question.wording}\n\n"
            "Edit it under **Research question** in the sidebar.\n\n"
            + "\n".join(f"- {line}" for line in NOT_RECORDED_YET)
            + "\n- HER search outcome: `not yet searched`"
            "\n- OER search outcome: `not yet searched`"
        )
    st.caption(
        "This startup validates the entry point only. "
        "It does not validate provider access, chemistry, or any scientific claim."
    )
