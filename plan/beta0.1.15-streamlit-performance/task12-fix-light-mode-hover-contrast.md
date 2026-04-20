# Task 12: Perbaikan Kontras Hover di Mode Terang

## 1. Judul Task

Perbaiki kontras warna hover pada button di mode terang agar teks tetap jelas dan nyaman dibaca.

## 2. Deskripsi

Saat theme Terang aktif, beberapa state hover button terlalu pucat (latar mendekati putih) sehingga teks terlihat tipis dan membuat mata cepat lelah. Task ini fokus pada aksesibilitas visual: meningkatkan kontras hover/focus/active tanpa mengubah layout atau alur interaksi.

## 3. Tujuan Teknis

- Semua button utama di mode terang memiliki kontras teks terhadap background hover yang cukup.
- Hover state tidak memakai warna putih yang terlalu dominan untuk area interaktif.
- Focus-visible state tetap jelas untuk keyboard navigation.
- Konsistensi warna hover antara sidebar, settings dialog, dan area konten utama.

## 4. Scope

Yang dikerjakan:
- Refactor style hover/focus/active di streamlit_app/styles/components.css.
- Jika perlu, penyesuaian token tema terang di streamlit_app/styles/base.css agar kontras lebih stabil.
- Tambah regression test ringan (snapshot/style assertion berbasis selector yang ada) bila framework test memungkinkan.

Yang tidak dikerjakan:
- Redesign UI besar.
- Perubahan struktur komponen Streamlit.
- Perubahan behavior business logic.

## 5. Langkah Implementasi

1. Audit selector button aktif di mode terang:
   - Sidebar button (primary/secondary).
   - Settings dialog navigation button.
   - Button umum di area konten.
2. Ukur kontras visual minimal untuk state hover/focus:
   - Target praktis: teks normal mendekati standar WCAG AA (minimal 4.5:1 untuk teks biasa).
3. Ubah color-mix atau token warna agar hover tetap terlihat namun tidak menyilaukan.
4. Tambahkan style focus-visible yang kontras dan konsisten.
5. Verifikasi manual pada mode Terang:
   - sidebar,
   - settings dialog,
   - button aksi utama.
6. Jalankan regression test agar tidak merusak mode Gelap dan state lain.

## 6. Output yang Diharapkan

- Di mode Terang, teks button saat hover tetap mudah dibaca.
- Tidak ada lagi hover putih pucat yang membuat label button menghilang secara visual.
- Interaksi hover/focus terasa konsisten di seluruh area app.

## 7. Dependencies

- Task 6 selesai (boot/theme optimization).
- Task 10 selesai (settings dialog stabil).
- Task 11 selesai (i18n sudah aktif, sehingga label lintas bahasa juga tervalidasi keterbacaannya).

## 8. Acceptance Criteria

- [ ] Kontras teks pada button hover mode Terang membaik dan terbaca jelas.
- [ ] Sidebar button hover tidak menyilaukan dan tidak membuat label pudar.
- [ ] Settings dialog nav hover tetap jelas di mode Terang.
- [ ] Focus-visible state terlihat jelas untuk keyboard user.
- [ ] Tidak ada regresi visual berarti di mode Gelap.
- [ ] Regression test yang relevan tetap lulus.

## 9. Estimasi

Low sampai Medium (1-3 jam)
