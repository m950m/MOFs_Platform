-- 0001: research question (issue #4). One saved question (singleton row);
-- every save after the first appends a correction event. Fields left unset
-- stay NULL = unknown; the tool never fills scientific values.
CREATE TABLE question (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    wording TEXT NOT NULL,
    reactions TEXT,
    material_classes TEXT,
    conditions TEXT,
    hard_requirements TEXT,
    preferences TEXT,
    meaning_of_improvement TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE question_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL CHECK (action IN ('created', 'corrected')),
    previous_json TEXT,
    updated_json TEXT NOT NULL
);
