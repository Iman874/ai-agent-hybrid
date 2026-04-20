# Task 2: Forward Model Options ke Backend

## 1. Judul Task
Kirim `options.chat_mode` dan `model_preference` dari `model-store` ke request `/hybrid`.

## 2. Deskripsi
Saat ini `sendMessage()` di `chat-store.ts` mengirim `HybridRequest` tanpa field `options`. Backend menerima `HybridOptions` yang mendukung `chat_mode` (local/gemini) dan field lainnya, tapi frontend tidak pernah mengirimnya. Akibatnya, pemilihan model di sidebar tidak berdampak pada respons yang diterima.

## 3. Tujuan Teknis
- `sendMessage()` harus membaca `chatMode` dan `activeModelId` dari `useModelStore`
- Sisipkan ke field `options` pada `HybridRequest`
- Update TypeScript type `HybridRequest.options` agar match dengan backend `HybridOptions`

## 4. Scope
### Yang dikerjakan
- Modifikasi `sendMessage()` di `src/stores/chat-store.ts`
- Update interface `HybridRequest` di `src/types/api.ts`

### Yang tidak dikerjakan
- Tidak mengubah backend (backend sudah support `HybridOptions`)
- Tidak mengubah `ModelSelector.tsx` (sudah berfungsi untuk set state)
- Tidak mengubah WebSocket flow

## 5. Langkah Implementasi

### Step 1: Update `HybridRequest` type di `src/types/api.ts`
Ubah `options` agar sesuai dengan backend `HybridOptions`:

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

### Step 2: Import `useModelStore` di `src/stores/chat-store.ts`

```typescript
import { useModelStore } from "./model-store";
```

### Step 3: Modifikasi `sendMessage()` — HTTP fallback path
Di blok `try` sebelum `apiSendMessage`, baca model state:

```typescript
// Baca model preference dari model-store
const { chatMode, activeModelId } = useModelStore.getState();

const response = await apiSendMessage({
  session_id: sessionId,
  message: text,
  options: {
    chat_mode: chatMode,
    model_preference: activeModelId ?? undefined,
  },
});
```

### Step 4: Verifikasi di browser
1. Buka React app
2. Pilih model Gemini di sidebar
3. Kirim pesan
4. Buka DevTools → Network → klik request `/hybrid`
5. Cek Request Payload → harus ada `options.chat_mode: "gemini"`
6. Ganti ke model Ollama → kirim pesan → payload harus `options.chat_mode: "local"`

## 6. Output yang Diharapkan

**Request body SEBELUM fix:**
```json
{
  "session_id": "abc123",
  "message": "Halo"
}
```

**Request body SETELAH fix:**
```json
{
  "session_id": "abc123",
  "message": "Halo",
  "options": {
    "chat_mode": "gemini",
    "model_preference": "gemini-2.0-flash"
  }
}
```

## 7. Dependencies
- Task 1 (session sync harus sudah benar agar `session_id` ter-forward)

## 8. Acceptance Criteria
- [ ] `HybridRequest.options` type di `types/api.ts` mengandung `chat_mode`, `model_preference`, `force_generate`, `language`, `think`
- [ ] `sendMessage()` membaca `useModelStore.getState()` dan menyisipkan `options`
- [ ] Request ke `/hybrid` mengandung `options.chat_mode` yang sesuai dengan pilihan di ModelSelector
- [ ] Berganti model di sidebar → request berikutnya mengirim chat_mode yang benar
- [ ] `npm run build` sukses tanpa error

## 9. Estimasi
**Low** (~30 menit)
