-- 0015: compound profiles (issue #18). A compound is a RESEARCHER-GROUPED
-- aggregation record: never a merge, never an equivalence claim (D5). Same
-- composition with a different arrangement/morphology belongs in a separate
-- compound with a separate profile. Membership is attributed and reasoned;
-- every change is audited. The framework key (MOFid/MOFkey or equivalent)
-- is OPTIONAL — its absence never blocks a profile.
CREATE TABLE compound (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT NOT NULL,
    framework_key TEXT,
    identity_note TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE compound_member (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    compound_id INTEGER NOT NULL REFERENCES compound(id),
    member_type TEXT NOT NULL CHECK (member_type IN ('sample_record', 'structure_index')),
    member_id INTEGER NOT NULL,
    added_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (compound_id, member_type, member_id)
);

CREATE TABLE compound_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL CHECK (action IN ('compound_created', 'member_attached', 'member_detached')),
    compound_id INTEGER NOT NULL,
    actor TEXT,
    detail TEXT NOT NULL
);
