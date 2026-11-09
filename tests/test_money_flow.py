import sqlite3
import threading
import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app, create_withdrawal, get_db, init_db, verify_password


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("app.main.DB_PATH", tmp_path / "ledger.db")
    init_db(reset=True)
    with TestClient(app) as c:
        yield c


def admin_token(client):
    response = client.post("/login", json={"username": "admin", "password": "adminpass"})
    assert response.status_code == 200, response.text
    return response.json()["token"]


def user_token(client, username):
    response = client.post("/login", json={"username": username, "password": "pass123"})
    assert response.status_code == 200, response.text
    return response.json()["token"]


def test_money_is_conserved_and_balances_match_totals(client):
    admin = admin_token(client)
    alice = user_token(client, "alice")
    bob = user_token(client, "bob")

    accounts = client.get("/accounts", headers={"Authorization": f"Bearer {admin}"})
    ids = {acc["name"]: acc["id"] for acc in accounts.json()}
    a1 = ids["Alice Checking"]
    a2 = ids["Bob Checking"]

    before_total = sum(acc["balance"] for acc in client.get("/accounts", headers={"Authorization": f"Bearer {admin}"}).json())

    client.post("/deposits", json={"account_id": a1, "amount": 1000, "description": "seed"}, headers={"Authorization": f"Bearer {admin}"})
    client.post("/deposits", json={"account_id": a2, "amount": 500, "description": "seed"}, headers={"Authorization": f"Bearer {admin}"})

    transfer = client.post(
        "/transfers",
        json={"from_account_id": a1, "to_account_id": a2, "amount": 200, "description": "move funds", "client_key": "conserve-1"},
        headers={"Authorization": f"Bearer {alice}"},
    )
    assert transfer.status_code == 200, transfer.text

    after_total = sum(acc["balance"] for acc in client.get("/accounts", headers={"Authorization": f"Bearer {admin}"}).json())
    assert after_total == before_total + 1500


def test_replayed_request_does_not_double_pay(client):
    admin = admin_token(client)
    alice = user_token(client, "alice")
    accounts = client.get("/accounts", headers={"Authorization": f"Bearer {admin}"})
    ids = {acc["name"]: acc["id"] for acc in accounts.json()}
    a1 = ids["Alice Checking"]
    a2 = ids["Bob Checking"]

    first = client.post(
        "/transfers",
        json={"from_account_id": a1, "to_account_id": a2, "amount": 75, "description": "retry test", "client_key": "retry-1"},
        headers={"Authorization": f"Bearer {alice}"},
    )
    second = client.post(
        "/transfers",
        json={"from_account_id": a1, "to_account_id": a2, "amount": 75, "description": "retry test", "client_key": "retry-1"},
        headers={"Authorization": f"Bearer {alice}"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["idempotent"] is True
    assert second.json()["amount"] == 75
    assert first.json()["result"] == second.json()["result"]


def test_concurrent_withdrawals_do_not_overdraw(client):
    init_db(reset=True)
    user = {"id": 2, "username": "bob", "role": "account_holder"}
    with get_db() as conn:
        acc_id = conn.execute("SELECT id FROM accounts WHERE owner_username = ?", ("bob",)).fetchone()["id"]

    results = []

    def worker(i):
        payload = SimpleNamespace(
            account_id=acc_id,
            amount=150,
            description="race",
            client_key=f"race-{i}-{time.time_ns()}",
        )
        results.append(create_withdrawal(payload, user))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sum(1 for r in results if r["result"] == "posted") == 1
    with get_db() as conn:
        balance = conn.execute("SELECT balance FROM accounts WHERE id = ?", (acc_id,)).fetchone()["balance"]
    assert balance == 100


def test_user_cannot_move_another_user_money(client):
    admin = admin_token(client)
    alice = user_token(client, "alice")
    bob = user_token(client, "bob")
    accounts = client.get("/accounts", headers={"Authorization": f"Bearer {admin}"})
    ids = {acc["name"]: acc["id"] for acc in accounts.json()}
    a1 = ids["Alice Checking"]
    b1 = ids["Bob Checking"]

    response = client.post(
        "/transfers",
        json={"from_account_id": b1, "to_account_id": a1, "amount": 25, "description": "not allowed"},
        headers={"Authorization": f"Bearer {alice}"},
    )

    assert response.status_code == 403


def test_root_serves_web_ui(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "LedgerLine" in response.text
    assert "<html" in response.text.lower()


def test_default_initialization_preserves_money_and_idempotency(client):
    alice = user_token(client, "alice")
    with get_db() as conn:
        account_id = conn.execute(
            "SELECT id FROM accounts WHERE owner_username = ?", ("alice",)
        ).fetchone()["id"]

    response = client.post(
        "/deposits",
        json={"account_id": account_id, "amount": 25, "client_key": "persist-1"},
        headers={"Authorization": f"Bearer {alice}"},
    )
    assert response.status_code == 200, response.text

    with get_db() as conn:
        entries_before = conn.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0]

    init_db()

    with get_db() as conn:
        balance = conn.execute(
            "SELECT balance FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()["balance"]
        entries_after = conn.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0]
        idempotency_count = conn.execute(
            "SELECT COUNT(*) FROM idempotency_keys WHERE client_key = ?", ("persist-1",)
        ).fetchone()[0]

    assert balance == 1025
    assert entries_after == entries_before
    assert idempotency_count == 1


def test_fresh_database_is_initialized_only_once(monkeypatch, tmp_path):
    monkeypatch.setattr("app.main.DB_PATH", tmp_path / "fresh-ledger.db")

    init_db()
    with get_db() as conn:
        account_count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        entry_count = conn.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0]

    init_db()
    with get_db() as conn:
        repeated_account_count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        repeated_entry_count = conn.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0]

    assert account_count == repeated_account_count == 3
    assert entry_count == repeated_entry_count == 3


def test_deposit_withdrawal_and_transfer_are_persisted(client):
    alice = user_token(client, "alice")
    with get_db() as conn:
        accounts = {
            row["owner_username"]: row["id"]
            for row in conn.execute(
                "SELECT id, owner_username FROM accounts WHERE owner_username IN ('alice', 'bob')"
            )
        }

    deposit = client.post(
        "/deposits",
        json={"account_id": accounts["alice"], "amount": 200, "client_key": "flow-deposit"},
        headers={"Authorization": f"Bearer {alice}"},
    )
    withdrawal = client.post(
        "/withdrawals",
        json={"account_id": accounts["alice"], "amount": 50, "client_key": "flow-withdraw"},
        headers={"Authorization": f"Bearer {alice}"},
    )
    transfer = client.post(
        "/transfers",
        json={
            "from_account_id": accounts["alice"],
            "to_account_id": accounts["bob"],
            "amount": 100,
            "client_key": "flow-transfer",
        },
        headers={"Authorization": f"Bearer {alice}"},
    )

    assert deposit.status_code == withdrawal.status_code == transfer.status_code == 200
    with get_db() as conn:
        balances = {
            row["owner_username"]: row["balance"]
            for row in conn.execute(
                "SELECT owner_username, balance FROM accounts WHERE owner_username IN ('alice', 'bob')"
            )
        }
    assert balances == {"alice": 1050, "bob": 350}


def test_auditor_can_read_but_cannot_move_money(client):
    auditor = user_token(client, "auditor")
    with get_db() as conn:
        ids = {
            row["owner_username"]: row["id"]
            for row in conn.execute(
                "SELECT id, owner_username FROM accounts WHERE owner_username IN ('alice', 'bob')"
            )
        }
    headers = {"Authorization": f"Bearer {auditor}"}

    assert client.get("/accounts", headers=headers).status_code == 200
    assert client.get(f"/accounts/{ids['alice']}/statement", headers=headers).status_code == 200
    assert client.post(
        "/deposits",
        json={"account_id": ids["alice"], "amount": 1, "client_key": "auditor-deposit"},
        headers=headers,
    ).status_code == 403
    assert client.post(
        "/withdrawals",
        json={"account_id": ids["alice"], "amount": 1, "client_key": "auditor-withdraw"},
        headers=headers,
    ).status_code == 403
    assert client.post(
        "/transfers",
        json={
            "from_account_id": ids["alice"],
            "to_account_id": ids["bob"],
            "amount": 1,
            "client_key": "auditor-transfer",
        },
        headers=headers,
    ).status_code == 403


def test_idempotency_key_is_bound_to_actor_and_request(client):
    alice = user_token(client, "alice")
    bob = user_token(client, "bob")
    with get_db() as conn:
        ids = {
            row["owner_username"]: row["id"]
            for row in conn.execute(
                "SELECT id, owner_username FROM accounts WHERE owner_username IN ('alice', 'bob')"
            )
        }

    first = client.post(
        "/deposits",
        json={"account_id": ids["alice"], "amount": 40, "client_key": "bound-key"},
        headers={"Authorization": f"Bearer {alice}"},
    )
    replay = client.post(
        "/deposits",
        json={"account_id": ids["alice"], "amount": 40, "client_key": "bound-key"},
        headers={"Authorization": f"Bearer {alice}"},
    )
    changed_request = client.post(
        "/deposits",
        json={"account_id": ids["alice"], "amount": 41, "client_key": "bound-key"},
        headers={"Authorization": f"Bearer {alice}"},
    )
    other_actor = client.post(
        "/deposits",
        json={"account_id": ids["bob"], "amount": 40, "client_key": "bound-key"},
        headers={"Authorization": f"Bearer {bob}"},
    )

    assert first.status_code == replay.status_code == 200
    assert replay.json()["idempotent"] is True
    assert changed_request.status_code == other_actor.status_code == 409
    with get_db() as conn:
        assert conn.execute(
            "SELECT balance FROM accounts WHERE id = ?", (ids["alice"],)
        ).fetchone()["balance"] == 1040
        assert conn.execute(
            "SELECT balance FROM accounts WHERE id = ?", (ids["bob"],)
        ).fetchone()["balance"] == 250


def test_refused_attempt_is_in_statement_and_ledger_is_append_only(client):
    bob = user_token(client, "bob")
    admin = admin_token(client)
    with get_db() as conn:
        account_id = conn.execute(
            "SELECT id FROM accounts WHERE owner_username = 'bob'"
        ).fetchone()["id"]

    refused = client.post(
        "/withdrawals",
        json={"account_id": account_id, "amount": 300, "client_key": "refused-1"},
        headers={"Authorization": f"Bearer {bob}"},
    )
    statement = client.get(
        f"/accounts/{account_id}/statement",
        headers={"Authorization": f"Bearer {bob}"},
    )

    assert refused.status_code == 200
    assert refused.json()["result"] == "rejected"
    refused_entry = statement.json()["entries"][-1]
    assert refused_entry["kind"] == "refused"
    assert refused_entry["running_balance"] == 250
    assert refused_entry["actor_username"] == "bob"
    assert statement.json()["hash_valid"] is True
    assert client.get("/ledger/verify", headers={"Authorization": f"Bearer {admin}"}).json()["hash_valid"] is True

    with get_db() as conn:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute("UPDATE ledger_entries SET amount = 0 WHERE id = ?", (refused_entry["id"],))
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute("DELETE FROM ledger_entries WHERE id = ?", (refused_entry["id"],))


def test_seed_passwords_are_hashed_and_login_still_works(client):
    with get_db() as conn:
        passwords = [
            row["password"]
            for row in conn.execute("SELECT password FROM users")
        ]
    assert all(password.startswith("pbkdf2_sha256$") for password in passwords)
    assert client.post(
        "/login", json={"username": "admin", "password": "adminpass"}
    ).status_code == 200


def test_legacy_database_migrates_without_losing_records(monkeypatch, tmp_path):
    database_path = tmp_path / "legacy-ledger.db"
    with sqlite3.connect(database_path) as conn:
        conn.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES ('admin', 'legacy-password', 'admin')"
        )
        conn.execute(
            """
            CREATE TABLE idempotency_keys (
                client_key TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO idempotency_keys VALUES ('legacy-key', '{\"result\":\"posted\"}', 1)"
        )

    monkeypatch.setattr("app.main.DB_PATH", database_path)
    init_db()

    with get_db() as conn:
        password = conn.execute(
            "SELECT password FROM users WHERE username = 'admin'"
        ).fetchone()["password"]
        keys = {
            row["name"] for row in conn.execute("PRAGMA table_info(idempotency_keys)")
        }
        saved_key = conn.execute(
            "SELECT response_json FROM idempotency_keys WHERE client_key = 'legacy-key'"
        ).fetchone()["response_json"]
        entries = conn.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0]

    assert password.startswith("pbkdf2_sha256$")
    assert {"actor_user_id", "request_hash"}.issubset(keys)
    assert saved_key == '{"result":"posted"}'
    assert entries == 3


def test_production_database_requires_configured_credentials(monkeypatch, tmp_path):
    monkeypatch.setattr("app.main.DB_PATH", tmp_path / "production.db")
    monkeypatch.setenv("LEDGERLINE_ENV", "production")
    for name in (
        "LEDGERLINE_TOKEN_SECRET",
        "LEDGERLINE_ADMIN_PASSWORD",
        "LEDGERLINE_ALICE_PASSWORD",
        "LEDGERLINE_BOB_PASSWORD",
        "LEDGERLINE_AUDITOR_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="LEDGERLINE_TOKEN_SECRET"):
        init_db()

    assert not (tmp_path / "production.db").exists()


def test_production_replaces_existing_demo_seed_passwords(monkeypatch, tmp_path):
    database_path = tmp_path / "production-seeded.db"
    with sqlite3.connect(database_path) as conn:
        conn.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES ('admin', 'adminpass', 'admin')"
        )

    monkeypatch.setattr("app.main.DB_PATH", database_path)
    monkeypatch.setenv("LEDGERLINE_ENV", "production")
    monkeypatch.setenv("LEDGERLINE_TOKEN_SECRET", "production-secret-value")
    production_passwords = {
        "LEDGERLINE_ADMIN_PASSWORD": "secure-admin-password",
        "LEDGERLINE_ALICE_PASSWORD": "secure-alice-password",
        "LEDGERLINE_BOB_PASSWORD": "secure-bob-password",
        "LEDGERLINE_AUDITOR_PASSWORD": "secure-auditor-password",
    }
    for name, password in production_passwords.items():
        monkeypatch.setenv(name, password)

    init_db()

    with get_db() as conn:
        stored_password = conn.execute(
            "SELECT password FROM users WHERE username = 'admin'"
        ).fetchone()["password"]

    assert verify_password(production_passwords["LEDGERLINE_ADMIN_PASSWORD"], stored_password)
    assert not verify_password("adminpass", stored_password)
