-- 0003: reference capture (issue #6). References are leads linked to the
-- saved research question; metadata enrichment never verifies a sample.
-- Re-captures append events so every capture context stays auditable.
CREATE TABLE source (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL DEFAULT 1 REFERENCES question(id),
    doi TEXT,
    url TEXT,
    title TEXT,
    container TEXT,
    issued_year TEXT,
    license_url TEXT,
    entry_method TEXT NOT NULL CHECK (entry_method IN ('manual', 'crossref')),
    supplied_input TEXT,
    retrieval_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    inspected_level TEXT NOT NULL DEFAULT 'unknown'
        CHECK (inspected_level IN ('unknown', 'metadata', 'abstract', 'full_text', 'user_passage')),
    contributor TEXT,
    rights_note TEXT
);

CREATE TABLE source_capture_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL CHECK (action IN ('captured', 'crossref_enriched')),
    source_id INTEGER NOT NULL REFERENCES source(id) ON DELETE CASCADE,
    previous_json TEXT,
    updated_json TEXT NOT NULL
);
