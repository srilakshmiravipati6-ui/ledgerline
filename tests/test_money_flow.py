import sqlite3
import threading
import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app, create_withdrawal, get_db, init_db


@pytest.fixture()
def client():
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
