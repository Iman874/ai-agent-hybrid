# Plan Design: Beta 0.1.10 — Document Export Module (PDF/DOCX)

## 1. Latar Belakang & Tujuan
Setelah berhasil mengimplementasikan sistem pembentukan TOR dengan berbagai gaya formalitas (Standard, Academic, Creative) di versi `beta0.1.9`, aplikasi kini dapat memproduksi metadata dan dokumen *Term of Reference* yang valid di layer state.

Saat ini (beta 0.1.9), modul UI Streamlit sebenarnya telah melakukan proses *export* `PDF` dan `MD` secara lokal menggunakan fungsi `export_to_pdf` (`xhtml2pdf`) yang ada di folder `streamlit_app/utils/formatters.py`. Namun, pendekatan ini memiliki kelemahan:
1. Terbatas pada klien frontend (Streamlit); aplikasi eksternal (API Consumers) tidak dapat melakukan generate file dokumen fisik.
2. Belum ada dukungan eksport format `Microsoft Word (.docx)`, yang mana merupakan format standar paling krusial bagi instansi pemerintahan maupun dunia profesional.

Pada versi **Beta 0.1.10** ini, kita akan membangun ulang dan mensentralisasi modul **Document Export** agar diproses seutuhnya di sisi Backend (API Layer) dan mendukung format Markdown (`.md`), Microsoft Word (`.docx`), maupun `.pdf`.

## 2. Arsitektur Komponen
Fitur ini akan diimplementasikan dengan pemisahan *concern* (Separation of Concerns) yang jelas berdasarkan codebase:

- **Data Fetching (Repository Layer)**: Menggunakan `CacheRepo` (`app/db/repositories/cache_repo.py`) untuk melakukan *query* markdown konten `TORDocument` berdasarkan `session_id` langsung dari layer SQLite yang saat ini sudah berjalan baik.
- **Backend Service (`app/services/document_exporter.py`)**: 
  - `DocumentExporterService`: Layanan abstraksi backend utama yang menerima string Markdown dan parameter tipe format.
  - Berisi konverter yang memanfaatkan parser regex/Markdown yang memetakan elemen (Heading, Bolds, Lists, dsb) ke dalam fungsi *native* objek `python-docx` untuk file MS Word.
  - Mengambil alih proses styling ke PDF dan MD.
- **Backend API Endpoint (`app/api/routes/export.py`)**: 
  - Endpoint `GET /api/v1/export/{session_id}?format={docx|pdf|md}`
  - Mengembalikan `StreamingResponse` dengan tipe MIME spesifik sesuai format agar kompatibel dengan sistem browser download.
- **Frontend Streamlit Refactor (`streamlit_app/components/tor_preview.py`)**: 
  - Menghapus dependensi rendering eksport dari Frontend (`utils.formatters.py`).
  - Streamlit UI (`st.download_button`) hanya akan melakukan `API Client Fetch` *byte stream* dari endpoint *export* pada Backend dan menampilkan dokumen ke User.

## 3. Dependency Tambahan
Untuk mendukung generasi file fisik secara *native* di Python lokal, kita perlu memodifikasi `requirements.txt`:
- Menambahkan `python-docx` untuk memanipulasi dokumen Microsoft Word.
- Pindah dependensi format ekspor (`xhtml2pdf`, `markdown`) yang sebelumnya hanya terpasang untuk UI ke cakupan backend.

## 4. Alur Integrasi (Flow Data)
1. **User (Streamlit)** telah selesai di tahap _Generating_ dan memvalidasi `TOR` di preview komponen `tor_preview.py`. Backend secara simultan sudah menyimpan `TORDocument` di cache `SQLite` dengan unik `session_id`.
2. Muncul barisan *button* **[Download as .DOCX]**, **[Download as .PDF]**, **[Download as .MD]**.
3. Saat user menekan tombol `Download`, script Streamlit via modul API Client (misal `streamlit_app/api/client.py`) melakukan request *streaming*:
   `GET /api/v1/export/{session_id}?format=docx`
4. Routing API memvalidasi format. `CacheRepo.get(session_id)` mengekstrak string `content` MD yang ada.
5. Service class `DocumentExporterService` mengubah string MD ke `io.BytesIO` menggunakan *engine* konversi berdasarkan argumen format:
   - Jika `docx`: merangkai `.docx` element dan stream file buffer.
   - Jika `pdf`: merangkai HTML->PDF stream file buffer.
6. API merespons dengan header `Content-Disposition: attachment; filename="tor.docx"` dan tipe MIME yang sesuai.
7. File otomatis terunduh lewat browser klien Streamlit.

## 5. Daftar Sub-Task Eksekusi
Rencana operasional dibagi menjadi task-task spesifik:
- **`task01-export-service.md`**: Pembuatan service layer `document_exporter.py` serta penginstalan dependensi backend `python-docx`.
- **`task02-export-api.md`**: Pembuatan router `export.py` dan mengintegrasikannya ke router utama FastAPI di `main.py` atau `app/api/router.py`.
- **`task03-frontend-refactor.md`**: Penyesuaian `streamlit_app/api/client.py` dan `tor_preview.py` untuk menggunakan endpoint *export* dan menghapus fungsi *legacy* lokal.
- **`task04-testing.md`**: Penulisan unit-test `test_export_integration.py` untuk menjamin hasil konversi ke byte berhasil diproduksi tanpa merusak data asli TOR.

## 6. Menunggu Konfirmasi User
*(Agen AI akan berhenti sejenak pada fase ini. Setelah user memvalidasi rancangan ini, saya akan men-generate task detail dalam skema `task01-xxx` sampai akhir di dalam folder `plan`.)*

*Note to User:*
Apakah kamu setuju dengan perancangan arsitektur terpusat (*backend centralized export*) ini? (Mohon berikan perintah balasan "Setuju, buatkan task" atau berikan catatan revisi tambahan).
