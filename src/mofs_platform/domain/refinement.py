"""Mechanical question-refinement observations (issue #15, Part A).

Deterministic, fully offline rules over the SAVED question — recomputed live
on every render, never persisted, never auto-applied. Every observation reads
as `tool inference` for review, never as an authority: the researcher edits
and saves through the normal flow or ignores them.

The vague-term list below is the COMPLETE, visible set — the UI renders this
documentation so a silent rule change is impossible.
"""

import re

from mofs_platform.domain.hints import question_hints
from mofs_platform.domain.questions import Question

# The documented vague-term list (issue #15 acceptance criterion). Each entry
# is matched word-boundary, case-insensitive, inside the question wording.
# Multi-word entries allow flexible spacing.
VAGUE_TERMS = (
    "several",
    "various",
    "some",
    "many",
    "low-cost",
    "low cost",
    "high performance",
    "efficient",
    "novel",
    "stable",
    "fast",
    "significantly",
    "good",
)

VAGUE_TERMS_DOCUMENTATION = (
    "Vague-term rules (deterministic, offline — the complete visible set): "
    + ", ".join(f"'{t}'" for t in VAGUE_TERMS)
    + ". Each is flagged when it appears in the question wording, because a "
    "downstream comparison needs it defined (what counts as low-cost? "
    "efficient at what?). Review suggestions only — nothing is changed."
)

# The question fields whose absence gates downstream matching (#16 criteria,
# #17 comparisons, #18 profiles).
_FIELD_LABELS = {
    "reactions": "Reaction / application",
    "material_classes": "Allowed material classes",
    "conditions": "Relevant conditions",
    "hard_requirements": "Hard requirements",
    "preferences": "Preferences",
    "meaning_of_improvement": "Meaning of improvement",
}


def _vague_pattern(term: str) -> re.Pattern:
    escaped = re.escape(term).replace(r"\ ", r"\s+")
    return re.compile(r"\b" + escaped + r"\b", re.IGNORECASE)


def mechanical_observations(question: Question) -> list[dict]:
    """All mechanical observations for the saved question: vague terms,
    unknown fields, and #14's hint rules reused verbatim. A precise, complete
    question yields an empty list — no false alarms."""
    observations: list[dict] = []
    wording = question.wording or ""
    for term in VAGUE_TERMS:
        if _vague_pattern(term).search(wording):
            observations.append({
                "kind": "vague_term",
                "detail": term,
                "message": (
                    f"The wording uses '{term}' — state what it means here "
                    "(a number, a threshold, or a definition), because "
                    "downstream comparisons cannot resolve it."
                ),
            })
    for field, label in _FIELD_LABELS.items():
        if not getattr(question, field, None):
            observations.append({
                "kind": "unknown_field",
                "detail": field,
                "message": (
                    f"{label} is `unknown` — it gates lead matching and any "
                    "later comparison. Fill it when you can, or leave it "
                    "honestly unknown."
                ),
            })
    for hint in question_hints(question):
        observations.append({
            "kind": "hint",
            "detail": hint["rule"],
            "message": hint["message"],
        })
    return observations
