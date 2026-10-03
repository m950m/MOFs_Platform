-- 0013: AI refinement attempts (issue #15, D10: Z.ai GLM). The route_attempt
-- audit log gains attempt_kind 'ai_refinement' and outcome 'no_key' so every
-- assistant call is auditable like the other routes. Append-only history is
-- preserved through the table rebuild (SQLite cannot alter a CHECK in place).
CREATE TABLE route_attempt_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    target TEXT NOT NULL,
    attempt_kind TEXT NOT NULL CHECK (attempt_kind IN ('crossref_enrichment', 'manual_capture', 'ai_refinement')),
    outcome TEXT NOT NULL CHECK (outcome IN ('success', 'no_hit', 'rate_limited', 'timeout', 'offline', 'bad_response', 'bad_input', 'restricted', 'no_key')),
    next_step TEXT,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO route_attempt_new (id, provider, target, attempt_kind, outcome,
                               next_step, note, created_at)
SELECT id, provider, target, attempt_kind, outcome, next_step, note, created_at
FROM route_attempt;

DROP TABLE route_attempt;
ALTER TABLE route_attempt_new RENAME TO route_attempt;
