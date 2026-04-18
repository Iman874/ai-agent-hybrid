# Task 06 — API Endpoint: POST /api/v1/generate/from-document

## 1. Judul Task

Buat endpoint FastAPI `POST /api/v1/generate/from-document` yang menerima file upload + konteks, parse dokumen, dan generate TOR via Gemini.

## 2. Deskripsi

Endpoint ini menerima multipart form data: file (PDF/TXT/MD/DOCX) + konteks tambahan (string opsional). Parse file via `DocumentParser`, build prompt, panggil Gemini, post-process, return TOR.

## 3. Tujuan Teknis

- `POST /api/v1/generate/from-document` menerima `file: UploadFile` + `context: str`
- Parse file → text → prompt → Gemini → post-process → response
- Return `GenerateResponse` yang sudah ada (reuse model)
- Endpoint stateless (tidak buat session)

## 4. Scope

### Yang dikerjakan
- `app/api/routes/generate_doc.py` — endpoint baru
- Register di `app/api/router.py`
- Error handler untuk `DocumentParseError`

### Yang tidak dikerjakan
- Menyimpan file ke disk
- Membuat session

## 5. Langkah Implementasi

### Step 1: Buat `app/api/routes/generate_doc.py`

```python
import logging
import uuid
from fastapi import APIRouter, Request, UploadFile, File, Form

from app.core.document_parser import DocumentParser
from app.core.gemini_prompt_builder import GeminiPromptBuilder
from app.models.generate import TORDocument, TORMetadata, GenerateResponse
from app.utils.errors import DocumentParseError

logger = logging.getLogger("ai-agent-hybrid.api.generate_doc")

router = APIRouter()


@router.post("/generate/from-document", response_model=GenerateResponse)
async def generate_from_document(
    request: Request,
    file: UploadFile = File(..., description="Dokumen sumber (PDF/TXT/MD/DOCX)"),
    context: str = Form("", description="Konteks tambahan dari user"),
):
    """
    Generate TOR dari dokumen yang diupload.
    
    - **file**: Dokumen sumber (PDF, TXT, MD, DOCX). Maks 20MB.
    - **context**: Konteks tambahan, misal "Buat TOR lanjutan 2026".
    """
    gemini = request.app.state.gemini_provider
    post_processor = request.app.state.post_processor
    rag_pipeline = getattr(request.app.state, "rag_pipeline", None)

    # Step 1: Read file
    file_bytes = await file.read()
    filename = file.filename or "unknown.txt"

    # Step 2: Parse
    document_text = await DocumentParser.parse(file_bytes, filename)

    # Step 3: RAG (optional — retrieve style examples)
    rag_examples = None
    if rag_pipeline:
        try:
            # Gunakan 200 chars pertama dokumen sebagai query
            query = document_text[:200]
            rag_examples = await rag_pipeline.retrieve(query, top_k=2)
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")

    # Step 4: Build prompt
    prompt = GeminiPromptBuilder.build_from_document(
        document_text=document_text,
        user_context=context,
        rag_examples=rag_examples,
    )

    # Step 5: Call Gemini
    gemini_response = await gemini.generate(prompt)

    # Step 6: Post-process
    processed = post_processor.process(gemini_response.text)

    tor_doc = TORDocument(
        content=processed.content,
        metadata=TORMetadata(
            generated_by=gemini.model_name,
            mode="document",
            word_count=processed.word_count,
            generation_time_ms=gemini_response.duration_ms,
            has_assumptions=processed.has_assumptions,
            prompt_tokens=gemini_response.prompt_tokens,
            completion_tokens=gemini_response.completion_tokens,
        ),
    )

    # Generate a pseudo session_id for the response
    session_id = f"doc-{uuid.uuid4().hex[:8]}"

    logger.info(
        f"TOR from document: file={filename}, "
        f"chars={len(document_text)}, words={processed.word_count}, "
        f"time={gemini_response.duration_ms}ms"
    )

    return GenerateResponse(
        session_id=session_id,
        message=f"TOR berhasil dibuat dari dokumen '{filename}'.",
        tor_document=tor_doc,
        cached=False,
    )
```

### Step 2: Register di `app/api/router.py`

Tambah:
```python
from app.api.routes.generate_doc import router as generate_doc_router
api_router.include_router(generate_doc_router, tags=["generate-document"])
```

### Step 3: Register error handler untuk DocumentParseError

Di `app/api/error_handlers.py`, tambah handler:

```python
from app.utils.errors import DocumentParseError

@app.exception_handler(DocumentParseError)
async def document_parse_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )
```

### Step 4: Expose `gemini_provider` dan `post_processor` di `app.state`

Verifikasi bahwa `app.state.gemini_provider` dan `app.state.post_processor` sudah tersedia. Jika belum (hanya `generate_service` yang ada), tambahkan di `app/main.py` lifespan:

```python
app.state.gemini_provider = gemini_provider
app.state.post_processor = post_processor
```

### Step 5: Test via curl

```bash
curl -X POST http://localhost:8000/api/v1/generate/from-document \
  -F "file=@test_document.txt" \
  -F "context=Buat TOR lanjutan" | python -m json.tool
```

## 6. Output yang Diharapkan

```json
{
    "session_id": "doc-a1b2c3d4",
    "type": "generate",
    "message": "TOR berhasil dibuat dari dokumen 'laporan.pdf'.",
    "tor_document": {
        "format": "markdown",
        "content": "# TERM OF REFERENCE\n...",
        "metadata": {
            "generated_by": "gemini-2.0-flash",
            "mode": "document",
            "word_count": 850,
            "generation_time_ms": 4200
        }
    },
    "cached": false
}
```

## 7. Dependencies

- **Task 02-04** — `DocumentParser` lengkap
- **Task 05** — `build_from_document()` prompt builder

## 8. Acceptance Criteria

- [ ] Endpoint `POST /api/v1/generate/from-document` accessible
- [ ] Menerima file upload (multipart)
- [ ] Menerima konteks tambahan (form field)
- [ ] Parse file → text → prompt → Gemini → TOR
- [ ] Response menggunakan `GenerateResponse` model
- [ ] `DocumentParseError` return 400 dengan pesan jelas
- [ ] Gemini error (timeout, rate limit) return error sesuai
- [ ] RAG diambil optional sebagai style reference
- [ ] File TIDAK disimpan di server
- [ ] Endpoint terdaftar di router

## 9. Estimasi

**Medium** — ~1.5 jam
