# Task 01: Wire Active Style ke generate_doc.py

> **Status**: [x] Selesai
> **Estimasi**: Low (30 menit – 1 jam)
> **Dependency**: Tidak ada (task pertama, bug fix kritis)

## 1. Deskripsi

Fix bug di `app/api/routes/generate_doc.py` di mana `format_spec` **tidak di-pass** ke `GeminiPromptBuilder.build_from_document()`, sehingga TOR yang di-generate dari dokumen upload mengabaikan active style. Juga fix `post_processor.process()` yang tidak menerima `style`.

## 2. Tujuan Teknis

- `generate_doc.py` menggunakan `style_manager.get_active_style()` untuk mendapatkan format spec
- `format_spec` di-inject ke `GeminiPromptBuilder.build_from_document()`
- `post_processor.process()` menerima `style=active_style` untuk validasi seksi dinamis

## 3. Scope

**Yang dikerjakan:**
- Modifikasi `app/api/routes/generate_doc.py` — 3 perubahan:
  1. Ambil `style_manager` dari `app.state`
  2. Pass `format_spec` ke prompt builder
  3. Pass `style` ke post_processor

**Yang tidak dikerjakan:**
- Parameter `style_id` spesifik (task02)
- UI perubahan (task03-04)

## 4. Langkah Implementasi

### 4.1 Ambil `style_manager` dari `app.state`

- [x] Di `generate_from_document()` (line 27-29), tambahkan:

```python
    gemini = request.app.state.gemini_provider
    post_processor = request.app.state.post_processor
    rag_pipeline = getattr(request.app.state, "rag_pipeline", None)
    style_manager = request.app.state.style_manager  # ← BARU
```

### 4.2 Ambil Active Style dan Build Format Spec

- [x] Sebelum Step 4 (Build prompt, line 47), tambahkan:

```python
    # Step 3b: Get active formatting style
    active_style = style_manager.get_active_style()
    format_spec = active_style.to_prompt_spec()
```

### 4.3 Inject `format_spec` ke Prompt Builder

- [x] Ubah Step 4 (line 48-52) dari:

```python
    # SEBELUM:
    prompt = GeminiPromptBuilder.build_from_document(
        document_text=document_text,
        user_context=context,
        rag_examples=rag_examples,
    )
```

Menjadi:

```python
    # SESUDAH:
    prompt = GeminiPromptBuilder.build_from_document(
        document_text=document_text,
        user_context=context,
        rag_examples=rag_examples,
        format_spec=format_spec,  # ← BARU
    )
```

### 4.4 Pass Style ke PostProcessor

- [x] Ubah Step 6 (line 58) dari:

```python
    # SEBELUM:
    processed = post_processor.process(gemini_response.text)
```

Menjadi:

```python
    # SESUDAH:
    processed = post_processor.process(gemini_response.text, style=active_style)
```

## 5. Output yang Diharapkan

Setelah perubahan, file `generate_doc.py` line 27-58 menjadi:

```python
    gemini = request.app.state.gemini_provider
    post_processor = request.app.state.post_processor
    rag_pipeline = getattr(request.app.state, "rag_pipeline", None)
    style_manager = request.app.state.style_manager

    # ... existing Step 1, 2, 3 ...

    # Step 3b: Get active formatting style
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
```

## 6. Acceptance Criteria

- [x] Server start tanpa error.
- [x] `generate_doc.py` mengambil `style_manager` dari `app.state`.
- [x] `format_spec` di-pass ke `build_from_document()`.
- [x] `post_processor.process()` menerima `style=active_style`.
- [x] Endpoint `POST /generate/from-document` masih return 200 untuk file valid.
