"""Integration tests for the FastAPI application.

Uses an in-memory SQLite database so no external PostgreSQL is required.
LLM calls are mocked to avoid API costs during testing.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """Use SQLite for testing."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test_db.db")
    monkeypatch.setenv("AI_INTEGRATIONS_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")


@pytest_asyncio.fixture
async def client():
    """Async HTTP client pointed at the test app."""
    from main import create_app
    from infrastructure.database.postgres import init_db

    app = create_app()
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_analyze_repo_validates_url(client: AsyncClient):
    """Submitting a bad URL should fail gracefully."""
    with patch(
        "services.repo_service.RepoIngestionService.ingest",
        side_effect=Exception("Invalid URL"),
    ):
        response = await client.post(
            "/analyze-repo",
            json={"github_url": "not-a-valid-url", "branch": "main"},
        )
        assert response.status_code in (422, 500)


@pytest.mark.asyncio
async def test_repo_summary_not_found(client: AsyncClient):
    response = await client.get("/repo-summary/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ask_repo_not_found(client: AsyncClient):
    response = await client.post(
        "/ask",
        json={
            "repo_id": "nonexistent-id",
            "question": "What does this repo do?",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_issues_repo_not_found(client: AsyncClient):
    response = await client.get("/issues/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_repos_empty(client: AsyncClient):
    response = await client.get("/repo-summary")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_dependency_graph_not_found(client: AsyncClient):
    response = await client.get("/dependency-graph/nonexistent-id")
    assert response.status_code == 404
