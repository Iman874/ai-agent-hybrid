# Task 10: Perbaikan Edit Format TOR di Settings

## 1. Judul Task

Pulihkan fitur edit pada tab Format TOR di Settings untuk semua style non-default.

## 2. Deskripsi

Pada implementasi performa sebelumnya, kontrol edit style menjadi tidak terlihat di alur Settings sehingga terkesan hilang. Task ini memulihkan visibilitas aksi edit tanpa mengubah aturan utama: hanya style default yang read-only, style selain default tetap bisa diedit.

## 3. Tujuan Teknis

- Aksi `Edit Style` selalu terlihat untuk style non-default.
- Style default tetap tidak dapat diedit.
- Deteksi `is_default` tahan terhadap variasi tipe nilai (`bool`/`str`/`int`).
- Aksi edit/simpan di Settings tetap berada di dialog (tidak menutup ke halaman utama).
- Tidak ada perubahan perilaku untuk aksi clone/delete/extract selain perbaikan visibilitas.

## 4. Scope

Yang dikerjakan:
- Refactor `streamlit_app/components/format_tab.py`.
- Tambah test logika deteksi default-style.

Yang tidak dikerjakan:
- Redesign UI besar.
- Perubahan kontrak API style.

## 5. Langkah Implementasi

1. Keluarkan action row edit/clone/delete dari area expander lanjutan.
2. Tampilkan form edit inline hanya saat mode edit aktif dan style bukan default.
3. Tambahkan helper normalisasi `is_default` agar string seperti `"false"` tidak terbaca sebagai default.
4. Simpan extraction section di expander lanjutan agar alur edit tetap fokus.
5. Ubah mekanisme rerun action style menjadi fragment-first fallback global agar dialog tidak tertutup.
6. Tambahkan test unit untuk helper deteksi default-style dan rerun behavior.

## 6. Output yang Diharapkan

- Di Settings > Format TOR, style non-default menampilkan tombol `Edit Style`.
- Style default tetap menampilkan status read-only.
- Klik `Edit Style` / `Selesai Edit` / `Simpan Perubahan` tidak menutup dialog Pengaturan.
- Tidak ada regresi pada flow clone/delete/extract.

## 7. Dependencies

- Task 7 selesai.
- Task 9 regression baseline tersedia.

## 8. Acceptance Criteria

- [ ] Tombol edit muncul untuk style non-default.
- [ ] Style default tetap tidak bisa diedit.
- [ ] Form edit hanya aktif ketika mode edit dinyalakan.
- [ ] Aksi edit/simpan di Format TOR tidak menutup dialog Pengaturan.
- [ ] Test otomatis deteksi default-style dan rerun fragment lulus.
- [ ] Tidak ada perubahan UI/UX di luar perbaikan visibilitas edit.

## 9. Estimasi

Low (1-2 jam)
