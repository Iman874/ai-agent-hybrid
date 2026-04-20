# Task 8: Harmonisasi Chat dan Sidebar dengan Event Guard Lanjutan

## 1. Judul Task

Integrasikan helper event guard state ke alur chat dan sidebar agar anti double trigger secara menyeluruh.

## 2. Deskripsi

Task ini memakai fondasi state guard dari task sebelumnya untuk memastikan action utama user aman dari re-entrant dan duplicate send.

## 3. Tujuan Teknis

- Chat submit tidak dapat mengirim request ganda karena klik/enter berulang.
- Aksi sidebar kritis (load session, delete, reset) patuh _ui_busy dan dedupe action.
- Rerun global hanya terjadi setelah guard meloloskan action.

## 4. Scope

Yang dikerjakan:
- Refactor streamlit_app/components/chat.py.
- Penyesuaian lanjutan streamlit_app/components/sidebar.py.

Yang tidak dikerjakan:
- Perubahan alur bisnis chat.
- Perubahan tampilan chat/sidebar.

## 5. Langkah Implementasi

1. Integrasikan helper state guard dari state.py ke chat submit flow.
2. Tambahkan action id untuk setiap submit prompt.
3. Jika action duplikat atau _ui_busy aktif, skip proses dan tampilkan notifikasi ringan jika perlu.
4. Terapkan pola yang sama di aksi sidebar yang memodifikasi session.
5. Pastikan begin/end action dipanggil berpasangan (try/finally).
6. Rekam perf sample untuk action penting (chat_send, session_open, session_delete).

## 6. Output yang Diharapkan

- Submit chat cepat berulang tidak menghasilkan request ganda.
- Aksi session di sidebar tetap responsif dan tidak re-entrant.
- Data perf sample bertambah saat action dijalankan.

## 7. Dependencies

- Task 2 selesai.
- Task 5 selesai.

## 8. Acceptance Criteria

- [ ] Tidak ada duplicate send pada chat submit.
- [ ] Sidebar action patuh _ui_busy dan dedupe id.
- [ ] Global rerun terjadi hanya setelah guard pass.
- [ ] Tidak ada perubahan UI/UX.

## 9. Estimasi

Medium (2-4 jam)
