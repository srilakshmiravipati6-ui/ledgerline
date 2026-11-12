from pathlib import Path
from sqlalchemy import inspect
from app.models import Base, User, Account, LedgerEntry, IdempotencyKey


def test_models_schema_structure():
    # Verify tables defined in Base metadata
    tables = Base.metadata.tables
    assert "users" in tables
    assert "accounts" in tables
    assert "ledger_entries" in tables
    assert "idempotency_keys" in tables

    # Verify User columns
    user_cols = tables["users"].columns
    assert "id" in user_cols
    assert "username" in user_cols
    assert "password" in user_cols
    assert "role" in user_cols
    assert "email" in user_cols
    assert user_cols["username"].unique is True

    # Verify Account columns & constraints
    account_cols = tables["accounts"].columns
    assert "id" in account_cols
    assert "balance" in account_cols
    assert "overdraft_limit" in account_cols
    assert account_cols["name"].unique is True

    # Verify LedgerEntry append-only columns
    ledger_cols = tables["ledger_entries"].columns
    assert "prev_hash" in ledger_cols
    assert "hash_value" in ledger_cols
    assert "running_balance" in ledger_cols
    assert "operation_id" in ledger_cols

    # Verify IdempotencyKey
    idemp_cols = tables["idempotency_keys"].columns
    assert "client_key" in idemp_cols
    assert "response_json" in idemp_cols
    assert "request_hash" in idemp_cols


def test_alembic_migrations_exist():
    versions_dir = Path(__file__).resolve().parent.parent / "alembic" / "versions"
    assert versions_dir.exists()
    migration_files = list(versions_dir.glob("*.py"))
    assert len(migration_files) >= 1
    # Check that initial migration references balancevault
    contents = [f.read_text(encoding="utf-8") for f in migration_files]
    assert any("accounts" in c and "ledger_entries" in c for c in contents)

