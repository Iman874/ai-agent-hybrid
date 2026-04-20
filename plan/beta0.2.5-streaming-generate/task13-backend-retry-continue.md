# Task 13: Backend — Infrastruktur Retry & Continue Generation

## 1. Judul Task
Backend: Simpan Source Text di DB + Endpoint Regenerate & Continue Stream

## 2. Deskripsi
Agar fitur Retry (generate ulang dari awal) dan Continue (lanjutkan dari titik putus) bisa bekerja,
backend perlu menyimpan **parsed document text** di database saat pertama kali generate.
Tanpa ini, retry/continue mustahil karena file asli yang di-upload sudah hilang dari memori server
begitu request selesai.

Task ini juga menambahkan **2 endpoint streaming baru**:
- `POST /generate/{id}/retry-stream` — generate ulang dari awal pakai source text yang tersimpan
- `POST /generate/{id}/continue-stream` — lanjutkan TOR dari partial content yang sudah ada

## 3. Tujuan Teknis
- Source document text ter-persist di database agar bisa dipakai ulang
- Retry stream menghasilkan TOR baru dari nol menggunakan source text yang tersimpan
- Continue stream melanjutkan TOR parsial dengan prompt khusus "lanjutkan dari sini"

## 4. Scope

### Yang Dikerjakan
- **Database migration**: Tambah kolom `source_text TEXT` ke tabel `document_generations`
- **Repository update**: `DocGenerationRepo.create()` menerima param `source_text`
- **Endpoint streaming**: Simpan `document_text` ke DB setelah parsing berhasil
- **Prompt baru**: `CONTINUE_TOR_PROMPT` di `app/ai/prompts/` — instruksi Gemini untuk melanjutkan TOR parsial
- **Endpoint `retry-stream`**: Ambil `source_text` + `style_id` dari DB, build prompt, stream ulang
- **Endpoint `continue-stream`**: Ambil `source_text` + `tor_content` (partial), build continue prompt, stream

### Yang TIDAK Dikerjakan
- Frontend UI (dikerjakan di Task 14)
- i18n / terjemahan (dikerjakan di Task 15)

## 5. File yang Dimodifikasi/Ditambah

| File | Aksi |
|------|------|
| `app/db/schema.py` (atau migration inline) | Tambah kolom `source_text` |
| `app/db/repositories/doc_generation_repo.py` | Update `create()` + tambah `get_source_text()` |
| `app/api/routes/generate_doc.py` | Simpan source_text saat stream + 2 endpoint baru |
| `app/ai/prompts/continue_tor.py` | **[NEW]** Prompt template untuk Continue |
| `app/core/gemini_prompt_builder.py` | Tambah `build_continue()` static method |

## 6. Detail Implementasi

### 6.1 Database: Tambah kolom `source_text`
```sql
ALTER TABLE document_generations ADD COLUMN source_text TEXT;
```
- Jalankan saat startup di `init_db()` dengan `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
- Kolom nullable (backward-compatible dengan record lama)

### 6.2 Repository: Update `create()` 
```python
async def create(self, ..., source_text: str | None = None) -> None:
    # INSERT ... (id, filename, ..., source_text, status)
```
Tambah juga helper:
```python
async def get_source_text(self, gen_id: str) -> str | None:
    # SELECT source_text FROM document_generations WHERE id=?
```

### 6.3 Simpan source_text saat streaming
Di `generate_from_document_stream()`, setelah `DocumentParser.parse()`:
```python
document_text = await DocumentParser.parse(file_bytes, filename)
# Persist source text ke DB agar bisa retry/continue nanti
await doc_gen_repo.update_source_text(session_id, document_text)
```

### 6.4 Prompt Continue
```python
CONTINUE_TOR_PROMPT = """# INSTRUKSI
Kamu sedang MELANJUTKAN pembuatan dokumen TOR yang terputus.

## TOR YANG SUDAH DIHASILKAN (JANGAN ULANGI)
---
{PARTIAL_TOR}
---

## TUGAS
Lanjutkan TOR di atas TEPAT dari titik terakhir. 
JANGAN mengulangi bagian yang sudah ada.
Tulis kelanjutannya saja.

## DOKUMEN SUMBER (REFERENSI)
---
{DOCUMENT_TEXT}
---

{FORMAT_SPEC}
"""
```

### 6.5 Endpoint `retry-stream`
```
POST /generate/{gen_id}/retry-stream
```
- Ambil record dari DB: `source_text`, `context`, `style_id`
- Validasi: source_text harus ada (kalau null → 400)
- Buat session baru (`doc-{uuid}`)
- Persist record baru
- Build prompt standar (`build_from_document`)
- Stream Gemini → SSE

### 6.6 Endpoint `continue-stream`
```
POST /generate/{gen_id}/continue-stream
```
- Ambil record: `source_text`, `tor_content` (partial), `context`, `style_id`
- Validasi: source_text + tor_content harus ada
- Buat session baru
- Build continue prompt (`build_continue`)
- Stream Gemini → SSE (hanya kelanjutan baru)
- Di `done` event, **gabungkan** `old_partial + new_continuation` sebagai final tor_content

## 7. Acceptance Criteria
- [x] Kolom `source_text` ada di DB
- [x] Source text tersimpan saat generate pertama kali
- [x] `retry-stream` menghasilkan TOR baru dari source text yang tersimpan
- [x] `continue-stream` melanjutkan TOR parsial tanpa mengulangi bagian yang sudah ada
- [x] Kedua endpoint mengembalikan SSE events yang sama formatnya (`status/token/done/error`)
- [x] Record lama tanpa source_text → return error 400 yang jelas
