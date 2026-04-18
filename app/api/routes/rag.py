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
