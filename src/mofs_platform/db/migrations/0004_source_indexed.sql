-- 0004: record which Crossref record version responded (issue #6 QA finding).
-- The indexed timestamp documents the provider-record version at enrichment.
ALTER TABLE source ADD COLUMN indexed_at TEXT;
