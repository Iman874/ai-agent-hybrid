# Task 4: Cache Policy Matrix dan Invalidasi Terpusat di API Client

## 1. Judul Task

Implement cache policy matrix wajib dan helper invalidasi terpusat pada client API Streamlit.

## 2. Deskripsi

Task ini mengunci perilaku cache pada layer client agar tidak terjadi network call berulang saat render pasif, serta memastikan invalidasi cache konsisten setelah mutasi data.

## 3. Tujuan Teknis

- Semua fungsi yang ada di matrix memakai TTL sesuai plan.
- Tersedia helper invalidasi cache terpusat:
  - invalidate_session_cache()
  - invalidate_style_cache()
- Fungsi cache tidak memiliki side effect notifikasi.

## 4. Scope

Yang dikerjakan:
- Refactor streamlit_app/api/client.py.
- Tambah decorator cache pada fungsi yang belum sesuai matrix.
- Tambah helper invalidasi cache dan panggilannya pada mutasi.

Yang tidak dikerjakan:
- Perubahan kontrak endpoint backend.
- Perubahan business logic backend.

## 5. Langkah Implementasi

1. Audit fungsi client dan mapping ke matrix TTL.
2. Terapkan TTL sesuai plan:
   - models 30s,
   - health 15s,
   - session list 10s,
   - active style 20s,
   - styles list 20s,
   - session detail 15s.
3. Tambahkan helper invalidasi:
   - invalidate_session_cache() -> clear cache session list/detail,
   - invalidate_style_cache() -> clear cache style list/active.
4. Pastikan fungsi cache tidak memanggil notify() atau side effect lain.
5. Update call site mutasi agar memanggil helper invalidasi setelah sukses.
6. Tambahkan docstring dan catatan kapan helper wajib dipanggil.

## 6. Output yang Diharapkan

- Data session/style tidak stale setelah mutasi.
- Render pasif tidak menembak request berulang.
- Invalidation bisa dipanggil dari komponen tanpa duplikasi logika.

## 7. Dependencies

- Task 3 selesai.

## 8. Acceptance Criteria

- [ ] Semua fungsi pada matrix memiliki TTL sesuai plan.
- [ ] invalidate_session_cache() tersedia dan bekerja.
- [ ] invalidate_style_cache() tersedia dan bekerja.
- [ ] Tidak ada notify() di fungsi cache.
- [ ] Mutasi utama memicu invalidasi cache yang relevan.

## 9. Estimasi

Medium (2-4 jam)
