# Task 5: Frontend — Type + Store Capabilities

## Deskripsi

Update TypeScript types dan Zustand stores untuk mengakomodasi model capabilities dan image attachments.

## Tujuan Teknis

- `ModelCapabilities` interface di `types/api.ts`
- `ModelInfo` extended dengan `capabilities` field
- `Message` extended dengan `images` field
- `HybridRequest` extended dengan `images` field
- `model-store` track `activeCapabilities`
- `chat-store` `sendMessage()` menerima images parameter

## Scope

**Dikerjakan:**
- `app_frontend/src/types/api.ts` — type updates
- `app_frontend/src/types/chat.ts` — Message type update
- `app_frontend/src/stores/model-store.ts` — activeCapabilities
- `app_frontend/src/stores/chat-store.ts` — sendMessage images param

**Tidak dikerjakan:**
- UI components (Task 6-8)

## Langkah Implementasi

### Step 1: Update types

File: `app_frontend/src/types/api.ts`

```typescript
// NEW
export interface ModelCapabilities {
  supports_text: boolean;
  supports_image_input: boolean;
  supports_streaming: boolean;
}

// UPDATED — tambah capabilities
export interface ModelInfo {
  id: string;
  type: "local" | "gemini";
  provider: string;
  status: "available" | "offline";
  capabilities: ModelCapabilities;  // NEW
}
```

Juga update `HybridRequest` jika ada di file ini:
```typescript
export interface HybridRequest {
  session_id: string | null;
  message: string;
  images?: string[];  // NEW — base64 encoded
  options?: {
    chat_mode?: string;
    model_preference?: string;
    think?: boolean;
  };
}
```

### Step 2: Update Message type

File: `app_frontend/src/types/chat.ts`

```typescript
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  status: MessageStatus;
  errorMessage?: string;
  thinkingContent?: string;
  images?: string[];  // NEW — base64 encoded images
}
```

### Step 3: Update model-store

File: `app_frontend/src/stores/model-store.ts`

```typescript
import type { ModelInfo, ModelCapabilities } from "@/types/api";

interface ModelStore {
  models: ModelInfo[];
  activeModelId: string | null;
  chatMode: "local" | "gemini";
  isLoading: boolean;
  activeCapabilities: ModelCapabilities | null;  // NEW

  fetchModels: () => Promise<void>;
  setActiveModel: (id: string, type: string) => void;
}

export const useModelStore = create<ModelStore>((set, get) => ({
  models: [],
  activeModelId: null,
  chatMode: "local",
  isLoading: false,
  activeCapabilities: null,  // NEW

  fetchModels: async () => {
    set({ isLoading: true });
    try {
      const data = await listModels();
      const available = data.models.filter((m: ModelInfo) =>
        m.status === "available" &&
        !m.id.toLowerCase().includes("embed") &&
        !m.id.toLowerCase().includes("nomic")
      );
      const first = available[0];
      set({
        models: available,
        isLoading: false,
        activeModelId: first?.id ?? null,
        chatMode: first?.type === "local" ? "local" : "gemini",
        activeCapabilities: first?.capabilities ?? null,  // NEW
      });
    } catch {
      set({ isLoading: false });
    }
  },

  setActiveModel: (id, type) => {
    const model = get().models.find(m => m.id === id);
    set({
      activeModelId: id,
      chatMode: type === "local" ? "local" : "gemini",
      activeCapabilities: model?.capabilities ?? null,  // NEW
    });
  },
}));
```

### Step 4: Update chat-store `sendMessage()`

File: `app_frontend/src/stores/chat-store.ts`

Update signature dan logic:

```typescript
sendMessage: async (text: string, sessionId: string | null, images?: string[]) => {
  const userMsg: Message = {
    id: crypto.randomUUID(),
    role: "user",
    content: text,
    timestamp: Date.now(),
    status: "done",
    images: images,  // NEW — simpan images di message
  };

  set(state => ({ messages: [...state.messages, userMsg] }));

  // ... rest of sendMessage logic ...
  // Teruskan images ke API calls:
  
  const response = await apiSendMessage({
    session_id: sessionId,
    message: text,
    images: images,  // NEW
    options: { ... },
  });
},
```

## Output yang Diharapkan

```typescript
// model-store sekarang punya:
const caps = useModelStore(s => s.activeCapabilities);
// caps = { supports_text: true, supports_image_input: true, supports_streaming: true }

// Message sekarang bisa punya images:
const msg: Message = {
  id: "...", role: "user", content: "Apa ini?",
  images: ["base64data..."],
  timestamp: Date.now(), status: "done",
};
```

## Dependencies

- Task 2: Backend `GET /models` harus return capabilities

## Acceptance Criteria

- [ ] `ModelCapabilities` interface ditambahkan
- [ ] `ModelInfo.capabilities` field ada
- [ ] `Message.images` optional field ada
- [ ] `HybridRequest.images` optional field ada
- [ ] `model-store` track `activeCapabilities`
- [ ] `activeCapabilities` ter-update saat `setActiveModel()` dipanggil
- [ ] `activeCapabilities` ter-set saat `fetchModels()` pertama kali
- [ ] `chat-store.sendMessage()` menerima `images` parameter
- [ ] `npm run build` clean — tidak ada TypeScript error

## Estimasi

Low (1 jam)
