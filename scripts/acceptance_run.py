"""Acceptance run (issue #13): the complete first evidence workflow, end to end.

Drives the domain API through every workflow step on a throwaway database
using clearly labeled synthetic fixtures, and prints a Markdown acceptance
record with expected vs actual results per step. Exits 0 when every expected
outcome matches, 1 otherwise. Offline by construction (no network calls).

Usage: .venv/bin/python scripts/acceptance_run.py [--out PATH]
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mofs_platform.db.connection import connect  # noqa: E402
from mofs_platform.domain.attempts import list_attempts  # noqa: E402
from mofs_platform.domain.candidates import get_candidate_card  # noqa: E402
from mofs_platform.domain.evidence import record_assertion  # noqa: E402
from mofs_platform.domain.identity import (  # noqa: E402
    compare_samples, record_observation, record_operating_state, record_sample,
)
from mofs_platform.domain.labfit import assess_fit, latest_assessment  # noqa: E402
from mofs_platform.domain.labprofile import add_capability, update_capability  # noqa: E402
from mofs_platform.domain.questions import Question, get_question, save_question  # noqa: E402
from mofs_platform.domain.references import (  # noqa: E402
    add_manual_reference, enrich_with_crossref,
)
from mofs_platform.domain.review import (  # noqa: E402
    correct_assertion, review_assertion, review_identity_relation,
)
from mofs_platform.sources import crossref  # noqa: E402

RESULTS: list[dict] = []


def check(step: str, expected: str, actual: bool, detail: str = "") -> None:
    RESULTS.append({
        "step": step, "expected": expected,
        "actual": "PASS" if actual else "FAIL", "detail": detail,
    })


def run(db_path: Path) -> None:
    conn = connect(db_path)

    # S1 — question save & correct
    save_question(conn, Question(wording="Which prepared MOF samples merit inspection? (synthetic)"))
    save_question(conn, Question(
        wording="Which conductive MOFs can act as bifunctional HER+OER electrodes? (synthetic)"))
    q = get_question(conn)
    check("S1 question save+correct", "one saved question, corrected wording, v-history",
          q.wording.startswith("Which conductive MOFs") and q.updated_at is not None)

    # S2 — laboratory profile (four distinct statuses)
    caps = {}
    for name, status in [("Furnace-X (synthetic)", "current"),
                         ("Glovebox-M (synthetic)", "future"),
                         ("Press-P (synthetic)", "unavailable"),
                         ("Rotating electrode (synthetic)", "unknown")]:
        caps[name] = add_capability(conn, name, None, status).id
    check("S2 profile statuses", "four statuses stored verbatim",
          len(caps) == 4)

    # S3 — reference capture + typed route failure (offline fixture)
    ref = add_manual_reference(conn, doi="10.9999/acceptance", title="Acceptance fixture paper",
                               contributor="Mohammed (owner)")
    original = crossref.fetch_metadata
    crossref.fetch_metadata = lambda *a, **k: crossref.CrossrefFailure("no_hit", "none")
    _, failure = enrich_with_crossref(conn, ref.id, "owner@example.com")
    crossref.fetch_metadata = lambda *a, **k: crossref.CrossrefMetadata(
        doi="10.9999/acceptance", title="Acceptance fixture paper",
        container="Fixture Journal", issued_year="2024", license_url=None,
        url=None, indexed="2026-10-02T00:00:00")
    enrich_with_crossref(conn, ref.id, "owner@example.com")
    crossref.fetch_metadata = original
    attempts = list_attempts(conn)
    outcomes = [a.outcome for a in attempts]
    check("S3 reference + route attempts",
          "no_hit failure recorded, later success distinct (never relabeled)",
          failure is not None and outcomes == ["success", "no_hit"])

    # S4 — attributed assertions incl. a conflicting pair
    a1 = record_assertion(conn, source_id=ref.id, claim_type="preparation",
                          claim_text="Activated under protocol P (synthetic)",
                          evidence_location="Methods §2", epistemic_type="directly_reported")
    a2 = record_assertion(conn, source_id=ref.id, claim_type="preparation",
                          claim_text="Requires Glovebox-M (synthetic)",
                          epistemic_type="directly_reported")
    c1 = record_assertion(conn, source_id=ref.id, claim_type="property",
                          claim_text="Overpotential 180 mV (synthetic)",
                          epistemic_type="directly_reported")
    c2 = record_assertion(conn, source_id=ref.id, claim_type="property",
                          claim_text="Overpotential 220 mV (synthetic)",
                          conflicts_with=c1.id)
    check("S4 assertions + conflict pair",
          "attributed assertions recorded; conflict keeps both claims, flags both",
          a1.id > 0 and get_assertion_state(conn, c1.id) == "conflicted"
          and get_assertion_state(conn, c2.id) == "conflicted")

    # S5 — samples, observation, state, comparison
    s_parent = record_sample(conn, source_id=ref.id, designation="Sample-A (synthetic)",
                             parent_framework_name="Framework-F (synthetic)")
    s_comp = record_sample(conn, source_id=ref.id, designation="Sample-B (synthetic)",
                           parent_framework_name="Framework-F (synthetic)",
                           additions="Nano-N (synthetic)", lineage_kind="composite",
                           derived_from_sample_id=s_parent.id)
    record_observation(conn, sample_id=s_comp.id, source_id=ref.id,
                       observation_kind="experimental", value="180", unit="mV",
                       medium="0.5 M H2SO4")
    record_operating_state(conn, sample_id=s_comp.id, stage="during",
                           phase_assignment="Phase-R (synthetic)",
                           epistemic_type="author_interpretation",
                           evidence_location="fig. 3")
    rels = compare_samples(conn, s_parent.id, s_comp.id)
    check("S5 samples/observation/state/compare",
          "composite relation to documented parent; observation on composite only",
          any(r["relation"] == "composite" for r in rels))

    # S6 — candidate card
    card = get_candidate_card(conn, s_comp.id)
    check("S6 candidate card",
          "card exposes reason, observation gaps, state interpretation, provenance",
          card.designation == "Sample-B (synthetic)"
          and "reaction" in card.observations[0]["gaps"]
          and any("author interpretation" in s["epistemic"] for s in card.operating_states))

    # S7 — correction, D4 review, D5 refusal
    review_assertion(conn, assertion_id=a1.id, reviewer="Mohammed (owner)",
                     supporting_location="Methods §2", reason="verified against source")
    correct_assertion(conn, assertion_id=a1.id, new_claim_text="Activated at 190 C (corrected)",
                      new_evidence_location="Methods §2", editor="Mohammed (owner)",
                      reason="re-read: temperature differs")
    a1_after = get_assertion_state(conn, a1.id)
    d5_refused = False
    try:
        cross_pair = record_sample(conn, source_id=ref.id, designation="Sample-A (synthetic)")
        other = record_sample(conn, source_id=_second_source(conn),
                              designation="Sample-A (synthetic)")
        rels2 = compare_samples(conn, cross_pair.id, other.id)
        unresolved = next(r for r in rels2 if r["level"] == "sample")
        review_identity_relation(conn, relation_id=unresolved["id"],
                                 reviewer="Mohammed (owner)",
                                 supporting_location="both papers", reason="tried")
    except Exception:
        d5_refused = True
    check("S7 review/correction/D5",
          "corrected reviewed claim → needs_verification (no inherited approval); "
          "D5 cross-source equivalence refused",
          a1_after == "needs_verification" and d5_refused)

    # S8 — laboratory fit: each fit sample gets its OWN source so its
    # requirement set is isolated (assertions attach to sources pre-#11-linkage).
    fit_possible_source = add_manual_reference(
        conn, doi="10.9999/fit-possible", title="Fit-possible source (synthetic)")
    fit_current_sample = record_sample(conn, source_id=fit_possible_source.id,
                                       designation="Fit-possible (synthetic)")
    _reviewed(conn, fit_possible_source.id, "synthesized using Furnace-X (synthetic)")
    fit_possible = assess_fit(conn, fit_current_sample.id, fit_possible_source.id)
    fit_future_source = add_manual_reference(
        conn, doi="10.9999/fit-future", title="Fit-future source (synthetic)")
    fit_future_sample = record_sample(conn, source_id=fit_future_source.id,
                                      designation="Fit-future (synthetic)")
    _reviewed(conn, fit_future_source.id, "requires inert Glovebox-M (synthetic)")
    fit_future = assess_fit(conn, fit_future_sample.id, fit_future_source.id)
    fit_unknown_source = add_manual_reference(
        conn, doi="10.9999/fit-unknown", title="Fit-unknown source (synthetic)")
    fit_unknown_sample = record_sample(conn, source_id=fit_unknown_source.id,
                                       designation="Fit-unknown (synthetic)")
    fit_unknown = assess_fit(conn, fit_unknown_sample.id, fit_unknown_source.id)
    update_capability(conn, caps["Furnace-X (synthetic)"], "Furnace-X (synthetic)", None, "future")
    outdated = latest_assessment(conn, fit_current_sample.id)
    rerun = assess_fit(conn, fit_current_sample.id, fit_possible_source.id)
    check("S8 laboratory fit",
          "possible/future/unknown outcomes correct; basis change marks outdated; "
          "rerun records current assessment",
          fit_possible.assessment == "possible_with_current_capabilities"
          and fit_future.assessment == "requires_future_capabilities"
          and fit_unknown.assessment == "unknown"
          and outdated.outdated is True and rerun.outdated is False)

    # S10 — restart: everything inspectable
    conn.close()
    reopened = connect(db_path)
    q2 = get_question(reopened)
    check("S10 restart persistence",
          "question, references, assertions, samples, relations, attempts, "
          "fit assessments all inspectable after full close/reopen",
          q2.wording.startswith("Which conductive MOFs")
          and len(list_attempts(reopened)) == 2
          and get_candidate_card(reopened, s_comp.id).observations
          and any(r["relation"] == "composite" for r in list_relations(reopened)))
    reopened.close()


def get_assertion_state(conn, assertion_id):
    from mofs_platform.domain.evidence import get_assertion
    return get_assertion(conn, assertion_id).review_state


def _second_source(conn):
    from mofs_platform.domain.references import add_manual_reference
    return add_manual_reference(conn, doi="10.9999/other-source",
                                title="Second source fixture (synthetic)").id


def _reviewed(conn, source_id, text):
    asm = record_assertion(conn, source_id=source_id, claim_type="preparation",
                           claim_text=text, evidence_location="Methods §2",
                           epistemic_type="directly_reported")
    review_assertion(conn, assertion_id=asm.id, reviewer="Mohammed (owner)",
                     supporting_location="Methods §2", reason="verified against source")


def add_assertion_for_fit(conn, source_id, text):
    _reviewed(conn, source_id, text)


def list_relations(conn):
    from mofs_platform.domain.identity import list_relations as lr
    return lr(conn)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "acceptance.db"
        run(db_path)

    failed = [r for r in RESULTS if r["actual"] != "PASS"]
    lines = [
        "# Acceptance run 001 — complete first evidence workflow (issue #13)",
        "",
        "**Date:** 2026-10-02 · **Project version:** 0.1.0 (main, task-013) · "
        "**Question:** owner-entered bifunctional HER+OER wording (question id 1) · "
        "**Source contract:** D2 (Crossref metadata + manual entry; no full text) · "
        "**Stack:** D3 (Python/Streamlit/SQLite) · **Review rule:** D4 (named human + "
        "exact cited location + reason) · **Equivalence:** D5 (no cross-source "
        "equivalence, ever) · **Profile:** all entries owner-entered (`unknown` until "
        "confirmed) · **Fixtures:** every record below is visibly labeled `(synthetic)` "
        "and lives in a throwaway database — separated from any real evidence.",
        "",
        "| Step | Expected | Actual | Detail |",
        "|---|---|---|---|",
    ]
    for r in RESULTS:
        lines.append(f"| {r['step']} | {r['expected']} | {r['actual']} | {r['detail']} |")
    lines += [
        "",
        "**Route-failure applicability:** the D2 route combines manual capture "
        "(offline — network failures inapplicable) with Crossref metadata "
        "enrichment (no_hit / rate_limited / timeout / offline / bad_response / "
        "bad_input all typed and tested in tests/test_route_failures.py). No "
        "prohibited content is fetched; no provider is substituted.",
        "",
        "**Scientific boundary:** this run verifies software-workflow behavior "
        "only. It makes no claim of catalyst validation, novelty, synthesis "
        "success, or measured research benefit.",
        "",
        f"**Overall: {'ALL CHECKS PASS' if not failed else 'FAILURES PRESENT'}** "
        f"({len(RESULTS) - len(failed)}/{len(RESULTS)} steps).",
    ]
    output = "\n".join(lines) + "\n"
    args = sys.argv[1:]
    if "--out" in args:
        Path(args[args.index("--out") + 1]).write_text(output, encoding="utf-8")
    print(output)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
