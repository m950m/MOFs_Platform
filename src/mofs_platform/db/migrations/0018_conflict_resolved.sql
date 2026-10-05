-- 0018: fix the resolve-conflict dead end (strict-audit BLOCKING finding).
-- resolve_conflict writes action 'conflict_resolved', which the review_event
-- CHECK (0008, extended 0010/0017) forbids — every resolution attempt failed
-- at persist time and the UI path was a dead end. The CHECK is extended via
-- the rebuild pattern; the append-only history is preserved.
CREATE TABLE review_event_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('assertion', 'identity_relation', 'sample_record', 'reference_number')),
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('corrected', 'reviewed', 'review_rejected', 'conflict_resolved')),
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
