import pytest
from fastapi.testclient import TestClient

from app.main import app, init_db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("app.main.DB_PATH", tmp_path / "health_test.db")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    init_db(reset=True)
    return TestClient(app)


def test_health_endpoint_liveness(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["app"] == "BalanceVault"
    assert data["version"] == "2.0.0"
    assert "timestamp" in data


def test_readiness_endpoint_when_healthy(client):
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert "healthy" in data["database"].lower()


def test_readiness_endpoint_when_db_down(client, monkeypatch):
    # Simulate DB failure by pointing to an unopenable path or invalid URL
    def failing_health():
        return False, "connection failed"

    monkeypatch.setattr("app.main.check_database_health", failing_health)
    res = client.get("/ready")
    assert res.status_code == 503
    data = res.json()
    assert data["status"] == "not_ready"
    # Ensure no passwords or credentials are leaked
    assert "password" not in str(data).lower()


def test_change_password_endpoint(client):
    reg = client.post("/auth/register", json={"username": "pwuser", "password": "originalPassword123!"})
    assert reg.status_code == 200
    token = reg.json()["token"]

    # Change password
    res = client.post(
        "/auth/change-password",
        json={"old_password": "originalPassword123!", "new_password": "newSecurePassword123!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    # Verify old password fails and new password works
    fail_login = client.post("/auth/login", json={"username": "pwuser", "password": "originalPassword123!"})
    assert fail_login.status_code == 401

    ok_login = client.post("/auth/login", json={"username": "pwuser", "password": "newSecurePassword123!"})
    assert ok_login.status_code == 200


def test_statement_csv_export(client):
    login = client.post("/auth/login", json={"username": "alice", "password": "pass123"})
    token = login.json()["token"]

    accs = client.get("/accounts", headers={"Authorization": f"Bearer {token}"}).json()
    acc_id = accs[0]["id"]

    res = client.get(f"/accounts/{acc_id}/statement/csv", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "Entry ID" in res.text
    assert "Previous Hash" in res.text


def test_ledger_entries_auditor(client):
    auditor = client.post("/auth/login", json={"username": "auditor", "password": "pass123"})
    token = auditor.json()["token"]

    res = client.get("/ledger/entries", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "entries" in data
    assert data["hash_valid"] is True
