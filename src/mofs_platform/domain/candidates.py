"""Candidate cards (issue #10): inspect why a candidate appeared and follow
each displayed claim to its recorded evidence.

Cards aggregate what is already stored — samples, observations, operating
states, assertions, references, route attempts — and add no ranking, no
scoring, and no inference. Missing evidence and uncertainty render as
explicit `unknown` / needs-verification labels.
"""

import sqlite3
from dataclasses import dataclass

from mofs_platform.domain.attempts import list_attempts
from mofs_platform.domain.evidence import EPISTEMIC_LABELS, list_assertions
from mofs_platform.domain.identity import list_observations, list_samples, list_states
from mofs_platform.domain.references import level_label, list_references


class CandidateValidationError(ValueError):
    """The requested candidate cannot be inspected."""


@dataclass(frozen=True)
class CandidateCard:
    sample_id: int
    designation: str
    basis: str
    source_id: int
    source_label: str
    source_inspected_level: str
    retrieval_reason: str
    material_class: str | None
    parent_relation: str | None
    modifications: str | None
    operating_states: list[dict]
    observations: list[dict]
    assertions: list[dict]
    conflicts: list[int]
    route_outcomes: list[dict]


def _reference_label(ref) -> str:
    return f"#{ref.id} — {ref.title or ref.doi or 'untitled'} (captured {ref.retrieval_date})"


def get_candidate_card(conn: sqlite3.Connection, sample_id: int) -> CandidateCard:
    sample = next((s for s in list_samples(conn) if s.id == sample_id), None)
    if sample is None:
        raise CandidateValidationError(f"Sample #{sample_id} does not exist.")
    references = {r.id: r for r in list_references(conn)}
    ref = references.get(sample.source_id)
    ref_label = _reference_label(ref) if ref else f"source #{sample.source_id} `unknown`"
    inspected = level_label(ref.inspected_level) if ref else "`unknown`"

    lineage = ""
    if sample.derived_from_sample_id:
        lineage = f"{sample.lineage_kind} of sample #{sample.derived_from_sample_id}"
    retrieval_reason = (
        f"Recorded under source {ref_label}: designation '{sample.designation}'"
        + (f" as {lineage}" if lineage else "")
        + (f", parent framework '{sample.parent_framework_name}'" if sample.parent_framework_name else "")
        + "."
    )

    observations = [
        {
            "id": ob.id,
            "kind": ob.observation_kind,
            "value": ob.value or "`unknown`",
            "unit": ob.unit or "",
            "gaps": [
                name for name, v in {
                    "reaction": ob.reaction, "medium": ob.medium,
                    "reference/conversion": ob.reference_convention,
                    "loading": ob.loading, "duration": ob.duration,
                    "protocol": ob.protocol,
                }.items() if not v
            ],
            "evidence_location": ob.evidence_location or "`unknown`",
            "sample_id": ob.sample_id,
        }
        for ob in list_observations(conn, sample.id)
    ]
    states = [
        {
            "id": st.id, "stage": st.stage,
            "phase": st.phase_assignment or "`unresolved`",
            "epistemic": EPISTEMIC_LABELS[st.epistemic_type],
            "evidence_location": st.evidence_location or "`unknown`",
        }
        for st in list_states(conn, sample.id)
    ]
    assertions = [
        {
            "id": a.id, "claim_type": a.claim_type, "claim_text": a.claim_text,
            "location": a.evidence_location or "`unknown`",
            "epistemic": EPISTEMIC_LABELS[a.epistemic_type],
            "review_state": a.review_state,
            "conflicts_with": a.conflicts_with,
        }
        for a in list_assertions(conn, source_id=sample.source_id)
    ]
    conflicts = [a["id"] for a in assertions if a["review_state"] == "conflicted"]
    route_outcomes = [
        {"outcome": at.outcome, "created_at": at.created_at}
        for at in list_attempts(conn) if ref is not None and at.target == ref.doi
    ]

    return CandidateCard(
        sample_id=sample.id,
        designation=sample.designation,
        basis=sample.basis,
        source_id=sample.source_id,
        source_label=ref_label,
        source_inspected_level=inspected,
        retrieval_reason=retrieval_reason,
        material_class=sample.composition,
        parent_relation=sample.parent_framework_name,
        modifications=sample.additions or lineage or None,
        operating_states=states,
        observations=observations,
        assertions=assertions,
        conflicts=conflicts,
        route_outcomes=route_outcomes,
    )


def list_candidate_cards(conn: sqlite3.Connection) -> list[CandidateCard]:
    return [get_candidate_card(conn, s.id) for s in list_samples(conn)]


def retrieval_outcome_summary(conn: sqlite3.Connection) -> dict:
    """Route-attempt outcome counts for the empty-state honest summary."""
    summary: dict[str, int] = {}
    for at in list_attempts(conn):
        summary[at.outcome] = summary.get(at.outcome, 0) + 1
    return summary
