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
    doc_gen_repo = request.app.state.doc_gen_repo

    # Step 1: Read file
    file_bytes = await file.read()
    filename = file.filename or "unknown.txt"
    session_id = f"doc-{uuid.uuid4().hex[:8]}"

    # Step 2: Get active style
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

    # Step 3: Persist record (status=processing)
    await doc_gen_repo.create(
        gen_id=session_id,
        filename=filename,
        file_size=len(file_bytes),
        context=context,
        style_id=getattr(active_style, 'id', style_id),
        style_name=getattr(active_style, 'name', None),
    )

    try:
        # Step 4: Parse document → text
        document_text = await DocumentParser.parse(file_bytes, filename)

        # Step 5: RAG (optional — retrieve style examples)
        rag_examples = None
        if rag_pipeline:
            try:
                query = document_text[:200]
                rag_examples = await rag_pipeline.retrieve(query, top_k=2)
            except Exception as e:
                logger.warning(f"RAG retrieval failed, continuing without: {e}")

        format_spec = active_style.to_prompt_spec()

        # Step 6: Build prompt
        prompt = GeminiPromptBuilder.build_from_document(
            document_text=document_text,
            user_context=context,
            rag_examples=rag_examples,
            format_spec=format_spec,
        )

        # Step 7: Call Gemini
        gemini_response = await gemini.generate(prompt)

        # Step 8: Post-process
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

        # Step 9: Persist completed
        import json
        await doc_gen_repo.update_completed(
            session_id,
            tor_content=processed.content,
            metadata_json=json.dumps(tor_doc.metadata.model_dump()),
        )

        # Simpan TOR ke cache agar bisa diakses oleh export endpoint lama
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

    except Exception as e:
        # Step 10: Persist failure
        await doc_gen_repo.update_failed(session_id, str(e)[:500])
        raise


from app.models.generate import DocGenListItem, DocGenDetail

@router.get("/generate/history", response_model=list[DocGenListItem])
async def list_generations(request: Request, limit: int = 30):
    """List riwayat generate dari dokumen, urut terbaru."""
    doc_gen_repo = request.app.state.doc_gen_repo
    rows = await doc_gen_repo.list_all(limit=limit)

    return [
        DocGenListItem(
            id=r["id"],
            filename=r["filename"],
            file_size=r["file_size"],
            style_name=r.get("style_name"),
            status=r["status"],
            word_count=r.get("word_count"),
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/generate/{gen_id}", response_model=DocGenDetail)
async def get_generation(gen_id: str, request: Request):
    """Ambil detail satu generate result."""
    doc_gen_repo = request.app.state.doc_gen_repo
    row = await doc_gen_repo.get(gen_id)

    if not row:
        raise HTTPException(status_code=404, detail="Record tidak ditemukan")

    metadata = None
    if row.get("metadata"):
        try:
            metadata = TORMetadata(**row["metadata"])
        except Exception:
            pass

    return DocGenDetail(
        id=row["id"],
        filename=row["filename"],
        file_size=row["file_size"],
        context=row.get("context", ""),
        style_name=row.get("style_name"),
        status=row["status"],
        tor_content=row.get("tor_content"),
        metadata=metadata,
        error_message=row.get("error_message"),
        created_at=row["created_at"],
    )


@router.delete("/generate/{gen_id}")
async def delete_generation(gen_id: str, request: Request):
    """Hapus record riwayat generate."""
    doc_gen_repo = request.app.state.doc_gen_repo
    success = await doc_gen_repo.delete(gen_id)
    if not success:
        raise HTTPException(status_code=404, detail="Record tidak ditemukan")
    return {"status": "deleted", "id": gen_id}
