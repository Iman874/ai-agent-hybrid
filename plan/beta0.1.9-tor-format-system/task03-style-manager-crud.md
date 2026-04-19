# Task 03: Style Manager CRUD

## 1. Judul Task
Implementasi Sistem Penulisan & Pembacaan Data Style Lokal (`StyleManager`)

## 2. Deskripsi
Membangun service lokal yang akan merepresentasikan File System sebagai backend database untuk persistensi style pengguna di direktori `data/tor_styles/`. Meliputi pembuatan file `_active.txt` untuk menandai template yg dipakai.

## 3. Tujuan Teknis
Membuat file manajemen `app/core/style_manager.py` dengan metode CRUD lengkap agar UI bisa membuat format custom baru, mengaksesnya, menyimpannya di file .json, mengubah id active, dan juga read `_default.json` dengan aman (locked edit & delete).

## 4. Scope
* **Yang dikerjakan**: Menulis class `StyleManager`, logic baca/tulis JSON, logic `_active.txt`, validasi proteksi `_default` JSON.
* **Yang tidak dikerjakan**: Pembuatan koneksi Database sungguhan. Integrasi dengan endpoints.

## 5. Langkah Implementasi
1. Buat class `StyleManager` di `app/core/style_manager.py`.
2. Init: cek eksistensi folder dan run self check apakah file `_default.json` masih ada, jika hilang maka re-create.
3. Method **READ**:
    * `list_styles()` -> Menggunakan format globbing atau file checking dir .json yang di convert ke Python Objects list. Sort supaya `_default` ada di pertama.
    * `get_style()` -> Read spesifik ID.
    * `get_active_style()` -> Baca isi file txt, lalu pakai sebagai ID rujukan mengambil filenya.
4. Method **WRITE**:
    * `create_style()`, `update_style()`, `delete_style()`, `duplicate_style()`.
    * Memiliki validasi error saat user/sistem call delete ke ID bernilai `_default`.
5. Method **ACTIVE**:
    * `set_active()` -> Membuka dan menulis (overwrite) file `_active.txt` lalu update status `is_active` pada objects secara logic.

## 6. Output yang Diharapkan
Metode yang berjalan lancar untuk Create, Read, Update, Delete JSON configs.

## 7. Dependencies
- [task01-data-model-torstyle.md]
- [task02-default-style-json.md]

## 8. Acceptance Criteria
- [ ] Bisa membuat JSON baru dari variable pydantic python.
- [ ] Error handling proper: Exception saat coba `update_style("_default")`.
- [ ] Active state switching beroperasi lewat `_active.txt`.

## 9. Estimasi
Medium
