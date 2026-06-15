from unittest.mock import AsyncMock, patch

from services.agents.arrowera_agents.runtime import CompletionResult, ProviderUnavailable


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_contact_and_dashboard(client):
    response = client.post(
        "/api/v1/contact",
        json={
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "company": "Analytical Engines",
            "message": "We need a reliable research operations platform.",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "received"
    dashboard = client.get("/api/v1/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["portfolioValue"] == "$0.00"


def test_contact_validation(client):
    response = client.post("/api/v1/contact", json={"name": "x"})
    assert response.status_code == 422


def test_agent_success(client):
    result = CompletionResult("openai", "test-model", "Measured analysis", 12)
    with patch(
        "services.api.app.routers.AgentRuntime.complete",
        new=AsyncMock(return_value=result),
    ):
        response = client.post(
            "/api/v1/agents/market-analyst",
            json={"prompt": "Assess the risk regime for a diversified equity portfolio."},
        )
    assert response.status_code == 200
    assert response.json()["content"] == "Measured analysis"


def test_agent_provider_failure(client):
    with patch(
        "services.api.app.routers.AgentRuntime.complete",
        new=AsyncMock(side_effect=ProviderUnavailable("provider offline")),
    ):
        response = client.post(
            "/api/v1/agents/market-analyst",
            json={"prompt": "Assess the current market risk regime in detail."},
        )
    assert response.status_code == 503
