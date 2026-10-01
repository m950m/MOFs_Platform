-- 0005: attributed evidence assertions (issue #7). Each assertion carries its
-- own evidence pointer, epistemic type, and review state. Recording never
-- marks an assertion reviewed; conflicts keep both claims side by side.
CREATE TABLE assertion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES source(id) ON DELETE CASCADE,
    claim_type TEXT NOT NULL CHECK (claim_type IN ('preparation', 'composition', 'property', 'application', 'other')),
    claim_text TEXT NOT NULL,
    evidence_location TEXT,
    extraction_author TEXT,
    epistemic_type TEXT NOT NULL CHECK (epistemic_type IN ('directly_reported', 'author_interpretation', 'tool_inference', 'user_judgment', 'unknown')),
    review_state TEXT NOT NULL DEFAULT 'needs_verification' CHECK (review_state IN ('needs_verification', 'in_review', 'reviewed', 'conflicted')),
    conflicts_with INTEGER REFERENCES assertion(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE assertion_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL CHECK (action IN ('recorded', 'flagged_conflict')),
    assertion_id INTEGER NOT NULL REFERENCES assertion(id) ON DELETE CASCADE,
    previous_json TEXT,
    updated_json TEXT NOT NULL
);
