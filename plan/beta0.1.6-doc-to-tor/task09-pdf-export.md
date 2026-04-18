# Task 09: Fitur Export TOR ke PDF

## Deskripsi
Menambahkan fungsionalitas untuk mengunduh dokumen TOR yang telah di-generate dalam format PDF pada UI Streamlit. Fitur ini harus tersedia di semua tab (Hybrid Chat, Gemini Direct, dan From Document).

## Tujuan Teknis
1. Menambahkan konversi Markdown ke PDF.
2. Memperbarui komponen reusabe `render_tor_preview()` di Streamlit agar menyediakan dua tombol unduh (Markdown dan PDF).

## Scope
- [x] Install dependensi tambahan untuk membuat PDF dari markdown (contoh: `markdown-pdf`, `fpdf2`, atau kombinasi `markdown` + `pdfkit`).
- [x] Buat helper function `export_to_pdf(markdown_text: str) -> bytes` di dalam file baru atau di `streamlit_app.py`.
- [x] Tambahkan opsi tombol `st.download_button(..., mime="application/pdf")` disamping tombol render Markdown di fungsi `render_tor_preview()`.
- [ ] Opsi styling PDF untuk membuatnya formal (menggunakan font yang pas).

## Out of Scope
- Format doc/docx export (hanya fokus PDF dan MD saat ini).
- Kustomisasi header/footer PDf tingkat lanjut.

## Acceptance Criteria
- [ ] Hasil generate TOR di semua 3 tab memiliki opsi "Download TOR (.pdf)".
- [ ] File yang didownload bisa dibuka dan isinya sesuai dengan markdown preview yang ditampilkan.

## Dependensi Baru (Opsional)
Pilih salah satu librari dari python untuk implementasi yang tidak memerlukan binary instalasi sistem (opsional tapi disarankan agar lebih portabel):
- `markdown-pdf`
- ATAU `markdown` + `weasyprint` / `pdfkit` (pastikan environment requirements diperhatikan).
