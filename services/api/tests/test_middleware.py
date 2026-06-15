from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.api.app.middleware import RateLimitMiddleware, RequestContextMiddleware


def test_request_context_headers():
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/")
    async def root():
        return {"ok": True}

    response = TestClient(app).get("/")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-request-id"]


def test_rate_limit(monkeypatch):
    monkeypatch.setattr("services.api.app.middleware.settings.rate_limit_per_minute", 1)
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/")
    async def root():
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert client.get("/").status_code == 429
