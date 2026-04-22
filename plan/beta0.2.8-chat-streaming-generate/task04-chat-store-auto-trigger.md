# Task 04 — Frontend: Chat Store Auto-Trigger ke Generate Store

## 1. Judul Task

Menyambungkan `chat-store.ts` agar secara otomatis memicu `generateFromChatStream()` saat chat menghasilkan status `READY_TO_GENERATE` atau `ESCALATE_TO_GEMINI`.

## 2. Deskripsi

Ini adalah **inti perbaikan bug**. Saat ini, `chat-store.ts` menerima event SSE `"done"` dengan payload `status: "READY_TO_GENERATE"` lalu berhenti — tidak ada aksi lanjutan. Task ini menambahkan logic deteksi status tersebut di `finalizeStream()` dan secara otomatis memanggil `useGenerateStore.getState().generateFromChatStream()`.

## 3. Tujuan Teknis

- Di dalam `finalizeStream()` pada `chat-store.ts`, deteksi apakah `data.state.status` bernilai `READY_TO_GENERATE` atau `ESCALATE_TO_GEMINI`.
- Jika ya: panggil `useGenerateStore.getState().generateFromChatStream(data.session_id, mode)`.
- Switch `activeTool` UI ke `"generate"` agar `AppLayout.tsx` menampilkan `GenerateContainer` (yang akan otomatis menampilkan `StreamingResult`).

## 4. Scope

### Yang dikerjakan
- Modifikasi `finalizeStream()` di `src/stores/chat-store.ts`.
- Import `useGenerateStore` dan `useUIStore` (untuk switch tool).

### Yang tidak dikerjakan
- Perubahan pada `generate-store.ts` (sudah di task 03).
- Perubahan pada komponen `StreamingResult.tsx` (sudah fungsional).
- Perubahan pada `GenerateContainer.tsx` (auto-transition sudah ada).

## 5. Langkah Implementasi

### Step 1: Tambahkan import di `src/stores/chat-store.ts`

Tambahkan di bagian import (setelah line 4):
```typescript
import { useGenerateStore } from "./generate-store";
import { useUIStore } from "./ui-store";
```

### Step 2: Modifikasi `finalizeStream()` (line 263–315)

Di akhir method `finalizeStream`, **tepat sebelum blok sinkronisasi `session_id`** (line 309), tambahkan logic deteksi status:

```typescript
  finalizeStream: (data) => {
    set(state => {
      // ... (kode existing di lines 264–306 TETAP UTUH) ...
    });

    // === BARU: Auto-trigger TOR generation jika status READY ===
    const status = data.state?.status;
    if (
      status === "READY_TO_GENERATE" ||
      status === "ESCALATE_TO_GEMINI"
    ) {
      const mode = status === "ESCALATE_TO_GEMINI" ? "escalation" : "standard";
      const sessionId = data.session_id;

      if (sessionId) {
        // 1. Switch UI ke tab "generate" agar StreamingResult tampil
        useUIStore.getState().setActiveTool("generate_doc");

        // 2. Panggil generate store untuk mulai streaming TOR
        // Sedikit delay agar React sempat merender tab switch
        setTimeout(() => {
          useGenerateStore.getState().generateFromChatStream(sessionId, mode);
        }, 100);
      }
    }

    // Sync session_id ke session store (existing code, TETAP UTUH)
    const currentActiveId = useSessionStore.getState().activeSessionId;
    if (data.session_id && !currentActiveId) {
      useSessionStore.getState().setActiveSession(data.session_id);
      useSessionStore.getState().fetchSessions();
    }
  },
```

### Step 3: Verifikasi `useUIStore` mempunyai `setActiveTool`

Buka `src/stores/ui-store.ts` dan pastikan method `setActiveTool` ada. Jika belum, maka perlu dicek nama method yang ada (misalnya `setView`, `switchTool`, dll) dan sesuaikan pemanggilan di Step 2.

## 6. Output yang Diharapkan

### Alur UX setelah fix:

1. User mengirim pesan chat → lokal AI merespons via streaming.
2. AI menentukan semua data lengkap → event `"done"` dengan `status: "READY_TO_GENERATE"`.
3. Chat flow selesai, `finalizeStream()` mendeteksi status.
4. UI otomatis berpindah ke tab **Generate** (menampilkan `GenerateContainer`).
5. `GenerateContainer` mendeteksi `isStreaming === true` → menampilkan `StreamingResult`.
6. Token TOR mengalir satu per satu di `StreamingResult`.
7. Setelah selesai, auto-transition ke `GenerateResult` (handled by existing `useEffect` di `GenerateContainer.tsx` line 24–33).

### Yang dilihat user:
```
[Chat] "Saya perlu TOR untuk pelatihan..."
[AI]   "Baik, semua informasi sudah lengkap. Saya akan mulai membuat TOR."
       ↓ (otomatis pindah tab)
[Generate - Streaming]
   ⏳ Mulai membuat dokumen TOR...
   # Kerangka Acuan Kerja
   ## 1. Latar Belakang
   Berdasarkan hasil... █
```

## 7. Dependencies

- **Task 03** harus selesai (`generateFromChatStream()` harus tersedia di `generate-store`).

## 8. Acceptance Criteria

- [ ] Saat `finalizeStream()` menerima `data.state.status === "READY_TO_GENERATE"`, ia memanggil `generateFromChatStream(sessionId, "standard")`.
- [ ] Saat `finalizeStream()` menerima `data.state.status === "ESCALATE_TO_GEMINI"`, ia memanggil `generateFromChatStream(sessionId, "escalation")`.
- [ ] UI otomatis berpindah ke tab "generate" via `useUIStore.getState().setActiveTool("generate_doc")`.
- [ ] Jika `status` bukan kedua nilai di atas (misalnya `NEED_MORE_INFO`), tidak ada aksi tambahan — flow chat berjalan normal.
- [ ] Tidak ada regresi: pesan chat biasa (tanpa generate) tetap berfungsi normal.
- [ ] `npm run build` → zero TypeScript errors.

## 9. Estimasi

**Low** — ~30 menit kerja (menambahkan logic deteksi + memanggil store cross-store).
