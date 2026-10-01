"""Research-question entry, inspection, and correction (issue #4).

Hard requirements and preferences are visibly distinguished (design-system
rule 2); unset scientific fields display as `unknown` and are never defaulted
(rule 7). Unsaved edits are discarded on navigation — only an explicit save
persists (issue #4: leave-edits-unsaved criterion).
"""

import streamlit as st

from mofs_platform.domain.questions import (
    Question,
    QuestionPersistenceError,
    QuestionValidationError,
    count_events,
    get_question,
    save_question,
)

PAGE_TITLE = "Research question"


def _show_saved(question: Question, corrections: int) -> None:
    st.success(f"Saved question (last updated: {question.updated_at}).")
    st.markdown(f"**Question wording:**\n\n> {question.wording}")
    left, right = st.columns(2)
    with left:
        st.subheader("Hard requirements", help="Must be met by a candidate.")
        st.markdown(question.hard_requirements or "`unknown`")
    with right:
        st.subheader("Preferences", help="Nice to have; not required.")
        st.markdown(question.preferences or "`unknown`")
    st.markdown(
        f"- Reaction / application: {question.reactions or '`unknown`'}\n"
        f"- Allowed material classes: {question.material_classes or '`unknown`'}\n"
        f"- Relevant conditions: {question.conditions or '`unknown`'}\n"
        f"- Meaning of improvement: {question.meaning_of_improvement or '`unknown`'}"
    )
    st.caption(
        f"{corrections} correction event(s) recorded. "
        "Saving a question establishes no material identity, measured "
        "performance, laboratory feasibility, novelty, or scientific conclusion."
    )


def render_question_page(conn) -> None:
    st.header(PAGE_TITLE)
    flash = st.session_state.pop("flash", None)  # one-shot display notice
    if flash:
        st.success(flash)
    current = get_question(conn)
    if current is None:
        st.info(
            "No research question saved yet. Enter it below — blank wording "
            "cannot be saved, and fields you leave blank stay `unknown`."
        )
    else:
        _show_saved(current, count_events(conn))

    with st.form("question_form", clear_on_submit=False):
        wording = st.text_area(
            "Question wording",
            value=current.wording if current else "",
            height=100,
            placeholder="Type your research question here…",
        )
        reactions = st.text_input(
            "Reaction / application",
            value=current.reactions or "" if current else "",
            placeholder="e.g. HER, OER — leave blank for unknown",
        )
        material_classes = st.text_input(
            "Allowed material classes",
            value=current.material_classes or "" if current else "",
            placeholder="e.g. MOF, ZIF, composite, derived — leave blank for unknown",
        )
        conditions = st.text_area(
            "Relevant conditions",
            value=current.conditions or "" if current else "",
            height=70,
            placeholder="e.g. electrolyte, pH, temperature — leave blank for unknown",
        )
        col_hard, col_pref = st.columns(2)
        with col_hard:
            hard = st.text_area(
                "Hard requirements (must be met)",
                value=current.hard_requirements or "" if current else "",
                height=70,
                placeholder="Leave blank for unknown",
            )
        with col_pref:
            preferences = st.text_area(
                "Preferences (nice to have, not required)",
                value=current.preferences or "" if current else "",
                height=70,
                placeholder="Leave blank for unknown",
            )
        improvement = st.text_area(
            "Meaning of improvement (for this question)",
            value=current.meaning_of_improvement or "" if current else "",
            height=70,
            placeholder="Leave blank for unknown",
        )
        submitted = st.form_submit_button("Save question", type="primary")

    if submitted:
        candidate = Question(
            wording=wording,
            reactions=reactions.strip() or None,
            material_classes=material_classes.strip() or None,
            conditions=conditions.strip() or None,
            hard_requirements=hard.strip() or None,
            preferences=preferences.strip() or None,
            meaning_of_improvement=improvement.strip() or None,
        )
        try:
            save_question(conn, candidate)
        except QuestionValidationError as exc:
            st.error(str(exc))
        except QuestionPersistenceError as exc:
            st.error(str(exc))
        else:
            st.session_state["flash"] = "Question saved."
            st.rerun()
