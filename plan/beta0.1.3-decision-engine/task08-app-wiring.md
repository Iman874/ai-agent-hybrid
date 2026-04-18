# Task 08 — App Wiring: Init DecisionEngine di main.py

## 1. Judul Task

Wire semua komponen Decision Engine di `app/main.py` lifespan dan attach ke `app.state.decision_engine`.

## 2. Deskripsi

Menginisialisasi `EscalationChecker`, `ProgressTracker`, `EscalationLogger`, dan `DecisionEngine` di dalam lifespan FastAPI, lalu attach ke `app.state` agar bisa diakses oleh endpoint hybrid di beta0.1.4.

## 3. Tujuan Teknis

- Init `EscalationChecker(EscalationConfig())` di lifespan
- Init `ProgressTracker()` di lifespan
- Init `EscalationLogger(settings.session_db_path)` di lifespan
- Init `DecisionEngine(...)` dengan semua dependencies
- Attach ke `app.state.decision_engine`

## 4. Scope

### Yang dikerjakan
- Update `app/main.py` — init dan wiring DecisionEngine

### Yang tidak dikerjakan
- API endpoint (itu beta0.1.4)
- Perubahan ke komponen lain

## 5. Langkah Implementasi

### Step 1: Update `app/main.py` lifespan

Setelah inisialisasi GenerateService dan sebelum ChatService (atau setelahnya), tambahkan:

```python
from app.core.escalation_config import EscalationConfig
from app.core.escalation_checker import EscalationChecker
from app.core.progress_tracker import ProgressTracker
from app.core.decision_engine import DecisionEngine
from app.db.repositories.escalation_repo import EscalationLogger

# Init Decision Engine components
escalation_checker = EscalationChecker(EscalationConfig())
progress_tracker = ProgressTracker()
escalation_logger = EscalationLogger(settings.session_db_path)

app.state.decision_engine = DecisionEngine(
    chat_service=app.state.chat_service,
    generate_service=app.state.generate_service,
    session_mgr=session_mgr,
    escalation_checker=escalation_checker,
    progress_tracker=progress_tracker,
    escalation_logger=escalation_logger,
    rag_pipeline=rag_pipeline,
)
logger.info("Decision Engine initialized")
```

**PENTING**: Pastikan block ini SETELAH `chat_service` dan `generate_service` sudah di-init.

### Step 2: Verifikasi

```bash
# Start server — harus tidak ada error
.\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

Cek log harus menunjukkan:
```
INFO: Decision Engine initialized
```

Atau via TestClient:
```python
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert hasattr(app.state, "decision_engine")
    print("WIRING TEST PASSED")
```

## 6. Output yang Diharapkan

Server startup menunjukkan "Decision Engine initialized" tanpa error.

## 7. Dependencies

- **Task 02** — `EscalationConfig`
- **Task 03** — `EscalationChecker`
- **Task 04** — `ProgressTracker`
- **Task 06** — `EscalationLogger`
- **Task 07** — `DecisionEngine`
- **beta0.1.0** — `ChatService`, `SessionManager` (existing)
- **beta0.1.2** — `GenerateService` (existing)

## 8. Acceptance Criteria

- [ ] Server start tanpa error setelah wiring
- [ ] `app.state.decision_engine` ter-set
- [ ] Log menunjukkan "Decision Engine initialized"
- [ ] Health check masih berjalan normal

## 9. Estimasi

**Low** — ~30 menit
