"""Z.ai GLM chat adapter — the D10 owner contract (issue #15, optional).

First AI provider for question refinement: OpenAI-compatible chat completions
endpoint. The adapter sends ONLY the question fields the caller passes —
nothing else from the database ever leaves the machine. The model must reply
with strict JSON; anything else is a typed failure. Failures mirror the
shared vocabulary plus `no_key`. The optional `transport` parameter injects
httpx.MockTransport in tests so the suite never touches the live API.

The API key is supplied per call by the UI (session-only) or the
MOFS_AI_API_KEY environment variable — it is never persisted anywhere.
"""

import json
import re
from dataclasses import dataclass

import httpx

BASE_URL = "https://api.z.ai/api/paas/v4/chat/completions"
MODEL = "glm-4.6"
DEFAULT_TIMEOUT = 30.0

FAILURE_KINDS = (
    "no_key", "bad_input", "timeout", "offline", "rate_limited", "bad_response",
)

_REFINEMENT_FIELDS = (
    "wording", "reactions", "material_classes", "conditions",
    "hard_requirements", "preferences", "meaning_of_improvement",
)

_SYSTEM_PROMPT = (
    "You help a materials-science researcher refine an electrochemistry "
    "research question. Reply with STRICT JSON only (no markdown, no prose): "
    '{"wording": "...", "reactions": "...", "material_classes": "...", '
    '"conditions": "...", "hard_requirements": "...", "preferences": "...", '
    '"meaning_of_improvement": "...", "notes": "one short paragraph: why each '
    "change improves precision\"}. Rules: keep the researcher's scientific "
    "meaning; replace vague terms with precise, defined wording; propose "
    "values for unknown fields ONLY as clearly marked suggestions; never "
    "invent hard requirements; leave a field as an empty string if you have "
    "no suggestion for it."
)


@dataclass(frozen=True)
class GLMRefinement:
    suggestions: dict[str, str]
    notes: str | None


@dataclass(frozen=True)
class GLMFailure:
    kind: str
    detail: str = ""


def _parse_content(content: str) -> GLMRefinement | GLMFailure:
    text = content.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return GLMFailure("bad_response", f"Assistant reply was not valid JSON. ({exc})")
    if not isinstance(data, dict) or not isinstance(data.get("wording"), str):
        return GLMFailure(
            "bad_response", "Assistant reply JSON lacked a wording string."
        )
    suggestions = {}
    for field in _REFINEMENT_FIELDS:
        value = data.get(field)
        if isinstance(value, str) and value.strip():
            suggestions[field] = value.strip()
    notes = data.get("notes")
    return GLMRefinement(
        suggestions=suggestions,
        notes=notes.strip() if isinstance(notes, str) and notes.strip() else None,
    )


def suggest_refinement(
    question_fields: dict[str, str | None],
    api_key: str | None,
    timeout: float = DEFAULT_TIMEOUT,
    transport: httpx.BaseTransport | None = None,
    model: str = MODEL,
) -> GLMRefinement | GLMFailure:
    """POST one chat completion (OpenAI-compatible). Returns the parsed
    refinement or a typed failure. The caller owns the key and the enable
    decision — the adapter never persists either."""
    if not api_key or not api_key.strip():
        return GLMFailure(
            "no_key", "No API key configured for this session — nothing was sent."
        )
    clean_fields = {
        k: (v.strip() if isinstance(v, str) else "") for k, v in question_fields.items()
    }
    if not clean_fields.get("wording"):
        return GLMFailure("bad_input", "The saved question has no wording to refine.")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(clean_fields, ensure_ascii=False)},
        ],
        "temperature": 0.2,
    }
    try:
        with httpx.Client(timeout=timeout, transport=transport) as client:
            response = client.post(
                BASE_URL,
                json=payload,
                headers={"Authorization": f"Bearer {api_key.strip()}"},
            )
    except httpx.TimeoutException as exc:
        return GLMFailure("timeout", f"The assistant did not respond in time. ({exc})")
    except httpx.ConnectError as exc:
        return GLMFailure("offline", f"Could not reach the assistant endpoint. ({exc})")
    except httpx.HTTPError as exc:
        return GLMFailure("bad_response", f"HTTP problem talking to the assistant. ({exc})")

    if response.status_code == 429:
        return GLMFailure("rate_limited", "Assistant rate limit hit — retry later.")
    if response.status_code != 200:
        return GLMFailure(
            "bad_response", f"Assistant returned HTTP {response.status_code}."
        )
    try:
        content = response.json()["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001 - any malformed body is a bad response
        return GLMFailure(
            "bad_response", f"Assistant body had an unexpected shape. ({exc})"
        )
    if not isinstance(content, str):
        return GLMFailure("bad_response", "Assistant content was not text.")
    return _parse_content(content)
