"""Streamlit entry point (issues #3-#5).

Startup proves the entry point works; it does not validate provider access
or chemistry. Data is stored in a local SQLite database (data/platform.db by
default; override with the MOFS_DB_PATH environment variable).
"""

import os
from pathlib import Path

import streamlit as st

from mofs_platform.db.connection import connect
from mofs_platform.ui.pages.candidates import CANDIDATES_PAGE_TITLE, render_candidates_page
from mofs_platform.ui.pages.evidence import EVIDENCE_PAGE_TITLE, render_evidence_page
from mofs_platform.ui.pages.home import render_home
from mofs_platform.ui.pages.lab_profile import LAB_PAGE_TITLE, render_lab_profile_page
from mofs_platform.ui.pages.question_page import PAGE_TITLE, render_question_page
from mofs_platform.ui.pages.review import REVIEW_PAGE_TITLE, render_review_page
from mofs_platform.ui.pages.samples import SAMPLES_PAGE_TITLE, render_samples_page
from mofs_platform.ui.pages.sources import SOURCES_PAGE_TITLE, render_sources_page

st.set_page_config(page_title="MOF Platform", page_icon=":microscope:")


def db_path() -> Path:
    env = os.environ.get("MOFS_DB_PATH")
    if env:
        path = Path(env)
    else:
        root = Path(__file__).resolve().parents[2]
        path = root / "data" / "platform.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


conn = connect(db_path())

st.title("MOF Electrochemistry Research Tool")
section = st.sidebar.radio(
    "Section",
    ["Home", PAGE_TITLE, LAB_PAGE_TITLE, SOURCES_PAGE_TITLE, EVIDENCE_PAGE_TITLE,
     SAMPLES_PAGE_TITLE, CANDIDATES_PAGE_TITLE, REVIEW_PAGE_TITLE],
    key="nav",
)

if section == "Home":
    render_home(conn)
elif section == PAGE_TITLE:
    render_question_page(conn)
elif section == LAB_PAGE_TITLE:
    render_lab_profile_page(conn)
elif section == SOURCES_PAGE_TITLE:
    render_sources_page(conn)
elif section == EVIDENCE_PAGE_TITLE:
    render_evidence_page(conn)
elif section == SAMPLES_PAGE_TITLE:
    render_samples_page(conn)
elif section == CANDIDATES_PAGE_TITLE:
    render_candidates_page(conn)
else:
    render_review_page(conn)
