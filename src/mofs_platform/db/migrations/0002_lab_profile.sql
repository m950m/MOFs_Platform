-- 0002: laboratory capability profile (issue #5). A set of named capability
-- entries, each with one of four distinct statuses. The tool never seeds
-- equipment and never infers suitability; corrections append events.
CREATE TABLE lab_capability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK (status IN ('current', 'future', 'unavailable', 'unknown')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lab_profile_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL CHECK (action IN ('added', 'corrected')),
    capability_id INTEGER,
    previous_json TEXT,
    updated_json TEXT NOT NULL
);
