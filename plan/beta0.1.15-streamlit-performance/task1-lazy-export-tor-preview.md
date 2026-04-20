# Task 1: Lazy Export di TOR Preview

## 1. Judul Task

Implement lazy export pada komponen preview TOR agar tidak ada API call saat render pasif.

## 2. Deskripsi

Task ini menghilangkan side effect network pada render preview. Export docx/pdf/md hanya boleh dipanggil saat user klik tombol Siapkan.

## 3. Tujuan Teknis

- Preview tidak memanggil endpoint export secara otomatis.
- Export dipanggil hanya saat user action.
- Hasil export disimpan di session state per session_id dan format.
- Download menggunakan data lokal yang sudah disiapkan.

## 4. Scope

Yang dikerjakan:
- Ubah alur export di streamlit_app/components/tor_preview.py.
- Tambahkan struktur cache export di session state.
- Tambahkan tombol Siapkan per format dan tombol Download yang membaca cache lokal.

Yang tidak dikerjakan:
- Perubahan endpoint backend export.
- Perubahan UI besar atau redesign komponen preview.

## 5. Langkah Implementasi

1. Tambahkan key state untuk export cache, contoh: tor_export_cache (dict).
2. Definisikan cache key stabil: session_id + key_suffix + format.
3. Hapus pemanggilan export_document() dari jalur render default.
4. Buat helper prepare export:
   - validasi key cache,
   - jika belum ada, panggil export_document(session_id, fmt),
   - simpan bytes ke cache state.
5. Ubah blok tombol per format:
   - tombol Siapkan .docx/.pdf/.md,
   - setelah sukses, tampilkan download button dari bytes lokal.
6. Jika prepare gagal, tampilkan notifikasi error tanpa loop rerun.
7. Pastikan rerender tidak memicu fetch ulang jika bytes sudah tersedia.

## 6. Output yang Diharapkan

- Saat preview TOR pertama kali tampil, tidak ada request export.
- User klik Siapkan .pdf -> satu request ke endpoint export pdf.
- Tombol Download .pdf aktif dan memakai bytes lokal dari state.
- Rerun berikutnya tidak memanggil ulang export selama cache masih ada.

## 7. Dependencies

- Tidak ada. Task ini wajib dikerjakan paling awal.

## 8. Acceptance Criteria

- [ ] Preview TOR tidak melakukan API call export saat render pasif.
- [ ] Export dipanggil hanya saat klik tombol Siapkan.
- [ ] Data export disimpan di session state dengan key yang konsisten.
- [ ] Download button membaca data lokal, bukan fetch ulang.
- [ ] Tidak ada perubahan UI/UX besar selain alur Siapkan -> Download.

## 9. Estimasi

Medium (2-4 jam)
