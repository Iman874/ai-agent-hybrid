# Task 09 — Testing: Verifikasi End-to-End & Edge Cases

## 1. Judul Task

Pengujian end-to-end alur Chat-to-TOR Streaming Generate dan penanganan edge cases.

## 2. Deskripsi

Setelah semua task implementasi selesai, task ini mendefinisikan skenario pengujian manual yang harus diverifikasi. Tujuannya memastikan seluruh alur berfungsi tanpa regresi, termasuk kasus error, cancel, dan timeout.

## 3. Tujuan Teknis

- Verifikasi alur happy path: Chat → READY_TO_GENERATE → auto-switch tab → streaming TOR → GenerateResult.
- Verifikasi rollback state: cancel, error, timeout.
- Verifikasi no regresi: chat biasa (NEED_MORE_INFO), generate dari dokumen upload, session history.

## 4. Scope

### Yang dikerjakan
- Pengujian manual 8 skenario.
- Fix bug yang ditemukan saat testing.
- Verifikasi `npm run build` zero errors.
- Verifikasi backend startup tanpa error.

### Yang tidak dikerjakan
- Menulis automated test (bisa dilakukan di version berikutnya).
- Pengujian performa / load testing.

## 5. Skenario Pengujian

### Skenario 1: Happy Path — Chat sampai Generate
**Prasyarat**: Backend dan frontend running.

1. Buka app, mulai chat baru.
2. Berikan semua informasi yang diminta AI secara lengkap (judul, latar belakang, ruang lingkup, output, timeline, anggaran).
3. AI merespons dengan status `READY_TO_GENERATE`.
4. **Ekspektasi**:
   - Muncul bubble transisi "Semua informasi sudah lengkap!".
   - Tab otomatis berpindah ke Generate.
   - `StreamingResult` menampilkan status "Memeriksa data sesi chat...".
   - Token TOR mengalir.
   - Label "Sumber: Sesi chat" tampil.
   - Setelah selesai, transisi ke `GenerateResult`.
   - History generate menampilkan entry baru.
   - Session state di DB = `COMPLETED`.

### Skenario 2: Cancel Mid-Stream
1. Mulai skenario 1 sampai token TOR mulai mengalir.
2. Klik tombol "Stop Generating".
3. **Ekspektasi**:
   - Streaming berhenti segera.
   - Partial content tetap ditampilkan.
   - Label error "Dibatalkan oleh user" tampil.
   - Tombol "Generate Ulang" tersedia.
   - Session state di DB = `READY` (bukan stuck `GENERATING`).

### Skenario 3: Error dari Backend
1. Simulasikan error (misalnya matikan Gemini API key atau set timeout sangat rendah).
2. Mulai chat sampai READY, biarkan auto-trigger.
3. **Ekspektasi**:
   - Error message tampil di `StreamingResult`.
   - Partial content (jika ada) tetap tampil.
   - Tombol retry tersedia.
   - Session state = `READY`.

### Skenario 4: Tombol Manual "Buat TOR"
1. Mulai chat baru, berikan informasi lengkap sampai READY.
2. Jika auto-trigger sudah berjalan, cancel.
3. Kembali ke tab Chat.
4. Tombol "Buat TOR Sekarang" harus tampil.
5. Klik tombol.
6. **Ekspektasi**: Tab berpindah, streaming dimulai.

### Skenario 5: Session Lama yang Sudah READY
1. Dari sidebar, buka session lama yang pernah berstatus READY.
2. **Ekspektasi**: 
   - Chat history tampil.
   - Tombol "Buat TOR Sekarang" tampil (jika belum pernah generate).

### Skenario 6: No Regresi — Chat Biasa
1. Mulai chat baru.
2. Berikan informasi parsial (baru 1-2 field).
3. **Ekspektasi**: 
   - Tidak ada auto-trigger.
   - Tidak ada tab switch.
   - Chat berjalan normal.

### Skenario 7: No Regresi — Generate dari Dokumen
1. Buka tab Generate.
2. Upload dokumen dan generate TOR via streaming.
3. **Ekspektasi**: Alur upload → streaming → result berjalan normal tanpa perubahan.

### Skenario 8: Duplikat Request Guard
1. Mulai generate streaming dari chat.
2. Sebelum selesai, coba trigger generate lagi (misal via DevTools curl ke endpoint).
3. **Ekspektasi**: Request kedua mendapat error "Sesi ini sedang dalam proses generate".

## 6. Output yang Diharapkan

Semua 8 skenario di atas berjalan sesuai ekspektasi tanpa crash, stuck, atau regresi.

## 7. Dependencies

- **Semua task (01–08)** harus selesai sebelum testing menyeluruh.

## 8. Acceptance Criteria

- [ ] Skenario 1 (Happy Path) berjalan end-to-end tanpa error.
- [ ] Skenario 2 (Cancel) rollback state benar dan UI stabil.
- [ ] Skenario 3 (Error) error message tampil, state rollback benar.
- [ ] Skenario 4 (Tombol Manual) berfungsi.
- [ ] Skenario 5 (Session Lama) tombol tampil jika applicable.
- [ ] Skenario 6 (No Regresi Chat) chat biasa berjalan normal.
- [ ] Skenario 7 (No Regresi Upload) generate dari dokumen berjalan normal.
- [ ] Skenario 8 (Guard Duplikat) request kedua ditolak.
- [ ] `npm run build` → zero errors.
- [ ] Backend startup tanpa import/runtime error.
- [ ] Console browser bersih dari unhandled exceptions.

## 9. Estimasi

**Medium** — ~2 jam kerja (termasuk waktu fixing bug yang ditemukan).
