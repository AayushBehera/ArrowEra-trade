import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test-arrowera.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-longer-than-32-characters")

import pytest
from fastapi.testclient import TestClient

from services.api.app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
