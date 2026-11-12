import pytest
from fastapi.testclient import TestClient

from app.main import app, init_db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("app.main.DB_PATH", tmp_path / "auth_test.db")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    init_db(reset=True)
    return TestClient(app)


def test_user_registration_and_automatic_account_provisioning(client):
    # Register new user
    res = client.post(
        "/auth/register",
        json={
            "username": "charlie",
            "password": "charliepassword123",
            "email": "charlie@example.com",
            "initial_deposit": 500,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["message"] == "User registered successfully"
    assert data["user"]["username"] == "charlie"
    assert data["user"]["role"] == "account_holder"
    assert "token" in data
    assert data["account"]["balance"] == 500

    # Verify duplicate registration is rejected with 409
    dup = client.post(
        "/auth/register",
        json={
            "username": "charlie",
            "password": "anotherpassword123",
        },
    )
    assert dup.status_code == 409
    assert "already registered" in dup.json()["detail"].lower()


def test_registration_validation(client):
    # Short password
    res = client.post(
        "/auth/register",
        json={"username": "shortpass", "password": "123"},
    )
    assert res.status_code == 422

    # Short username
    res2 = client.post(
        "/auth/register",
        json={"username": "ab", "password": "validpassword123"},
    )
    assert res2.status_code == 422


def test_auth_login_and_me_endpoints(client):
    # Register
    client.post(
        "/auth/register",
        json={"username": "david", "password": "davidpassword123"},
    )

    # Login via /auth/login
    login_res = client.post(
        "/auth/login",
        json={"username": "david", "password": "davidpassword123"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["token"]
    assert "account_holder" == login_res.json()["user"]["role"]

    # Verify /auth/me
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "david"
    assert "transactions:deposit" in me_res.json()["permissions"]


def test_rbac_account_holder_cannot_create_accounts(client):
    # Register account holder
    reg = client.post(
        "/auth/register",
        json={"username": "eve", "password": "evepassword123"},
    )
    token = reg.json()["token"]

    # Eve tries to create a new account
    res = client.post(
        "/accounts",
        json={"name": "Eve Secret Stash", "owner_username": "eve", "overdraft_limit": 1000},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_rbac_account_holder_cannot_verify_ledger(client):
    reg = client.post(
        "/auth/register",
        json={"username": "frank", "password": "frankpassword123"},
    )
    token = reg.json()["token"]

    res = client.get("/ledger/verify", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_rbac_super_admin_can_perform_admin_tasks(client):
    # Admin login
    res = client.post("/auth/login", json={"username": "admin", "password": "adminpass"})
    admin_token = res.json()["token"]

    # Admin creates an account for an existing user
    acc = client.post(
        "/accounts",
        json={"name": "Alice Vault Reserve", "owner_username": "alice", "overdraft_limit": 5000},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert acc.status_code == 200
    assert acc.json()["name"] == "Alice Vault Reserve"

    # Admin verifies ledger
    verify = client.get("/ledger/verify", headers={"Authorization": f"Bearer {admin_token}"})
    assert verify.status_code == 200
    assert verify.json()["hash_valid"] is True

