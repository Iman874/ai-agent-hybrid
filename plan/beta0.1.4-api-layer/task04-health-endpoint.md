# Task 04 — Enhanced Health Check Endpoint

## 1. Judul Task

Upgrade `GET /api/v1/health` — cek status semua komponen (Ollama, Gemini, RAG, Database) dengan latency measurement dan uptime tracking.

## 2. Deskripsi

Health check endpoint yang sudah ada (beta0.1.0) hanya return `{ "status": "OK" }`. Sekarang di-upgrade menjadi full component health check yang menampilkan status setiap subsystem, latency, dan uptime.

## 3. Tujuan Teknis

- Return `HealthResponse` dengan status per component
- Check Ollama connectivity + latency
- Check Gemini API key validity
- Check RAG pipeline status
- Check SQLite database accessibility
- Overall status: healthy / degraded / unhealthy
- Uptime tracking

## 4. Scope

### Yang dikerjakan
- Replace `app/api/routes/health.py` — full health check
- Tambah `app.state.start_time` di `app/main.py` (jika belum)

### Yang tidak dikerjakan
- Monitoring dashboard
- Alerting

## 5. Langkah Implementasi

### Step 1: Update `app/api/routes/health.py`

```python
import logging
import time
import aiosqlite
from fastapi import APIRouter, Request
from app.models.api import HealthResponse, ComponentHealth

logger = logging.getLogger("ai-agent-hybrid.api.health")

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    settings = request.app.state.settings
    components = {}
    overall = "healthy"

    # Check Ollama
    try:
        start = time.monotonic()
        ollama = request.app.state.chat_service.ollama
        await ollama.client.list()
        latency = (time.monotonic() - start) * 1000
        components["ollama"] = ComponentHealth(
            status="up",
            details={"model": settings.ollama_chat_model},
            latency_ms=round(latency, 1),
        )
    except Exception as e:
        components["ollama"] = ComponentHealth(status="down", details={"error": str(e)[:100]})
        overall = "degraded"

    # Check Gemini (key configured?)
    if settings.gemini_api_key and settings.gemini_api_key != "your-api-key-here":
        components["gemini"] = ComponentHealth(
            status="up",
            details={"model": settings.gemini_model},
        )
    else:
        components["gemini"] = ComponentHealth(
            status="degraded",
            details={"reason": "API key not configured"},
        )
        overall = "degraded"

    # Check RAG
    rag = getattr(request.app.state, "rag_pipeline", None)
    if rag:
        try:
            status = await rag.get_status()
            components["rag"] = ComponentHealth(
                status="up",
                details={"chunks": status.get("vector_db", {}).get("total_chunks", 0)},
            )
        except Exception:
            components["rag"] = ComponentHealth(status="down")
    else:
        components["rag"] = ComponentHealth(
            status="degraded", details={"reason": "not initialized"}
        )

    # Check Database
    try:
        async with aiosqlite.connect(settings.session_db_path) as db:
            await db.execute("SELECT 1")
        components["database"] = ComponentHealth(status="up", details={"type": "sqlite"})
    except Exception as e:
        components["database"] = ComponentHealth(status="down", details={"error": str(e)[:100]})
        overall = "unhealthy"

    uptime = time.time() - getattr(request.app.state, "start_time", time.time())

    return HealthResponse(
        status=overall,
        version=settings.app_version,
        uptime_seconds=round(uptime, 1),
        components=components,
    )
```

### Step 2: Tambah `start_time` di `app/main.py` lifespan (jika belum)

Pastikan ada: `app.state.start_time = time.time()` di awal lifespan.

### Step 3: Verifikasi

```bash
curl -s http://localhost:8000/api/v1/health | python -m json.tool
```

Expected output:
```json
{
    "status": "healthy",
    "version": "0.1.0",
    "uptime_seconds": 42.0,
    "components": {
        "ollama": {"status": "up", "details": {"model": "qwen2.5:7b-instruct"}, "latency_ms": 12.3},
        "gemini": {"status": "up", "details": {"model": "gemini-2.0-flash"}},
        "rag": {"status": "up", "details": {"chunks": 11}},
        "database": {"status": "up", "details": {"type": "sqlite"}}
    }
}
```

## 6. Output yang Diharapkan

Full health check response dengan status per component.

## 7. Dependencies

- **Task 01** — `HealthResponse`, `ComponentHealth` models
- **Task 02** — `app_version` config

## 8. Acceptance Criteria

- [ ] `GET /api/v1/health` return `HealthResponse`
- [ ] Ollama check dengan latency measurement
- [ ] Gemini API key check
- [ ] RAG pipeline check
- [ ] Database connectivity check
- [ ] Overall status: healthy/degraded/unhealthy
- [ ] Uptime tracking

## 9. Estimasi

**Medium** — ~1 jam
