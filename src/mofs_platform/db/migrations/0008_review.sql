-- 0008: attributed review and correction (issue #11). Every correction or
-- review appends an event with the previous state; a correction of reviewed
-- content returns it to needs_verification (no inherited approvals).
CREATE TABLE review_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('assertion', 'identity_relation')),
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
