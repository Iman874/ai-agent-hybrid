# Task 1: DB Migration — Tabel `document_generations`

## 1. Judul Task
Buat migration SQL baru untuk tabel `document_generations` yang menyimpan riwayat generate TOR dari dokumen.

## 2. Deskripsi
Saat ini generate-from-document tidak menyimpan record permanen ke database. Perlu tabel khusus untuk menyimpan metadata setiap generate: nama file, konteks, style, status, hasil TOR, dan error jika gagal.

## 3. Tujuan Teknis
- File migration `006_doc_generations.sql` berhasil dibuat
- Tabel `document_generations` terbuat saat app startup
- Tabel memiliki semua kolom sesuai plan design

## 4. Scope
### Yang dikerjakan
- Buat file `app/db/migrations/006_doc_generations.sql`

### Yang tidak dikerjakan
- Tidak membuat repository Python (task 2)
- Tidak mengubah file migration lainnya

## 5. Langkah Implementasi

### Step 1: Buat file `app/db/migrations/006_doc_generations.sql`

```sql
-- Migration 006: Document generation history
-- Menyimpan riwayat setiap generate TOR dari dokumen yang diupload

CREATE TABLE IF NOT EXISTS document_generations (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    context TEXT DEFAULT '',
    style_id TEXT,
    style_name TEXT,
    status TEXT DEFAULT 'processing'
        CHECK(status IN ('processing','completed','failed')),
    tor_content TEXT,
    metadata_json TEXT DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_docgen_created ON document_generations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_docgen_status ON document_generations(status);
```

### Step 2: Verifikasi
- Restart backend (`uvicorn`) → cek log bahwa `Migration applied: 006_doc_generations.sql` muncul
- Atau jalankan manual: `sqlite3 data/app.db ".tables"` → `document_generations` harus muncul

## 6. Output yang Diharapkan

Log backend saat startup:
```
INFO  Migration applied: 006_doc_generations.sql
```

Tabel berhasil dibuat:
```
sqlite> .schema document_generations
CREATE TABLE document_generations (
    id TEXT PRIMARY KEY,
    ...
);
```

## 7. Dependencies
Tidak ada (task pertama)

## 8. Acceptance Criteria
- [ ] File `006_doc_generations.sql` ada di `app/db/migrations/`
- [ ] Backend startup tanpa error
- [ ] Tabel `document_generations` terbuat dengan semua kolom
- [ ] Index `idx_docgen_created` dan `idx_docgen_status` terbuat

## 9. Estimasi
**Low** (~15 menit)
