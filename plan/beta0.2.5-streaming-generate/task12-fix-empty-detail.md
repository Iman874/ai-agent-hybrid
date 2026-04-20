# Task 12: Fix Empty Detail View & Missing Retry Button untuk Dokumen Batal (History)

## 1. Analisis Bug
- **Hasil Generate Kosong (Black Box)**: Pengguna membuka riwayat TOR yang dibatalkan paksa dari sesi yang *lampau* (sebelum fitur update `partial_content` di database diterapkan pada Task sebelumnya). Karena database untuk document session `TOR_d333` terekam tanpa adanya isi teks, maka `torContent` bernilai `null` / `""`. Akibatnya, UI merender container hitam kosong tanpa kejelasan.
- **Tidak Ada Tombol Retry**: Di layar `GenerateResult.tsx` (mode detail riwayat), belum ada fitur/tombol "Coba Lagi" apabila status generasi adalah "failed" atau "partial". Perlu diingat, backend tidak menyimpan file fisik PDF/DOCX yang sudah di-upload demi privasi (hanya mencatat `filename` dan `size`), sehingga proses generate ulang otomatis dari riwayat *tidak bisa* dilakukan secara instan.

## 2. Rencana Implementasi (Fixes)

### 2.1. Memperbaiki Indikator Error di GenerateResult (UI Kosong)
- **File**: `app_frontend/src/components/generate/GenerateResult.tsx`
- **Tindakan**:
  - Jika konten `torContent` kosong dan document record memiliki `error_message` atau status `"failed"`, segera tampilkan pesan error tersebut di dalam panel (agar user tahu alasannya berhenti), bukan kotak hitam biasa.
  - Sembunyikan tombol "Download/Ekspor" jika konten kosong, karena men-download teks kosong akan membuat error eksportir.

### 2.2. Menyediakan "Virtual Retry" (Arahkan Ulang Upload)
- **File**: `app_frontend/src/components/generate/GenerateResult.tsx` (dan Store)
- **Tindakan**:
  - Tambahkan tombol "Upload Ulang / Retry" ketika status gagal / konten kosong.
  - Karena file tidak ada, tombol ini tidak men-trigger API stream, melainkan sebuah pintasan untuk menutup layar `activeResult` (Clear Active Result) lalu meminta user melakukan *"Drop the file again"*. Ini memberikan kejelasan _User Experience_ tanpa rasa menggantung.

## 3. Eksekusi Mandiri
Task ini akan segera diimplementasikan layaknya task sebelumnya: 
- Menambahkan fallback Error State.
- Tombol Upload Kembali.
