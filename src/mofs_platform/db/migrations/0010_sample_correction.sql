-- 0010: sample-record corrections (issue #20). The review_event log gains
-- entity_type 'sample_record'; the append-only history is preserved through
-- the table rebuild (SQLite cannot alter a CHECK constraint in place).
CREATE TABLE review_event_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('assertion', 'identity_relation', 'sample_record')),
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('corrected', 'reviewed', 'review_rejected')),
    reviewer TEXT,
    reason TEXT,
    supporting_location TEXT,
    threshold_note TEXT,
    previous_json TEXT,
    updated_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO review_event_new (id, entity_type, entity_id, action, reviewer, reason,
                              supporting_location, threshold_note, previous_json,
                              updated_json, created_at)
SELECT id, entity_type, entity_id, action, reviewer, reason,
       supporting_location, threshold_note, previous_json,
       updated_json, created_at
FROM review_event;

DROP TABLE review_event;
ALTER TABLE review_event_new RENAME TO review_event;
