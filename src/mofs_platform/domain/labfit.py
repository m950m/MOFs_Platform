"""Laboratory-fit explanation (issue #12).

Deterministically matches a sample's recorded preparation/testing requirement
assertions against the confirmed laboratory capability profile. Outcomes are
exactly: `possible_with_current_capabilities`, `requires_future_capabilities`,
or `unknown` — with per-requirement reasons. Missing, unconfirmed, conflicting,
or unavailable facts prevent positive assessments; future never counts as
current; an explicitly unavailable capability is never relabeled as future.
No synthesis success, catalytic performance, or universal suitability is ever
claimed. Assessments store their input basis so later changes mark them
visibly outdated until re-run.
"""

import json
import sqlite3
from dataclasses import dataclass

from mofs_platform.domain.evidence import list_assertions
from mofs_platform.domain.labprofile import list_capabilities

OUTCOMES = (
    "possible_with_current_capabilities",
    "requires_future_capabilities",
    "unknown",
)


class LabFitValidationError(ValueError):
    """The assessment cannot be produced."""


@dataclass(frozen=True)
class FitAssessment:
    id: int
    sample_id: int
    assessment: str
    reasons: list[dict]
    basis: dict
    created_at: str
    outdated: bool


def _basis_stamps(conn: sqlite3.Connection, source_id: int) -> dict:
    """Content digests of the assessment inputs. Second-granularity timestamps
    cannot detect same-second edits, so staleness is detected by CONTENT —
    a status/text change always marks older assessments outdated."""
    question = conn.execute("SELECT text FROM question WHERE id = 1").fetchone()
    caps = conn.execute(
        "SELECT COALESCE(GROUP_CONCAT(digest), 'none') AS m FROM "
        "(SELECT name || ':' || status AS digest FROM lab_capability ORDER BY id)"
    ).fetchone()
    asserts = conn.execute(
        "SELECT COALESCE(GROUP_CONCAT(digest), 'none') AS m FROM "
        "(SELECT claim_text || ':' || review_state AS digest FROM assertion "
        "WHERE source_id = ? ORDER BY id)",
        (source_id,),
    ).fetchone()
    return {
        "question_text": question["text"] if question else "none",
        "capabilities_digest": caps["m"],
        "assertions_digest": asserts["m"],
    }


def _match_capability(requirement_text: str, capabilities) -> dict | None:
    """Deterministic keyword match: a capability entry applies when its name
    (case-insensitive) appears in the requirement text or vice versa."""
    req = requirement_text.lower()
    for cap in capabilities:
        name = cap.name.lower()
        if name in req or (len(req) >= 4 and req in name):
            return {"id": cap.id, "name": cap.name, "status": cap.status}
    return None


def assess_fit(conn: sqlite3.Connection, sample_id: int, source_id: int) -> FitAssessment:
    sample = conn.execute(
        "SELECT designation FROM sample_record WHERE id = ?", (sample_id,)
    ).fetchone()
    if sample is None:
        raise LabFitValidationError(f"Sample #{sample_id} does not exist.")
    capabilities = list_capabilities(conn)
    assertions = list_assertions(conn, source_id=source_id)

    preparation = [a for a in assertions if a.claim_type == "preparation"]
    testing = [a for a in assertions if a.claim_type == "application"]

    reasons: list[dict] = []
    blocked = False
    needs_future = False
    unknowns = False

    for claim_type, reqs in (("preparation", preparation), ("testing", testing)):
        for a in reqs:
            entry = {
                "kind": claim_type, "assertion_id": a.id,
                "requirement": a.claim_text,
                "evidence_location": a.evidence_location or "`unknown`",
                "review_state": a.review_state,
            }
            if a.review_state in ("needs_verification", "conflicted"):
                entry.update({
                    "match": "insufficiently reviewed",
                    "effect": "unknown",
                    "reason": "The requirement assertion has not been reviewed (or is "
                              "conflicted), so it cannot ground a positive assessment.",
                })
                unknowns = True
            else:
                match = _match_capability(a.claim_text, capabilities)
                if match is None:
                    entry.update({
                        "match": "no confirmed capability entry",
                        "effect": "unknown",
                        "reason": "No laboratory capability entry matches this "
                                  "requirement — the fact is `unknown`.",
                    })
                    unknowns = True
                else:
                    entry.update({"match": f"capability '{match['name']}'",
                                  "capability_status": match["status"]})
                    if match["status"] == "current":
                        entry.update({
                            "effect": "possible",
                            "reason": f"'{match['name']}' is confirmed current in the profile.",
                        })
                    elif match["status"] == "future":
                        entry.update({
                            "effect": "requires future",
                            "reason": f"'{match['name']}' is recorded as future — planned, "
                                      "NOT currently available.",
                        })
                        needs_future = True
                    elif match["status"] == "unavailable":
                        entry.update({
                            "effect": "blocked",
                            "reason": f"'{match['name']}' is explicitly unavailable — "
                                      "this is not silently relabeled as future.",
                        })
                        blocked = True
                    else:  # unknown
                        entry.update({
                            "effect": "unknown",
                            "reason": f"'{match['name']}' is `unknown` in the profile — "
                                      "unconfirmed facts cannot ground an assessment.",
                        })
                        unknowns = True
            reasons.append(entry)

    if blocked:
        assessment = "unknown"
        reasons.append({
            "effect": "unknown", "reason": "An explicitly unavailable capability "
            "blocks any positive assessment (it is never relabeled as future).",
        })
    elif unknowns:
        assessment = "unknown"
        reasons.append({
            "effect": "unknown", "reason": "Missing, unconfirmed, or insufficiently "
            "reviewed facts prevent a positive assessment.",
        })
    elif needs_future:
        assessment = "requires_future_capabilities"
        reasons.append({
            "effect": "requires future", "reason": "All matched requirements are "
            "covered, but some depend on capabilities recorded as future.",
        })
    elif preparation or testing:
        assessment = "possible_with_current_capabilities"
        reasons.append({
            "effect": "possible", "reason": "The sourced requirements are covered by "
            "capabilities confirmed as current.",
        })
    else:
        assessment = "unknown"
        reasons.append({
            "effect": "unknown", "reason": "No sourced preparation or testing "
            "requirements recorded for this sample — insufficient evidence.",
        })

    basis = _basis_stamps(conn, source_id)
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO fit_assessment (sample_id, assessment, reasons_json, "
                "basis_json) VALUES (?, ?, ?, ?)",
                (sample_id, assessment, json.dumps(reasons), json.dumps(basis)),
            )
            new_id = int(cur.lastrowid)
    except sqlite3.Error as exc:
        raise LabFitValidationError(f"Saving failed. ({exc})") from exc
    return FitAssessment(
        id=new_id, sample_id=sample_id, assessment=assessment, reasons=reasons,
        basis=basis, created_at=conn.execute(
            "SELECT created_at FROM fit_assessment WHERE id = ?", (new_id,)
        ).fetchone()[0],
        outdated=False,
    )


def latest_assessment(conn: sqlite3.Connection, sample_id: int) -> FitAssessment | None:
    row = conn.execute(
        "SELECT * FROM fit_assessment WHERE sample_id = ? ORDER BY id DESC LIMIT 1",
        (sample_id,),
    ).fetchone()
    if row is None:
        return None
    basis = json.loads(row["basis_json"])
    sample_row = conn.execute(
        "SELECT source_id FROM sample_record WHERE id = ?", (sample_id,)
    ).fetchone()
    current_basis = _basis_stamps(conn, sample_row["source_id"]) if sample_row else {}
    outdated = any(basis.get(k) != v for k, v in current_basis.items())
    return FitAssessment(
        id=row["id"], sample_id=row["sample_id"], assessment=row["assessment"],
        reasons=json.loads(row["reasons_json"]), basis=basis,
        created_at=row["created_at"], outdated=outdated,
    )
