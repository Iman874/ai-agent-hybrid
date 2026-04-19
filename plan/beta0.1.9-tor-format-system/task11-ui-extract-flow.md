# Task 11: UI — Extract Flow (File Upload Analysis)

## 1. Judul Task
Flow Ekstraksi Format dari PDF di UI Streamlit

## 2. Deskripsi
Menambah User experience pengunggahan File rujukan untuk secara sihir di ekstrak formatnya ke database JSON style milik sistem oleh module AI.

## 3. Tujuan Teknis
Menyisipkan stream widget file loader uploader `st.file_uploader` ke dalam Tab UI Format. Widget dikaitkan ke execution parsing byte api trigger extraction form data request payload.

## 4. Scope
* **Yang dikerjakan**: Ekstensi fungsi di modul code property file `streamlit_app/components/format_tab.py` (Modals/State expansion loader upload preview text result list).
* **Yang tidak dikerjakan**: Ekstraksi PDF text di Streamlit python side. Ekstraksi murni diserahkan HTTP form kirim ke port router Fastapi API backend ekstensi service module task 07.

## 5. Langkah Implementasi
1. Pada `format_tab.py`, tambahkan tombol/menu dropdown logic expand: `[📄 Extract dari Dokumen]`.
2. Jika ter-trigger render st.file_uploader menerima extension docx pdf md txt.
3. Setelah trigger receive byte upload selesai, render spinner UI progress. Lakukan trigger Request API call upload ke route task ke 12 uploader extract model payload HTTP.
4. Response property dict map result ekstraksi json dikembalikan ke Streamlit Session State memvisualkan kotak UI Review property array extracted structure.
5. Sediakan dua aksi konfirmasi button widget state: Edit Lebih Lanjut Format Ini (ubah ke mode edit sebelum simpan mode array array Streamlit state input field widget), ATAU Simpan Permanen (trigger api commit write endpoint).

## 6. Output yang Diharapkan
Menu di frontend Streamlit memampukan AI otomatis cloning form structure format yang diberikan PDF dokumen instansi target.

## 7. Dependencies
- [task10-ui-format-tab.md]

## 8. Acceptance Criteria
- [ ] Streamlit file loader mengijinkan tipe extensi spesifik text parser requirement system backend.
- [ ] Sukses loading render parsing message tunggu UI blocker feedback spinner progress.
- [ ] Memunculkan alert error box state toast message alert exception handling saat payload doc pdf parser response format format model text prompt Gemini dari backend is malformed failed.

## 9. Estimasi
Medium
