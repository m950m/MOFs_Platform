-- 0012: per-criterion lead matching (issue #16 completion). Each hit stores
-- the mechanical criteria check performed at run time — which phrases from
-- the question's hard requirements and preferences matched the title. Stored
-- as JSON (criterion text -> matched) computed at insert time, so later
-- edits to the saved question never retroactively change recorded runs.
ALTER TABLE search_hit ADD COLUMN criteria_json TEXT;
