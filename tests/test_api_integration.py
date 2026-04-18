"""Integration tests untuk API Layer."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "version" in data
        assert "components" in data
        assert "uptime_seconds" in data

    def test_health_has_all_components(self, client):
        resp = client.get("/api/v1/health")
        data = resp.json()
        components = data["components"]
        assert "database" in components
        assert "ollama" in components
        assert "gemini" in components
        assert "rag" in components

    def test_health_version_matches(self, client):
        resp = client.get("/api/v1/health")
        data = resp.json()
        assert data["version"] == "0.1.0"


class TestHybridEndpoint:
    def test_hybrid_exists_in_swagger(self, client):
        resp = client.get("/openapi.json")
        paths = resp.json()["paths"]
        assert "/api/v1/hybrid" in paths

    def test_hybrid_empty_message_422(self, client):
        resp = client.post("/api/v1/hybrid", json={"message": ""})
        assert resp.status_code == 422

    def test_hybrid_invalid_session_error(self, client):
        resp = client.post("/api/v1/hybrid", json={
            "session_id": "nonexistent-uuid",
            "message": "halo",
        })
        assert resp.status_code in (404, 500)
        data = resp.json()
        assert "error" in data


class TestErrorHandlers:
    def test_404_on_unknown_route(self, client):
        resp = client.get("/api/v1/nonexistent")
        assert resp.status_code in (404, 405)

    def test_generic_error_format(self, client):
        """Test that error responses have proper format."""
        resp = client.post("/api/v1/hybrid", json={
            "session_id": "bad-session-id",
            "message": "test",
        })
        if resp.status_code != 200:
            data = resp.json()
            assert "error" in data
            assert "code" in data["error"]
            assert "message" in data["error"]
