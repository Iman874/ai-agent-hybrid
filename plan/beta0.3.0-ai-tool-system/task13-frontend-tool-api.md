# Task 13 — Frontend Tool API Client

## Deskripsi

Membuat API client untuk tool system di frontend. Client ini digunakan oleh `tool-store` untuk berkomunikasi dengan backend endpoint tools, dan mengupdate `chat.ts` untuk mengirim opsi `tools_enabled` ke backend.

---

## Tujuan Teknis

- Fungsi `fetchTools()` untuk mengambil daftar tool dari `GET /tools`
- Update `sendMessageStream()` dan `sendMessage()` untuk mengirim `tools_enabled` di request body
- Integrasi dengan API client pattern yang sudah ada (`apiGet`, `apiPost`)
- Error handling: jika API gagal, return empty array (jangan throw)

---

## Scope

### Termasuk

- Membuat `app_frontend/src/api/tools.ts`:
  ```typescript
  import { apiGet } from "./client";
  import type { ToolsListResponse, ToolSpec } from "@/types/api";

  export async function fetchTools(): Promise<ToolSpec[]> {
    try {
      const response = await apiGet<ToolsListResponse>("/tools");
      return response.tools;
    } catch (error) {
      console.warn("Failed to fetch tools:", error);
      return [];
    }
  }
  ```

- Modifikasi `app_frontend/src/api/chat.ts`:
  - Update `ChatStreamCallbacks` — tambah callback untuk tool events:
    ```typescript
    export interface ChatStreamCallbacks {
      // ... existing callbacks ...
      onToolStart?: (tool: string, args: Record<string, unknown>) => void;
      onToolResult?: (tool: string, status: string, resultCount?: number) => void;
      onToolError?: (tool: string, error: string) => void;
    }
    ```
  - Update `sendMessageStream()` — parse event type `tool_start`, `tool_result`, `tool_error`:
    ```typescript
    // Di dalam SSE reader switch
    case "tool_start":
      callbacks.onToolStart?.(data.tool as string, data.args as Record<string, unknown>);
      break;
    case "tool_result":
      callbacks.onToolResult?.(
        data.tool as string,
        data.status as string,
        data.result_count as number | undefined,
      );
      break;
    case "tool_error":
      callbacks.onToolError?.(data.tool as string, data.error as string);
      break;
    ```
  - Update `sendMessageStream()` — tambah parameter `toolsEnabled?: boolean`:
    ```typescript
    export async function sendMessageStream(
      req: HybridRequest,
      callbacks: ChatStreamCallbacks,
      abortSignal?: AbortSignal,
      toolsEnabled?: boolean,  // NEW
    ): Promise<void> {
      const body = {
        ...req,
        options: {
          ...req.options,
          tools_enabled: toolsEnabled ?? true,
        },
      };
      // ... sisanya sama ...
    }
    ```
  - Update `sendMessage()` — tambah parameter `toolsEnabled?: boolean`:
    ```typescript
    export async function sendMessage(
      req: HybridRequest,
      toolsEnabled?: boolean,  // NEW
    ): Promise<HybridResponse> {
      const body = {
        ...req,
        options: {
          ...req.options,
          tools_enabled: toolsEnabled ?? true,
        },
      };
      return apiPost<HybridResponse>("/hybrid", body);
    }
    ```

### Tidak Termasuk

- Tool store (Task 12)
- ToolCallIndicator component (Task 14)
- ChatStore integration (Task 15)

---

## Langkah Implementasi

### Langkah 1: Buat `app_frontend/src/api/tools.ts`

```typescript
import { apiGet } from "./client";
import type { ToolsListResponse, ToolSpec } from "@/types/api";

/**
 * Fetch daftar tool yang tersedia dari backend.
 * @returns Promise<ToolSpec[]> — empty array jika gagal
 */
export async function fetchTools(): Promise<ToolSpec[]> {
  try {
    const response = await apiGet<ToolsListResponse>("/tools");
    return response.tools;
  } catch (error) {
    console.warn("[tools.ts] Failed to fetch tools:", error);
    return [];
  }
}
```

### Langkah 2: Update `app_frontend/src/api/chat.ts`

Update `ChatStreamCallbacks`, `sendMessageStream()`, dan `sendMessage()` sesuai kode di Scope.

### Langkah 3: Validasi

```typescript
// Test fetchTools
const tools = await fetchTools();
console.log(`Found ${tools.length} tool(s):`, tools.map(t => t.name));

// Test sendMessageStream dengan toolsEnabled
await sendMessageStream(
  { session_id: null, message: "test" },
  {
    onToolStart: (tool, args) => console.log(`Tool started: ${tool}`, args),
    onToolResult: (tool, status, count) => console.log(`Tool ${tool}: ${status}, ${count} results`),
    onToolError: (tool, error) => console.error(`Tool ${tool} error: ${error}`),
    onDone: (data) => console.log("Done", data),
    onError: (msg) => console.error("Error", msg),
    onToken: (t) => {},
    onStatus: () => {},
    onThinkingStart: () => {},
    onThinking: () => {},
    onThinkingEnd: () => {},
  },
  undefined,
  true, // toolsEnabled
);
```

---

## Output yang Diharapkan

- `app_frontend/src/api/tools.ts` — fungsi `fetchTools()`
- `chat.ts` — request body menyertakan `tools_enabled`
- `ChatStreamCallbacks` — callback untuk tool_start, tool_result, tool_error

---

## Dependencies

- **Task 10 (Tools API Endpoint)** — endpoint GET /tools
- **Task 12 (Frontend Tool Types)** — type definitions

---

## Acceptance Criteria

### Tools API
- [ ] `fetchTools()` mengembalikan array `ToolSpec[]`
- [ ] Jika API gagal, `fetchTools()` mengembalikan empty array (tidak throw)
- [ ] Error di-log dengan `console.warn`

### Chat API
- [ ] `sendMessageStream()` mengirim `tools_enabled` di request body options
- [ ] `sendMessage()` mengirim `tools_enabled` di request body options
- [ ] Default `toolsEnabled` adalah `true`
- [ ] `ChatStreamCallbacks` memiliki `onToolStart`, `onToolResult`, `onToolError`
- [ ] SSE reader memproses event type `tool_start`, `tool_result`, `tool_error`

---

## Estimasi

**Low** (~1 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Membuat tools.ts | 15 menit |
| Update ChatStreamCallbacks | 10 menit |
| Update sendMessageStream | 20 menit |
| Update sendMessage | 10 menit |
| Validasi & testing | 15 menit |
