from __future__ import annotations

import os
import sqlite3
from pathlib import Path
import sys

from datetime import datetime, timezone


def _default_db_path() -> Path:
    if sys.platform == "win32":
        app_data = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if app_data:
            return Path(app_data) / "ClientLedgerDesk" / "ledger_desktop.db"
    return Path.home() / ".client_ledger_desk" / "ledger_desktop.db"


DB_PATH = Path(os.environ.get("CLIENT_LEDGER_DESK_DB", _default_db_path()))
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
SCHEMA_MIGRATIONS_TABLE = "schema_migrations"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS_TABLE} (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )


def _applied_migration_versions(conn: sqlite3.Connection) -> set[int]:
    rows = conn.execute(f"SELECT version FROM {SCHEMA_MIGRATIONS_TABLE}").fetchall()
    return {int(row[0]) for row in rows}


def _migration_files() -> list[tuple[int, Path]]:
    if not MIGRATIONS_DIR.exists():
        return []

    migrations: list[tuple[int, Path]] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        try:
            version = int(path.stem.split("_", 1)[0])
        except (ValueError, IndexError):
            continue
        migrations.append((version, path))
    return sorted(migrations, key=lambda item: item[0])


def _apply_migration(conn: sqlite3.Connection, version: int, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        conn.executescript(sql)
        conn.execute(
            f"INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (version, applied_at) VALUES (?, ?)",
            (version, datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        conn.commit()
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def init_db() -> None:
    with get_connection() as conn:
        _ensure_migrations_table(conn)
        applied_versions = _applied_migration_versions(conn)
        for version, path in _migration_files():
            if version not in applied_versions:
                _apply_migration(conn, version, path)
