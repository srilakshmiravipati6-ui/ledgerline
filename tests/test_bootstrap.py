
import pytest
from app.db import get_db_connection
from scripts.bootstrap_admin import bootstrap_admin


def test_bootstrap_admin_creates_admin_and_prevents_duplicates(tmp_path, monkeypatch):
    test_db = tmp_path / "bootstrap_test.db"
    monkeypatch.setattr("app.db.DEFAULT_SQLITE_PATH", test_db)
    monkeypatch.setattr("app.db.DB_PATH", test_db)

    # 1. First bootstrap should succeed
    success = bootstrap_admin(username="chiefadmin", password="supersecretpassword123!", db_path=test_db)
    assert success is True

    with get_db_connection(test_db) as conn:
        admin_row = conn.execute("SELECT * FROM users WHERE username = ?", ("chiefadmin",)).fetchone()
        assert admin_row is not None
        assert admin_row["role"] == "super_admin"
        assert admin_row["password"].startswith("pbkdf2_sha256$")

        account_row = conn.execute("SELECT * FROM accounts WHERE owner_username = ?", ("chiefadmin",)).fetchone()
        assert account_row is not None
        assert "Chiefadmin Treasury Operations" in account_row["name"]

    # 2. Second bootstrap attempt must detect existing admin and return False
    duplicate_success = bootstrap_admin(username="anotheradmin", password="anothersecretpassword123!", db_path=test_db)
    assert duplicate_success is False


def test_bootstrap_admin_rejects_short_passwords(tmp_path, monkeypatch):
    test_db = tmp_path / "bootstrap_short_test.db"
    monkeypatch.setattr("app.db.DEFAULT_SQLITE_PATH", test_db)
    monkeypatch.setattr("app.db.DB_PATH", test_db)

    # Password less than 12 chars should fail
    success = bootstrap_admin(username="badadmin", password="short")
    assert success is False
