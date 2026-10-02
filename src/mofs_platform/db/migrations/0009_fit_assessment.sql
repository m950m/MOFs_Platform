-- 0009: laboratory-fit assessments (issue #12). Each assessment stores its
-- reasons and the basis stamps it was computed from, so a later input change
-- visibly marks it outdated until re-run. No guessing, no success promises.
CREATE TABLE fit_assessment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id INTEGER NOT NULL REFERENCES sample_record(id) ON DELETE CASCADE,
    assessment TEXT NOT NULL CHECK (assessment IN ('possible_with_current_capabilities', 'requires_future_capabilities', 'unknown')),
    reasons_json TEXT NOT NULL,
    basis_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
