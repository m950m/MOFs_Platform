"""Domain tests for research-question persistence (issue #4)."""

import sqlite3

import pytest

from mofs_platform.db.connection import connect
from mofs_platform.domain.questions import (
    Question,
    QuestionPersistenceError,
    QuestionValidationError,
    count_events,
    get_question,
    save_question,
)


def test_migrations_are_idempotent(db_path):
    first = connect(db_path)
    first.close()
    second = connect(db_path)
    names = [
        row["filename"]
        for row in second.execute("SELECT filename FROM schema_migrations")
    ]
    assert names == [
        "0001_question.sql",
        "0002_lab_profile.sql",
        "0003_sources.sql",
        "0004_source_indexed.sql",
        "0005_assertions.sql",
        "0006_identity.sql",
        "0007_route_attempts.sql",
        "0008_review.sql",
        "0009_fit_assessment.sql",
        "0010_sample_correction.sql",
        "0011_active_search.sql",
        "0012_criteria_matching.sql",
        "0013_ai_refinement_attempts.sql",
        "0014_structure_index.sql",
        "0015_compound_profiles.sql",
        "0016_number_streams.sql",
        "0017_number_corrections.sql",
        "0018_conflict_resolved.sql",
        "0019_package_route.sql",
    ]
    second.close()


def test_no_question_initially(db_path):
    conn = connect(db_path)
    assert get_question(conn) is None
    assert count_events(conn) == 0


def test_blank_wording_rejected_and_nothing_saved(db_path):
    conn = connect(db_path)
    for blank in ("", "   ", "\n\t "):
        with pytest.raises(QuestionValidationError):
            save_question(conn, Question(wording=blank))
    assert get_question(conn) is None
    assert count_events(conn) == 0


def test_save_and_reopen_after_restart(db_path):
    conn = connect(db_path)
    save_question(
        conn,
        Question(
            wording="Which prepared MOF samples warrant closer inspection?",
            reactions="HER, OER",
            hard_requirements="Documented experimental preparation",
        ),
    )
    conn.close()

    reopened = connect(db_path)  # fresh application session
    saved = get_question(reopened)
    assert saved is not None
    assert saved.wording == "Which prepared MOF samples warrant closer inspection?"
    assert saved.reactions == "HER, OER"
    assert saved.hard_requirements == "Documented experimental preparation"
    assert saved.preferences is None  # stays unknown, not defaulted
    assert saved.conditions is None
    assert count_events(reopened) == 1


def test_correction_updates_in_place_and_keeps_history(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="First wording", reactions="HER"))
    save_question(
        conn,
        Question(wording="Corrected wording", reactions="HER, OER"),
    )
    saved = get_question(conn)
    assert saved is not None
    assert saved.wording == "Corrected wording"
    assert saved.reactions == "HER, OER"
    rows = conn.execute("SELECT COUNT(*) FROM question").fetchone()[0]
    assert rows == 1  # one saved question, not duplicates
    assert count_events(conn) == 2  # created + corrected
    event = conn.execute(
        "SELECT action, previous_json FROM question_event ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert event["action"] == "corrected"
    assert "First wording" in event["previous_json"]


def test_reclassification_between_hard_and_preference(db_path):
    conn = connect(db_path)
    save_question(
        conn,
        Question(
            wording="Q",
            hard_requirements="Published synthesis route",
            preferences="Accessible linker",
        ),
    )
    # The researcher moves "Accessible linker" from preferences to hard
    # requirements; untouched fields (wording, conditions) are retained.
    save_question(
        conn,
        Question(
            wording="Q",
            hard_requirements="Accessible linker",
        ),
    )
    saved = get_question(conn)
    assert saved is not None
    assert saved.wording == "Q"  # untouched field retained
    assert saved.hard_requirements == "Accessible linker"
    assert saved.conditions is None  # untouched unknown stays unknown
    assert count_events(conn) == 2


def test_unknown_fields_stay_unknown_not_defaulted(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Only wording supplied"))
    saved = get_question(conn)
    assert saved is not None
    for name in (
        "reactions",
        "material_classes",
        "conditions",
        "hard_requirements",
        "preferences",
        "meaning_of_improvement",
    ):
        assert getattr(saved, name) is None, f"{name} must stay unknown"


def test_blank_save_after_previous_preserves_previous(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Already saved question"))
    with pytest.raises(QuestionValidationError):
        save_question(conn, Question(wording="   "))
    saved = get_question(conn)
    assert saved is not None
    assert saved.wording == "Already saved question"  # prior value untouched
    assert count_events(conn) == 1  # no extra event from the failed save


def test_save_failure_reports_and_preserves_previous(db_path):
    conn = connect(db_path)
    save_question(conn, Question(wording="Original saved question"))
    conn.close()

    readonly = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    readonly.row_factory = sqlite3.Row
    with pytest.raises(QuestionPersistenceError):
        save_question(readonly, Question(wording="Edited but not saved"))
    saved = get_question(readonly)
    assert saved is not None
    assert saved.wording == "Original saved question"  # prior value intact
    readonly.close()


def test_failed_migration_rolls_back_completely(tmp_path, monkeypatch):
    """Strict-audit MAJOR fix: a migration that fails mid-way (e.g. after a
    DROP) must leave the database exactly as it was — no destroyed tables,
    no bookkeeping row — so a corrected retry applies cleanly."""
    import sqlite3

    from mofs_platform.db import connection as conn_mod

    bad_dir = tmp_path / "migrations"
    bad_dir.mkdir()
    for name in ("0001_question.sql", "0002_lab_profile.sql"):
        source = conn_mod.MIGRATIONS_DIR / name
        (bad_dir / name).write_text(source.read_text(encoding="utf-8"))
    (bad_dir / "0003_bad.sql").write_text(
        "CREATE TABLE temp_probe (id INTEGER);\n"
        "DROP TABLE question;\n"
        "INSERT INTO no_such_table VALUES (1);\n"
    )
    monkeypatch.setattr(conn_mod, "MIGRATIONS_DIR", bad_dir)
    db = tmp_path / "probe.db"
    with pytest.raises(sqlite3.Error):
        conn_mod.connect(db)
    check = sqlite3.connect(str(db))
    # rolled back: the probe table and the DROP never happened
    tables = {r[0] for r in check.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()}
    assert "temp_probe" not in tables
    assert "question" in tables  # survived — the DROP rolled back
    assert check.execute(
        "SELECT COUNT(*) FROM schema_migrations WHERE filename = '0003_bad.sql'"
    ).fetchone()[0] == 0  # bookkeeping rolled back — retry is clean
    check.close()


def test_migration_0019_parent_rebuild_preserves_children(db_path):
    """Gate-critical probe (issue #19): 0019 rebuilds `source`, a PARENT of
    sample_record/observation/assertion/source_capture_event (ON DELETE
    CASCADE) — the FK-off runner must keep every child row alive, and the
    new entry_method vocabulary must work."""
    import sqlite3

    from mofs_platform.db.connection import MIGRATIONS_DIR, connect

    # build a PRE-0019 database via the real runner (0013 era semantics for
    # search tables are irrelevant here; assert on the four child tables)
    raw = sqlite3.connect(str(db_path))
    raw.row_factory = sqlite3.Row
    raw.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "filename TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name >= "0019":
            continue
        raw.executescript(path.read_text(encoding="utf-8"))
        raw.execute(
            "INSERT INTO schema_migrations (filename) VALUES (?)", (path.name,)
        )
    raw.execute("INSERT INTO question (wording) VALUES ('Probe question')")
    raw.execute(
        "INSERT INTO source (question_id, doi, entry_method, title) "
        "VALUES (1, '10.9999/parent', 'manual', 'Parent paper')"
    )
    source_id = raw.execute("SELECT MAX(id) FROM source").fetchone()[0]
    raw.execute(
        "INSERT INTO sample_record (source_id, designation, basis) "
        "VALUES (?, 'Child sample', 'experimental')", (source_id,))
    child_samples = raw.execute("SELECT COUNT(*) FROM sample_record").fetchone()[0]
    child_obs = raw.execute("SELECT COUNT(*) FROM observation").fetchone()[0]
    child_events = raw.execute("SELECT COUNT(*) FROM source_capture_event").fetchone()[0]
    raw.commit()
    raw.close()

    # apply 0019 through the REAL connect() runner (FK-safe path)
    conn = connect(db_path)
    samples_after = conn.execute("SELECT COUNT(*) FROM sample_record").fetchone()[0]
    obs_after = conn.execute("SELECT COUNT(*) FROM observation").fetchone()[0]
    events_after = conn.execute(
        "SELECT COUNT(*) FROM source_capture_event").fetchone()[0]
    assert (samples_after, obs_after, events_after) == (
        child_samples, child_obs, child_events), "CASCADE deleted children!"
    conn.execute(
        "INSERT INTO source (question_id, doi, entry_method, title) "
        "VALUES (1, '10.9999/pkg', 'package', 'Imported via package')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO source (question_id, doi, entry_method) "
            "VALUES (1, '10.9999/x', 'carrier_pigeon')")
    orphans = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert orphans == []
