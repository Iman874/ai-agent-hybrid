import logging
import uuid
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException

from app.core.document_parser import DocumentParser
from app.core.gemini_prompt_builder import GeminiPromptBuilder
from app.core.style_manager import StyleNotFoundError
from app.models.generate import TORDocument, TORMetadata, GenerateResponse
from app.utils.errors import DocumentParseError

logger = logging.getLogger("ai-agent-hybrid.api.generate_doc")

router = APIRouter()


@router.post("/generate/from-document", response_model=GenerateResponse)
async def generate_from_document(
    request: Request,
    file: UploadFile = File(..., description="Dokumen sumber (PDF/TXT/MD/DOCX)"),
    context: str = Form("", description="Konteks tambahan dari user"),
    style_id: str | None = Form(None, description="ID style TOR spesifik (default=aktif)"),
):
    """
    Generate TOR dari dokumen yang diupload.

    - **file**: Dokumen sumber (PDF, TXT, MD, DOCX). Maks 20MB.
    - **context**: Konteks tambahan, misal "Buat TOR lanjutan 2026".
    """
    gemini = request.app.state.gemini_provider
    post_processor = request.app.state.post_processor
    rag_pipeline = getattr(request.app.state, "rag_pipeline", None)
    style_manager = request.app.state.style_manager

    # Step 1: Read file
    file_bytes = await file.read()
    filename = file.filename or "unknown.txt"

    # Step 2: Parse document → text
    document_text = await DocumentParser.parse(file_bytes, filename)

    # Step 3: RAG (optional — retrieve style examples)
    rag_examples = None
    if rag_pipeline:
        try:
            query = document_text[:200]
            rag_examples = await rag_pipeline.retrieve(query, top_k=2)
        except Exception as e:
            logger.warning(f"RAG retrieval failed, continuing without: {e}")

    # Step 3b: Get formatting style
    if style_id:
        try:
            active_style = style_manager.get_style(style_id)
        except StyleNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Style '{style_id}' tidak ditemukan.",
            )
    else:
        active_style = style_manager.get_active_style()

    format_spec = active_style.to_prompt_spec()

    # Step 4: Build prompt
    prompt = GeminiPromptBuilder.build_from_document(
        document_text=document_text,
        user_context=context,
        rag_examples=rag_examples,
        format_spec=format_spec,
    )

    # Step 5: Call Gemini
    gemini_response = await gemini.generate(prompt)

    # Step 6: Post-process
    processed = post_processor.process(gemini_response.text, style=active_style)

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

    session_id = f"doc-{uuid.uuid4().hex[:8]}"

    # Simpan TOR ke cache agar bisa diakses oleh export endpoint
    tor_cache = request.app.state.tor_cache
    await tor_cache.store(session_id, tor_doc)

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
