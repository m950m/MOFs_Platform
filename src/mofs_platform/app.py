"""Streamlit entry point — issue #3 empty/ready state.

Renders an honest empty state: names what is absent, invents nothing
(see _docs/design-system.md, rule 7). Startup proves the entry point works;
it does not validate provider access or chemistry.
"""

import streamlit as st

st.set_page_config(page_title="MOF Platform", page_icon=":microscope:")

st.title("MOF Electrochemistry Research Tool")

st.success("Empty / ready — no data recorded yet.")

st.markdown(
    """
- No research questions recorded yet.
- No laboratory capability profile recorded yet.
- No sources recorded yet.
- No candidates, samples, or evidence assertions recorded yet.
- HER search outcome: `not yet searched`
- OER search outcome: `not yet searched`
"""
)

st.caption(
    "This startup validates the entry point only. "
    "It does not validate provider access, chemistry, or any scientific claim."
)
