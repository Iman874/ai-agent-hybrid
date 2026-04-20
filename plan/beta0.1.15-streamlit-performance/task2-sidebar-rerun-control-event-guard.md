# Task 2: Sidebar Rerun Control dan Event Guard Dasar

## 1. Judul Task

Minimasi rerun di sidebar dengan controlled rerun dan event guard dasar.

## 2. Deskripsi

Task ini menstabilkan interaksi sidebar (session list, tool switch, new chat, delete) agar tidak memicu rerun berulang tanpa perubahan state.

## 3. Tujuan Teknis

- Semua aksi sidebar hanya rerun jika ada state change.
- Tidak ada double trigger pada klik cepat.
- Global rerun tetap tersedia sebagai fallback aman.

## 4. Scope

Yang dikerjakan:
- Refactor alur event di streamlit_app/components/sidebar.py.
- Tambahkan guard untuk klik berulang dan re-entry pada aksi kritis.
- Tambahkan helper internal untuk rerun terkontrol.

Yang tidak dikerjakan:
- Perubahan desain sidebar.
- Perubahan API backend.

## 5. Langkah Implementasi

1. Buat helper internal sidebar, contoh:
   - has_state_changed(old, new)
   - safe_rerun_if_changed(changed: bool)
2. Terapkan guard pada tool radio:
   - hanya update active_tool bila nilai berubah,
   - rerun hanya jika berubah.
3. Terapkan guard pada model selector:
   - hindari reset/rerun jika model sama.
4. Terapkan guard pada klik session list:
   - gunakan loading flag untuk anti double click,
   - skip load jika session yang sama sudah aktif dan bukan history mode.
5. Terapkan guard pada delete session:
   - jalankan delete sekali per klik,
   - invalidasi cache session list setelah sukses,
   - rerun hanya setelah delete sukses.
6. Pastikan fallback global rerun tetap dipakai ketika scoped rerun tidak tersedia.

## 6. Output yang Diharapkan

- Klik item session tidak menimbulkan flicker berulang.
- Ganti tool ke nilai yang sama tidak memicu rerun.
- Delete session sukses langsung refresh list sekali.

## 7. Dependencies

- Task 1 selesai.

## 8. Acceptance Criteria

- [ ] Sidebar tidak melakukan rerun jika tidak ada perubahan state.
- [ ] Klik cepat pada aksi session tidak memicu double trigger.
- [ ] Fallback global rerun tetap berfungsi.
- [ ] Tidak ada perubahan UI/UX selain stabilitas interaksi.

## 9. Estimasi

Medium (2-4 jam)
