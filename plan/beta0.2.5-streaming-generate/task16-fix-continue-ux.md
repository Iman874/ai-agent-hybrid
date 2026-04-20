# Task 16: Fix Continue Generate — UX & Data Persistence

## 1. Deskripsi Masalah

Ada beberapa bug kritis di fitur Continue Generate:

### Bug A: `update_failed` tidak `db.commit()`
Pada edit sebelumnya, `await db.commit()` secara tidak sengaja hilang dari method
`update_failed()` di repository. Ini menyebabkan:
- Partial content TIDAK pernah benar-benar disimpan ke database
- Status "failed" tidak ter-commit

### Bug B: `source_text` tidak tersimpan (konsekuensi Bug A)
Karena `update_source_text` sudah benar (punya commit), tapi fleksibilitas
cancel & error path terganggu oleh Bug A.

### Bug C: StreamingResult — tombol salah
Saat TOR terhenti parsial di StreamingResult:
- Tombol hanya menunjukkan **"Generate Ulang"** (retry dari nol)
- Seharusnya tombol utama adalah **"Lanjutkan Generate"** (continue dari titik putus)
- "Lanjutkan" tidak muncul karena `streamSessionId` null (endpoint 400 → SSE tidak pernah kirim session_id)

### Bug D: Continue dari StreamingResult = pindah halaman
Saat user klik "Lanjutkan" di StreamingResult, `continueGeneration` me-reset state
lalu me-navigate ke `StreamingResult` baru (via GenerateContainer routing).
Harusnya **tetap di halaman yang sama**, token baru menyambung langsung.

### Bug E: State hilang saat continue
Store perlu menyimpan `_sourceGenId` (ID record asal) agar bisa retry/continue
walaupun `streamSessionId` belum didapat dari backend (karena error sebelum SSE pertama).

## 2. Solusi

### Fix A: Tambahkan `db.commit()` kembali ke `update_failed`

### Fix B: Otomatis selesai setelah Fix A

### Fix C & D: Redesign StreamingResult buttons
- Saat `isPartial` (terhenti + ada content):
  - Tombol utama = **"Lanjutkan Generate"** (continue in-place)
  - Tombol sekunder = kembali
- Continue in-place: panggil `continueStream` langsung dari StreamingResult
  tanpa me-reset `streamingContent`. Token baru di-append di akhir.

### Fix E: Simpan `_sourceGenId` di store
- `continueGeneration` dan `retryGeneration` set `_sourceGenId = genId`
- StreamingResult bisa fallback ke `_sourceGenId` jika `streamSessionId` null

## 3. File yang Dimodifikasi

| File | Perubahan |
|------|-----------|
| `app/db/repositories/doc_generation_repo.py` | Fix missing `db.commit()` |
| `app_frontend/src/stores/generate-store.ts` | Tambah `_sourceGenId`, fix continue flow |
| `app_frontend/src/components/generate/StreamingResult.tsx` | Fix buttons, in-place continue |
| `app_frontend/src/components/generate/GenerateResult.tsx` | Cleanup |

## 4. Acceptance Criteria
- [ ] `update_failed` commit ke database
- [ ] StreamingResult: tombol utama "Lanjutkan Generate" saat partial
- [ ] Continue dari StreamingResult: token baru nyambung di halaman yang sama
- [ ] Continue dari history detail (GenerateResult): langsung mulai streaming
- [ ] Fallback ke `_sourceGenId` jika `streamSessionId` null
