-- 0016: number streams (issue #17, D11). Laboratory-measured numbers and
-- industry/reference numbers are SEPARATE streams (rows), never merged into
-- one verdict. Every row carries its provenance: who entered it, from which
-- source pointer or citation, under what conditions. The table starts EMPTY
-- — nothing enters from memory; the initial reference set is the owner's
-- decision. Comparison is display-only: no ranking, no meet/fail verdicts,
-- no unit conversion (values shown as recorded).
CREATE TABLE reference_number (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream TEXT NOT NULL CHECK (stream IN ('laboratory', 'industry_reference')),
    label TEXT NOT NULL,
    value TEXT NOT NULL,
    unit TEXT,
    reaction TEXT NOT NULL CHECK (reaction IN ('HER', 'OER', 'other')),
    conditions_note TEXT,
    source_id INTEGER REFERENCES source(id),
    source_citation TEXT,
    source_year TEXT,
    contributor TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
