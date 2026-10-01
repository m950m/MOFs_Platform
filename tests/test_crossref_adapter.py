"""Offline tests for the Crossref adapter (issue #6) — httpx.MockTransport only.

The guard test at the bottom asserts no test in this suite constructs a live
HTTP client; the only permitted injection point is `transport=`.
"""

import json
from pathlib import Path

import httpx

from mofs_platform.sources import crossref

FIXTURE = Path(__file__).resolve().parents[1] / "src" / "mofs_platform" / "sources" / "fixtures" / "crossref_doi_ok.json"
DOI = "10.1016/j.matt.2021.02.015"


def _transport(handler) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def test_maps_real_fixture_fields_offline():
    body = json.loads(FIXTURE.read_text(encoding="utf-8"))
    message = body["message"]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.crossref.org"
        assert "mailto=" in str(request.url)  # polite pool
        return httpx.Response(200, json=body)

    result = crossref.fetch_metadata(DOI, "owner@example.com", transport=_transport(handler))
    assert isinstance(result, crossref.CrossrefMetadata)
    assert result.doi == DOI
    assert result.title == (message.get("title") or [None])[0]
    assert result.url == message.get("URL")


def test_missing_optional_fields_become_none():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok", "message": {"DOI": DOI}})

    result = crossref.fetch_metadata(DOI, "owner@example.com", transport=_transport(handler))
    assert isinstance(result, crossref.CrossrefMetadata)
    assert result.title is None
    assert result.container is None
    assert result.issued_year is None
    assert result.license_url is None


def test_404_maps_to_no_hit():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"status": "error"})

    result = crossref.fetch_metadata(DOI, "owner@example.com", transport=_transport(handler))
    assert result == crossref.CrossrefFailure("no_hit", f"No Crossref record for DOI {DOI}.")


def test_429_maps_to_rate_limited():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429)

    result = crossref.fetch_metadata(DOI, "owner@example.com", transport=_transport(handler))
    assert result.kind == "rate_limited"


def test_500_maps_to_bad_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    result = crossref.fetch_metadata(DOI, "owner@example.com", transport=_transport(handler))
    assert result.kind == "bad_response"


def test_timeout_maps_to_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("too slow", request=request)

    result = crossref.fetch_metadata(DOI, "owner@example.com", transport=_transport(handler))
    assert result.kind == "timeout"


def test_connect_error_maps_to_offline():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route", request=request)

    result = crossref.fetch_metadata(DOI, "owner@example.com", transport=_transport(handler))
    assert result.kind == "offline"


def test_empty_doi_is_bad_input():
    result = crossref.fetch_metadata("   ", "owner@example.com")
    assert result.kind == "bad_input"


def test_guard_no_test_constructs_a_live_http_client():
    """The suite must never go live: only `transport=` injection is allowed."""
    needle = "httpx." + "Client("  # split so this guard does not match itself
    test_dir = Path(__file__).resolve().parent
    offenders = []
    for path in test_dir.glob("test_*.py"):
        if needle in path.read_text(encoding="utf-8"):
            offenders.append(path.name)
    assert offenders == []
