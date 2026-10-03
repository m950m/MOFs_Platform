-- 0014: structure index (issue #24, D12 slice 1). A generic,
-- provider-attributed index of structure records (CoRE MOF 2019 first;
-- QMOF/DigiMOF/COD reuse the same table via the provider field). The index
-- is imported from owner-supplied files — no fetch route exists. Capturing
-- a structure's reference goes through the attributed reference flow; the
-- index row itself stays immutable provenance. The identity_event CHECK is
-- extended with 'structure_imported' (rebuild — SQLite cannot alter a CHECK
-- in place; append-only history preserved).
CREATE TABLE structure_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL CHECK (provider IN ('core_mof_2019', 'qmof', 'digimof', 'cod', 'other')),
    external_id TEXT,
    name TEXT NOT NULL,
    formula TEXT,
    doi TEXT,
    file_ref TEXT,
    extra_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_structure_provider_external
    ON structure_index (provider, external_id)
    WHERE external_id IS NOT NULL;

CREATE TABLE identity_event_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL CHECK (action IN ('sample_recorded', 'state_recorded', 'observation_recorded', 'relation_recorded', 'structure_imported')),
    entity_id INTEGER NOT NULL,
    detail TEXT NOT NULL
);

INSERT INTO identity_event_new (id, changed_at, action, entity_id, detail)
SELECT id, changed_at, action, entity_id, detail FROM identity_event;

DROP TABLE identity_event;
ALTER TABLE identity_event_new RENAME TO identity_event;
