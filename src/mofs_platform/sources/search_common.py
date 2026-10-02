"""Shared contract for active-search providers (issue #16, D9).

Both permitted providers (Crossref, OpenAlex) return the same SearchHit
shape and the same typed failure vocabulary as the enrichment route.
Provider hit order is retrieval order — never a ranking claim.
"""

from dataclasses import dataclass

FAILURE_KINDS = ("no_hit", "rate_limited", "timeout", "offline", "bad_response", "bad_input")

PROVIDERS = ("crossref", "openalex")

# Case-sensitive reaction acronyms (same convention as the hints rules):
# a token in the title is a metadata fact about the title, never evidence
# that the paper reports HER or OER measurements.
HER_TOKEN = "HER"
OER_TOKEN = "OER"


@dataclass(frozen=True)
class SearchHit:
    doi: str | None
    title: str | None
    issued_year: str | None
    container: str | None
    her_token: bool
    oer_token: bool


@dataclass(frozen=True)
class SearchFailure:
    kind: str
    detail: str = ""


def title_tokens(title: str | None) -> tuple[bool, bool]:
    text = title or ""
    return HER_TOKEN in text, OER_TOKEN in text


def normalize_doi(raw: str | None) -> str | None:
    """Strip a https://doi.org/ prefix; return the bare DOI or None."""
    if not raw:
        return None
    clean = raw.strip()
    lower = clean.lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi.org/"):
        if lower.startswith(prefix):
            clean = clean[len(prefix):]
            break
    return clean or None
