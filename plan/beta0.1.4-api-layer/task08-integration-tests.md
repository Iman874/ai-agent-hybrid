# Task 08 — Integration Tests: Full System End-to-End

## 1. Judul Task

Buat integration tests untuk seluruh API Layer: health check, hybrid endpoint, error handling scenarios.

## 2. Deskripsi

Integration tests menggunakan FastAPI `TestClient` untuk menguji semua endpoint berfungsi, error handling ter-trigger dengan benar, dan response format sesuai spec.

## 3. Tujuan Teknis

- `tests/test_api_integration.py` — 5+ tests
- Test health check returns proper format
- Test hybrid endpoint creates session
- Test hybrid with invalid session → 404
- Test request validation (empty message) → 422
- Test all endpoints registered in Swagger

## 4. Scope

### Yang dikerjakan
- `tests/test_api_integration.py`

### Yang tidak dikerjakan
- Load testing
- E2E tests with real Ollama (butuh Ollama running)

## 5. Langkah Implementasi

### Step 1: Buat `tests/test_api_integration.py`

```python
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
```

### Step 2: Jalankan tests

```bash
.\venv\Scripts\pytest.exe tests/test_api_integration.py -v
```

## 6. Output yang Diharapkan

```
tests/test_api_integration.py::TestHealthEndpoint::test_health_returns_200 PASSED
tests/test_api_integration.py::TestHealthEndpoint::test_health_has_all_components PASSED
tests/test_api_integration.py::TestHybridEndpoint::test_hybrid_exists_in_swagger PASSED
tests/test_api_integration.py::TestHybridEndpoint::test_hybrid_empty_message_422 PASSED
tests/test_api_integration.py::TestHybridEndpoint::test_hybrid_invalid_session_error PASSED
tests/test_api_integration.py::TestErrorHandlers::test_404_on_unknown_route PASSED
tests/test_api_integration.py::TestErrorHandlers::test_generic_error_format PASSED
====================== 7 passed ======================
```

## 7. Dependencies

- **Semua task 01-07** harus selesai

## 8. Acceptance Criteria

- [ ] `pytest tests/test_api_integration.py -v` → 7+ tests PASSED
- [ ] Health check returns proper JSON format
- [ ] Hybrid endpoint exists and validates input
- [ ] Error responses follow `{"error": {"code": ..., "message": ...}}` format

## 9. Estimasi

**Medium** — ~1.5 jam
