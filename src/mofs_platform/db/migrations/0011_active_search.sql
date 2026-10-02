-- 0011: active search (issue #16, D9: Crossref + OpenAlex). Every run is
-- recorded with the exact query text and a typed outcome; hits are stored as
-- leads (needs_verification) that can be dismissed with a recorded reason or
-- captured into the attributed reference flow. HER and OER title tokens are
-- stored separately per hit — a bifunctional question never collapses the
-- two evidence streams into one verdict.
CREATE TABLE search_run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL CHECK (provider IN ('crossref', 'openalex')),
    query_text TEXT NOT NULL,
    scope TEXT NOT NULL CHECK (scope IN ('owner_question_verbatim', 'owner_edited')),
    outcome TEXT NOT NULL CHECK (outcome IN ('success', 'no_hit', 'rate_limited',
                                             'timeout', 'offline', 'bad_response', 'bad_input')),
    result_count INTEGER NOT NULL DEFAULT 0,
    next_step TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE search_hit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES search_run(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider IN ('crossref', 'openalex')),
    doi TEXT,
    title TEXT,
    issued_year TEXT,
    container TEXT,
    her_token INTEGER NOT NULL DEFAULT 0 CHECK (her_token IN (0, 1)),
    oer_token INTEGER NOT NULL DEFAULT 0 CHECK (oer_token IN (0, 1)),
    status TEXT NOT NULL DEFAULT 'needs_verification'
        CHECK (status IN ('needs_verification', 'dismissed', 'captured')),
    dismissed_by TEXT,
    dismiss_reason TEXT,
    captured_source_id INTEGER REFERENCES source(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
