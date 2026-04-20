# Task 6: Boot Optimization untuk Styles Loader dan Theme Apply

## 1. Judul Task

Optimasi bootstrap Streamlit agar CSS dan apply theme tidak melakukan kerja berulang di setiap rerun.

## 2. Deskripsi

Task ini menurunkan beban startup per rerun dengan cache CSS loader dan guard apply theme sekali.

## 3. Tujuan Teknis

- CSS tidak dibaca dari disk pada setiap rerun.
- Theme apply hanya dijalankan saat benar-benar perlu.
- Rerun tema tetap terkontrol dan anti double trigger.

## 4. Scope

Yang dikerjakan:
- Refactor streamlit_app/styles/loader.py.
- Refactor streamlit_app/theme.py.

Yang tidak dikerjakan:
- Perubahan palet tema.
- Perubahan tampilan UI.

## 5. Langkah Implementasi

1. Tambah helper cache untuk membaca dan menggabungkan CSS, contoh @st.cache_data.
2. Ubah inject_styles() agar memakai hasil CSS yang sudah di-cache.
3. Tambahkan state guard tema, contoh _theme_applied_once atau _theme_last_mode.
4. Di apply_saved_theme(), skip apply jika mode sama dan sudah pernah diterapkan.
5. Di switch_theme(), pertahankan rerun global tetapi pastikan tidak dobel via guard.
6. Tambahkan logging/perf sample ringan untuk waktu apply CSS dan theme.

## 6. Output yang Diharapkan

- Disk read untuk CSS berkurang drastis saat rerun.
- Theme apply tidak dieksekusi ulang tanpa perubahan mode.
- UX tetap sama, hanya lebih ringan.

## 7. Dependencies

- Task 5 selesai.

## 8. Acceptance Criteria

- [ ] Loader CSS memakai cache dan tidak baca file berulang.
- [ ] apply_saved_theme memiliki guard apply sekali.
- [ ] switch_theme tetap aman dan tidak double trigger.
- [ ] Tidak ada perubahan visual yang tidak direncanakan.

## 9. Estimasi

Low (1-2 jam)
