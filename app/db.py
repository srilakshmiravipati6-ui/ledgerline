from __future__ import annotations

import logging
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional, Tuple, Union

logger = logging.getLogger("balancevault.db")

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = BASE_DIR / "ledger.db"
DB_PATH = DEFAULT_SQLITE_PATH


def is_postgres() -> bool:
    url = os.environ.get("DATABASE_URL", "")
    return url.startswith("postgres://") or url.startswith("postgresql://")


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class RowWrapper:
    """Row wrapper that supports both string key access row['name'] and index access row[0]."""
    def __init__(self, raw_row: Any, is_pg: bool = False):
        if is_pg:
            # psycopg2 RealDictRow
            self._data = dict(raw_row)
            self._values = list(raw_row.values())
        elif isinstance(raw_row, sqlite3.Row):
            self._data = dict(raw_row)
            self._values = [raw_row[i] for i in range(len(raw_row))]
        elif isinstance(raw_row, dict):
            self._data = dict(raw_row)
            self._values = list(raw_row.values())
        else:
            self._data = dict(raw_row)
            self._values = list(raw_row.values()) if hasattr(raw_row, "values") else list(raw_row)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __contains__(self, key):
        return key in self._data

    def __repr__(self):
        return repr(self._data)


class DBConnection:
    """Unified Database Connection supporting both SQLite and PostgreSQL."""

    def __init__(self, raw_conn: Any, is_pg: bool):
        self.raw_conn = raw_conn
        self.is_pg = is_pg
        self.cursor = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        self.close()

    def __iter__(self):
        if self.cursor is None:
            return iter([])
        for row in self.cursor:
            yield RowWrapper(row, is_pg=self.is_pg)

    def execute(self, sql: str, params: Union[tuple, list, dict] = ()):
        if self.is_pg:
            adapted_sql = sql.replace("?", "%s")
            if adapted_sql.strip().upper().startswith("PRAGMA"):
                return self
            if adapted_sql.strip().upper() == "BEGIN IMMEDIATE":
                return self

            cur = self.raw_conn.cursor()
            cur.execute(adapted_sql, params)
            self.cursor = cur
            return self
        else:
            cur = self.raw_conn.execute(sql, params)
            self.cursor = cur
            return self

    def fetchone(self) -> Optional[RowWrapper]:
        if self.cursor is None:
            return None
        row = self.cursor.fetchone()
        if row is None:
            return None
        return RowWrapper(row, is_pg=self.is_pg)

    def fetchall(self) -> list[RowWrapper]:
        if self.cursor is None:
            return []
        rows = self.cursor.fetchall()
        return [RowWrapper(r, is_pg=self.is_pg) for r in rows]

    def commit(self):
        self.raw_conn.commit()

    def rollback(self):
        self.raw_conn.rollback()

    def close(self):
        try:
            if self.is_pg:
                if self.cursor:
                    self.cursor.close()
                self.raw_conn.close()
            else:
                self.raw_conn.close()
        except Exception:
            pass


def get_raw_pg_connection():
    import psycopg2
    import psycopg2.extras
    url = get_database_url()
    conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = False
    return conn


@contextmanager
def get_db_connection(db_path: Optional[Path] = None) -> Generator[DBConnection, None, None]:
    """Context manager for obtaining a database connection."""
    if is_postgres():
        conn = get_raw_pg_connection()
        wrapper = DBConnection(conn, is_pg=True)
        try:
            yield wrapper
        finally:
            wrapper.close()
    else:
        path = db_path or getattr(get_db_connection, "db_path", DEFAULT_SQLITE_PATH)
        conn = sqlite3.connect(path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        wrapper = DBConnection(conn, is_pg=False)
        try:
            yield wrapper
        finally:
            wrapper.close()


def check_database_health() -> Tuple[bool, str]:
    """Check database health for readiness checks."""
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
            row = conn.fetchone()
            if row is not None:
                backend = "PostgreSQL" if is_postgres() else "SQLite"
                return True, f"healthy ({backend})"
            return False, "query returned empty"
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return False, f"unreachable: {str(exc)}"


def init_database_schema(conn: DBConnection) -> None:
    """Initialize table schemas, indexes, and append-only triggers."""
    if conn.is_pg:
        # PostgreSQL Schema
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) NOT NULL UNIQUE,
                password VARCHAR(256) NOT NULL,
                role VARCHAR(32) NOT NULL,
                email VARCHAR(255),
                created_at BIGINT NOT NULL DEFAULT 0
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(120) NOT NULL UNIQUE,
                owner_username VARCHAR(80) NOT NULL REFERENCES users(username),
                balance BIGINT NOT NULL DEFAULT 0,
                overdraft_limit BIGINT NOT NULL DEFAULT 0,
                created_at BIGINT NOT NULL DEFAULT 0
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger_entries (
                id SERIAL PRIMARY KEY,
                account_id INTEGER NOT NULL REFERENCES accounts(id),
                kind VARCHAR(32) NOT NULL,
                amount BIGINT NOT NULL,
                running_balance BIGINT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                actor_user_id INTEGER NOT NULL,
                request_key VARCHAR(128) NOT NULL,
                operation_id VARCHAR(128) NOT NULL,
                actor_username VARCHAR(80) NOT NULL,
                prev_hash VARCHAR(64) NOT NULL,
                hash_value VARCHAR(64) NOT NULL,
                created_at BIGINT NOT NULL DEFAULT 0
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS idempotency_keys (
                client_key VARCHAR(128) PRIMARY KEY,
                response_json TEXT NOT NULL,
                actor_user_id INTEGER NOT NULL,
                request_hash VARCHAR(64) NOT NULL,
                created_at BIGINT NOT NULL DEFAULT 0
            );
            """
        )
        # Indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_accounts_owner ON accounts (owner_username);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ledger_account_id ON ledger_entries (account_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ledger_hash ON ledger_entries (hash_value);")

        # Append-Only Trigger in PostgreSQL
        conn.execute(
            """
            CREATE OR REPLACE FUNCTION prevent_ledger_mutation()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'ledger_entries is append-only';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        conn.execute("DROP TRIGGER IF EXISTS trg_prevent_ledger_update ON ledger_entries;")
        conn.execute(
            """
            CREATE TRIGGER trg_prevent_ledger_update
            BEFORE UPDATE ON ledger_entries
            FOR EACH ROW EXECUTE FUNCTION prevent_ledger_mutation();
            """
        )
        conn.execute("DROP TRIGGER IF EXISTS trg_prevent_ledger_delete ON ledger_entries;")
        conn.execute(
            """
            CREATE TRIGGER trg_prevent_ledger_delete
            BEFORE DELETE ON ledger_entries
            FOR EACH ROW EXECUTE FUNCTION prevent_ledger_mutation();
            """
        )
        conn.commit()
    else:
        # SQLite Schema
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'super_admin', 'account_holder', 'auditor')),
                email TEXT,
                created_at INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                owner_username TEXT NOT NULL,
                balance INTEGER NOT NULL DEFAULT 0,
                overdraft_limit INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (owner_username) REFERENCES users(username)
            );
            """
        )
        # Migrate any older SQLite tables missing columns
        user_cols = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
        if "email" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
        if "created_at" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN created_at INTEGER NOT NULL DEFAULT 0")

        acc_cols = {row["name"] for row in conn.execute("PRAGMA table_info(accounts)").fetchall()}
        if "created_at" not in acc_cols:
            conn.execute("ALTER TABLE accounts ADD COLUMN created_at INTEGER NOT NULL DEFAULT 0")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('credit', 'debit', 'refused')),
                amount INTEGER NOT NULL,
                running_balance INTEGER NOT NULL,
                description TEXT,
                actor_user_id INTEGER,
                request_key TEXT,
                operation_id TEXT NOT NULL,
                actor_username TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                hash_value TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS idempotency_keys (
                client_key TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                actor_user_id INTEGER,
                request_hash TEXT
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_accounts_owner ON accounts (owner_username);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ledger_account_id ON ledger_entries (account_id, id);")

        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS prevent_ledger_update
            BEFORE UPDATE ON ledger_entries
            BEGIN
                SELECT RAISE(FAIL, 'ledger entries are append-only');
            END;
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS prevent_ledger_delete
            BEFORE DELETE ON ledger_entries
            BEGIN
                SELECT RAISE(FAIL, 'ledger entries are append-only');
            END;
            """
        )
        conn.commit()
