-- 0019: evidence packages (issue #19). entry_method gains 'package' so a
-- source imported from an evidence package records its route honestly
-- (contributor attribution carries the identity). Rebuild pattern — CHECK
-- cannot be altered in place; all rows preserved.
CREATE TABLE source_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL DEFAULT 1 REFERENCES question(id),
    doi TEXT,
    url TEXT,
    title TEXT,
    container TEXT,
    issued_year TEXT,
    license_url TEXT,
    entry_method TEXT NOT NULL DEFAULT 'manual' CHECK (entry_method IN ('manual', 'crossref', 'package')),
    supplied_input TEXT,
    retrieval_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    inspected_level TEXT NOT NULL DEFAULT 'unknown'
        CHECK (inspected_level IN ('unknown', 'metadata', 'abstract', 'full_text', 'user_passage')),
    contributor TEXT,
    rights_note TEXT,
    indexed_at TEXT
);

INSERT INTO source_new (id, question_id, doi, url, title, container, issued_year,
                        license_url, entry_method, supplied_input, retrieval_date,
                        inspected_level, contributor, rights_note, indexed_at)
SELECT id, question_id, doi, url, title, container, issued_year, license_url,
       entry_method, supplied_input, retrieval_date, inspected_level, contributor,
       rights_note, indexed_at
FROM source;

DROP TABLE source;
ALTER TABLE source_new RENAME TO source;
