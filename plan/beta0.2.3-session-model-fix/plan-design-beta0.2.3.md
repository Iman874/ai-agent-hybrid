# Beta 0.2.3 — Session Continuity, Model Forwarding & TOR Display Fix

## 1. Ringkasan

Version ini berfokus pada **3 bug kritis** yang menghalangi alur kerja inti pengguna di React frontend:

1. **Session tidak bisa dilanjutkan** — Setiap pesan lanjutan selalu membuat session baru karena `session_id` dari server tidak di-sync balik.
2. **Pemilihan model tidak diteruskan** — User memilih Gemini di sidebar tapi chat tetap menggunakan Ollama (default) karena `chatMode` tidak dikirim ke backend.
3. **Hasil TOR tidak tampil di chat** — `TORPreview` membutuhkan `activeSessionId` yang selalu `null` akibat Bug 1, dan `loadSession()` tidak memulihkan `torDocument`.

Ketiga bug ini **saling terkait** — root cause utama ada di `chat-store.ts`.

---

## 2. Root Cause Analysis

### 2.1 Bug 1: Session Tidak Bisa Dilanjutkan

**Alur yang terjadi:**

```
1. User buka app         → activeSessionId = null
2. User kirim pesan      → server buat session "abc123", return session_id: "abc123"
3. finalizeStream()      → update torDocument, sessionState, dll
                         → ⚠️ TIDAK sync session_id ke session-store
4. User kirim pesan ke-2 → activeSessionId masih null → server buat session baru lagi!
```

**File bermasalah:** `src/stores/chat-store.ts` → `finalizeStream()`

```typescript
// SEKARANG: finalizeStream hanya update messages + state
finalizeStream: (data) => {
  set(state => {
    // ... update messages ...
    return {
      messages: updatedMessages,
      stream: { ... },
      torDocument: data.tor_document ?? state.torDocument,  // ✓ 
      sessionState: data.state,                              // ✓
      // ⚠️ TIDAK ADA: sync data.session_id ke session-store
    };
  });
},
```

**Fix:** Setelah `finalizeStream()`, panggil `useSessionStore.getState().setActiveSession(data.session_id)`.

---

### 2.2 Bug 2: Model Preference Tidak Diteruskan

**Alur yang terjadi:**

```
1. User pilih "Gemini" di ModelSelector → model-store.chatMode = "gemini"
2. User kirim pesan     → chat-store.sendMessage() dipanggil
3. sendMessage()        → apiSendMessage({ session_id, message })
                        → ⚠️ TIDAK menyertakan options.chat_mode
4. Backend menerima     → options = None → default ke "local"
```

**File bermasalah:** `src/stores/chat-store.ts` → `sendMessage()`

```typescript
// SEKARANG: sendMessage tidak membaca model-store
const response = await apiSendMessage({
  session_id: sessionId,
  message: text,
  // ⚠️ options TIDAK dikirim
});
```

**Backend `HybridOptions`** (`app/models/routing.py`):
```python
class HybridOptions(BaseModel):
    force_generate: bool = False
    language: str = "id"
    chat_mode: str = "local"   # "local" | "gemini"
    think: bool = True
```

**Fix:** Import `useModelStore`, baca `chatMode`, masukkan ke `options.chat_mode`.

---

### 2.3 Bug 3: TOR Preview Tidak Tampil

**Alur yang terjadi:**

```
1. AI selesai wawancara   → response.tor_document berisi konten TOR
2. finalizeStream()       → torDocument di-set ✓
3. ChatArea.tsx render    → {torDocument && activeSessionId && <TORPreview ... />}
                          → ⚠️ activeSessionId masih null (Bug 1) → TORPreview SKIP
```

**Tambahan:** Saat user klik session lama di sidebar:

```
1. loadSession()          → fetch detail dari API
2. detail.generated_tor   → ⚠️ TIDAK dipulihkan ke chat-store.torDocument
3. ChatArea render        → torDocument = null → TORPreview SKIP
```

**Fix:** 
- Bug 1 fix otomatis menyelesaikan kasus pertama.
- `loadSession()` perlu memulihkan `generated_tor` ke `chat-store.torDocument`.

---

## 3. Proposed Changes

### 3.1 `src/stores/chat-store.ts` — Session Sync + Model Forwarding

Perubahan utama:

```typescript
// [1] Import model-store
import { useModelStore } from "./model-store";

sendMessage: async (text, sessionId) => {
  // ...existing user message logic...
  
  // [2] Baca model preference
  const { chatMode, activeModelId } = useModelStore.getState();
  
  const response = await apiSendMessage({
    session_id: sessionId,
    message: text,
    options: {                              // [3] Kirim options
      chat_mode: chatMode,
      model_preference: activeModelId ?? undefined,
    },
  });
  get().finalizeStream(response);
},

finalizeStream: (data) => {
  set(state => {
    // ...existing messages logic...
    return { ... };
  });
  
  // [4] Sync session_id ke session-store
  const currentActiveId = useSessionStore.getState().activeSessionId;
  if (data.session_id && !currentActiveId) {
    useSessionStore.getState().setActiveSession(data.session_id);
    useSessionStore.getState().fetchSessions();  // refresh sidebar
  }
},
```

### 3.2 `src/stores/session-store.ts` — Restore TOR Document

```typescript
loadSession: async (sessionId) => {
  // ...existing fetch + map messages...
  
  useChatStore.getState().loadMessages(messages);
  
  // [5] Restore TOR document jika ada
  if (detail.generated_tor) {
    useChatStore.getState().setTorDocument({
      content: detail.generated_tor,
      metadata: {
        generated_by: "restored",
        mode: "restored",
        word_count: detail.generated_tor.split(/\s+/).length,
        generation_time_ms: 0,
        has_assumptions: false,
        prompt_tokens: 0,
        completion_tokens: 0,
      },
    });
  } else {
    useChatStore.getState().clearTorDocument();
  }
  
  set({ activeSessionId: sessionId, isLoading: false });
},
```

### 3.3 `src/types/api.ts` — Update Request Options Type

```typescript
export interface HybridRequest {
  session_id: string | null;
  message: string;
  options?: {
    force_generate?: boolean;
    chat_mode?: "local" | "gemini";
    model_preference?: string;
    language?: string;
    think?: boolean;
  };
}
```

### 3.4 `src/components/shared/ModelSelector.tsx` — i18n

Mengganti string hardcoded `"Model tidak tersedia"` dan `"Pilih model..."` dengan terjemahan.

### 3.5 `src/components/chat/ChatInput.tsx` — Auto-refresh Sessions

Setelah `sendMessage` berhasil, sidebar otomatis ter-refresh karena `finalizeStream()` sudah memanggil `fetchSessions()`. Tidak ada perubahan di ChatInput.

---

## 4. Aturan Bisnis

> [!IMPORTANT]
> **Session continuity rule:** Jika `activeSessionId` ada (non-null), chat HARUS melanjutkan session tersebut. Jika `null`, server boleh membuat session baru, tapi `session_id` dari response HARUS di-sync segera.

> [!IMPORTANT] 
> **Model forwarding rule:** Setiap request ke `/hybrid` HARUS menyertakan `options.chat_mode` dari state model selector saat ini. Backend yang menentukan apakah model tersebut masih available.

---

## 5. File yang Diubah

| File | Perubahan | Bug yang Diperbaiki |
|------|-----------|---------------------|
| `src/stores/chat-store.ts` | Sync session_id + forward model options + tambah `setTorDocument` & `clearTorDocument` actions | Bug 1, 2, 3 |
| `src/stores/session-store.ts` | Restore `generated_tor` di `loadSession()` | Bug 3 |
| `src/types/api.ts` | Update `HybridRequest.options` type | Type safety |
| `src/components/shared/ModelSelector.tsx` | Apply i18n | Polish |
| `src/i18n/locales/id.ts` | Tambah translation keys baru | Polish |
| `src/i18n/locales/en.ts` | Tambah translation keys baru | Polish |

---

## 6. Task Breakdown

| #   | Task                                  | Scope                                              | Estimasi |
|-----|---------------------------------------|------------------------------------------------------|----------|
| T01 | Fix session_id sync di finalizeStream | `chat-store.ts` — sync + refresh sidebar             | 30 min   |
| T02 | Forward model options ke backend      | `chat-store.ts` + `types/api.ts`                     | 30 min   |
| T03 | Restore TOR doc di loadSession        | `session-store.ts` + `chat-store.ts` (new actions)   | 45 min   |
| T04 | ModelSelector i18n + polish           | `ModelSelector.tsx` + locales                        | 15 min   |
| T05 | QA + Build Verification              | `npm run build`, manual test 3 alur                  | 30 min   |

**Total: ~2.5 jam kerja**

---

## 7. Dependency Graph

```
T01 → T02 → T03 → T04 → T05
```

Semua task bersifat sequential karena T01 (session sync) adalah fondasi untuk T02 (model forwarding yang butuh session context yang benar) dan T03 (restore TOR doc yang butuh session_id sync untuk tampil).

---

## 8. Verification Plan

### Automated
- `npm run build` → zero TypeScript errors

### Manual Test Scenarios

**Skenario 1: Session Continuity**
1. Buka app segar (clear localStorage)
2. Kirim pesan pertama → sidebar harus menampilkan session baru
3. Kirim pesan kedua → cek tab Network: request harus mengandung `session_id: "xxx"` (bukan null)
4. Refresh browser → klik session di sidebar → kirim pesan lanjutan → masih session yang sama

**Skenario 2: Model Forwarding**
1. Pilih "Gemini" di ModelSelector
2. Kirim pesan → cek tab Network: request body harus mengandung `options.chat_mode: "gemini"`
3. Ganti ke model Ollama → kirim pesan → `options.chat_mode: "local"`

**Skenario 3: TOR Display**
1. Jalankan wawancara sampai selesai (atau force generate)
2. `TORPreview` harus muncul di bawah messages terakhir
3. Klik session lain → kembali ke session TOR → TORPreview masih tampil
4. Tombol Download DOCX/PDF/MD berfungsi
