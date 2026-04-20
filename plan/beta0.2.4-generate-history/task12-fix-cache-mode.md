# Task 12: Fix TOR Cache Mode Constraint

## 1. Judul Task
Ubah nilai `mode` yang dikirim dari `generate_doc.py` ke cache agar sesuai dengan constraint database.

## 2. Deskripsi
Pada saat generate TOR dari dokumen, aplikasi menghasilkan error `CHECK constraint failed: mode IN ('standard', 'escalation')`. Ini trjadi karena di `generate_doc.py` nilai metadata mode diset sebagai `"document"`, sedangkan di database SQLite (tabel `tor_cache`) membatasi hanya `standard` dan `escalation`.

## 3. Tujuan Teknis
- Memperbaiki `app/api/routes/generate_doc.py`.
- Metadata `mode` pada tipe `TORDocument` diubah menjadi `"standard"`.

## 4. Scope
### Yang dikerjakan
- Ubah baris `mode="document",` menjadi `mode="standard",` di `generate_doc.py`.

### Yang tidak dikerjakan
- Tidak mengubah skema tabel `tor_cache`.

## 5. Langkah Implementasi
1. Buka `app/api/routes/generate_doc.py`
2. Cari instansiasi `TORDocument` di sekitar baris 90-100:
   ```python
   tor_doc = TORDocument(
       content=processed.content,
       metadata=TORMetadata(
           generated_by=gemini.model_name,
           mode="standard", # ASALNYA: "document"
           word_count=processed.word_count,
           ...
       ),
   )
   ```

## 6. Output yang Diharapkan
- Fitur `Generate TOR dari Dokumen` akan sukses, error "failed" sebelumnya pada UI hilang, status berubah ke completeted (icon hijau), dan hasil bisa di View.

## 7. Dependencies
- Semua task 1 hingga 11.

## 8. Acceptance Criteria
- [ ] Pengguna bisa men-generate ulang file dokumen tanpa menyebabkan error failed di history.
- [ ] `document_generations` di DB mencatat status completed.

## 9. Estimasi
**Low** (5 Menit)
