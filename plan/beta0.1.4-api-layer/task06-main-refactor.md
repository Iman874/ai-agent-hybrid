# Task 06 — Main.py Refactor: Clean Lifespan + start_time

## 1. Judul Task

Refactor `app/main.py` — clean up lifespan, add `start_time` tracking, use modular error handlers, update app metadata.

## 2. Deskripsi

Finalisasi `app/main.py` sebagai entry point aplikasi yang bersih: update title/description, gunakan `register_error_handlers()` dari file terpisah, tambah `start_time` untuk uptime tracking, pastikan semua services ter-wire.

## 3. Tujuan Teknis

- `app.state.start_time = time.time()` di awal lifespan
- Remove inline error handlers (pindah ke error_handlers.py)
- Update FastAPI metadata (title, description, version)
- Pastikan import error_handlers dan panggil `register_error_handlers(app)`

## 4. Scope

### Yang dikerjakan
- Update `app/main.py`

### Yang tidak dikerjakan
- Tidak mengubah logic init services yang sudah ada

## 5. Langkah Implementasi

### Step 1: Update `app/main.py`

Key changes:
1. Tambah `import time` dan `app.state.start_time = time.time()` di lifespan
2. Remove semua inline `@app.exception_handler(...)` blocks (5 handlers)
3. Tambah `from app.api.error_handlers import register_error_handlers`
4. Tambah `register_error_handlers(app)` setelah CORS middleware
5. Update `title` dan `description` FastAPI

```python
import time

# Di lifespan, awal:
app.state.start_time = time.time()

# Setelah CORS:
from app.api.error_handlers import register_error_handlers
register_error_handlers(app)

# Update FastAPI metadata:
app = FastAPI(
    title="AI Agent Hybrid — TOR Generator",
    description="Hybrid AI system combining local LLM and Google Gemini for TOR generation.",
    version="0.1.0",
    ...
)
```

### Step 2: Verifikasi

```python
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert hasattr(app.state, "start_time")
    assert hasattr(app.state, "decision_engine")
    print("MAIN.PY REFACTOR TEST PASSED")
```

## 6. Output yang Diharapkan

Clean `main.py` tanpa inline error handlers, dengan start_time tracking.

## 7. Dependencies

- **Task 05** — `error_handlers.py`

## 8. Acceptance Criteria

- [ ] `app.state.start_time` ter-set
- [ ] Tidak ada inline error handlers di main.py
- [ ] `register_error_handlers(app)` dipanggil
- [ ] Server start tanpa error
- [ ] App title updated

## 9. Estimasi

**Low** — ~30 menit
