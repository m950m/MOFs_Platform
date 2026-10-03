"""Offline tests for the Z.ai GLM adapter (issue #15, D10).

The suite never touches the live API — every call uses an injected
httpx.MockTransport.
"""

import httpx

from mofs_platform.sources import glm


def _transport(handler):
    return httpx.MockTransport(handler)


def _ok_body(content: str) -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}]
    }


GOOD_JSON = (
    '{"wording": "Which conductive MOFs ...", "reactions": "HER, OER", '
    '"material_classes": "", "conditions": "1 M KOH", '
    '"hard_requirements": "", "preferences": "", '
    '"meaning_of_improvement": "", "notes": "adds the missing electrolyte."}'
)


def test_no_key_never_sends_anything():
    called = []

    def handler(request):
        called.append(request)
        return httpx.Response(200, json=_ok_body(GOOD_JSON))

    result = glm.suggest_refinement(
        {"wording": "Q"}, None, transport=_transport(handler)
    )
    assert result.kind == "no_key"
    assert called == []  # nothing left the machine


def test_bad_input_without_wording():
    result = glm.suggest_refinement({"wording": "  "}, "key")
    assert result.kind == "bad_input"


def test_success_parses_suggestions_and_notes():
    def handler(request):
        body = request.read()
        assert b"wording" in body  # only the question fields are sent
        return httpx.Response(200, json=_ok_body(GOOD_JSON))

    result = glm.suggest_refinement(
        {"wording": "Q", "reactions": None}, "key", transport=_transport(handler)
    )
    assert result.suggestions["wording"].startswith("Which conductive MOFs")
    assert result.suggestions["conditions"] == "1 M KOH"
    assert "electrolyte" in result.notes
    assert "material_classes" not in result.suggestions  # empty string dropped


def test_success_handles_markdown_fences():
    fenced = "```json\n" + GOOD_JSON + "\n```"

    def handler(request):
        return httpx.Response(200, json=_ok_body(fenced))

    result = glm.suggest_refinement({"wording": "Q"}, "key", transport=_transport(handler))
    assert result.suggestions["reactions"] == "HER, OER"


def test_malformed_reply_is_bad_response():
    def handler(request):
        return httpx.Response(200, json=_ok_body("I suggest you... (prose, not JSON)"))

    result = glm.suggest_refinement({"wording": "Q"}, "key", transport=_transport(handler))
    assert result.kind == "bad_response"


def test_http_and_transport_failures():
    def limited(request):
        return httpx.Response(429)

    result = glm.suggest_refinement({"wording": "Q"}, "k", transport=_transport(limited))
    assert result.kind == "rate_limited"

    def timeout_handler(request):
        raise httpx.TimeoutException("slow")

    result = glm.suggest_refinement({"wording": "Q"}, "k", transport=_transport(timeout_handler))
    assert result.kind == "timeout"

    def offline_handler(request):
        raise httpx.ConnectError("down")

    result = glm.suggest_refinement({"wording": "Q"}, "k", transport=_transport(offline_handler))
    assert result.kind == "offline"
