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
