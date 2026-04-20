# Task 7: Harmonisasi Form Document dan Format Tab

## 1. Judul Task

Sinkronisasi komponen form_document dan format_tab agar patuh cache policy, invalidasi terpusat, dan controlled rerun.

## 2. Deskripsi

Task ini menyelaraskan komponen yang sering memicu rerun dan fetch style agar tidak ada network call berulang saat render pasif.

## 3. Tujuan Teknis

- get_active_style/get_styles memakai cache yang sudah distandardkan.
- Mutasi style memanggil invalidate_style_cache() secara konsisten.
- Rerun terjadi hanya saat state benar-benar berubah.

## 4. Scope

Yang dikerjakan:
- Refactor streamlit_app/components/form_document.py.
- Refactor streamlit_app/components/format_tab.py.

Yang tidak dikerjakan:
- Perubahan struktur fitur style.
- Perubahan teks UI yang tidak perlu.

## 5. Langkah Implementasi

1. Audit pemanggilan get_active_style() dan get_styles() di dua komponen.
2. Pastikan fetch terjadi sesuai alur cache client, bukan request langsung berulang.
3. Untuk aksi mutasi style (activate/create/update/delete/duplicate/extract):
   - panggil API,
   - jika sukses panggil invalidate_style_cache(),
   - lanjutkan rerun sekali bila perlu.
4. Kurangi rerun beruntun dalam satu flow submit.
5. Pastikan notifikasi hanya muncul saat event user, bukan saat render pasif.

## 6. Output yang Diharapkan

- Form document menampilkan style aktif tanpa fetch berulang tiap rerun pasif.
- Format tab tetap fungsional tetapi mutasi style lebih stabil.
- Tidak ada stale data style setelah aksi mutasi.

## 7. Dependencies

- Task 4 selesai.
- Task 6 selesai.

## 8. Acceptance Criteria

- [ ] get_active_style dan get_styles tidak memicu network berulang saat render pasif.
- [ ] Semua mutasi style memanggil invalidate_style_cache setelah sukses.
- [ ] Tidak ada rerun berulang yang tidak perlu di flow style.
- [ ] UI/UX tetap sama.

## 9. Estimasi

Medium (2-4 jam)
