-- 0007: route attempts (issue #9). Every attempt against the selected source
-- route is recorded with its outcome and the contract-permitted next step, so
-- failures stay auditable and a later success never relabels an earlier one.
CREATE TABLE route_attempt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    target TEXT NOT NULL,
    attempt_kind TEXT NOT NULL CHECK (attempt_kind IN ('crossref_enrichment', 'manual_capture')),
    outcome TEXT NOT NULL CHECK (outcome IN ('success', 'no_hit', 'rate_limited', 'timeout', 'offline', 'bad_response', 'bad_input', 'restricted')),
    next_step TEXT,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
