"""Shared UI helpers (small, deliberate).

`esc()` neutralizes Markdown control characters in stored user/provider text
before rendering through st.markdown. Stored content is data (AGENTS.md rule 5):
it must display verbatim and must not render links, images, or structure that
could trigger browser fetches or look like tool UI.
"""

import streamlit as st

_ESCAPES = str.maketrans({
    "\\": "\\\\", "`": "\\`", "*": "\\*", "_": "\\_", "{": "\\{", "}": "\\}",
    "[": "\\[", "]": "\\]", "(": "\\(", ")": "\\)", "#": "\\#", "+": "\\+",
    "-": "\\-", "!": "\\!", ">": "\\>", "|": "\\|", "~": "\\~",
})


def esc(text: object) -> str:
    """Escape Markdown control characters for safe verbatim display."""
    return str(text).translate(_ESCAPES)


def pop_flash() -> str | None:
    """One-shot success notice (established page idiom)."""
    return st.session_state.pop("flash", None)
