# Task 07: Frontend — Generator Mode di Store & API Types

## Status
[ ] Belum dimulai

## Deskripsi
Update frontend types, API client, dan stores untuk mendukung generator mode ("auto", "local", "gemini").

## File yang Diubah
- **MODIFY**: `app_frontend/src/types/api.ts`
- **MODIFY**: `app_frontend/src/stores/model-store.ts`
- **MODIFY**: `app_frontend/src/stores/chat-store.ts`
- **MODIFY**: `app_frontend/src/stores/generate-store.ts`
- **MODIFY**: `app_frontend/src/api/chat.ts`
- **MODIFY**: `app_frontend/src/api/generate.ts`

## Spesifikasi

### 1. Update Types (`app_frontend/src/types/api.ts`)

```typescript
export interface HybridRequest {
  session_id: string | null;
  message: string;
  images?: string[];
  options?: {
    force_generate?: boolean;
    chat_mode?: "local" | "gemini";
    model_preference?: string;
    language?: string;
    think?: boolean;
    generator?: "auto" | "gemini" | "ollama";  // NEW
  };
}

export interface TORMetadata {
  generated_by: string;
  generator: string;          // NEW: "gemini" | "ollama"
  mode: string;
  word_count: number;
  generation_time_ms: number;
  has_assumptions: boolean;
  prompt_tokens: number;
  completion_tokens: number;
}
```

### 2. Update Model Store (`app_frontend/src/stores/model-store.ts`)

```typescript
interface ModelStore {
  models: ModelInfo[];
  activeModelId: string | null;
  activeCapabilities: ModelCapabilities;
  chatMode: "local" | "gemini";
  generatorMode: "auto" | "gemini" | "ollama";  // NEW
  isLoading: boolean;

  fetchModels: () => Promise<void>;
  setActiveModel: (id: string, type: string) => void;
  setGeneratorMode: (mode: "auto" | "gemini" | "ollama") => void;  // NEW
}
```

Default value: `generatorMode: "auto"`

### 3. Update Chat Store (`app_frontend/src/stores/chat-store.ts`)

Saat mengirim request, sertakan `generator` dari model store:

```typescript
// Di dalam sendMessage()
const { chatMode, activeModelId, generatorMode } = useModelStore.getState();
const requestBody = {
  session_id: sessionId,
  message: text,
  images: images,
  options: {
    chat_mode: chatMode,
    model_preference: activeModelId ?? undefined,
    generator: generatorMode,  // NEW
  },
};
```

### 4. Update Generate Store (`app_frontend/src/stores/generate-store.ts`)

Saat memanggil `generateFromChatStream()`, kirim generator mode:

```typescript
generateFromChatStream: async (sessionId, mode) => {
  const { generatorMode } = useModelStore.getState();
  // ... existing logic ...
  await streamGenerateFromChat(sessionId, mode, generatorMode, {  // NEW param
    onStatus: ...,
    onToken: ...,
    onDone: ...,
    onError: ...,
  }, abortController.signal);
},
```

### 5. Update API Client — Generate (`app_frontend/src/api/generate.ts`)

```typescript
export async function streamGenerateFromChat(
  sessionId: string,
  mode: "standard" | "escalation",
  generator: "auto" | "gemini" | "ollama" = "auto",  // NEW
  callbacks: StreamCallbacks,
  abortSignal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/generate/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      mode: mode,
      generator: generator,  // NEW
    }),
    signal: abortSignal,
  });
  await consumeStream(response, callbacks);
}
```

## Catatan
- Generator mode disimpan di `model-store` karena berkaitan dengan model/provider
- Default selalu "auto" — sistem memilih terbaik
- Frontend tidak perlu validasi — backend yang menentukan fallback
