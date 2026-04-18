# Task 10 — REST API Endpoints: POST /ingest dan GET /status

## 1. Judul Task

Implementasi dua REST endpoint RAG: `POST /api/v1/rag/ingest` (upload & index dokumen) dan `GET /api/v1/rag/status` (status vector DB).

## 2. Deskripsi

Membuat route FastAPI untuk RAG system dan mendaftarkannya ke central router. Endpoint ingest menerima multipart/form-data (file upload + category), melakukan validasi format file, lalu memanggil `RAGPipeline.ingest_from_uploads()`. Endpoint status memanggil `RAGPipeline.get_status()`.

## 3. Tujuan Teknis

- `POST /api/v1/rag/ingest` — max 10 file, only `.md` / `.txt`, max 1MB per file
- `GET /api/v1/rag/status` — return vector DB metadata
- `RAGPipeline` diakses via `request.app.state.rag_pipeline`
- Error handling: file format salah → 400, category salah → 422, embedding model down → 503

## 4. Scope

### Yang dikerjakan
- `app/api/routes/rag.py` — endpoint ingest dan status
- Update `app/api/router.py` — register RAG router
- Update `app/main.py` — init `RAGPipeline` di lifespan dan attach ke `app.state`

### Yang tidak dikerjakan
- Batch ingest script (itu task 11)
- Integration dengan ChatService (itu task 12)

## 5. Langkah Implementasi

### Step 1: Install `python-multipart`

Tambahkan ke `requirements.txt`:
```
python-multipart>=0.0.9
```

```bash
.\venv\Scripts\pip.exe install "python-multipart>=0.0.9"
```

### Step 2: Buat `app/api/routes/rag.py`

```python
import logging
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse

from app.utils.errors import UnsupportedFormatError, EmbeddingModelError

logger = logging.getLogger("ai-agent-hybrid.api.rag")

router = APIRouter()

MAX_FILES = 10
MAX_FILE_SIZE_MB = 1
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
SUPPORTED_FORMATS = {".md", ".txt"}


@router.post("/rag/ingest")
async def ingest_documents(
    request: Request,
    files: list[UploadFile] = File(..., description="File .md atau .txt. Max 10 file."),
    category: Literal["tor_template", "tor_example", "guideline"] = Form(...),
):
    """
    Upload dan index dokumen ke vector database.

    - **files**: List file `.md` atau `.txt` (max 10, masing-masing max 1MB)
    - **category**: Kategori dokumen: `tor_template`, `tor_example`, atau `guideline`
    """
    rag_pipeline = request.app.state.rag_pipeline

    # Validasi jumlah file
    if len(files) > MAX_FILES:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "E012",
                    "message": f"Terlalu banyak file. Maksimum {MAX_FILES} file per request.",
                }
            }
        )

    # Baca dan validasi setiap file
    uploads = []
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in SUPPORTED_FORMATS:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "E009",
                        "message": f"Format file tidak didukung: {file.filename}. Gunakan .md atau .txt",
                        "supported_formats": list(SUPPORTED_FORMATS),
                    }
                }
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "E013",
                        "message": f"File terlalu besar: {file.filename}. Maksimum {MAX_FILE_SIZE_MB}MB.",
                    }
                }
            )

        uploads.append((file.filename, content))

    # Jalankan ingest pipeline
    try:
        result = await rag_pipeline.ingest_from_uploads(uploads, category)
    except EmbeddingModelError as e:
        return JSONResponse(
            status_code=503,
            content={"error": {"code": e.code, "message": e.details}}
        )

    return result


@router.get("/rag/status")
async def rag_status(request: Request):
    """
    Status vector database dan daftar dokumen yang sudah di-ingest.
    """
    rag_pipeline = request.app.state.rag_pipeline

    try:
        status = await rag_pipeline.get_status()
        return status
    except Exception as e:
        logger.error(f"RAG status error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "E005",
                    "message": "Vector database tidak accessible",
                    "details": str(e),
                }
            }
        )
```

### Step 3: Update `app/api/router.py`

Tambahkan import dan include router untuk RAG:

```python
from app.api.routes import health, chat, session, rag  # tambah rag

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(session.router, tags=["Session"])
api_router.include_router(rag.router, tags=["RAG"])  # tambah ini
```

### Step 4: Update `app/main.py` lifespan

Di dalam `async with lifespan(app)`, tambahkan setelah init `session_mgr`:

```python
from app.rag.pipeline import RAGPipeline

# Init RAG Pipeline
rag_pipeline = RAGPipeline(settings)
app.state.rag_pipeline = rag_pipeline
logger.info("RAG Pipeline initialized")
```

### Step 5: Verifikasi dengan TestClient

```python
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    # Test 1: GET /status (tanpa dokumen)
    resp = client.get("/api/v1/rag/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "vector_db" in data
    print(f"Test 1 passed: status={data['status']}")

    # Test 2: POST /ingest dengan format tidak didukung
    resp2 = client.post(
        "/api/v1/rag/ingest",
        data={"category": "tor_example"},
        files={"files": ("test.pdf", b"PDF content", "application/pdf")},
    )
    assert resp2.status_code == 400
    assert resp2.json()["error"]["code"] == "E009"
    print("Test 2 passed: unsupported format → 400")

    # Test 3: Category tidak valid
    resp3 = client.post(
        "/api/v1/rag/ingest",
        data={"category": "invalid_category"},
        files={"files": ("test.md", b"# Test\n\nIni test markdown.", "text/markdown")},
    )
    assert resp3.status_code == 422
    print("Test 3 passed: invalid category → 422")

    print("ALL RAG ENDPOINT TESTS PASSED")
```

## 6. Output yang Diharapkan

### GET /api/v1/rag/status:
```json
{
    "status": "healthy",
    "vector_db": {
        "type": "chromadb",
        "collection": "tor_documents",
        "total_chunks": 0,
        "total_documents": 0,
        "embedding_model": "bge-m3",
        "embedding_dimensions": 1024
    },
    "documents": []
}
```

### POST /api/v1/rag/ingest (400 Bad Request):
```json
{
    "error": {
        "code": "E009",
        "message": "Format file tidak didukung: proposal.pdf. Gunakan .md atau .txt",
        "supported_formats": [".md", ".txt"]
    }
}
```

## 7. Dependencies

- **Task 08** — `RAGPipeline`
- **Task 12 (beta0.1.0)** — `app/main.py`, `app/api/router.py`

## 8. Acceptance Criteria

- [ ] `GET /api/v1/rag/status` return 200 dengan struktur `{status, vector_db, documents}`
- [ ] `POST /api/v1/rag/ingest` dengan file `.md` valid → 200 OK
- [ ] `POST /api/v1/rag/ingest` dengan file `.pdf` → 400, code `E009`
- [ ] `POST /api/v1/rag/ingest` dengan `category="invalid"` → 422 Pydantic error
- [ ] `POST /api/v1/rag/ingest` lebih dari 10 file → 400, code `E012`
- [ ] Endpoint muncul di Swagger `/docs` under tag "RAG"

## 9. Estimasi

**Medium** — ~2 jam
