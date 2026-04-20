# Task 15: i18n, Edge Cases & Polish Retry/Continue

## 1. Judul Task
Polish: Terjemahan, Error Handling, dan Edge Cases untuk Retry/Continue

## 2. Deskripsi
Task akhir yang memoles fitur Retry & Continue agar production-ready:
terjemahan bahasa, handling limitasi, loading states, dan validasi edge cases.

## 3. Tujuan Teknis
- Semua string baru ter-translate di `id.ts` dan `en.ts`
- Error states ditangani dengan baik (source text hilang, quota habis, dll)
- UX sudah bersih tanpa raw key language di UI

## 4. Scope

### Yang Dikerjakan
- **i18n**: Tambah translation keys untuk semua tombol dan pesan baru
- **Error handling**: Record lama tanpa `source_text` → pesan jelas, bukan crash
- **Loading state**: Animasi saat retry/continue dimulai (sebelum token pertama)
- **Retry dari StreamingResult**: Tombol retry di footer StreamingResult juga bisa trigger retry-stream
- **Validasi backend**: Rate limit check (max_gemini_calls_per_hour) berlaku juga untuk retry/continue

### Yang TIDAK Dikerjakan
- Implementasi core (sudah di Task 13 & 14)

## 5. File yang Dimodifikasi

| File | Aksi |
|------|------|
| `app_frontend/src/i18n/locales/id.ts` | Tambah keys baru |
| `app_frontend/src/i18n/locales/en.ts` | Tambah keys baru |
| `app_frontend/src/components/generate/GenerateResult.tsx` | Gunakan t() keys |
| `app_frontend/src/components/generate/StreamingResult.tsx` | Retry button improved |
| `app/api/routes/generate_doc.py` | Validasi source_text null + meaningful error |

## 6. Detail Implementasi

### 6.1 Translation Keys Baru

**id.ts:**
```typescript
"generate.retry_generate": "Generate Ulang",
"generate.continue_generate": "Lanjutkan Generate",
"generate.retry_desc": "Buat TOR baru dari dokumen sumber yang sama.",
"generate.continue_desc": "Lanjutkan dari titik terakhir yang terputus.",
"generate.source_unavailable": "Dokumen sumber tidak tersedia lagi (rekam lama). Upload ulang untuk generate baru.",
"generate.continue_unavailable": "Tidak ada hasil parsial untuk dilanjutkan.",
```

**en.ts:**
```typescript
"generate.retry_generate": "Regenerate",
"generate.continue_generate": "Continue Generating",
"generate.retry_desc": "Create a new TOR from the same source document.",
"generate.continue_desc": "Continue from where it was interrupted.",
"generate.source_unavailable": "Source document is no longer available (old record). Re-upload to generate.",
"generate.continue_unavailable": "No partial result available to continue.",
```

### 6.2 Edge Cases yang Harus Ditangani

| Kasus | Handling |
|-------|----------|
| Record lama tanpa `source_text` | Backend return 400, UI tampilkan `source_unavailable` |
| Continue tanpa `tor_content` | Tombol Continue disembunyikan |
| Retry/Continue saat ada streaming aktif | Disable tombol jika `isStreaming === true` |
| Gemini quota habis | Error SSE diteruskan ke UI seperti biasa |
| Network putus saat retry/continue | Partial content di-save (reuse mekanisme Task 12) |

### 6.3 Retry dari StreamingResult
Saat ini, tombol Retry di `StreamingResult` hanya memanggil `clearStreamState()`.
Setelah task ini, tombol tersebut harus:
- Jika `streamSessionId` tersedia → panggil `retryGeneration(streamSessionId)`
- Jika tidak → fallback ke `clearStreamState()` (kembali ke upload form)

## 7. Acceptance Criteria
- [ ] Semua button label menggunakan `t()` tanpa raw key di UI
- [ ] Record lama (sebelum source_text ada) → pesan error yang jelas, bukan crash
- [ ] Retry & continue dihitung ke rate limit yang sama
- [ ] Loading states berjalan mulus tanpa visual glitch
- [ ] QA: test manual full flow → generate → stop → continue → selesai → export ✅
