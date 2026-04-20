# Task 3: Stabilisasi Settings Dialog dengan Scoped Fallback

## 1. Judul Task

Stabilkan update settings dialog dengan scoped rerun jika kompatibel dan fallback global rerun + guard.

## 2. Deskripsi

Task ini memastikan navigasi section di settings dialog tetap ringan, tidak memicu refresh area yang tidak relevan, dan tetap aman di environment tanpa scoped rerun.

## 3. Tujuan Teknis

- Scoped rerun dipakai jika kompatibel.
- Jika tidak kompatibel, fallback ke global rerun dengan event guard.
- Navigasi section tidak memicu loop atau double trigger.

## 4. Scope

Yang dikerjakan:
- Refactor event nav di streamlit_app/components/settings_dialog.py.
- Tambahkan helper rerun scope-safe.

Yang tidak dikerjakan:
- Perubahan struktur UI dialog.
- Perubahan isi pengaturan di luar kebutuhan stabilitas event.

## 5. Langkah Implementasi

1. Buat helper rerun dialog, contoh run_dialog_rerun():
   - coba st.rerun(scope="fragment"),
   - fallback ke st.rerun() dalam try/except.
2. Pada klik nav section, cek current section:
   - jika section sama, skip rerun,
   - jika berubah, update state lalu rerun via helper.
3. Tambahkan guard anti repeat click saat dialog sedang update.
4. Pastikan aksi section umum/format/lanjutan tidak memicu fetch data yang tidak dibutuhkan.
5. Verifikasi kompatibilitas pada Streamlit yang tidak mendukung scope argument.

## 6. Output yang Diharapkan

- Pindah section settings terasa ringan.
- Jika scope tidak didukung, dialog tetap berjalan melalui global rerun tanpa error.
- Tidak ada loop rerun saat klik section yang sama.

## 7. Dependencies

- Task 2 selesai.

## 8. Acceptance Criteria

- [ ] Scoped rerun digunakan saat kompatibel.
- [ ] Fallback global rerun bekerja tanpa crash.
- [ ] Klik section yang sama tidak memicu rerun.
- [ ] Tidak ada rerun loop di settings dialog.

## 9. Estimasi

Low (1-2 jam)
