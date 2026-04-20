# Task 14: Frontend — UI Tombol Retry & Continue + Store Integration

## 1. Judul Task
Frontend: Tombol Generate Ulang & Lanjutkan di Halaman Detail Riwayat

## 2. Deskripsi
Setelah Task 13 menyediakan endpoint backend, task ini membangun UI tombol dan
integrasi Zustand store agar user bisa:
- **Generate Ulang (Retry)**: Klik tombol → stream TOR baru dari source text yang tersimpan
- **Lanjutkan (Continue)**: Klik tombol → lanjutkan TOR dari titik putus, hasilnya digabung

## 3. Tujuan Teknis
- Tombol Retry dan Continue muncul di halaman detail riwayat (`GenerateResult`) saat status `failed`
- Tombol Continue muncul hanya jika ada partial `tor_content` 
- Saat diklik, berpindah ke `StreamingResult` view dengan streaming dari endpoint baru
- Setelah selesai, riwayat terupdate dan user bisa melihat hasil lengkap

## 4. Scope

### Yang Dikerjakan
- **API client**: Tambah fungsi `retryStream()` dan `continueStream()` di `api/generate.ts`
- **Store**: Tambah action `retryGeneration(id)` dan `continueGeneration(id)` di `generate-store.ts`
- **UI GenerateResult**: Tampilkan tombol Retry/Continue sesuai kondisi
- **UI StreamingResult**: (minor) Support mode continue — gabungkan old + new content

### Yang TIDAK Dikerjakan
- Backend endpoint (sudah di Task 13)
- i18n keys (dikerjakan di Task 15)

## 5. File yang Dimodifikasi

| File | Aksi |
|------|------|
| `app_frontend/src/api/generate.ts` | Tambah `retryStream()` + `continueStream()` |
| `app_frontend/src/stores/generate-store.ts` | Tambah 2 action baru |
| `app_frontend/src/components/generate/GenerateResult.tsx` | Tombol Retry + Continue |
| `app_frontend/src/components/generate/GenerateContainer.tsx` | Wiring state untuk continue mode |

## 6. Detail Implementasi

### 6.1 API Client: `retryStream()` dan `continueStream()`
```typescript
// Retry: generate ulang dari awal
export async function retryStream(
  genId: string,
  callbacks: StreamCallbacks,
  abortSignal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/generate/${genId}/retry-stream`, {
    method: "POST",
    signal: abortSignal,
  });
  // ... SSE reader loop (sama seperti streamGenerateFromDocument)
}

// Continue: lanjutkan dari partial
export async function continueStream(
  genId: string,
  callbacks: StreamCallbacks,
  abortSignal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/generate/${genId}/continue-stream`, {
    method: "POST",
    signal: abortSignal,
  });
  // ... SSE reader loop
}
```

> **CATATAN**: SSE reader loop bisa di-extract ke shared helper untuk menghindari duplikasi.

### 6.2 Store: `retryGeneration()` dan `continueGeneration()`
```typescript
retryGeneration: async (genId: string) => {
  const abortController = new AbortController();
  set({ isStreaming: true, streamingContent: "", ... });
  
  await retryStream(genId, {
    onStatus: ...,
    onToken: ...,
    onDone: ...,
    onError: ...,
  }, abortController.signal);
},

continueGeneration: async (genId: string, existingContent: string) => {
  const abortController = new AbortController();
  // PENTING: mulai dengan existingContent yang sudah ada!
  set({ isStreaming: true, streamingContent: existingContent, ... });
  
  await continueStream(genId, {
    onToken: (t) => set(s => ({ streamingContent: s.streamingContent + t })),
    ...
  }, abortController.signal);
},
```

### 6.3 UI: GenerateResult — Conditional Buttons

Kondisi tampil tombol:
```
┌────────────────────────────────────────────┐
│ Status    │ Content │ Retry │ Continue │
├───────────┼─────────┼───────┼──────────┤
│ failed    │ empty   │  ✅   │   ❌     │
│ failed    │ partial │  ✅   │   ✅     │
│ completed │ full    │  ✅   │   ❌     │
│ processing│ -       │  ❌   │   ❌     │
└────────────────────────────────────────────┘
```

Desain visual tombol:
```tsx
{/* Section: Action buttons for failed/completed */}
{resultFromHistory?.status === "failed" && (
  <div className="flex gap-2 mt-4">
    <Button variant="outline" onClick={handleRetry}>
      <RotateCcw className="w-4 h-4 mr-1.5" />
      Generate Ulang
    </Button>
    {torContent && (
      <Button variant="default" onClick={handleContinue}>
        <Play className="w-4 h-4 mr-1.5" />
        Lanjutkan
      </Button>
    )}
  </div>
)}
```

### 6.4 Flow Continue: Gabungkan Content
Saat Continue, `StreamingResult` harus:
1. Mulai dengan `streamingContent = existingPartialContent`
2. Token baru dari Gemini di-append di akhir
3. Visual: konten lama tampil langsung, kursor berkedip dari titik terakhir

## 7. Acceptance Criteria
- [ ] Tombol "Generate Ulang" muncul saat detail riwayat yang status `failed` dibuka
- [ ] Tombol "Lanjutkan" muncul hanya jika ada partial content
- [ ] Klik Retry → streaming TOR baru dari awal (StreamingResult view)
- [ ] Klik Continue → streaming lanjutan, hasilnya gabungan old + new
- [ ] Cancel di tengah retry/continue → partial tersimpan (reuse flow Task 12)
- [ ] Setelah selesai, riwayat lama di-replace atau record baru muncul
