# Task 02: Export API Endpoint

> **File Target**: `app/api/routes/export.py`, `app/api/router.py`
> **Dependency**: ⚠️ Membutuhkan Task 01 selesai (service + app.state setup)
> **Status**: [ ] Belum Dikerjakan

## 1. Tujuan

Membuat endpoint REST `GET /api/v1/export/{session_id}` yang menerima query param `format`, mengambil `TORDocument` dari `TORCache` (SQLite), memanggil `DocumentExporterService` untuk konversi, dan mengembalikan file binary sebagai response yang bisa langsung di-download oleh browser.

## 2. Buat File Route

- [ ] Buat file `app/api/routes/export.py`.

### 2.1 Full Implementation

```python
import logging
from typing import Literal

from fastapi import APIRouter, Request, Query
from fastapi.responses import Response

from app.utils.errors import ExportError

logger = logging.getLogger("ai-agent-hybrid.api.export")

router = APIRouter()

# Mapping format → MIME type
MIME_TYPES: dict[str, str] = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "md": "text/markdown; charset=utf-8",
}

# Mapping format → file extension
FILE_EXTENSIONS: dict[str, str] = {
    "docx": "docx",
    "pdf": "pdf",
    "md": "md",
}


@router.get("/export/{session_id}")
async def export_document(
    request: Request,
    session_id: str,
    format: Literal["docx", "pdf", "md"] = Query(
        default="docx",
        description="Format output: docx, pdf, atau md",
    ),
) -> Response:
    """Export TOR document ke format file yang diminta.

    - **session_id**: ID session yang TOR-nya sudah di-generate dan ter-cache.
    - **format**: Format file output (default: docx).

    Returns:
        Binary file content dengan header Content-Disposition untuk download.

    Raises:
        404: Session tidak ditemukan / TOR belum di-generate.
        400: Format tidak valid (ditangani oleh FastAPI type validation).
    """
    # Step 1: Ambil TORDocument dari cache
    # NOTE: app.state.tor_cache di-setup di task01 (main.py lifespan)
    tor_cache = request.app.state.tor_cache
    tor_doc = await tor_cache.get(session_id)

    if tor_doc is None:
        from app.utils.errors import SessionNotFoundError
        raise SessionNotFoundError(session_id)

    # Step 2: Konversi via DocumentExporterService
    exporter = request.app.state.document_exporter
    file_bytes = exporter.export(tor_doc.content, format)

    # Step 3: Build response
    mime = MIME_TYPES[format]
    ext = FILE_EXTENSIONS[format]
    # Truncate session_id agar filename tidak terlalu panjang
    short_id = session_id[:8] if len(session_id) > 8 else session_id
    filename = f"TOR_{short_id}.{ext}"

    logger.info(
        f"Export document: session={session_id}, "
        f"format={format}, size={len(file_bytes)} bytes"
    )

    return Response(
        content=file_bytes,
        media_type=mime,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
```

### 2.2 Catatan Desain

| Keputusan | Alasan |
|---|---|
| **`Response` bukan `StreamingResponse`** | File TOR umumnya kecil (< 1MB). `Response` lebih simpel dan cukup. `StreamingResponse` hanya perlu jika file sangat besar. |
| **`Literal["docx", "pdf", "md"]`** | FastAPI otomatis validasi dan return 422 jika format invalid. Tidak perlu validasi manual. |
| **`SessionNotFoundError`** | Reuse error class yang sudah ada di `app/utils/errors.py` (code E006). Error handler di `app/api/error_handlers.py` sudah menangani class ini → return HTTP 404. |
| **Truncate session_id di filename** | UUID penuh (36 char) membuat filename terlalu panjang. 8 char cukup untuk identifikasi. |

## 3. Registrasi Router

- [ ] Update file `app/api/router.py` — tambahkan import dan include router:

```diff
 from fastapi import APIRouter
 
-from app.api.routes import health, chat, session, rag, generate, hybrid, generate_doc, models, styles
+from app.api.routes import health, chat, session, rag, generate, hybrid, generate_doc, models, styles, export
 
 api_router = APIRouter()
 
 api_router.include_router(hybrid.router, tags=["Hybrid"])
 api_router.include_router(chat.router, tags=["Chat"])
 api_router.include_router(generate.router, tags=["Generate"])
 api_router.include_router(generate_doc.router, tags=["Generate-Document"])
+api_router.include_router(export.router, tags=["Export"])
 api_router.include_router(models.router, tags=["Models"])
 api_router.include_router(session.router, tags=["Session"])
 api_router.include_router(rag.router, tags=["RAG"])
 api_router.include_router(styles.router, tags=["Styles"])
 api_router.include_router(health.router, tags=["Health"])
```

## 4. Verifikasi Error Handler Compatibility

- [ ] Pastikan `SessionNotFoundError` sudah ditangani di `app/api/error_handlers.py`.

Dari kode yang ada, `register_error_handlers()` sudah menangkap `AppError` secara generik. `SessionNotFoundError` extends `AppError`, jadi seharusnya otomatis return:

```json
{
  "error": {
    "code": "E006",
    "message": "Session tidak ditemukan. Mulai percakapan baru.",
    "details": "session_id: ..."
  }
}
```

- [ ] Pastikan juga `ExportError` (dari task01) ditangani — sudah covered karena extends `AppError`.

## 5. Test Manual (Quick Smoke Test)

Setelah server berjalan:

```bash
# Pastikan ada TOR yang ter-cache untuk session tertentu
# (generate TOR via chat dulu, lalu coba export)

# Test happy path:
curl -o test.docx "http://localhost:8000/api/v1/export/{SESSION_ID}?format=docx"
curl -o test.pdf  "http://localhost:8000/api/v1/export/{SESSION_ID}?format=pdf"
curl -o test.md   "http://localhost:8000/api/v1/export/{SESSION_ID}?format=md"

# Test 404 (session tidak ada):
curl -v "http://localhost:8000/api/v1/export/nonexistent-id?format=docx"

# Test 422 (format invalid — ditolak oleh FastAPI validation):
curl -v "http://localhost:8000/api/v1/export/{SESSION_ID}?format=xlsx"
```

## 6. Acceptance Criteria

- [ ] `GET /api/v1/export/{valid_session}?format=docx` → HTTP 200, header `Content-Disposition` berisi `.docx`, MIME type benar.
- [ ] `GET /api/v1/export/{valid_session}?format=pdf` → HTTP 200, MIME `application/pdf`.
- [ ] `GET /api/v1/export/{valid_session}?format=md` → HTTP 200, MIME `text/markdown`.
- [ ] `GET /api/v1/export/{invalid_session}` → HTTP 404 dengan body error code `E006`.
- [ ] `GET /api/v1/export/{valid_session}?format=xlsx` → HTTP 422 (FastAPI validation error).
- [ ] Endpoint muncul di Swagger docs (`/docs`) di bawah tag "Export".
