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
        # Atomic + FK-safe per migration (two strict-audit fixes):
        # 1. executescript commits implicitly — the script + bookkeeping run
        #    inside one explicit BEGIN IMMEDIATE..COMMIT so a crash mid-rebuild
        #    is all-or-nothing.
        # 2. PRAGMA foreign_keys cannot change inside a transaction, so it is
        #    turned OFF around the script (a parent-table rebuild with DROP
        #    must not CASCADE-delete child tables) and ON after; a
        #    foreign_key_check then runs and raises LOUDLY on any orphan.
        script = (
            "BEGIN IMMEDIATE;\n"
            + path.read_text(encoding="utf-8")
            + f"\nINSERT INTO schema_migrations (filename) VALUES ('{path.name}');\n"
            + "COMMIT;"
        )
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.executescript(script)
        orphans = conn.execute("PRAGMA foreign_key_check").fetchall()
        conn.execute("PRAGMA foreign_keys = ON")
        if orphans:
            tables = ", ".join(f"{r[0]}(row {r[1]})" for r in orphans[:5])
            raise sqlite3.IntegrityError(
                f"Migration {path.name} left orphaned rows ({tables}) — restore "
                "from backup before continuing; the migration is applied but "
                "the store is inconsistent."
            )


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open (creating if needed) the local database and apply migrations."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    apply_migrations(conn)
    return conn
