# Task 5: QA + Build Verification

## 1. Judul Task
Verifikasi akhir: build check, manual testing tiga skenario utama, dan version bump.

## 2. Deskripsi
Jalankan `npm run build` untuk memastikan zero TypeScript errors, lalu lakukan manual testing untuk ketiga bug yang diperbaiki. Bump version ke `0.2.3`.

## 3. Tujuan Teknis
- `npm run build` sukses tanpa error
- Ketiga skenario (session continuity, model forwarding, TOR display) terverifikasi
- Version di `package.json` di-bump ke `0.2.3`

## 4. Scope
### Yang dikerjakan
- Build verification
- Manual test 3 skenario
- Version bump
- Audit dark mode pada komponen yang dimodifikasi

### Yang tidak dikerjakan
- Tidak membuat automated test (akan di-scope di versi selanjutnya)
- Tidak deploy ke production

## 5. Langkah Implementasi

### Step 1: Build Check
```bash
cd app_frontend
npm run build
```
Pastikan output menunjukkan zero errors. Jika ada error, fix sebelum lanjut.

### Step 2: Version Bump
```bash
npm version 0.2.3 --no-git-tag-version
```

### Step 3: Manual Test — Skenario 1: Session Continuity
1. Buka React app (clear localStorage jika perlu)
2. Kirim pesan pertama → **CECK**: sidebar harus menampilkan session baru
3. Kirim pesan kedua → **CECK** Network tab: request body harus mengandung `session_id` yang sama (bukan null)
4. Refresh browser → klik session di sidebar → kirim pesan lanjutan → **CECK**: masih session yang sama

### Step 4: Manual Test — Skenario 2: Model Forwarding
1. Pilih "Gemini" di ModelSelector
2. Kirim pesan → **CECK** Network tab: request body harus mengandung `options.chat_mode: "gemini"`
3. Ganti ke model Ollama → kirim pesan → **CECK**: `options.chat_mode: "local"`

### Step 5: Manual Test — Skenario 3: TOR Display
1. Jalankan wawancara sampai AI generate TOR (atau gunakan `force_generate`)
2. **CECK**: `TORPreview` muncul di bawah messages terakhir
3. Klik session lain → kembali ke session TOR → **CECK**: `TORPreview` masih tampil
4. Tombol Download DOCX/PDF/MD → **CECK**: download berjalan

### Step 6: Dark Mode Audit
1. Switch ke dark mode di Settings
2. Periksa semua komponen yang diubah (ChatArea, Sidebar, TORPreview)
3. Pastikan contrast dan readability baik

## 6. Output yang Diharapkan

```
> npm run build
✓ built successfully
✓ zero TypeScript errors
✓ version: 0.2.3
```

Semua 3 skenario manual testing PASS.

## 7. Dependencies
- Task 1, 2, 3, 4 (semua task sebelumnya harus selesai)

## 8. Acceptance Criteria
- [ ] `npm run build` → zero errors
- [ ] Version di `package.json` = `0.2.3`
- [ ] Skenario 1 PASS: session_id konsisten antar pesan
- [ ] Skenario 2 PASS: model preference terkirim ke backend
- [ ] Skenario 3 PASS: TOR preview tampil + restore dari session lama
- [ ] Dark mode: tidak ada elemen yang broken/unreadable

## 9. Estimasi
**Low** (~30 menit)
