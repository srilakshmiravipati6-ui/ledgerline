
import os
import pytest
from app.ratelimit import reset_memory_store


@pytest.fixture(autouse=True)
def isolate_test_database(monkeypatch):
    """
    Ensure automated pytest test suites run against an isolated test database
    and do not pollute the remote production/staging Neon database.
    """
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    reset_memory_store()
