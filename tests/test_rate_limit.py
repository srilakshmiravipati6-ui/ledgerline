import pytest
from fastapi.testclient import TestClient

from app.main import app, init_db
from app.ratelimit import reset_memory_store


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("app.main.DB_PATH", tmp_path / "ratelimit_test.db")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    reset_memory_store()
    init_db(reset=True)
    return TestClient(app)


def test_rate_limiting_triggers_429_when_exceeded(client):
    # Attempt logins in rapid succession
    status_codes = []
    for _ in range(20):
        res = client.post("/auth/login", json={"username": "admin", "password": "wrongpassword"})
        status_codes.append(res.status_code)

    # At least some of the later requests must be 429 Too Many Requests
    assert 429 in status_codes
    rate_limited_response = [r for r in status_codes if r == 429]
    assert len(rate_limited_response) > 0


def test_rate_limit_disabled_allows_traffic(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    reset_memory_store()

    status_codes = []
    for _ in range(20):
        res = client.post("/auth/login", json={"username": "admin", "password": "wrongpassword"})
        status_codes.append(res.status_code)

    # When disabled, no 429s are generated
    assert 429 not in status_codes

