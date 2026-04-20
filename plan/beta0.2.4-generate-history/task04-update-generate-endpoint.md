# Task 4: Update `POST /generate/from-document` — Persist ke DB

## 1. Judul Task
Modifikasi endpoint generate agar setiap proses disimpan ke tabel `document_generations`.

## 2. Deskripsi
Saat ini `POST /generate/from-document` hanya menyimpan hasil ke `tor_cache` (volatile). Setelah task ini, setiap generate akan:
1. Insert record `processing` sebelum proses dimulai
2. Update `completed` + tor_content setelah berhasil
3. Update `failed` + error_message jika gagal

## 3. Tujuan Teknis
- Inisialisasi `DocGenerationRepo` di `app/main.py` dan attach ke `app.state`
- Modifikasi `generate_doc.py` untuk menggunakan repo
- Response tetap `GenerateResponse` (backward compatible)

## 4. Scope
### Yang dikerjakan
- Modifikasi `app/api/routes/generate_doc.py`
- Modifikasi `app/main.py` (init repo)

### Yang tidak dikerjakan
- Tidak membuat endpoint baru (task 5)
- Tidak mengubah frontend

## 5. Langkah Implementasi

### Step 1: Init repo di `app/main.py`

Cari bagian startup/lifespan di `main.py`. Tambahkan:

```python
from app.db.repositories.doc_generation_repo import DocGenerationRepo

# Di bagian startup:
app.state.doc_gen_repo = DocGenerationRepo(settings.db_path)
```

### Step 2: Modifikasi `app/api/routes/generate_doc.py`

Wrap logic existing dalam try-except untuk persist:

```python
@router.post("/generate/from-document", response_model=GenerateResponse)
async def generate_from_document(
    request: Request,
    file: UploadFile = File(...),
    context: str = Form(""),
    style_id: str | None = Form(None),
):
    gemini = request.app.state.gemini_provider
    post_processor = request.app.state.post_processor
    rag_pipeline = getattr(request.app.state, "rag_pipeline", None)
    style_manager = request.app.state.style_manager
    doc_gen_repo = request.app.state.doc_gen_repo

    file_bytes = await file.read()
    filename = file.filename or "unknown.txt"
    session_id = f"doc-{uuid.uuid4().hex[:8]}"

    # Resolve style name
    if style_id:
        try:
            active_style = style_manager.get_style(style_id)
        except StyleNotFoundError:
            raise HTTPException(status_code=404, detail=f"Style '{style_id}' tidak ditemukan.")
    else:
        active_style = style_manager.get_active_style()

    # Step 1: Persist record (status=processing)
    await doc_gen_repo.create(
        gen_id=session_id,
        filename=filename,
        file_size=len(file_bytes),
        context=context,
        style_id=active_style.id if hasattr(active_style, 'id') else style_id,
        style_name=active_style.name if hasattr(active_style, 'name') else None,
    )

    try:
        # Step 2: Parse + RAG + Prompt + Gemini + Post-process (existing logic)
        document_text = await DocumentParser.parse(file_bytes, filename)

        rag_examples = None
        if rag_pipeline:
            try:
                rag_examples = await rag_pipeline.retrieve(document_text[:200], top_k=2)
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")

        format_spec = active_style.to_prompt_spec()
        prompt = GeminiPromptBuilder.build_from_document(
            document_text=document_text, user_context=context,
            rag_examples=rag_examples, format_spec=format_spec,
        )
        gemini_response = await gemini.generate(prompt)
        processed = post_processor.process(gemini_response.text, style=active_style)

        tor_doc = TORDocument(
            content=processed.content,
            metadata=TORMetadata(
                generated_by=gemini.model_name, mode="document",
                word_count=processed.word_count,
                generation_time_ms=gemini_response.duration_ms,
                has_assumptions=processed.has_assumptions,
                prompt_tokens=gemini_response.prompt_tokens,
                completion_tokens=gemini_response.completion_tokens,
            ),
        )

        # Step 3: Persist completed
        import json
        await doc_gen_repo.update_completed(
            session_id,
            tor_content=processed.content,
            metadata_json=json.dumps(tor_doc.metadata.model_dump()),
        )

        # Also store in tor_cache for export compatibility
        tor_cache = request.app.state.tor_cache
        await tor_cache.store(session_id, tor_doc)

        logger.info(f"TOR from document: file={filename}, words={processed.word_count}")

        return GenerateResponse(
            session_id=session_id, message=f"TOR berhasil dibuat dari dokumen '{filename}'.",
            tor_document=tor_doc, cached=False,
        )

    except Exception as e:
        # Step 4: Persist failure
        await doc_gen_repo.update_failed(session_id, str(e)[:500])
        raise
```

## 6. Output yang Diharapkan

**Setelah generate berhasil:**
```sql
SELECT * FROM document_generations WHERE id='doc-abc123';
-- id=doc-abc123, filename=TOR.docx, status=completed, tor_content=...
```

**Setelah generate gagal:**
```sql
SELECT * FROM document_generations WHERE id='doc-fail01';
-- id=doc-fail01, filename=bad.txt, status=failed, error_message=...
```

## 7. Dependencies
- Task 1 (tabel harus ada)
- Task 2 (repo harus ada)

## 8. Acceptance Criteria
- [ ] `DocGenerationRepo` di-init di `main.py` dan attached ke `app.state`
- [ ] Setiap generate membuat record `processing` sebelum proses
- [ ] Generate sukses → record update ke `completed` + tor_content + metadata_json
- [ ] Generate gagal → record update ke `failed` + error_message
- [ ] Response API tetap sama (backward compatible)
- [ ] Backend restart tanpa error

## 9. Estimasi
**Medium** (~1 jam)
