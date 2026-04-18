# Task 01 — Install Dependencies: pypdf & python-docx

## 1. Judul Task

Install library parsing dokumen dan update requirements.txt.

## 2. Deskripsi

Tambah dependency `pypdf` untuk PDF text extraction dan `python-docx` untuk DOCX parsing. Verifikasi kedua library bisa diimport tanpa error.

## 3. Tujuan Teknis

- `pypdf>=4.0` dan `python-docx>=1.0` ter-install di venv
- `requirements.txt` updated
- Import test berhasil

## 4. Scope

### Yang dikerjakan
- Install 2 library baru
- Update `requirements.txt`
- Verifikasi import

### Yang tidak dikerjakan
- Implementasi parser (task selanjutnya)

## 5. Langkah Implementasi

### Step 1: Install

```bash
pip install pypdf>=4.0 python-docx>=1.0
```

### Step 2: Update `requirements.txt`

Tambahkan di bagian akhir:

```
# Document Parsing
pypdf>=4.0
python-docx>=1.0
```

### Step 3: Verifikasi

```python
from pypdf import PdfReader
from docx import Document
print("OK")
```

## 6. Output yang Diharapkan

Kedua library ter-install dan bisa diimport.

## 7. Dependencies

- beta0.1.5 selesai (Streamlit UI sudah ada)

## 8. Acceptance Criteria

- [ ] `pypdf` ter-install
- [ ] `python-docx` ter-install
- [ ] `requirements.txt` updated
- [ ] Import test passed

## 9. Estimasi

**Low** — ~10 menit
