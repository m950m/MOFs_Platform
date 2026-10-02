"""Crossref REST adapter — the D2 owner contract: metadata enrichment only.

Permitted content: bibliographic metadata (title, container, issued year,
license URL, link, indexed timestamp). A result is a metadata lead — it never
establishes experimental preparation, sample identity, or measured activity.
Failures are typed; "no_hit" never means "the material is unstudied".

The optional `transport` parameter injects httpx.MockTransport in tests so the
suite never touches the live API.
"""

import re
from dataclasses import dataclass

import httpx

BASE_URL = "https://api.crossref.org/works/"
DEFAULT_TIMEOUT = 10.0

FAILURE_KINDS = ("no_hit", "rate_limited", "timeout", "offline", "bad_response", "bad_input")


@dataclass(frozen=True)
class CrossrefMetadata:
    doi: str | None
    title: str | None
    container: str | None
    issued_year: str | None
    license_url: str | None
    url: str | None
    indexed: str | None


@dataclass(frozen=True)
class CrossrefFailure:
    kind: str
    detail: str = ""


def _first(values) -> str | None:
    if isinstance(values, list) and values and isinstance(values[0], str):
        return values[0]
    return None


def _map_message(doi: str, message: dict) -> CrossrefMetadata:
    issued = (message.get("issued") or {}).get("date-parts") or [[None]]
    year = issued[0][0] if issued and issued[0] else None
    licenses = message.get("license") or []
    license_url = licenses[0].get("URL") if licenses else None
    return CrossrefMetadata(
        doi=message.get("DOI") or doi,
        title=_first(message.get("title")),
        container=_first(message.get("container-title")),
        issued_year=str(year) if year is not None else None,
        license_url=license_url,
        url=message.get("URL"),
        indexed=(message.get("indexed") or {}).get("date-time"),
    )


def fetch_metadata(
    doi: str | None,
    mailto: str | None,
    timeout: float = DEFAULT_TIMEOUT,
    transport: httpx.BaseTransport | None = None,
) -> CrossrefMetadata | CrossrefFailure:
    """GET /works/{doi} (polite pool). Returns metadata or a typed failure."""
    if not doi or not doi.strip():
        return CrossrefFailure("bad_input", "DOI is empty.")
    clean = doi.strip()
    if not re.fullmatch(r"10\.\d{4,9}/\S+", clean):
        return CrossrefFailure(
            "bad_input", f"'{clean}' is not a syntactically valid DOI (expected 10.xxxx/...)."
        )
    try:
        with httpx.Client(timeout=timeout, transport=transport) as client:
            params = {"mailto": mailto} if mailto else None
            response = client.get(BASE_URL + clean, params=params)
    except httpx.TimeoutException as exc:
        return CrossrefFailure("timeout", f"Crossref did not respond in time. ({exc})")
    except httpx.ConnectError as exc:
        return CrossrefFailure("offline", f"Could not reach Crossref. ({exc})")
    except httpx.HTTPError as exc:
        return CrossrefFailure("bad_response", f"HTTP problem talking to Crossref. ({exc})")

    if response.status_code == 404:
        return CrossrefFailure("no_hit", f"No Crossref record for DOI {clean}.")
    if response.status_code == 429:
        return CrossrefFailure("rate_limited", "Crossref rate limit hit — back off and retry later.")
    if response.status_code != 200:
        return CrossrefFailure("bad_response", f"Crossref returned HTTP {response.status_code}.")
    try:
        message = response.json()["message"]
    except Exception as exc:  # noqa: BLE001 - any malformed body is a bad response
        return CrossrefFailure("bad_response", f"Crossref body was not valid metadata. ({exc})")
    if not isinstance(message, dict):
        return CrossrefFailure("bad_response", "Crossref body had an unexpected shape.")
    mapped = _map_message(clean, message)
    if mapped.doi and mapped.doi.strip().lower() != clean.lower():
        return CrossrefFailure(
            "bad_response",
            f"Provider record DOI '{mapped.doi}' does not match the requested "
            f"'{clean}' — nothing would be filled; verify the DOI.",
        )
    return mapped
