# Task 03 — Document Parser: PDF Support

## 1. Judul Task

Tambah PDF parsing ke `DocumentParser` menggunakan `pypdf`.

## 2. Deskripsi

Extend method `_parse_pdf()` di `DocumentParser` untuk mengekstrak teks dari PDF text-based. Handle edge cases: halaman kosong, PDF terproteksi, PDF scan-only.

## 3. Tujuan Teknis

- `DocumentParser._parse_pdf()` mengekstrak teks dari semua halaman PDF
- Handle: password-protected PDF, empty pages
- Deteksi scanned/image PDF (teks sangat sedikit)

## 4. Scope

### Yang dikerjakan
- `_parse_pdf()` method di `DocumentParser`
- Replace raise placeholder dengan implementasi nyata

### Yang tidak dikerjakan
- OCR (scan-based PDF)

## 5. Langkah Implementasi

### Step 1: Implementasi `_parse_pdf()`

```python
@staticmethod
def _parse_pdf(file_bytes: bytes) -> str:
    """Extract text dari PDF via pypdf."""
    import io
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as e:
        raise DocumentParseError(
            message="Tidak bisa membaca file PDF.",
            details=str(e)[:200],
        )

    if reader.is_encrypted:
        raise DocumentParseError(
            message="PDF terproteksi password. Hapus proteksi dulu.",
        )

    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())

    if not pages:
        raise DocumentParseError(
            message="Tidak bisa mengekstrak teks dari PDF. "
                    "Kemungkinan PDF ini berisi scan/gambar (bukan teks).",
        )

    return "\n\n".join(pages)
```

### Step 2: Update routing di `parse()` method

Ganti:
```python
elif ext == ".pdf":
    raise DocumentParseError(message="PDF parsing belum diimplementasi.")
```
Dengan:
```python
elif ext == ".pdf":
    text = DocumentParser._parse_pdf(file_bytes)
```

### Step 3: Test dengan file PDF

Buat test PDF sederhana atau gunakan PDF contoh yang sudah ada.

## 6. Output yang Diharapkan

```python
>>> with open("laporan.pdf", "rb") as f:
...     text = await DocumentParser.parse(f.read(), "laporan.pdf")
>>> print(text[:200])
"LAPORAN KEGIATAN WORKSHOP..."
```

## 7. Dependencies

- **Task 01** — `pypdf` installed
- **Task 02** — `DocumentParser` class sudah ada

## 8. Acceptance Criteria

- [ ] PDF text-based bisa di-parse
- [ ] Teks dari semua halaman digabung
- [ ] Error handling: encrypted PDF → pesan jelas
- [ ] Error handling: scanned PDF → pesan jelas
- [ ] Halaman kosong di-skip

## 9. Estimasi

**Low** — ~30 menit
