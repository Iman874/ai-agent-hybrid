# Task 15 — ChatStore Tool Events Integration

## Deskripsi

Mengintegrasikan tool events dari SSE stream ke `ChatStore`. Saat frontend menerima event `tool_start`, `tool_result`, atau `tool_error` dari backend, ChatStore harus memperbarui state tool di `tool-store` sehingga `ToolCallIndicator` bisa menampilkan status real-time ke user.

---

## Tujuan Teknis

- ChatStore bisa memproses SSE event type `tool_start`, `tool_result`, `tool_error`
- Tool calls otomatis tercatat di `tool-store` saat streaming berlangsung
- Tool indicator muncul di UI secara real-time (tanpa perlu refresh)
- Tool calls dibersihkan setelah stream selesai (done) atau error
- Tool calls tidak muncul jika `tools_enabled=false`

---

## Scope

### Termasuk

- Modifikasi `app_frontend/src/stores/chat-store.ts`:

  **Update `sendMessage()` method:**
  - Di dalam SSE consumer callback, handle tool events:
    ```typescript
    // Di dalam sendMessageStream callbacks
    onToolStart: (tool, args) => {
      useToolStore.getState().addToolCall({
        tool,
        args,
        status: "running",
      });
    },
    onToolResult: (tool, status, resultCount) => {
      useToolStore.getState().updateToolCall(tool, {
        status: "success",
        resultCount,
      });
    },
    onToolError: (tool, error) => {
      useToolStore.getState().updateToolCall(tool, {
        status: "error",
        error,
      });
    },
    ```

  **Update `finalizeStream()` method:**
  - Panggil `useToolStore.getState().clearToolCalls()` setelah stream selesai:
    ```typescript
    finalizeStream: (data) => {
      // ... existing logic ...
      useToolStore.getState().clearToolCalls();  // NEW
    },
    ```

  **Update `setError()` method:**
  - Panggil `useToolStore.getState().clearToolCalls()` jika error:
    ```typescript
    setError: (messageId, error) => {
      // ... existing logic ...
      useToolStore.getState().clearToolCalls();  // NEW
    },
    ```

  **Update `sendMessage()` — kirim toolsEnabled:**
  - Baca `toolsEnabled` dari `useToolStore`:
    ```typescript
    const { toolsEnabled } = useToolStore.getState();
    const requestBody = {
      // ... existing ...
      options: {
        // ... existing ...
        tools_enabled: toolsEnabled,
      },
    };
    ```

- Update `app_frontend/src/api/chat.ts`:
  - `ChatStreamCallbacks` sudah diupdate di Task 13 (onToolStart, onToolResult, onToolError)
  - `sendMessageStream()` sudah diupdate di Task 13 (parse tool events)

### Tidak Termasuk

- ToolCallIndicator component (Task 14)
- Tool toggle UI (Task 16)
- i18n translations (Task 17)

---

## Langkah Implementasi

### Langkah 1: Baca `chat-store.ts` yang sudah ada

Pahami struktur `sendMessage()`, `finalizeStream()`, dan `setError()`.

### Langkah 2: Update `sendMessage()` — Tool Events Callbacks

```typescript
// Di dalam sendMessage method
sendMessage: async (text, sessionId, images) => {
  // ... existing code ...
  
  const { toolsEnabled } = useToolStore.getState();  // NEW
  
  const requestBody = {
    session_id: sessionId,
    message: text,
    images: images,
    options: {
      chat_mode: chatMode,
      model_preference: activeModelId ?? undefined,
      tools_enabled: toolsEnabled,  // NEW
    },
  };

  // PRIMARY: SSE stream
  const abortController = new AbortController();
  let sseDone = false;
  let sseError = "";

  await sendMessageStream(
    requestBody,
    {
      // ... existing callbacks ...
      
      onToolStart: (tool, args) => {  // NEW
        useToolStore.getState().addToolCall({
          tool,
          args,
          status: "running",
        });
      },
      onToolResult: (tool, status, resultCount) => {  // NEW
        useToolStore.getState().updateToolCall(tool, {
          status: "success",
          resultCount,
        });
      },
      onToolError: (tool, error) => {  // NEW
        useToolStore.getState().updateToolCall(tool, {
          status: "error",
          error,
        });
      },
      
      // ... existing callbacks ...
    },
    abortController.signal,
    toolsEnabled,  // NEW — kirim ke sendMessageStream
  );
  
  // ... existing code ...
}
```

### Langkah 3: Update `finalizeStream()` — Clear Tool Calls

```typescript
finalizeStream: (data) => {
  set((state) => {
    // ... existing logic untuk update messages, stream state, dll ...
    
    // Bersihkan tool calls
    useToolStore.getState().clearToolCalls();  // NEW
    
    return { /* ... existing state updates ... */ };
  });
},
```

### Langkah 4: Update `setError()` — Clear Tool Calls

```typescript
setError: (messageId, error) => {
  set((state) => {
    // ... existing logic ...
    
    // Bersihkan tool calls
    useToolStore.getState().clearToolCalls();  // NEW
    
    return { /* ... existing state updates ... */ };
  });
},
```

### Langkah 5: Validasi

```typescript
// Simulasi alur tool events
import { useToolStore } from "@/stores/tool-store";
import { useChatStore } from "@/stores/chat-store";

// 1. User kirim pesan
await useChatStore.getState().sendMessage("Cari AI Indonesia", null);

// 2. SSE mengirim tool_start
// → onToolStart dipanggil
// → tool-store.activeToolCalls = [{tool: "web_search", args: {...}, status: "running"}]

// 3. SSE mengirim tool_result
// → onToolResult dipanggil
// → tool-store.activeToolCalls = [{tool: "web_search", args: {...}, status: "success", resultCount: 5}]

// 4. SSE mengirim done
// → finalizeStream dipanggil
// → tool-store.activeToolCalls = [] (clear)

// 5. ToolCallIndicator render berdasarkan activeToolCalls
```

---

## Output yang Diharapkan

- ChatStore memproses tool events dari SSE stream
- Tool calls tercatat di tool-store secara real-time
- Tool calls dibersihkan setelah stream selesai atau error
- `tools_enabled` dikirim ke backend dari tool-store

---

## Dependencies

- **Task 09 (SSE Tool Events)** — event types dari backend
- **Task 12 (Frontend Tool Types)** — ToolCallEvent type
- **Task 13 (Frontend Tool API)** — ChatStreamCallbacks + sendMessageStream update
- **Task 14 (ToolCallIndicator)** — komponen yang akan menggunakan state ini

---

## Acceptance Criteria

### Tool Events
- [ ] `tool_start` event memanggil `addToolCall()` dengan status "running"
- [ ] `tool_result` event memanggil `updateToolCall()` dengan status "success"
- [ ] `tool_error` event memanggil `updateToolCall()` dengan status "error"
- [ ] `finalizeStream()` membersihkan tool calls
- [ ] `setError()` membersihkan tool calls

### Tools Enabled
- [ ] `toolsEnabled` dibaca dari tool-store saat sendMessage
- [ ] `tools_enabled` dikirim ke backend di request options

### Edge Cases
- [ ] Multiple tool calls → semua tercatat di activeToolCalls
- [ ] Stream error → tool calls dibersihkan
- [ ] toolsEnabled=false → tool events tidak diproses (tool-store tidak diupdate)
- [ ] User kirim pesan baru sebelum stream selesai → tool calls dari stream sebelumnya dibersihkan

---

## Estimasi

**Low** (~1 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Update sendMessage — tool callbacks | 25 menit |
| Update finalizeStream — clear tool calls | 10 menit |
| Update setError — clear tool calls | 10 menit |
| Update sendMessage — toolsEnabled | 10 menit |
| Validasi & testing | 15 menit |
