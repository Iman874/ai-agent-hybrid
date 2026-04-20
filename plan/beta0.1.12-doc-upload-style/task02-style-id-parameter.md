# Task 02: Tambah Parameter `style_id` di Endpoint

> **Status**: [x] Selesai
> **Estimasi**: Low (30 menit – 1 jam)
> **Dependency**: Task 01

## 1. Deskripsi

Menambahkan parameter opsional `style_id` pada endpoint `POST /generate/from-document`, sehingga user bisa memilih style spesifik (bukan hanya active style) saat generate TOR dari dokumen.

## 2. Tujuan Teknis

- Endpoint menerima `style_id` sebagai Form parameter opsional
- Jika `style_id` di-provide → gunakan style tersebut
- Jika `style_id` kosong/None → fallback ke active style (behavior task01)
- Jika `style_id` invalid → return 404

## 3. Scope

**Yang dikerjakan:**
- Modifikasi `app/api/routes/generate_doc.py` — tambah parameter + logic routing

**Yang tidak dikerjakan:**
- Auto-detect style (task04)
- Frontend perubahan (task03)

## 4. Langkah Implementasi

### 4.1 Tambah Parameter di Endpoint Signature

- [x] Ubah function signature (line 15-19) dari:

```python
@router.post("/generate/from-document", response_model=GenerateResponse)
async def generate_from_document(
    request: Request,
    file: UploadFile = File(..., description="Dokumen sumber (PDF/TXT/MD/DOCX)"),
    context: str = Form("", description="Konteks tambahan dari user"),
):
```

Menjadi:

```python
@router.post("/generate/from-document", response_model=GenerateResponse)
async def generate_from_document(
    request: Request,
    file: UploadFile = File(..., description="Dokumen sumber (PDF/TXT/MD/DOCX)"),
    context: str = Form("", description="Konteks tambahan dari user"),
    style_id: str | None = Form(None, description="ID style TOR spesifik (default=aktif)"),
):
```

### 4.2 Update Logic Style Selection

- [x] Ubah logic pengambilan style (dari task01) menjadi:

```python
    # Step 3b: Get formatting style
    style_manager = request.app.state.style_manager

    if style_id:
        try:
            active_style = style_manager.get_style(style_id)
        except Exception:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=404,
                detail=f"Style '{style_id}' tidak ditemukan.",
            )
    else:
        active_style = style_manager.get_active_style()

    format_spec = active_style.to_prompt_spec()
```

### 4.3 Tambah Import HTTPException

- [x] Pastikan `HTTPException` sudah di-import di top file. Cek line 3:

```python
# Sudah ada Form di import, tambahkan HTTPException:
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
```

## 5. Output yang Diharapkan

```bash
# Tanpa style_id → pakai active style (sama seperti sebelumnya):
curl -X POST http://localhost:8000/api/v1/generate/from-document \
  -F "file=@doc.pdf" \
  -F "context=Buat TOR workshop"

# Dengan style_id spesifik:
curl -X POST http://localhost:8000/api/v1/generate/from-document \
  -F "file=@doc.pdf" \
  -F "context=Buat TOR workshop" \
  -F "style_id=pelatihan_resmi"

# Dengan style_id invalid → 404:
curl -X POST http://localhost:8000/api/v1/generate/from-document \
  -F "file=@doc.pdf" \
  -F "style_id=tidak_ada"
# → {"detail": "Style 'tidak_ada' tidak ditemukan."}
```

## 6. Acceptance Criteria

- [x] Endpoint menerima `style_id` sebagai parameter opsional.
- [x] Tanpa `style_id` → masih menggunakan active style (backward compatible).
- [x] Dengan `style_id` valid → menggunakan style tersebut.
- [x] Dengan `style_id` invalid → return HTTP 404 dengan detail jelas.
- [x] Swagger docs (`/docs`) menampilkan parameter `style_id` di form.
