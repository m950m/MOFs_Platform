"""Cross-field consistency hints (issue #14).

Deterministic keyword rules over the saved research question's fields — no
natural-language interpretation, no AI, no network. Hints are computed live
from saved values, never persisted, never block saving, and never change a
value. Every hint reads as a hint for review, never as a validation error.

The rules (R1–R4) are defined below and are the complete set; the UI renders
this documentation next to the hints so a silent rule change is impossible.
"""

import re

from mofs_platform.domain.questions import Question

# Word-boundary tokens: `\bher\b` cannot match "where"; full phrases cover
# spelled-out forms.
_REACTION_PATTERNS = {
    "HER": [re.compile(r"\bher\b", re.IGNORECASE),
            re.compile(r"hydrogen\s+evolution", re.IGNORECASE)],
    "OER": [re.compile(r"\boer\b", re.IGNORECASE),
            re.compile(r"oxygen\s+evolution", re.IGNORECASE)],
}

# Material-class tokens per plan §2 vocabulary.
_CLASS_PATTERNS = {
    "MOF": [re.compile(r"\bmofs?\b", re.IGNORECASE)],
    "ZIF": [re.compile(r"\bzifs?\b", re.IGNORECASE)],
    "composite": [re.compile(r"\bcomposites?\b", re.IGNORECASE)],
    "derived": [re.compile(r"\bderived\b", re.IGNORECASE)],
}

# Numeric electrochemical benchmark (e.g. "10 mA/cm2", "1 A/cm^2").
_BENCHMARK = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:mA|A)\s*/\s*cm", re.IGNORECASE)

HINT_RULES_DOCUMENTATION = (
    "Hint rules (deterministic keywords — no interpretation, no AI, no "
    "network): "
    "**R1** wording mentions a reaction (HER/OER) absent from Reaction/"
    "application; "
    "**R2** Reaction/application lists a reaction the wording never mentions; "
    "**R3** wording mentions a material class (MOF/ZIF/composite/derived) "
    "absent from Allowed material classes, or the field lists a class the "
    "wording never mentions; "
    "**R4** hard requirements or meaning of improvement cite a numeric "
    "benchmark (e.g. mA/cm²) while Relevant conditions is `unknown`. "
    "Hints are review suggestions only — saving is never blocked and no value "
    "is ever changed."
)


def _mentions(text: str, patterns: list[re.Pattern]) -> bool:
    return any(p.search(text) for p in patterns)


def question_hints(question: Question) -> list[dict]:
    """Compute the hint list from saved values. Pure function: no I/O, no
    persistence, no mutation — safe to call on every render."""
    hints: list[dict] = []
    wording = question.wording or ""
    field_reactions = question.reactions or ""
    field_classes = question.material_classes or ""

    for reaction, patterns in _REACTION_PATTERNS.items():
        in_wording = _mentions(wording, patterns)
        in_field = _mentions(field_reactions, patterns)
        if in_wording and not in_field:
            hints.append({
                "rule": "R1",
                "message": (
                    f"The wording mentions {reaction}, but the Reaction/"
                    "application field does not list it — review whether the "
                    "field should include it."
                ),
            })
        elif in_field and not in_wording:
            hints.append({
                "rule": "R2",
                "message": (
                    f"The Reaction/application field lists {reaction}, but the "
                    "wording never mentions it — review whether the wording or "
                    "the field should change."
                ),
            })

    for cls, patterns in _CLASS_PATTERNS.items():
        in_wording = _mentions(wording, patterns)
        in_field = _mentions(field_classes, patterns)
        if in_wording and not in_field:
            hints.append({
                "rule": "R3",
                "message": (
                    f"The wording mentions the material class {cls}, but Allowed "
                    "material classes does not list it — review whether the field "
                    "should include it."
                ),
            })
        elif in_field and not in_wording:
            hints.append({
                "rule": "R3",
                "message": (
                    f"Allowed material classes lists {cls}, but the wording never "
                    "mentions it — review whether the wording or the field should "
                    "change."
                ),
            })

    benchmark_context = (
        _mentions(question.hard_requirements or "", [_BENCHMARK])
        or _mentions(question.meaning_of_improvement or "", [_BENCHMARK])
    )
    if benchmark_context and not (question.conditions or "").strip():
        hints.append({
            "rule": "R4",
            "message": (
                "Hard requirements or meaning of improvement cite a numeric "
                "benchmark, while Relevant conditions is `unknown` — confirm "
                "and record the conditions the benchmark is meaningful under."
            ),
        })

    return hints
