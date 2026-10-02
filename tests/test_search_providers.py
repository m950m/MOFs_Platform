"""Offline adapter tests for active search (issue #16, D9).

Both providers are exercised through injected httpx.MockTransport — the
suite never touches the live APIs. The typed-failure vocabulary is shared
with the enrichment route (issue #9).
"""

import json

import httpx
import pytest

from mofs_platform.sources import crossref, openalex
from mofs_platform.sources.search_common import SearchFailure


def _transport(handler):
    return httpx.MockTransport(handler)


CROSSREF_BODY = {
    "message": {
        "items": [
            {
                "DOI": "10.9999/hit-1",
                "title": ["A conductive MOF for HER and OER"],
                "container-title": ["Journal of Synthetic Studies"],
                "issued": {"date-parts": [[2026]]},
            },
            {
                "DOI": "10.9999/hit-2",
                "title": ["Another MOF study"],
                "issued": {"date-parts": [[2025]]},
            },
        ]
    }
}

OPENALEX_BODY = {
    "results": [
        {
            "doi": "https://doi.org/10.9999/hit-1",
            "display_name": "A conductive MOF for HER and OER",
            "publication_year": 2026,
            "primary_location": {
                "source": {"display_name": "Journal of Synthetic Studies"}
            },
        }
    ]
}


def test_crossref_search_success_maps_hits_and_tokens():
    def handler(request):
        assert "query=bifunctional+MOF" in str(request.url)
        return httpx.Response(200, json=CROSSREF_BODY)

    result = crossref.search_works(
        "bifunctional MOF", None, transport=_transport(handler)
    )
    assert not isinstance(result, SearchFailure)
    assert result[0].doi == "10.9999/hit-1"
    assert result[0].title == "A conductive MOF for HER and OER"
    assert result[0].container == "Journal of Synthetic Studies"
    assert result[0].issued_year == "2026"
    assert result[0].her_token and result[0].oer_token  # both acronyms present
    assert not result[1].her_token and not result[1].oer_token


def test_crossref_search_no_hit_is_typed_not_novelty():
    def handler(request):
        return httpx.Response(200, json={"message": {"items": []}})

    result = crossref.search_works("obscure query", None, transport=_transport(handler))
    assert isinstance(result, SearchFailure) and result.kind == "no_hit"


@pytest.mark.parametrize("status,kind", [(429, "rate_limited"), (500, "bad_response")])
def test_crossref_search_http_failures(status, kind):
    def handler(request):
        return httpx.Response(status)

    result = crossref.search_works("q", None, transport=_transport(handler))
    assert isinstance(result, SearchFailure) and result.kind == kind


def test_crossref_search_timeout_and_offline():
    def timeout_handler(request):
        raise httpx.TimeoutException("too slow")

    result = crossref.search_works("q", None, transport=_transport(timeout_handler))
    assert isinstance(result, SearchFailure) and result.kind == "timeout"

    def offline_handler(request):
        raise httpx.ConnectError("no network")

    result = crossref.search_works("q", None, transport=_transport(offline_handler))
    assert isinstance(result, SearchFailure) and result.kind == "offline"


def test_crossref_search_bad_input_and_malformed_body():
    result = crossref.search_works("   ", None)
    assert isinstance(result, SearchFailure) and result.kind == "bad_input"

    def malformed(request):
        return httpx.Response(200, content=b"not-json")

    result = crossref.search_works("q", None, transport=_transport(malformed))
    assert isinstance(result, SearchFailure) and result.kind == "bad_response"


def test_openalex_search_success_normalizes_doi_and_tokens():
    def handler(request):
        assert "search=" in str(request.url)
        return httpx.Response(200, json=OPENALEX_BODY)

    result = openalex.search_works("bifunctional MOF", None, transport=_transport(handler))
    assert not isinstance(result, SearchFailure)
    assert result[0].doi == "10.9999/hit-1"  # https://doi.org/ prefix stripped
    assert result[0].issued_year == "2026"
    assert result[0].container == "Journal of Synthetic Studies"
    assert result[0].her_token and result[0].oer_token


def test_openalex_search_failures_match_shared_vocabulary():
    def no_hit(request):
        return httpx.Response(200, json={"results": []})

    result = openalex.search_works("q", None, transport=_transport(no_hit))
    assert isinstance(result, SearchFailure) and result.kind == "no_hit"

    def limited(request):
        return httpx.Response(429)

    result = openalex.search_works("q", None, transport=_transport(limited))
    assert isinstance(result, SearchFailure) and result.kind == "rate_limited"

    def malformed(request):
        return httpx.Response(200, json={"unexpected": json.dumps({})})

    result = openalex.search_works("q", None, transport=_transport(malformed))
    assert isinstance(result, SearchFailure) and result.kind == "bad_response"

    result = openalex.search_works("", None)
    assert isinstance(result, SearchFailure) and result.kind == "bad_input"


def test_openalex_search_timeout_and_offline():
    def timeout_handler(request):
        raise httpx.TimeoutException("too slow")

    result = openalex.search_works("q", None, transport=_transport(timeout_handler))
    assert isinstance(result, SearchFailure) and result.kind == "timeout"

    def offline_handler(request):
        raise httpx.ConnectError("no network")

    result = openalex.search_works("q", None, transport=_transport(offline_handler))
    assert isinstance(result, SearchFailure) and result.kind == "offline"
