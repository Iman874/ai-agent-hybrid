# Task 9: i18n + QA + Build Verification

## 1. Judul Task
Tambah translation keys baru untuk fitur streaming, verifikasi build, dan bump version ke 0.2.5.

## 2. Deskripsi
Menambahkan semua translation keys yang dibutuhkan oleh `StreamingResult.tsx` dan komponen streaming lainnya. Lalu menjalankan build check dan manual testing.

## 3. Tujuan Teknis
- Translation keys lengkap di `id.ts` dan `en.ts`
- `npm run build` sukses
- Version bump ke `0.2.5`

## 4. Scope
### Yang dikerjakan
- Update `src/i18n/locales/id.ts` dan `en.ts`
- `npm run build`
- `npm version 0.2.5 --no-git-tag-version`
- Manual test 6 skenario

### Yang tidak dikerjakan
- Tidak membuat automated test

## 5. Langkah Implementasi

### Step 1: Tambah translation keys di `id.ts`

Di section Generate, tambahkan:
```typescript
// Streaming
"generate.streaming_title": "Menghasilkan TOR...",
"generate.partial_title": "Hasil belum lengkap",
"generate.partial_warning": "Hasil ini belum lengkap karena proses dihentikan sebelum selesai.",
"generate.stop": "Stop",
"generate.retry": "Coba Lagi",
```

### Step 2: Tambah translation keys di `en.ts`

```typescript
// Streaming
"generate.streaming_title": "Generating TOR...",
"generate.partial_title": "Incomplete result",
"generate.partial_warning": "This result is incomplete because the process was stopped before finishing.",
"generate.stop": "Stop",
"generate.retry": "Retry",
```

### Step 3: Build Check

```bash
cd app_frontend
npm run build
```

### Step 4: Version Bump

```bash
npm version 0.2.5 --no-git-tag-version
```

### Step 5: Manual Test — 6 Skenario

**Skenario 1: Happy Path**
1. Upload file → Generate TOR
2. Status messages tampil
3. Teks muncul chunk per chunk, cursor berkedip
4. Setelah selesai, auto-transisi ke GenerateResult
5. Export buttons berfungsi
6. History entry baru ✓

**Skenario 2: User Cancel**
1. Upload file → mulai streaming
2. Klik "Stop"
3. Streaming berhenti, partial result tampil
4. Warning "Hasil belum lengkap" muncul
5. Tombol "Coba Lagi" tersedia

**Skenario 3: Error Mid-Stream**
1. Simulasikan error Gemini
2. Partial text tetap tampil + error message
3. History entry ✗ Failed

**Skenario 4: Network Disconnect**
1. Cabut WiFi saat streaming
2. Error muncul, partial text preserved
3. Tidak ada infinite loading

**Skenario 5: Timeout**
1. Tunggu >120 detik (atau turunkan timeout untuk test)
2. Auto-abort, error message muncul

**Skenario 6: Rapid Re-generate**
1. Generate → cancel → generate lagi
2. State reset benar, streaming kedua normal

## 6. Output yang Diharapkan

```
> npm run build
✓ built successfully
✓ zero TypeScript errors
✓ version: 0.2.5
```

## 7. Dependencies
- Task 1-8 (semua task sebelumnya)

## 8. Acceptance Criteria
- [ ] Semua translation keys tersedia di `id.ts` dan `en.ts`
- [ ] `npm run build` tanpa error
- [ ] Version `package.json` = `0.2.5`
- [ ] Skenario 1 PASS: streaming generate end-to-end
- [ ] Skenario 2 PASS: cancel mid-stream + partial preserved
- [ ] Skenario 3 PASS: error + partial preserved
- [ ] Skenario 4 PASS: disconnect handling
- [ ] Skenario 5 PASS: timeout auto-abort
- [ ] Skenario 6 PASS: rapid re-generate no stale state

## 9. Estimasi
**Low** (~30 menit)
