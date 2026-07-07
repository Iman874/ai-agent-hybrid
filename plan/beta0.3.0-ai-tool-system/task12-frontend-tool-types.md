# Task 12 — Frontend Tool Types & Store

## Deskripsi

Menambahkan type definitions untuk tool system di frontend dan membuat Zustand store untuk mengelola state tool. Ini adalah fondasi frontend untuk fitur tool calling — menyediakan tipe data yang konsisten dan state management yang terpusat.

---

## Tujuan Teknis

- TypeScript types untuk ToolSpec, ToolCallEvent, ToolsListResponse
- Zustand store (`tool-store`) untuk menyimpan state tool:
  - Daftar tool yang tersedia
  - Tool calls yang sedang aktif (real-time)
  - Status enable/disable tool
- Store actions: fetchTools, setToolsEnabled, addToolCall, updateToolCall, clearToolCalls
- Initial fetch tools dari `GET /tools` saat store diinisialisasi

---

## Scope

### Termasuk

- Modifikasi `app_frontend/src/types/api.ts`:
  ```typescript
  export interface ToolSpec {
    name: string;
    description: string;
    enabled: boolean;
    parameters: Record<string, unknown>;
  }

  export interface ToolsListResponse {
    tools: ToolSpec[];
  }

  export interface ToolCallEvent {
    tool: string;
    args: Record<string, unknown>;
    status: "running" | "success" | "error";
    resultCount?: number;
    error?: string;
  }
  ```

- Update `HybridRequest.options` — tambah `tools_enabled?: boolean`:
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
      generator?: "auto" | "gemini" | "ollama";
      tools_enabled?: boolean;  // NEW
    };
  }
  ```

- Membuat `app_frontend/src/stores/tool-store.ts`:
  ```typescript
  import { create } from "zustand";
  import { fetchTools } from "@/api/tools";
  import type { ToolSpec, ToolCallEvent } from "@/types/api";

  interface ToolStore {
    // State
    tools: ToolSpec[];
    activeToolCalls: ToolCallEvent[];
    toolsEnabled: boolean;
    isLoading: boolean;

    // Actions
    fetchTools: () => Promise<void>;
    setToolsEnabled: (enabled: boolean) => void;
    addToolCall: (call: ToolCallEvent) => void;
    updateToolCall: (tool: string, updates: Partial<ToolCallEvent>) => void;
    clearToolCalls: () => void;
    hasTools: () => boolean;
  }

  export const useToolStore = create<ToolStore>((set, get) => ({
    tools: [],
    activeToolCalls: [],
    toolsEnabled: true,
    isLoading: false,

    fetchTools: async () => {
      set({ isLoading: true });
      try {
        const tools = await fetchTools();
        set({ tools, isLoading: false });
      } catch {
        set({ isLoading: false });
      }
    },

    setToolsEnabled: (enabled) => set({ toolsEnabled: enabled }),

    addToolCall: (call) => set((state) => ({
      activeToolCalls: [...state.activeToolCalls, call],
    })),

    updateToolCall: (tool, updates) => set((state) => ({
      activeToolCalls: state.activeToolCalls.map((tc) =>
        tc.tool === tool && tc.status === "running"
          ? { ...tc, ...updates }
          : tc
      ),
    })),

    clearToolCalls: () => set({ activeToolCalls: [] }),

    hasTools: () => get().tools.length > 0,
  }));
  ```

### Tidak Termasuk

- API client untuk tools (Task 13)
- ToolCallIndicator component (Task 14)
- ChatStore integration (Task 15)

---

## Langkah Implementasi

### Langkah 1: Update `app_frontend/src/types/api.ts`

Tambah interface `ToolSpec`, `ToolsListResponse`, `ToolCallEvent`, dan update `HybridRequest`.

### Langkah 2: Buat `app_frontend/src/stores/tool-store.ts`

Implementasi Zustand store sesuai kode di atas.

### Langkah 3: Validasi

```typescript
// Test type definitions
const spec: ToolSpec = {
  name: "web_search",
  description: "Search the web",
  enabled: true,
  parameters: {
    type: "object",
    properties: {
      query: { type: "string" },
    },
    required: ["query"],
  },
};

const event: ToolCallEvent = {
  tool: "web_search",
  args: { query: "AI Indonesia" },
  status: "running",
};

const request: HybridRequest = {
  session_id: null,
  message: "test",
  options: {
    tools_enabled: true,
  },
};
```

---

## Output yang Diharapkan

- Type definitions untuk tool system di `api.ts`
- `tool-store.ts` dengan state dan actions lengkap
- Store bisa di-import dan digunakan oleh komponen

---

## Dependencies

- **Task 10 (Tools API Endpoint)** — untuk fetch tools dari backend

---

## Acceptance Criteria

### Types
- [ ] `ToolSpec` memiliki field: name, description, enabled, parameters
- [ ] `ToolsListResponse` memiliki field: tools (array of ToolSpec)
- [ ] `ToolCallEvent` memiliki field: tool, args, status, resultCount?, error?
- [ ] `HybridRequest.options` memiliki field `tools_enabled?: boolean`

### Store — State
- [ ] `tools: ToolSpec[]` — daftar tool dari backend
- [ ] `activeToolCalls: ToolCallEvent[]` — tool calls yang sedang berlangsung
- [ ] `toolsEnabled: boolean` — status enable/disable (default true)
- [ ] `isLoading: boolean` — status loading fetch tools

### Store — Actions
- [ ] `fetchTools()` mengambil data dari `GET /tools`
- [ ] `setToolsEnabled(true/false)` mengubah status
- [ ] `addToolCall({tool, args, status: "running"})` menambahkan tool call
- [ ] `updateToolCall("web_search", {status: "success", resultCount: 5})` mengupdate
- [ ] `clearToolCalls()` mereset activeToolCalls ke []
- [ ] `hasTools()` return true jika ada tool terdaftar

---

## Estimasi

**Low** (~1 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Update type definitions | 20 menit |
| Implementasi tool-store | 30 menit |
| Validasi & testing | 10 menit |
