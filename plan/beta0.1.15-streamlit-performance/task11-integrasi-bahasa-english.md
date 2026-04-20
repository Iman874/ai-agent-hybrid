# Task 11: Integrasi Bahasa English (i18n Runtime)

## 1. Judul Task

Aktifkan integrasi bahasa English agar pengaturan bahasa di Settings benar-benar berfungsi.

## 2. Deskripsi

Saat ini pilihan bahasa di Settings masih bersifat placeholder dan belum mengubah teks antarmuka. Task ini menambahkan fondasi i18n sederhana agar user bisa berpindah antara Bahasa Indonesia dan English secara runtime dengan fallback aman.

## 3. Tujuan Teknis

- Pilihan bahasa di Settings bukan lagi dummy, tetapi mengubah UI text secara nyata.
- Bahasa tersimpan di `session_state` dan dipakai lintas komponen utama.
- Default tetap Bahasa Indonesia, English sebagai opsi aktif.
- Ada fallback ke Bahasa Indonesia jika key terjemahan tidak ditemukan.

## 4. Scope

Yang dikerjakan:
- Refactor `streamlit_app/state.py` untuk state preferensi bahasa.
- Refactor `streamlit_app/components/settings_dialog.py` agar switch bahasa aktif.
- Tambah modul util i18n (misal `streamlit_app/utils/i18n.py`) berisi dictionary + helper translate.
- Integrasi minimal ke komponen utama berimpact tinggi:
  - `streamlit_app/components/sidebar.py`
  - `streamlit_app/components/header.py`
  - `streamlit_app/components/chat.py`
  - `streamlit_app/components/form_document.py`
  - `streamlit_app/components/format_tab.py`

Yang tidak dikerjakan:
- Multi-language tambahan selain ID/EN.
- Translasi seluruh string backend message.
- Redesign UI.

## 5. Langkah Implementasi

1. Tambahkan state key bahasa, contoh `app_language` dengan default `"id"`.
2. Buat helper i18n sederhana:
   - `tr(key: str, default: str | None = None) -> str`
   - dictionary `TRANSLATIONS = {"id": {...}, "en": {...}}`
   - fallback chain: selected language -> `id` -> `default`/`key`.
3. Hubungkan radio bahasa di Settings dengan state language dan rerun fragment-safe.
4. Ganti hardcoded string prioritas tinggi ke `tr(...)` di komponen scope.
5. Pastikan tombol/notifikasi event penting punya pasangan terjemahan ID/EN.
6. Tambahkan test unit untuk helper i18n dan fallback behavior.
7. Jalankan regression test otomatis.

## 6. Output yang Diharapkan

- User pilih `English` di Settings -> label utama UI berubah ke English.
- User pilih `Bahasa Indonesia` -> UI kembali ke Indonesian.
- Tidak ada crash jika key translation belum lengkap (fallback aktif).
- Performa tetap stabil dan dialog Settings tidak tertutup paksa.

## 7. Dependencies

- Task 3 selesai (stabilisasi settings dialog).
- Task 5 selesai (state helper dan guard).
- Task 10 selesai (format settings interaction stable).

## 8. Acceptance Criteria

- [ ] Switch bahasa di Settings benar-benar mengubah teks UI.
- [ ] State bahasa tersimpan konsisten selama sesi.
- [ ] Fallback translation berfungsi untuk key yang belum tersedia.
- [ ] Tidak ada regresi pada flow sidebar/chat/document/format settings.
- [ ] Test otomatis i18n helper lulus.

## 9. Estimasi

Medium (2-4 jam)
