-- 0006: tested-sample identity (issue #8). Parent frameworks, prepared
-- samples, operating states, and observations stay separate entities.
-- Observations attach ONLY to samples — never to a framework name or a
-- hypothesized phase. Relations are scoped, evidenced, and never merge rows.
CREATE TABLE sample_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES source(id) ON DELETE CASCADE,
    designation TEXT NOT NULL,
    parent_framework_name TEXT,
    linker TEXT,
    metal_node TEXT,
    composition TEXT,
    additions TEXT,
    structure_ref TEXT,
    activation TEXT,
    lineage_kind TEXT CHECK (lineage_kind IN ('composite', 'derived')),
    derived_from_sample_id INTEGER REFERENCES sample_record(id),
    basis TEXT NOT NULL DEFAULT 'experimental' CHECK (basis IN ('experimental', 'computational', 'hypothetical')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE operating_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id INTEGER NOT NULL REFERENCES sample_record(id) ON DELETE CASCADE,
    stage TEXT NOT NULL CHECK (stage IN ('before', 'during', 'after', 'unknown')),
    phase_assignment TEXT,
    epistemic_type TEXT NOT NULL CHECK (epistemic_type IN ('directly_reported', 'author_interpretation', 'tool_inference', 'user_judgment', 'unknown')),
    evidence_location TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE observation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id INTEGER NOT NULL REFERENCES sample_record(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES source(id),
    observation_kind TEXT NOT NULL CHECK (observation_kind IN ('experimental', 'computational', 'hypothetical')),
    value TEXT,
    unit TEXT,
    reaction TEXT CHECK (reaction IN ('HER', 'OER', 'other')),
    medium TEXT,
    reference_convention TEXT,
    loading TEXT,
    duration TEXT,
    protocol TEXT,
    evidence_location TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE identity_relation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    left_sample_id INTEGER NOT NULL REFERENCES sample_record(id) ON DELETE CASCADE,
    right_sample_id INTEGER NOT NULL REFERENCES sample_record(id) ON DELETE CASCADE,
    level TEXT NOT NULL CHECK (level IN ('framework', 'sample')),
    relation TEXT NOT NULL CHECK (relation IN ('same_reported_sample', 'same_parent_framework', 'derived', 'composite', 'different', 'unresolved')),
    reason TEXT NOT NULL,
    evidence_location TEXT,
    review_state TEXT NOT NULL DEFAULT 'needs_verification' CHECK (review_state IN ('needs_verification', 'in_review', 'reviewed', 'conflicted')),
    merge_permission TEXT NOT NULL DEFAULT 'none' CHECK (merge_permission IN ('none', 'within_source_after_review')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE identity_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL CHECK (action IN ('sample_recorded', 'state_recorded', 'observation_recorded', 'relation_recorded')),
    entity_id INTEGER NOT NULL,
    detail TEXT NOT NULL
);
