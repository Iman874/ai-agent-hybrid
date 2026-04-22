# Task 05 — Frontend: UI Transition dari Chat ke Streaming TOR

## 1. Judul Task

Menambahkan visual feedback transition saat UI berpindah dari Chat ke Streaming TOR Generate.

## 2. Deskripsi

Setelah task 04, perpindahan tab dari `chat` ke `generate_doc` sudah berjalan otomatis. Namun tanpa visual feedback, transisi ini bisa terasa mendadak bagi user. Task ini menambahkan:
1. **Pesan notifikasi dalam chat** — Tampilkan bubble khusus di chat yang menginformasikan "AI sedang membuat TOR Anda..." sebelum pindah tab.
2. **Source indicator di StreamingResult** — Tambahkan keterangan bahwa streaming ini berasal dari sesi chat (bukan upload dokumen).

## 3. Tujuan Teknis

- Menampilkan pesan transisi di chat bubble sebelum tab berpindah.
- Menambahkan property `streamSource` di `generate-store` agar `StreamingResult` bisa menampilkan konteks asal.

## 4. Scope

### Yang dikerjakan
- Tambahkan `streamSource` state di `generate-store.ts`: `"document" | "chat" | null`.
- Set `streamSource: "chat"` pada `generateFromChatStream()`.
- Set `streamSource: "document"` pada `generateFromDocStream()`.
- Tampilkan label konteks di `StreamingResult.tsx` berdasarkan `streamSource`.
- Tambahkan system-message bubble di chat sebelum pindah tab.

### Yang tidak dikerjakan
- Animasi transisi antar tab (out of scope — bisa ditambah nanti).
- Perubahan backend.

## 5. Langkah Implementasi

### Step 1: Tambahkan `streamSource` di `generate-store.ts`

Di interface `GenerateStore`:
```typescript
  streamSource: "document" | "chat" | null;
```

Di initial state:
```typescript
  streamSource: null,
```

Di `clearStreamState`:
```typescript
  streamSource: null,
```

### Step 2: Set `streamSource` di action-action yang relevan

Di `generateFromDocStream()`, tambahkan di `set()` awal:
```typescript
  streamSource: "document",
```

Di `generateFromChatStream()`, tambahkan di `set()` awal:
```typescript
  streamSource: "chat",
```

### Step 3: Tampilkan sumber di `StreamingResult.tsx`

Baca `streamSource` dari store:
```typescript
const streamSource = useGenerateStore(s => s.streamSource);
```

Tambahkan label kecil di bawah judul header (di dalam blok `isStreaming ? ...`):
```tsx
{streamSource === "chat" && (
  <p className="text-xs text-muted-foreground mt-0.5">
    Sumber: Sesi chat
  </p>
)}
```

### Step 4: Tambahkan system message di chat sebelum pindah tab

Di `chat-store.ts`, tepat sebelum `useUIStore.getState().setActiveTool("generate_doc")`, tambahkan system message:

```typescript
// Tambahkan pesan transisi di chat
set(state => ({
  messages: [
    ...state.messages,
    {
      id: crypto.randomUUID(),
      role: "assistant" as const,
      content: "✅ Semua informasi sudah lengkap! Memulai pembuatan dokumen TOR...",
      timestamp: Date.now(),
      status: "done" as const,
    },
  ],
}));
```

## 6. Output yang Diharapkan

### Chat view (sebelum transition):
```
[User] Judulnya "Pelatihan IT Dasar", anggaran 50 juta.
[AI]   Baik, semua data sudah lengkap. [JSON READY_TO_GENERATE]
[AI]   ✅ Semua informasi sudah lengkap! Memulai pembuatan dokumen TOR...
       ↓ (otomatis pindah tab ke Generate)
```

### StreamingResult view (setelah transition):
```
⏳ Menghasilkan TOR...
   Sumber: Sesi chat
   ─────────────────
   # Kerangka Acuan Kerja
   ## 1. Latar Belakang...
```

## 7. Dependencies

- **Task 03** harus selesai (`generateFromChatStream` dan `streamSource` state).
- **Task 04** harus selesai (auto-trigger di `finalizeStream`).

## 8. Acceptance Criteria

- [ ] `streamSource` tersedia di `GenerateStore` (`"document" | "chat" | null`).
- [ ] `generateFromDocStream` men-set `streamSource: "document"`.
- [ ] `generateFromChatStream` men-set `streamSource: "chat"`.
- [ ] `clearStreamState` men-reset `streamSource: null`.
- [ ] `StreamingResult` menampilkan label "Sumber: Sesi chat" saat `streamSource === "chat"`.
- [ ] Chat bubble transisi muncul sebelum tab berpindah.
- [ ] `npm run build` → zero TypeScript errors.

## 9. Estimasi

**Low** — ~45 menit kerja.
