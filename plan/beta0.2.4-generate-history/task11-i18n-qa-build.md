# Task 11: i18n Keys + QA + Build Verification

## 1. Judul Task
Tambah translation keys baru, verifikasi build, dan bump version ke 0.2.4.

## 2. Deskripsi
Menambahkan semua translation keys yang dibutuhkan oleh komponen baru (`GenerateHistory`, refactored components), lalu melakukan build check dan manual testing end-to-end.

## 3. Tujuan Teknis
- Translation keys lengkap di `id.ts` dan `en.ts`
- `npm run build` sukses
- Version bump ke `0.2.4`
- Backend restart tanpa error

## 4. Scope
### Yang dikerjakan
- Update `src/i18n/locales/id.ts` dan `en.ts`
- `npm run build`
- `npm version 0.2.4 --no-git-tag-version`
- Manual test 4 skenario

### Yang tidak dikerjakan
- Tidak membuat automated test

## 5. Langkah Implementasi

### Step 1: Tambah translation keys di `id.ts`

Di section Generate, tambahkan:
```typescript
// Generate History
"generate.history_title": "Riwayat Generate",
"generate.no_history": "Belum ada riwayat generate dari dokumen.",
"generate.words_label": "kata",
"generate.status_completed": "Selesai",
"generate.status_failed": "Gagal",
"generate.status_processing": "Memproses",
"generate.view": "Lihat",
"generate.delete": "Hapus",
"generate.delete_confirm": "Yakin hapus riwayat ini?",
```

### Step 2: Tambah translation keys di `en.ts`

```typescript
"generate.history_title": "Generation History",
"generate.no_history": "No document generation history yet.",
"generate.words_label": "words",
"generate.status_completed": "Completed",
"generate.status_failed": "Failed",
"generate.status_processing": "Processing",
"generate.view": "View",
"generate.delete": "Delete",
"generate.delete_confirm": "Delete this history item?",
```

### Step 3: Build Check

```bash
cd app_frontend
npm run build
```

### Step 4: Version Bump

```bash
npm version 0.2.4 --no-git-tag-version
```

### Step 5: Manual Test

**Skenario 1: Generate + Persist**
1. Upload file → Generate TOR → hasil muncul
2. Klik Back → riwayat tampil dengan entry baru ✓
3. Refresh browser → riwayat masih ada

**Skenario 2: View dari Riwayat**
1. Klik 👁 di riwayat → detail TOR muncul
2. Export DOCX/PDF/MD → download berhasil

**Skenario 3: Generate Gagal**
1. Upload file corrupt atau tanpa Gemini API key
2. Riwayat menampilkan entry ✗ Failed

**Skenario 4: Delete**
1. Klik 🗑 → entry hilang
2. Refresh → entry tetap tidak ada

## 6. Output yang Diharapkan

```
> npm run build
✓ built successfully
✓ zero TypeScript errors
✓ version: 0.2.4
```

## 7. Dependencies
- Task 1-10 (semua task sebelumnya)

## 8. Acceptance Criteria
- [ ] Semua translation keys tersedia di `id.ts` dan `en.ts`
- [ ] `npm run build` tanpa error
- [ ] Version `package.json` = `0.2.4`
- [ ] Backend startup: migration 006 applied
- [ ] Skenario 1 PASS: generate → persist → survive reload
- [ ] Skenario 2 PASS: view history result + export
- [ ] Skenario 3 PASS: failed generate recorded
- [ ] Skenario 4 PASS: delete works

## 9. Estimasi
**Low** (~45 menit)
