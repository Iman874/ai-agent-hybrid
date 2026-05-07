import logging
from typing import Literal

from fastapi import APIRouter, Request, Query
from fastapi.responses import Response

from app.utils.errors import SessionNotFoundError
from app.models.generate import TORDocument, TORMetadata

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

    - **session_id**: ID session yang TOR-nya sudah di-generate.
    - **format**: Format file output (default: docx).

    Returns:
        Binary file content dengan header Content-Disposition untuk download.

    Raises:
        404: Session/TOR tidak ditemukan.
        422: Format tidak valid (ditangani oleh FastAPI Literal validation).
    """
    # Step 1: Ambil TORDocument dari cache
    tor_cache = request.app.state.tor_cache
    tor_doc = await tor_cache.get(session_id)

    # Step 2: Fallback ke session manager jika cache miss
    if tor_doc is None:
        logger.info(f"Cache miss for session {session_id}, trying session manager fallback...")
        try:
            session_mgr = request.app.state.session_mgr
            session = await session_mgr.get(session_id)
            if session.generated_tor:
                tor_doc = TORDocument(
                    content=session.generated_tor,
                    metadata=TORMetadata(
                        generated_by="",
                        generator="",
                        mode="",
                        word_count=0,
                        generation_time_ms=0,
                        has_assumptions=False,
                        prompt_tokens=0,
                        completion_tokens=0,
                    ),
                )
                # Simpan ke cache untuk下次
                await tor_cache.store(session_id, tor_doc)
            else:
                raise SessionNotFoundError(session_id)
        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Session manager fallback failed: {e}")
            raise SessionNotFoundError(session_id)

    # Step 3: Konversi via DocumentExporterService
    exporter = request.app.state.document_exporter
    file_bytes = exporter.export(tor_doc.content, format)

    # Step 4: Build response
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
