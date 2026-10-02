"""OpenAlex REST adapter — the D9 owner contract: metadata search only.

Permitted content: bibliographic metadata (title, container, issued year,
DOI) from https://api.openalex.org/works. A hit is a lead — it never
establishes experimental preparation, sample identity, or measured activity.
Failures are typed; "no_hit" never means "the material is unstudied".

The optional `transport` parameter injects httpx.MockTransport in tests so
the suite never touches the live API.
"""

from dataclasses import dataclass

import httpx

from mofs_platform.sources.search_common import (
    SearchFailure,
    SearchHit,
    normalize_doi,
    title_tokens,
)

SEARCH_URL = "https://api.openalex.org/works"
DEFAULT_TIMEOUT = 10.0

FAILURE_KINDS = ("no_hit", "rate_limited", "timeout", "offline", "bad_response", "bad_input")


@dataclass(frozen=True)
class OpenAlexMetadata:
    """Enrichment-shape metadata (title/container/year/url) so a captured
    hit can also be enriched later through the existing D2 route."""

    doi: str | None
    title: str | None
    container: str | None
    issued_year: str | None
    url: str | None


def _map_result(result: dict) -> SearchHit:
    title = result.get("display_name")
    her, oer = title_tokens(title)
    location = result.get("primary_location") or {}
    source = location.get("source") or {}
    return SearchHit(
        doi=normalize_doi(result.get("doi")),
        title=title,
        issued_year=str(result["publication_year"]) if result.get("publication_year") else None,
        container=source.get("display_name"),
        her_token=her,
        oer_token=oer,
    )


def search_works(
    query: str,
    mailto: str | None,
    timeout: float = DEFAULT_TIMEOUT,
    rows: int = 8,
    transport: httpx.BaseTransport | None = None,
) -> list[SearchHit] | SearchFailure:
    """GET /works?search=... (polite pool). Hit order is provider retrieval
    order — never a ranking claim."""
    if not query or not query.strip():
        return SearchFailure("bad_input", "The search query is empty.")
    if rows < 1 or rows > 25:
        return SearchFailure("bad_input", f"rows must be 1..25 — got {rows}.")
    try:
        with httpx.Client(timeout=timeout, transport=transport) as client:
            params = {"search": query, "per-page": str(rows)}
            if mailto:
                params["mailto"] = mailto
            response = client.get(SEARCH_URL, params=params)
    except httpx.TimeoutException as exc:
        return SearchFailure("timeout", f"OpenAlex did not respond in time. ({exc})")
    except httpx.ConnectError as exc:
        return SearchFailure("offline", f"Could not reach OpenAlex. ({exc})")
    except httpx.HTTPError as exc:
        return SearchFailure("bad_response", f"HTTP problem talking to OpenAlex. ({exc})")

    if response.status_code == 429:
        return SearchFailure("rate_limited", "OpenAlex rate limit hit — back off and retry later.")
    if response.status_code != 200:
        return SearchFailure("bad_response", f"OpenAlex returned HTTP {response.status_code}.")
    try:
        results = response.json()["results"]
    except Exception as exc:  # noqa: BLE001 - any malformed body is a bad response
        return SearchFailure("bad_response", f"OpenAlex body was not valid search output. ({exc})")
    if not isinstance(results, list):
        return SearchFailure("bad_response", "OpenAlex search body had an unexpected shape.")
    if not results:
        return SearchFailure("no_hit", "No OpenAlex records matched this query.")
    return [_map_result(result) for result in results]
