# Task 04: Zustand Stores — chat, session, model, ui

## 1. Judul Task

Implementasi 4 Zustand stores untuk state management aplikasi

## 2. Deskripsi

Membuat stores Zustand yang mengontrol semua state aplikasi: chat messages + streaming, session management, model selection, dan UI state (sidebar, settings, theme).

## 3. Tujuan Teknis

- `chat-store.ts` — messages, streaming state, retry logic
- `session-store.ts` — session list, active session, CRUD
- `model-store.ts` — model list, active model
- `ui-store.ts` — sidebar, settings, theme, active tool

## 4. Scope

**Yang dikerjakan:**
- `src/stores/chat-store.ts`
- `src/stores/session-store.ts`
- `src/stores/model-store.ts`
- `src/stores/ui-store.ts`

**Yang tidak dikerjakan:**
- WebSocket integration (task 10 — akan hook ke chat-store)
- UI components (task 05+)

## 5. Langkah Implementasi

### 5.1 Chat Store — `src/stores/chat-store.ts`

```typescript
import { create } from "zustand";
import { sendMessage as apiSendMessage } from "@/api/chat";
import type { Message, StreamState } from "@/types/chat";
import type { HybridResponse, TORDocument, SessionState, EscalationInfo } from "@/types/api";

interface ChatStore {
  messages: Message[];
  stream: StreamState;
  torDocument: TORDocument | null;
  sessionState: SessionState | null;
  escalationInfo: EscalationInfo | null;

  sendMessage: (text: string, sessionId: string | null) => Promise<void>;
  retryMessage: (messageId: string, sessionId: string | null) => Promise<void>;
  appendToken: (token: string) => void;
  setThinking: (active: boolean) => void;
  appendThinkingToken: (token: string) => void;
  finalizeStream: (data: HybridResponse) => void;
  setError: (messageId: string, error: string) => void;
  clearMessages: () => void;
  loadMessages: (messages: Message[]) => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  stream: { isStreaming: false, isThinking: false, thinkingText: "", partialContent: "" },
  torDocument: null,
  sessionState: null,
  escalationInfo: null,

  sendMessage: async (text, sessionId) => {
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: Date.now(),
      status: "done",
    };

    set(state => ({ messages: [...state.messages, userMsg] }));

    // Note: WebSocket path will be added in task 10
    // For now, use HTTP fallback
    const assistantId = crypto.randomUUID();
    const assistantMsg: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: Date.now(),
      status: "sending",
    };
    set(state => ({ messages: [...state.messages, assistantMsg] }));

    try {
      const response = await apiSendMessage({
        session_id: sessionId,
        message: text,
      });
      get().finalizeStream(response);
    } catch (error) {
      const errMsg = error instanceof Error ? error.message : "Terjadi kesalahan";
      get().setError(assistantId, errMsg);
    }
  },

  retryMessage: async (messageId, sessionId) => {
    const { messages } = get();
    const failedIdx = messages.findIndex(m => m.id === messageId);
    if (failedIdx === -1) return;

    // Find the user message before the failed assistant message
    const userMsg = messages.slice(0, failedIdx).reverse().find(m => m.role === "user");
    if (!userMsg) return;

    // Remove the failed message
    set(state => ({
      messages: state.messages.filter(m => m.id !== messageId),
    }));

    // Re-send
    await get().sendMessage(userMsg.content, sessionId);
  },

  appendToken: (token) => {
    set(state => ({
      stream: { ...state.stream, partialContent: state.stream.partialContent + token },
    }));
  },

  setThinking: (active) => {
    set(state => ({
      stream: {
        ...state.stream,
        isThinking: active,
        isStreaming: active || state.stream.isStreaming,
        thinkingText: active ? "" : state.stream.thinkingText,
      },
    }));
  },

  appendThinkingToken: (token) => {
    set(state => ({
      stream: { ...state.stream, thinkingText: state.stream.thinkingText + token },
    }));
  },

  finalizeStream: (data) => {
    set(state => {
      const lastAssistant = [...state.messages].reverse().find(m => m.role === "assistant");
      const updatedMessages = state.messages.map(m =>
        m.id === lastAssistant?.id
          ? { ...m, content: data.message, status: "done" as const }
          : m,
      );

      return {
        messages: updatedMessages,
        stream: { isStreaming: false, isThinking: false, thinkingText: "", partialContent: "" },
        torDocument: data.tor_document ?? state.torDocument,
        sessionState: data.state,
        escalationInfo: data.escalation_info ?? null,
      };
    });
  },

  setError: (messageId, error) => {
    set(state => ({
      messages: state.messages.map(m =>
        m.id === messageId
          ? { ...m, status: "error" as const, errorMessage: error }
          : m,
      ),
      stream: { isStreaming: false, isThinking: false, thinkingText: "", partialContent: "" },
    }));
  },

  clearMessages: () => set({
    messages: [],
    stream: { isStreaming: false, isThinking: false, thinkingText: "", partialContent: "" },
    torDocument: null,
    sessionState: null,
    escalationInfo: null,
  }),

  loadMessages: (messages) => set({ messages }),
}));
```

### 5.2 Session Store — `src/stores/session-store.ts`

```typescript
import { create } from "zustand";
import * as sessionsApi from "@/api/sessions";
import { useChatStore } from "./chat-store";
import type { SessionListItem } from "@/types/session";

interface SessionStore {
  sessions: SessionListItem[];
  activeSessionId: string | null;
  isLoading: boolean;

  fetchSessions: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  createNewSession: () => void;
  setActiveSession: (id: string | null) => void;
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  isLoading: false,

  fetchSessions: async () => {
    set({ isLoading: true });
    try {
      const sessions = await sessionsApi.listSessions(50);
      set({ sessions, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  loadSession: async (sessionId) => {
    set({ isLoading: true });
    try {
      const detail = await sessionsApi.getSession(sessionId);
      const messages = detail.chat_history.map((msg, i) => ({
        id: `hist-${i}`,
        role: msg.role as "user" | "assistant",
        content: msg.content,
        timestamp: new Date(msg.timestamp).getTime(),
        status: "done" as const,
      }));
      useChatStore.getState().loadMessages(messages);
      set({ activeSessionId: sessionId, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  deleteSession: async (sessionId) => {
    await sessionsApi.deleteSession(sessionId);
    set(state => ({
      sessions: state.sessions.filter(s => s.id !== sessionId),
      activeSessionId: state.activeSessionId === sessionId ? null : state.activeSessionId,
    }));
    if (get().activeSessionId === null) {
      useChatStore.getState().clearMessages();
    }
  },

  createNewSession: () => {
    useChatStore.getState().clearMessages();
    set({ activeSessionId: null });
  },

  setActiveSession: (id) => set({ activeSessionId: id }),
}));
```

### 5.3 Model Store — `src/stores/model-store.ts`

```typescript
import { create } from "zustand";
import { listModels } from "@/api/models";
import type { ModelInfo } from "@/types/api";

interface ModelStore {
  models: ModelInfo[];
  activeModelId: string | null;
  chatMode: "local" | "gemini";
  isLoading: boolean;

  fetchModels: () => Promise<void>;
  setActiveModel: (id: string, type: string) => void;
}

export const useModelStore = create<ModelStore>((set) => ({
  models: [],
  activeModelId: null,
  chatMode: "local",
  isLoading: false,

  fetchModels: async () => {
    set({ isLoading: true });
    try {
      const data = await listModels();
      const available = data.models.filter(m =>
        m.status === "available" &&
        !m.id.toLowerCase().includes("embed") &&
        !m.id.toLowerCase().includes("nomic")
      );
      set({
        models: available,
        isLoading: false,
        activeModelId: available[0]?.id ?? null,
        chatMode: available[0]?.type === "local" ? "local" : "gemini",
      });
    } catch {
      set({ isLoading: false });
    }
  },

  setActiveModel: (id, type) => set({
    activeModelId: id,
    chatMode: type === "local" ? "local" : "gemini",
  }),
}));
```

### 5.4 UI Store — `src/stores/ui-store.ts`

```typescript
import { create } from "zustand";
import { persist } from "zustand/middleware";

type Theme = "system" | "dark" | "light";
type Tool = "chat" | "generate_doc";
type SettingsSection = "umum" | "format_tor" | "lanjutan";

interface UIStore {
  sidebarOpen: boolean;
  settingsOpen: boolean;
  settingsSection: SettingsSection;
  theme: Theme;
  activeTool: Tool;

  toggleSidebar: () => void;
  openSettings: (section?: SettingsSection) => void;
  closeSettings: () => void;
  setTheme: (theme: Theme) => void;
  setActiveTool: (tool: Tool) => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      settingsOpen: false,
      settingsSection: "umum",
      theme: "dark",
      activeTool: "chat",

      toggleSidebar: () => set(state => ({ sidebarOpen: !state.sidebarOpen })),
      openSettings: (section = "umum") => set({ settingsOpen: true, settingsSection: section }),
      closeSettings: () => set({ settingsOpen: false }),
      setTheme: (theme) => {
        set({ theme });
        // Apply to DOM
        const root = document.documentElement;
        root.classList.remove("dark", "light");
        if (theme === "dark") root.classList.add("dark");
        else if (theme === "light") root.classList.remove("dark");
        else {
          // system preference
          if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
            root.classList.add("dark");
          }
        }
      },
      setActiveTool: (tool) => set({ activeTool: tool }),
    }),
    { name: "tor-ui-settings", partialize: (state) => ({ theme: state.theme }) },
  ),
);
```

## 6. Output yang Diharapkan

```typescript
// Usage di component:
const messages = useChatStore(s => s.messages);
const isStreaming = useChatStore(s => s.stream.isStreaming);
const { sendMessage } = useChatStore();

const sessions = useSessionStore(s => s.sessions);
const activeTool = useUIStore(s => s.activeTool);
```

## 7. Dependencies

- Task 01 (zustand installed)
- Task 02 (TypeScript types)
- Task 03 (API client functions)

## 8. Acceptance Criteria

- [ ] 4 store files dibuat di `src/stores/`
- [ ] `useChatStore` — sendMessage, retry, clear berfungsi
- [ ] `useSessionStore` — fetch, load, delete, create berfungsi
- [ ] `useModelStore` — fetch, set active berfungsi
- [ ] `useUIStore` — theme persisted via `zustand/persist`
- [ ] Semua stores bisa di-import tanpa circular dependency
- [ ] `npm run build` tanpa error

## 9. Estimasi

Medium (2-3 jam)
