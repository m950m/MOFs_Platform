"""Laboratory capability profile page (issue #5).

Four statuses must stay visibly distinct: current (available now), future
(planned, NOT available yet), explicitly unavailable, and `unknown`. Nothing
is seeded; the profile implies no candidate suitability, no synthesis success,
and no material restriction such as a blanket HHTP exclusion.

Widget-state note: widget keys (cap_*) may only be written BEFORE the widgets
are instantiated in a run — mode changes are therefore queued as *_request
flags and applied at the top of the next render.
"""

import streamlit as st

from mofs_platform.domain.labprofile import (
    STATUS_LABELS,
    STATUSES,
    LabProfilePersistenceError,
    LabProfileValidationError,
    add_capability,
    list_capabilities,
    update_capability,
)
from mofs_platform.ui._widgets import esc

LAB_PAGE_TITLE = "Laboratory profile"

_STATUS_MARKERS = {
    "current": "**current — available now**",
    "future": "**future — planned, NOT currently available**",
    "unavailable": "**explicitly unavailable**",
    "unknown": "`unknown` — not yet confirmed",
}

def _apply_requests() -> None:
    """Apply queued mode changes before the form widgets are instantiated.

    After a form submit only non-widget state may be written — widget-key
    writes raise StreamlitWidgetAlreadyInstantiatedError in the real browser
    (guided session 001) — so success paths queue `exit_edit_request`, while
    the Cancel button (no form submit in flight) queues `reset_request`,
    which may also clear the fields. Field clearing on submit itself is
    st.form(clear_on_submit=True)."""
    if "exit_edit_request" in st.session_state:
        st.session_state.pop("exit_edit_request", None)
        st.session_state.pop("editing", None)
    if "reset_request" in st.session_state:
        st.session_state.pop("reset_request", None)
        st.session_state.pop("editing", None)
        st.session_state["cap_name"] = ""
        st.session_state["cap_desc"] = ""
        st.session_state["cap_status"] = "unknown"
    if "edit_request" in st.session_state:
        request = st.session_state.pop("edit_request")
        st.session_state["editing"] = {"id": request["id"], "name": request["name"]}
        st.session_state["cap_name"] = request["name"]
        st.session_state["cap_desc"] = request["description"] or ""
        st.session_state["cap_status"] = request["status"]

    if "cap_status" not in st.session_state:
        st.session_state["cap_status"] = "unknown"  # honest default for new entries


def render_lab_profile_page(conn) -> None:
    st.header(LAB_PAGE_TITLE)
    flash = st.session_state.pop("flash", None)  # one-shot display notice
    if flash:
        st.success(flash)
    _apply_requests()

    entries = list_capabilities(conn)
    if not entries:
        st.info(
            "No laboratory capability recorded yet. Add entries below — the tool "
            "invents no equipment, no restrictions, and no defaults."
        )
    else:
        st.subheader(f"Recorded capabilities ({len(entries)})")
        for cap in entries:
            line = f"- **{esc(cap.name)}** — {_STATUS_MARKERS[cap.status]}"
            if cap.description:
                line += f" — {esc(cap.description)}"
            st.markdown(line)
        st.caption(
            "current ≠ future ≠ explicitly unavailable ≠ `unknown`: each entry shows "
            "exactly the status that was entered. This profile implies no candidate "
            "suitability, no synthesis success, and no material restriction — no "
            "blanket HHTP exclusion or similar is inferred from it."
        )

    editing = st.session_state.get("editing")
    if editing:
        st.warning(f"Correcting entry #{editing['id']}: {esc(editing['name'])}")

    with st.form("capability_form", clear_on_submit=True):
        st.text_input("Capability name", key="cap_name")
        st.text_area("Description / notes (optional)", key="cap_desc")
        st.radio(
            "Status",
            list(STATUSES),
            key="cap_status",
            format_func=lambda s: STATUS_LABELS[s],
            horizontal=True,
        )
        st.form_submit_button(
            "Save correction" if editing else "Add capability",
            key="save_capability",
            type="primary",
        )

    if st.session_state.get("save_capability"):
        name = st.session_state.get("cap_name", "")
        desc = st.session_state.get("cap_desc") or None
        status = st.session_state.get("cap_status", "unknown")
        try:
            if editing:
                updated = update_capability(conn, editing["id"], name, desc, status)
                st.session_state["flash"] = f"Correction saved for {esc(updated.name)}."
            else:
                added = add_capability(conn, name, desc, status)
                st.session_state["flash"] = f"Capability added: {esc(added.name)}."
            st.session_state["exit_edit_request"] = True
            st.rerun()  # success path only — errors stay visible on this render
        except LabProfileValidationError as exc:
            st.error(str(exc))
        except LabProfilePersistenceError as exc:
            st.error(str(exc))

    if editing and st.button("Cancel correction", key="cancel_correction"):
        st.session_state["reset_request"] = True
        st.rerun()

    if entries and not editing:  # hidden while correcting: one edit target at a time
        st.subheader("Correct an entry")
        for cap in entries:
            if st.button(f"Correct: {cap.name}", key=f"correct_{cap.id}"):
                st.session_state["edit_request"] = {
                    "id": cap.id,
                    "name": cap.name,
                    "description": cap.description,
                    "status": cap.status,
                }
                st.rerun()
