# Task 04 — Document Parser: DOCX Support

## 1. Judul Task

Tambah DOCX parsing ke `DocumentParser` menggunakan `python-docx`.

## 2. Deskripsi

Extend method `_parse_docx()` di `DocumentParser` untuk mengekstrak teks dari file Word (.docx). Ambil semua paragraf dan gabung.

## 3. Tujuan Teknis

- `DocumentParser._parse_docx()` mengekstrak teks dari DOCX
- Paragraf kosong di-skip
- Handle file corrupt

## 4. Scope

### Yang dikerjakan
- `_parse_docx()` method di `DocumentParser`
- Replace raise placeholder dengan implementasi

### Yang tidak dikerjakan
- Tabel di dalam DOCX (cukup paragraf saja)
- Gambar di dalam DOCX

## 5. Langkah Implementasi

### Step 1: Implementasi `_parse_docx()`

```python
@staticmethod
def _parse_docx(file_bytes: bytes) -> str:
    """Extract text dari DOCX via python-docx."""
    import io
    from docx import Document

    try:
        doc = Document(io.BytesIO(file_bytes))
    except Exception as e:
        raise DocumentParseError(
            message="Tidak bisa membaca file DOCX.",
            details=str(e)[:200],
        )

    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    if not paragraphs:
        raise DocumentParseError(
            message="Dokumen DOCX kosong atau tidak berisi teks.",
        )

    return "\n\n".join(paragraphs)
```

### Step 2: Update routing di `parse()` method

Ganti:
```python
elif ext == ".docx":
    raise DocumentParseError(message="DOCX parsing belum diimplementasi.")
```
Dengan:
```python
elif ext == ".docx":
    text = DocumentParser._parse_docx(file_bytes)
```

## 6. Output yang Diharapkan

```python
>>> with open("proposal.docx", "rb") as f:
...     text = await DocumentParser.parse(f.read(), "proposal.docx")
>>> print(text[:200])
"PROPOSAL KEGIATAN WORKSHOP..."
```

## 7. Dependencies

- **Task 01** — `python-docx` installed
- **Task 02** — `DocumentParser` class sudah ada

## 8. Acceptance Criteria

- [ ] DOCX bisa di-parse
- [ ] Paragraf kosong di-skip
- [ ] Error handling: file corrupt → pesan jelas
- [ ] Output berupa gabungan paragraf (dipisah `\n\n`)

## 9. Estimasi

**Low** — ~20 menit
