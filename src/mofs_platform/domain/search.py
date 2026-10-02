"""Active search domain (issue #16, D9: Crossref + OpenAlex).

The tool searches the owner-approved metadata sources using queries derived
from the saved question and displays leads. A lead is never a verified
candidate: every hit starts `needs_verification`, HER and OER title tokens
are stored separately (a bifunctional question never collapses into one
verdict), and dismissal/capture are attributed. Failed runs stay failed —
every retry is a manual researcher action, and `no_hit` never means
"the material is unstudied".
"""

import sqlite3
from dataclasses import dataclass

from mofs_platform.sources import crossref, openalex
from mofs_platform.sources.search_common import PROVIDERS, SearchFailure

NEXT_STEPS = {
    "success": "Inspect the hits below; capture what merits a reference — a hit is a lead only.",
    "no_hit": "Rephrase the query or try the other provider — absence of a "
              "provider record is not evidence of novelty.",
    "rate_limited": "Wait and retry later (polite-pool limits apply).",
    "timeout": "Retry manually when the network is stable.",
    "offline": "Restore connectivity; retry manually.",
    "bad_response": "Retry later; the run was recorded as failed.",
    "bad_input": "Correct the query text and run again.",
}


class SearchValidationError(ValueError):
    """The proposed search/dismissal/capture cannot be applied."""


class SearchPersistenceError(RuntimeError):
    """Saving failed; previously saved records are unchanged."""


@dataclass(frozen=True)
class SearchRun:
    id: int
    provider: str
    query_text: str
    scope: str
    outcome: str
    result_count: int
    next_step: str | None
    created_at: str


@dataclass(frozen=True)
class StoredHit:
    id: int
    run_id: int
    provider: str
    doi: str | None
    title: str | None
    issued_year: str | None
    container: str | None
    her_token: bool
    oer_token: bool
    status: str
    dismissed_by: str | None
    dismiss_reason: str | None
    captured_source_id: int | None
    created_at: str


def _row_to_run(row: sqlite3.Row) -> SearchRun:
    return SearchRun(
        id=row["id"], provider=row["provider"], query_text=row["query_text"],
        scope=row["scope"], outcome=row["outcome"], result_count=row["result_count"],
        next_step=row["next_step"], created_at=row["created_at"],
    )


def _row_to_hit(row: sqlite3.Row) -> StoredHit:
    return StoredHit(
        id=row["id"], run_id=row["run_id"], provider=row["provider"],
        doi=row["doi"], title=row["title"], issued_year=row["issued_year"],
        container=row["container"], her_token=bool(row["her_token"]),
        oer_token=bool(row["oer_token"]), status=row["status"],
        dismissed_by=row["dismissed_by"], dismiss_reason=row["dismiss_reason"],
        captured_source_id=row["captured_source_id"], created_at=row["created_at"],
    )


def derive_query(question_wording: str) -> dict:
    """Transparent query derivation: the saved question's wording, verbatim.
    The UI shows this mapping — no invented terms, no hidden rewriting."""
    clean = (question_wording or "").strip()
    if not clean:
        raise SearchValidationError(
            "No saved question wording to derive a query from — save the "
            "question first."
        )
    return {"query": clean, "scope": "owner_question_verbatim"}


def prepare_query(provider: str, query_text: str) -> str:
    """Provider-specific, transparent normalization. OpenAlex treats '?'
    and '*' as wildcard operators in its stemmed search and rejects queries
    containing them (live finding, issue #16 smoke), so they are removed
    before sending. The recorded query_text is always the exact text that
    was sent — derivation stays auditable."""
    clean = (query_text or "").strip()
    if provider == "openalex":
        clean = clean.replace("?", "").replace("*", "").strip()
    return clean


def _adapter(provider: str, query: str, mailto: str | None):
    if provider == "crossref":
        return crossref.search_works(query, mailto)
    if provider == "openalex":
        return openalex.search_works(query, mailto)
    raise SearchValidationError(
        f"Provider must be one of {PROVIDERS!r} (decision D9) — got {provider!r}."
    )


def run_active_search(
    conn: sqlite3.Connection, provider: str, query_text: str, scope: str,
    mailto: str | None = None,
) -> tuple[SearchRun | None, SearchFailure | None]:
    """Run one search against a D9 provider and record the run (and its hits
    on success) in one transaction. scope is 'owner_question_verbatim' or
    'owner_edited' — the caller states which, and the stored query_text is
    the exact text that was sent."""
    if provider not in PROVIDERS:
        raise SearchValidationError(
            f"Provider must be one of {PROVIDERS!r} (decision D9) — got {provider!r}."
        )
    clean_query = prepare_query(provider, query_text)
    if not clean_query:
        raise SearchValidationError(
            "The search query is empty after provider normalization — enter or "
            "derive one first."
        )
    if scope not in ("owner_question_verbatim", "owner_edited"):
        raise SearchValidationError(f"Unknown query scope {scope!r}.")

    result = _adapter(provider, clean_query, mailto)
    if isinstance(result, SearchFailure):
        try:
            with conn:
                cur = conn.execute(
                    "INSERT INTO search_run (provider, query_text, scope, outcome, "
                    "result_count, next_step) VALUES (?, ?, ?, ?, 0, ?)",
                    (provider, clean_query, scope, result.kind, NEXT_STEPS[result.kind]),
                )
                run_id = int(cur.lastrowid)
        except sqlite3.Error as exc:
            raise SearchPersistenceError(
                f"Recording the failed run failed; nothing was recorded. ({exc})"
            ) from exc
        row = conn.execute("SELECT * FROM search_run WHERE id = ?", (run_id,)).fetchone()
        return _row_to_run(row), result

    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO search_run (provider, query_text, scope, outcome, "
                "result_count, next_step) VALUES (?, ?, ?, 'success', ?, ?)",
                (provider, clean_query, scope, len(result), NEXT_STEPS["success"]),
            )
            run_id = int(cur.lastrowid)
            for hit in result:
                conn.execute(
                    "INSERT INTO search_hit (run_id, provider, doi, title, issued_year, "
                    "container, her_token, oer_token) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, provider, hit.doi, hit.title, hit.issued_year,
                     hit.container, int(hit.her_token), int(hit.oer_token)),
                )
    except sqlite3.Error as exc:
        raise SearchPersistenceError(
            f"Saving the search run failed; nothing was recorded. ({exc})"
        ) from exc
    row = conn.execute("SELECT * FROM search_run WHERE id = ?", (run_id,)).fetchone()
    return _row_to_run(row), None


def list_runs(conn: sqlite3.Connection, limit: int = 20) -> list[SearchRun]:
    rows = conn.execute(
        "SELECT * FROM search_run ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [_row_to_run(row) for row in rows]


def list_hits(conn: sqlite3.Connection, run_id: int) -> list[StoredHit]:
    rows = conn.execute(
        "SELECT * FROM search_hit WHERE run_id = ? ORDER BY id", (run_id,)
    ).fetchall()
    return [_row_to_hit(row) for row in rows]


def get_hit(conn: sqlite3.Connection, hit_id: int) -> StoredHit | None:
    row = conn.execute("SELECT * FROM search_hit WHERE id = ?", (hit_id,)).fetchone()
    return None if row is None else _row_to_hit(row)


def dismiss_hit(
    conn: sqlite3.Connection, hit_id: int, dismissed_by: str | None, reason: str | None
) -> StoredHit:
    """Dismiss a lead with a recorded, attributed reason. Dismissed leads
    stay in the table — dismissal is auditable, never a deletion."""
    row = conn.execute("SELECT * FROM search_hit WHERE id = ?", (hit_id,)).fetchone()
    if row is None:
        raise SearchValidationError(f"Hit #{hit_id} does not exist.")
    if row["status"] == "captured":
        raise SearchValidationError(
            f"Hit #{hit_id} was already captured as reference "
            f"#{row['captured_source_id']} — dismissals do not undo captures."
        )
    if row["status"] == "dismissed":
        raise SearchValidationError(
            f"Hit #{hit_id} is already dismissed by {row['dismissed_by']} "
            f"({row['dismiss_reason']}) — the recorded attribution stays."
        )
    clean_by = (dismissed_by or "").strip()
    clean_reason = (reason or "").strip()
    missing = [name for name, value in (
        ("who is dismissing", clean_by), ("dismissal reason", clean_reason)
    ) if not value]
    if missing:
        raise SearchValidationError(
            "Dismissal rejected — missing: " + "; ".join(missing) + "."
        )
    try:
        with conn:
            conn.execute(
                "UPDATE search_hit SET status = 'dismissed', dismissed_by = ?, "
                "dismiss_reason = ? WHERE id = ?",
                (clean_by, clean_reason, hit_id),
            )
    except sqlite3.Error as exc:
        raise SearchPersistenceError(
            f"Saving the dismissal failed; the hit is unchanged. ({exc})"
        ) from exc
    return get_hit(conn, hit_id)


def capture_hit(
    conn: sqlite3.Connection, hit_id: int, contributor: str | None
) -> tuple[StoredHit, int]:
    """Capture a hit into the attributed reference flow. The reference's
    supplied passage records the search provenance (provider, run, exact
    query) so the lead's origin stays auditable. Re-capturing a DOI that
    already exists updates that reference (existing re-capture semantics)."""
    from mofs_platform.domain.references import add_manual_reference

    hit = get_hit(conn, hit_id)
    if hit is None:
        raise SearchValidationError(f"Hit #{hit_id} does not exist.")
    if hit.status == "dismissed":
        raise SearchValidationError(
            f"Hit #{hit_id} was dismissed ({hit.dismiss_reason}) — un-dismissal "
            "is not supported; run the search again."
        )
    if hit.status == "captured" and hit.captured_source_id is not None:
        return hit, hit.captured_source_id  # idempotent
    clean_contributor = (contributor or "").strip()
    if not clean_contributor:
        raise SearchValidationError("Capture rejected — missing: who is capturing.")
    run = conn.execute(
        "SELECT query_text, provider FROM search_run WHERE id = ?", (hit.run_id,)
    ).fetchone()
    provenance = (
        f"Captured from {hit.provider} active search run #{hit.run_id} "
        f"(query: {run['query_text']})."
    )
    ref = add_manual_reference(
        conn,
        doi=hit.doi,
        title=hit.title,
        supplied_input=provenance,
        contributor=clean_contributor,
        inspected_level="metadata",
    )
    try:
        with conn:
            conn.execute(
                "UPDATE search_hit SET status = 'captured', captured_source_id = ? "
                "WHERE id = ?",
                (ref.id, hit_id),
            )
    except sqlite3.Error as exc:
        raise SearchPersistenceError(
            f"The reference was captured (#{ref.id}) but marking the hit failed "
            f"({exc}); the hit still shows needs_verification."
        ) from exc
    return get_hit(conn, hit_id), ref.id
