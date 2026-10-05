"""SQLite connection with a numbered-migration runner (issue #4).

Migrations live in db/migrations/*.sql and are applied once, in filename
order, tracked in schema_migrations. Connecting twice to the same database
is idempotent.
"""

import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def apply_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "filename TEXT PRIMARY KEY, "
        "applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    applied = {row["filename"] for row in conn.execute("SELECT filename FROM schema_migrations")}
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in applied:
            continue
        # Atomic per migration: executescript commits implicitly, so a crash
        # mid-rebuild (after DROP, before RENAME) previously destroyed tables.
        # Wrapping the script + the bookkeeping insert in one explicit
        # transaction makes every migration all-or-nothing (strict audit).
        script = (
            "BEGIN IMMEDIATE;\n"
            + path.read_text(encoding="utf-8")
            + f"\nINSERT INTO schema_migrations (filename) VALUES ('{path.name}');\n"
            + "COMMIT;"
        )
        conn.executescript(script)


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open (creating if needed) the local database and apply migrations."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    apply_migrations(conn)
    return conn
