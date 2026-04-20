# Task 5: Endpoint Baru — History, Detail, Delete

## 1. Judul Task
Buat 3 endpoint baru untuk mengakses riwayat generate: list, detail, dan delete.

## 2. Deskripsi
Frontend memerlukan API untuk menampilkan riwayat generate, melihat detail hasil TOR, dan menghapus record yang tidak dibutuhkan.

## 3. Tujuan Teknis
- `GET /generate/history?limit=30` → list riwayat
- `GET /generate/{gen_id}` → detail satu result
- `DELETE /generate/{gen_id}` → hapus record

## 4. Scope
### Yang dikerjakan
- Tambah 3 endpoint di `app/api/routes/generate_doc.py`

### Yang tidak dikerjakan
- Tidak mengubah frontend (task 6-10)

## 5. Langkah Implementasi

### Step 1: Tambah endpoint di `app/api/routes/generate_doc.py`

```python
from app.models.generate import DocGenListItem, DocGenDetail, TORMetadata

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
```

### Step 2: Verifikasi

Test dengan `curl` atau browser:

```bash
# List history
curl http://localhost:8000/api/v1/generate/history

# Get detail
curl http://localhost:8000/api/v1/generate/doc-abc123

# Delete
curl -X DELETE http://localhost:8000/api/v1/generate/doc-abc123
```

## 6. Output yang Diharapkan

**GET /generate/history:**
```json
[
  {
    "id": "doc-abc123",
    "filename": "TOR_a2184d4d.docx",
    "file_size": 43008,
    "style_name": "Standar Pemerintah",
    "status": "completed",
    "word_count": 1240,
    "created_at": "2026-04-21T03:00:00"
  }
]
```

**GET /generate/doc-abc123:**
```json
{
  "id": "doc-abc123",
  "filename": "TOR_a2184d4d.docx",
  "file_size": 43008,
  "context": "Buat TOR lanjutan 2026",
  "style_name": "Standar Pemerintah",
  "status": "completed",
  "tor_content": "# TOR Kegiatan ...",
  "metadata": { "generated_by": "gemini-2.5-pro", "word_count": 1240, ... },
  "error_message": null,
  "created_at": "2026-04-21T03:00:00"
}
```

## 7. Dependencies
- Task 2 (repo harus ada)
- Task 3 (Pydantic models harus ada)

## 8. Acceptance Criteria
- [ ] `GET /generate/history` returns list of `DocGenListItem`
- [ ] `GET /generate/{gen_id}` returns `DocGenDetail` with tor_content
- [ ] `GET /generate/{gen_id}` returns 404 jika ID tidak valid
- [ ] `DELETE /generate/{gen_id}` deletes record and returns 200
- [ ] `DELETE /generate/{gen_id}` returns 404 jika ID tidak valid
- [ ] Backend restart tanpa error

## 9. Estimasi
**Medium** (~1 jam)
