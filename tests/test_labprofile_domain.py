"""Domain tests for the laboratory capability profile (issue #5)."""

import sqlite3

import pytest

from mofs_platform.db.connection import connect
from mofs_platform.domain.labprofile import (
    STATUSES,
    LabProfilePersistenceError,
    LabProfileValidationError,
    add_capability,
    count_events,
    list_capabilities,
    update_capability,
)


def test_no_capabilities_initially(db_path):
    conn = connect(db_path)
    assert list_capabilities(conn) == []
    assert count_events(conn) == 0


def test_blank_name_rejected_and_invalid_status_rejected(db_path):
    conn = connect(db_path)
    for blank in ("", "   ", "\n\t"):
        with pytest.raises(LabProfileValidationError):
            add_capability(conn, blank, "desc", "current")
    with pytest.raises(LabProfileValidationError):
        add_capability(conn, "Synthetic tool", "desc", "maybe")  # not a valid status
    assert list_capabilities(conn) == []
    assert count_events(conn) == 0


def test_add_entries_with_all_four_distinct_statuses(db_path):
    conn = connect(db_path)
    for i, status in enumerate(STATUSES):
        add_capability(conn, f"Synthetic entry {i}", None, status)
    entries = list_capabilities(conn)
    assert len(entries) == 4
    assert {e.status for e in entries} == set(STATUSES)  # preserved exactly, not collapsed
    assert count_events(conn) == 4


def test_duplicate_name_rejected_case_insensitive(db_path):
    conn = connect(db_path)
    add_capability(conn, "Glovebox (synthetic)", "inert atmosphere", "current")
    with pytest.raises(LabProfileValidationError):
        add_capability(conn, "glovebox (SYNTHETIC)", "again", "future")
    assert len(list_capabilities(conn)) == 1
    assert count_events(conn) == 1  # no event for the rejected duplicate


def test_correction_updates_in_place_and_keeps_history(db_path):
    conn = connect(db_path)
    first = add_capability(conn, "Reflux setup (synthetic)", None, "future")
    add_capability(conn, "Second entry (synthetic)", "untouched", "unknown")

    updated = update_capability(conn, first.id, "Reflux setup (synthetic)", "with inert line", "current")
    assert updated.id == first.id  # same entry, not a duplicate
    assert updated.status == "current"
    assert updated.description == "with inert line"

    entries = list_capabilities(conn)
    assert len(entries) == 2  # no duplication
    untouched = next(e for e in entries if e.id != first.id)
    assert untouched.description == "untouched"  # untouched entry retained
    assert untouched.status == "unknown"
    assert count_events(conn) == 3  # 2 added + 1 corrected

    event = conn.execute(
        "SELECT action, previous_json FROM lab_profile_event "
        "ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert event["action"] == "corrected"
    assert '"future"' in event["previous_json"]  # previous status preserved in history


def test_reclassification_unknown_to_current_is_explicit_only(db_path):
    conn = connect(db_path)
    cap = add_capability(conn, "Rotating electrode (synthetic)", None, "unknown")
    update_capability(conn, cap.id, cap.name, None, "current")
    entries = list_capabilities(conn)
    assert entries[0].status == "current"  # only because the researcher said so


def test_restart_persistence(db_path):
    conn = connect(db_path)
    add_capability(conn, "Persistent entry (synthetic)", "survives restart", "unavailable")
    conn.close()

    reopened = connect(db_path)
    entries = list_capabilities(reopened)
    assert len(entries) == 1
    assert entries[0].status == "unavailable"  # explicitly unavailable, not unknown
    assert entries[0].description == "survives restart"
    assert count_events(reopened) == 1


def test_save_failure_preserves_previous_profile(db_path):
    conn = connect(db_path)
    add_capability(conn, "Original entry (synthetic)", None, "current")
    conn.close()

    readonly = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    readonly.row_factory = sqlite3.Row
    with pytest.raises(LabProfilePersistenceError):
        add_capability(readonly, "Never saved (synthetic)", None, "future")
    with pytest.raises(LabProfilePersistenceError):
        update_capability(readonly, 1, "Edited but not saved", None, "future")
    entries = list_capabilities(readonly)
    assert len(entries) == 1
    assert entries[0].name == "Original entry (synthetic)"
    assert entries[0].status == "current"
    readonly.close()
