# Task 05: Hotfix — Export Gagal untuk "Generate dari Dokumen"

> **Status**: [ ] Belum Dikerjakan
> **Priority**: 🔴 Critical Bug
> **Dependency**: Tidak ada (hotfix mandiri)

## 1. Deskripsi Bug

Ketika user generate TOR melalui tab **"Dari Dokumen"** (upload file), tombol download (DOCX/PDF/MD) selalu gagal dengan error:
> "TOR belum di-generate untuk session ini."

### Akar Masalah

Route `POST /generate/from-document` di `app/api/routes/generate_doc.py` **tidak menyimpan TOR ke `TORCache`** setelah berhasil generate. Langkah yang terjadi:

1. ✅ User upload dokumen
2. ✅ Gemini generate TOR → `TORDocument` tercipta
3. ✅ Backend return response dengan `session_id = "doc-{uuid}"` dan `tor_document`
4. ✅ Frontend simpan `doc_session_id` dan `doc_tor` ke `st.session_state`
5. ✅ Frontend panggil `export_document(session_id, "docx")` → `GET /api/v1/export/{session_id}`
6. ❌ **Backend cari di `TORCache.get(session_id)` → NULL → 404**

**Penyebab**: `generate_doc.py` line 60-86 tidak pernah memanggil `tor_cache.store(session_id, tor_doc)`.

**Perbandingan**: Route `/generate` yang melalui `GenerateService` sudah benar — `generate_service.py` line 131 memanggil `cache.store()`.

## 2. File yang Perlu Diubah

Hanya **1 file**: `app/api/routes/generate_doc.py`

## 3. Solusi

- [ ] Tambahkan penyimpanan TOR ke cache **sebelum** return response.

### Kode Fix

```diff
 # app/api/routes/generate_doc.py

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

+    # Simpan TOR ke cache agar bisa diakses oleh export endpoint
+    tor_cache = request.app.state.tor_cache
+    await tor_cache.store(session_id, tor_doc)

     logger.info(
         f"TOR from document: file={filename}, "
```

## 4. Testing

- [ ] Start ulang server backend
- [ ] Upload dokumen di tab "Dari Dokumen"
- [ ] Setelah TOR muncul, ketiga tombol download (DOCX/PDF/MD) harus **enabled** dan berfungsi
- [ ] File yang didownload harus bisa dibuka dan isinya sesuai

### Quick Verification Command

```bash
# Setelah generate dari dokumen, ambil session_id dari response
# lalu test manual:
curl -o test.docx "http://localhost:8000/api/v1/export/{DOC_SESSION_ID}?format=docx"
# Harus return 200, bukan 404
```

## 5. Acceptance Criteria

- [ ] `TORCache.get("doc-xxxx")` mengembalikan `TORDocument` (bukan `None`) setelah generate from document.
- [ ] Semua 3 tombol download berfungsi di tab "Dari Dokumen".
- [ ] Existing tests di `test_export_api.py` masih pass (tidak ada regresi).
