"""Research-question entry, inspection, and correction (issue #4).

Hard requirements and preferences are visibly distinguished (design-system
rule 2); unset scientific fields display as `unknown` and are never defaulted
(rule 7). Unsaved edits are discarded on navigation — only an explicit save
persists (issue #4: leave-edits-unsaved criterion).
"""

import os

import streamlit as st

from mofs_platform.domain.attempts import NEXT_STEPS, PROVIDER_AI, record_attempt
from mofs_platform.domain.hints import (
    HINT_RULES_DOCUMENTATION,
    question_hints,
)
from mofs_platform.domain.questions import (
    Question,
    QuestionPersistenceError,
    QuestionValidationError,
    count_events,
    get_question,
    save_question,
)
from mofs_platform.domain.refinement import (
    VAGUE_TERMS_DOCUMENTATION,
    mechanical_observations,
)
from mofs_platform.sources import glm
from mofs_platform.ui._widgets import esc

PAGE_TITLE = "Research question"


def _show_saved(question: Question, corrections: int) -> None:
    st.success(f"Saved question (last updated: {question.updated_at}).")
    st.markdown(f"**Question wording:**\n\n> {esc(question.wording)}")
    left, right = st.columns(2)
    with left:
        st.subheader("Hard requirements", help="Must be met by a candidate.")
        st.markdown(esc(question.hard_requirements) if question.hard_requirements else "`unknown`")
    with right:
        st.subheader("Preferences", help="Nice to have; not required.")
        st.markdown(esc(question.preferences) if question.preferences else "`unknown`")
    st.markdown(
        f"- Reaction / application: {esc(question.reactions) if question.reactions else '`unknown`'}\n"
        f"- Allowed material classes: {esc(question.material_classes) if question.material_classes else '`unknown`'}\n"
        f"- Relevant conditions: {esc(question.conditions) if question.conditions else '`unknown`'}\n"
        f"- Meaning of improvement: {esc(question.meaning_of_improvement) if question.meaning_of_improvement else '`unknown`'}"
    )
    st.caption(
        f"{corrections} save event(s) recorded (first save + corrections). "
        "Saving a question establishes no material identity, measured "
        "performance, laboratory feasibility, novelty, or scientific conclusion."
    )


def render_question_page(conn) -> None:
    st.header(PAGE_TITLE)
    flash = st.session_state.pop("flash", None)  # one-shot display notice
    if flash:
        st.success(flash)
    current = get_question(conn)
    applied = st.session_state.get("ai_applied") or {}
    if current is not None:
        hints = question_hints(current)
        if hints:
            st.subheader("Consistency hints (review suggestions — nothing was changed)")
            for h in hints:
                st.markdown(f"- [{h['rule']}] {h['message']}")
            st.caption(HINT_RULES_DOCUMENTATION)
        observations = mechanical_observations(current)
        if observations:
            st.subheader(
                "Mechanical observations (`tool inference` — review suggestions, "
                "nothing was changed)"
            )
            for ob in observations:
                st.markdown(f"- **[{ob['kind']}]** {ob['message']}")
            st.caption(VAGUE_TERMS_DOCUMENTATION)
        else:
            st.caption(
                "No mechanical observations — the wording has no vague terms "
                "from the documented list and every refinement field is filled."
            )
    if current is None:
        st.info(
            "No research question saved yet. Enter it below — blank wording "
            "cannot be saved, and fields you leave blank stay `unknown`."
        )
    else:
        _show_saved(current, count_events(conn))

    # Applied AI suggestions prefill the form via value= overrides — the
    # owner still reviews and presses Save themselves; nothing auto-saves.
    with st.form("question_form", clear_on_submit=False):
        wording = st.text_area(
            "Question wording",
            value=applied.get("wording") or (current.wording if current else ""),
            height=100,
            placeholder="Type your research question here…",
        )
        reactions = st.text_input(
            "Reaction / application",
            value=applied.get("reactions") or (current.reactions or "" if current else ""),
            placeholder="e.g. HER, OER — leave blank for unknown",
        )
        material_classes = st.text_input(
            "Allowed material classes",
            value=applied.get("material_classes")
            or (current.material_classes or "" if current else ""),
            placeholder="e.g. MOF, ZIF, composite, derived — leave blank for unknown",
        )
        conditions = st.text_area(
            "Relevant conditions",
            value=applied.get("conditions") or (current.conditions or "" if current else ""),
            height=70,
            placeholder="e.g. electrolyte, pH, temperature — leave blank for unknown",
        )
        col_hard, col_pref = st.columns(2)
        with col_hard:
            hard = st.text_area(
                "Hard requirements (must be met)",
                value=applied.get("hard_requirements")
                or (current.hard_requirements or "" if current else ""),
                height=70,
                placeholder="Leave blank for unknown",
            )
        with col_pref:
            preferences = st.text_area(
                "Preferences (nice to have, not required)",
                value=applied.get("preferences")
                or (current.preferences or "" if current else ""),
                height=70,
                placeholder="Leave blank for unknown",
            )
        improvement = st.text_area(
            "Meaning of improvement (for this question)",
            value=applied.get("meaning_of_improvement")
            or (current.meaning_of_improvement or "" if current else ""),
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
            st.session_state.pop("ai_applied", None)  # applied values now saved
            st.session_state["flash"] = "Question saved."
            st.rerun()

    _render_ai_section(conn, current, applied)


def _render_ai_section(conn, current: Question | None, applied: dict) -> None:
    """Optional AI refinement (issue #15, D10: Z.ai GLM). Calls happen only
    when the owner explicitly enables the assistant for this session; the key
    is session-only and never persisted; only the question's own fields are
    sent. Suggestions render as `tool inference`, are visually distinct, and
    applying one prefills the form — the owner still saves explicitly."""
    if current is None:
        return
    st.subheader("AI refinement (optional — D10: Z.ai GLM)")
    st.caption(
        "Assistant route: Z.ai GLM chat endpoint (OpenAI-compatible), model "
        f"`{glm.MODEL}`. ONLY the question's own saved fields are sent to the "
        "provider — nothing else leaves this machine. Every call is logged in "
        "the route-attempt audit. Failure kinds: no_key / bad_input / timeout "
        "/ offline / rate_limited / bad_response. Suggestions are `tool "
        "inference` — never auto-applied; you apply, review, and save."
    )
    enabled = st.checkbox(
        "Enable assistant calls for this session", key="ai_enabled"
    )
    api_key = st.text_input(
        "API key (session-only — never stored)",
        value="",
        key="ai_key",
        type="password",
        help="Sent only with this request. Or set MOFS_AI_API_KEY in the "
        "environment and leave this blank.",
    )
    if st.button("Request suggestions", key="ai_request"):
        if not enabled:
            st.warning("Enable the assistant first — nothing was sent.")
        else:
            key = api_key.strip() or os.environ.get("MOFS_AI_API_KEY")
            fields = {
                "wording": current.wording,
                "reactions": current.reactions,
                "material_classes": current.material_classes,
                "conditions": current.conditions,
                "hard_requirements": current.hard_requirements,
                "preferences": current.preferences,
                "meaning_of_improvement": current.meaning_of_improvement,
            }
            result = glm.suggest_refinement(fields, key)
            outcome = "success" if not isinstance(result, glm.GLMFailure) else result.kind
            record_attempt(
                conn, provider=PROVIDER_AI, target="question_refinement",
                attempt_kind="ai_refinement", outcome=outcome,
                note=None if outcome == "success" else result.detail,
            )
            if isinstance(result, glm.GLMFailure):
                st.warning(
                    f"`{result.kind}` — {result.detail} Next step: "
                    f"{NEXT_STEPS.get(result.kind, 'none.')}"
                )
            else:
                st.session_state["ai_suggestion"] = result
    suggestion = st.session_state.get("ai_suggestion")
    if isinstance(suggestion, glm.GLMRefinement):
        st.info(
            "**`tool inference` — suggestion from the assistant ("
            f"`{glm.MODEL}`).** Nothing is applied until you press Apply and "
            "then Save." + (f"\n\n**Why:** {esc(suggestion.notes)}" if suggestion.notes else "")
        )
        for field, text in suggestion.suggestions.items():
            st.markdown(f"- **{field}:** {esc(text)}")
        if st.button("Apply suggestion to the form below", key="ai_apply"):
            st.session_state["ai_applied"] = dict(suggestion.suggestions)
            st.session_state.pop("ai_suggestion", None)
            st.rerun()

