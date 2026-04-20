# Task 11: Fix Streaming Table Lag & Extension of Timeouts

## 1. Analisis Bug
### Server Timeout Error & Safety Timeout Terlalu Singkat
- Saat merender TOR panjang, proses dari Gemini memakan waktu hingga 3-5 menit karena limit token output Gemini besar.
- Waktu `GEMINI_TIMEOUT` default di backend (kemungkinan 60-120 detik) serta `safetyTimeout` hardcode di `generate-store.ts` (120 detik) memicu status "Failed/Timeout" persis ketika AI masih asyik mengetik.

### Lag Extreme pada Markdown (Terutama Tabel)
- `StreamingResult.tsx` memanggil komponen `<MarkdownRenderer content={renderedContent} />` secara Throttle tiap 100ms.
- Jika teks sudah mencapai 70,000 karakter (seperti gambar 70456 chars), markdown parser me-reparse seluruh 70KB teks tersebut dari atas ke bawah *setiap* 0.1 detik di Main Thread UI!! Inilah yang membuat browser UI freeeze, scroll lag, dan memakan resource sangat tinggi ("nge-lag minta ampun").
- **Tabel Tidak Muncul**: Komponen MarkdownRenderer kemungkinan belum mendukung ekstensi tabel standard (remark-gfm), atau styling "prose" Tailwind belum diterapkan untuk tabel.

## 2. Rencana Implementasi (Fixes)

### 2.1. Memperpanjang Timeout backend & Store menjadi 5 Menit (300s)
- **`app/config.py` & `.env`**: Set `GEMINI_TIMEOUT=300`.
- **`generate-store.ts`**: Ubah fungsi `setTimeout` dari 120_000 menjadi 300_000 (300 detik/5 menit).

### 2.2. Optimasi Throttling & Markdown Rendering di Frontend
- **File**: `StreamingResult.tsx`
- Ubah interval `throttle` untuk panjang string ekstrem. Jika string masih pendek (<2000 chars), throttle 100ms tidak masalah. Jika teks bertambah masif (>10000 chars), perlebar throttle menjadi 500ms s/d 1000ms untuk mengurangi beban re-render.
- Memisahkan komponen markdown dengan `React.memo` (sudah dilakukan jika dari komponen, namun pastikan props tidak gampang berubah).

### 2.3. Memperbaiki Fitur Render Tabel
- **File**: `MarkdownRenderer.tsx`
- Pastikan kita meng-import package `remark-gfm` (untuk standard GitHub Flavored Markdown yang mencakup fitur tabel).
- Jika package module belum terinstall, instal via `npm i remark-gfm`.
- Terapkan style tabel sederhana jika CSS Tailwind Typography tidak termuat.

## 3. Eksekusi Mandiri
Tugas lanjutan ini akan diimplementasikan satu per satu.
