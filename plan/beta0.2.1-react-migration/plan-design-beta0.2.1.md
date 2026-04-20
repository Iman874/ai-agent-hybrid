# Beta 0.2.1 — Migrasi Frontend: Streamlit → React

> **Tujuan**: Migrasi total frontend dari Streamlit ke React SPA modern dengan chat interface ala ChatGPT/Claude, streaming response, thinking mode, dan retry mechanism.

---

## 1. Alasan Migrasi

| Masalah Streamlit | Solusi React |
|-------------------|-------------|
| Full page reload setiap interaksi | SPA — zero page reload |
| Tidak support streaming response | WebSocket + EventSource (SSE) |
| UI sangat terbatas (widget-based) | Komponen custom tanpa batas |
| Tidak ada retry mechanism | Retry per-message dengan state management |
| Thinking mode tidak bisa ditampilkan real-time | Streaming token-by-token ke UI |
| Flicker / double-render bugs | React reconciliation — predictable render |

---

## 2. Keputusan Teknologi

| Layer | Teknologi | Alasan |
|-------|-----------|--------|
| Framework | **React + Vite** | Build cepat, HMR instan, SPA native |
| Styling | **TailwindCSS v4** | Utility-first, dark mode built-in |
| UI Components | **Shadcn UI** | Accessible, customizable, copy-paste components |
| State | **Zustand** | Minimal boilerplate, no provider wrapping |
| Real-time | **WebSocket** (primary) + **SSE** (fallback) | Streaming token real-time |
| HTTP Client | **ky** atau **fetch** native | Lightweight, promise-based |
| Routing | **React Router v7** | SPA navigation |
| Markdown | **react-markdown** + **remark-gfm** | Render AI response dengan formatting |
| Code Highlight | **rehype-highlight** | Syntax highlight di response |
| Icons | **Lucide React** | Consistent, tree-shakeable |

---

## 3. Arsitektur Sistem

### 3.1 Diagram Arsitektur

```
┌─────────────────────────────────────────────────────────────┐
│                      REACT SPA (Vite)                       │
│                                                             │
│  ┌──────────┐  ┌───────────────┐  ┌──────────────────────┐  │
│  │ Zustand   │  │ WebSocket     │  │ API Client (HTTP)    │  │
│  │ Stores    │←─│ Manager       │  │ /api/v1/*            │  │
│  │           │  │               │  │                      │  │
│  │ • chat    │  │ • connect()   │  │ • hybrid.send()      │  │
│  │ • session │  │ • onMessage() │  │ • sessions.list()    │  │
│  │ • model   │  │ • reconnect() │  │ • models.list()      │  │
│  │ • ui      │  │ • fallbackSSE │  │ • styles.list()      │  │
│  └─────┬─────┘  └───────┬───────┘  └──────────┬───────────┘  │
│        │                │                      │              │
│  ┌─────▼────────────────▼──────────────────────▼───────────┐  │
│  │                    React Components                      │  │
│  │  Sidebar │ ChatArea │ MessageBubble │ ThinkingIndicator  │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP + WebSocket
                            ▼
┌───────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (:8000)                      │
│                                                               │
│  POST /api/v1/hybrid          ← Main chat endpoint            │
│  POST /api/v1/chat            ← Direct chat (legacy)          │
│  POST /api/v1/generate/from-document ← Upload+generate        │
│  GET  /api/v1/sessions        ← List sessions                 │
│  GET  /api/v1/session/{id}    ← Session detail + history      │
│  DELETE /api/v1/sessions/{id} ← Delete session                │
│  GET  /api/v1/models          ← Available AI models           │
│  GET  /api/v1/health          ← Health check                  │
│  GET  /api/v1/export/{id}     ← Export TOR (docx/pdf/md)      │
│  CRUD /api/v1/styles/*        ← TOR style management          │
│  WS   /ws/chat/{session_id}   ← [BARU] WebSocket streaming    │
└───────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow: Chat Message

```
User ketik pesan
      │
      ▼
[ChatInput] ── dispatch ──→ [chatStore.sendMessage()]
                                    │
                            ┌───────▼───────┐
                            │  Add optimistic│
                            │  user message  │
                            │  to messages[] │
                            └───────┬────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │ WebSocket connected?           │
                    ├── YES ─→ ws.send({message})    │
                    │          Stream tokens…        │
                    │          onToken → append       │
                    │          onDone → finalize      │
                    │                                │
                    ├── NO ──→ POST /api/v1/hybrid    │
                    │          await full response    │
                    │          set assistant message  │
                    └────────────────────────────────┘
                                    │
                            ┌───────▼────────┐
                            │  Update state:  │
                            │  • messages[]   │
                            │  • sessionState │
                            │  • torDocument  │
                            └────────────────┘
```

### 3.3 Data Flow: Streaming (WebSocket)

```
Client                              Server
  │                                    │
  │──── WS Connect ───────────────────→│
  │                                    │
  │──── {type:"message", text:"..."} ─→│
  │                                    │
  │←── {type:"thinking_start"} ────────│  ← Thinking mode mulai
  │←── {type:"thinking_token", t:"."} ─│  ← Token thinking (opsional)
  │←── {type:"thinking_end"} ──────────│  ← Thinking selesai
  │                                    │
  │←── {type:"token", t:"Untuk"} ──────│  ← Token response
  │←── {type:"token", t:" mem"} ───────│
  │←── {type:"token", t:"buat"} ───────│
  │                                    │
  │←── {type:"done", data:{...}} ──────│  ← Response complete
  │     session_id, state, tor_doc     │
  │                                    │
  │←── {type:"error", error:"..."} ────│  ← Error case
  │                                    │
```

---

## 4. Struktur Folder `app_frontend`

```
app_frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── components.json                    # shadcn config
│
├── public/
│   └── favicon.svg
│
├── src/
│   ├── main.tsx                       # Entry point
│   ├── App.tsx                        # Root component + Router
│   ├── index.css                      # Tailwind base + custom tokens
│   │
│   ├── api/                           # HTTP API client layer
│   │   ├── client.ts                  # Base fetch/ky instance + interceptors
│   │   ├── chat.ts                    # POST /hybrid, POST /chat
│   │   ├── sessions.ts               # GET/DELETE sessions
│   │   ├── models.ts                  # GET /models
│   │   ├── health.ts                  # GET /health
│   │   ├── styles.ts                  # CRUD /styles/*
│   │   ├── generate.ts               # POST /generate/from-document
│   │   └── export.ts                 # GET /export/{id}
│   │
│   ├── ws/                            # WebSocket layer
│   │   ├── socket.ts                  # WebSocket manager class
│   │   ├── types.ts                   # WS message type definitions
│   │   └── fallback.ts               # SSE fallback if WS unavailable
│   │
│   ├── stores/                        # Zustand state management
│   │   ├── chat-store.ts              # Messages, streaming state, retry
│   │   ├── session-store.ts           # Session list, active session
│   │   ├── model-store.ts            # Model list, active model
│   │   ├── ui-store.ts               # Sidebar open, settings open, theme
│   │   └── style-store.ts            # TOR styles management
│   │
│   ├── components/                    # React components
│   │   ├── ui/                        # Shadcn UI primitives (auto-generated)
│   │   │   ├── button.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── dropdown-menu.tsx
│   │   │   ├── input.tsx
│   │   │   ├── scroll-area.tsx
│   │   │   ├── separator.tsx
│   │   │   ├── sheet.tsx
│   │   │   ├── skeleton.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── textarea.tsx
│   │   │   └── tooltip.tsx
│   │   │
│   │   ├── layout/                    # Layout structure
│   │   │   ├── AppLayout.tsx          # Sidebar + Main area shell
│   │   │   ├── Sidebar.tsx            # Left sidebar (sessions, tools)
│   │   │   └── Header.tsx             # Top bar (model selector, title)
│   │   │
│   │   ├── chat/                      # Chat-specific components
│   │   │   ├── ChatArea.tsx           # The scrollable message list
│   │   │   ├── ChatInput.tsx          # Input bar (textarea + send btn)
│   │   │   ├── MessageBubble.tsx      # Single message (user / assistant)
│   │   │   ├── ThinkingIndicator.tsx  # "AI sedang berpikir..." animation
│   │   │   ├── StreamingText.tsx      # Token-by-token text render
│   │   │   ├── EmptyState.tsx         # "Ceritakan kebutuhan TOR Anda"
│   │   │   ├── RetryButton.tsx        # Retry failed message
│   │   │   └── TORPreview.tsx         # Rendered TOR document preview
│   │   │
│   │   ├── session/                   # Session management
│   │   │   ├── SessionList.tsx        # Sidebar session list
│   │   │   ├── SessionItem.tsx        # Single session row + delete
│   │   │   └── AllSessionsDialog.tsx  # Full session browser dialog
│   │   │
│   │   ├── settings/                  # Settings dialog
│   │   │   ├── SettingsDialog.tsx      # Main dialog container
│   │   │   ├── GeneralSettings.tsx     # Theme + language
│   │   │   ├── FormatTORSettings.tsx   # TOR style management
│   │   │   └── AdvancedSettings.tsx    # API, cache, developer
│   │   │
│   │   ├── generate/                  # Generate from document
│   │   │   ├── UploadForm.tsx         # File upload + context input
│   │   │   └── GenerateResult.tsx     # TOR result + export buttons
│   │   │
│   │   └── shared/                    # Shared utilities
│   │       ├── ModelSelector.tsx       # Model dropdown
│   │       ├── StatusIndicator.tsx     # API health dot
│   │       └── MarkdownRenderer.tsx   # AI response markdown render
│   │
│   ├── hooks/                         # Custom React hooks
│   │   ├── useWebSocket.ts            # WS connection lifecycle
│   │   ├── useAutoScroll.ts           # Auto-scroll chat to bottom
│   │   ├── useHealth.ts              # Periodic health check
│   │   └── useKeyboard.ts            # Keyboard shortcuts (Enter to send)
│   │
│   ├── lib/                           # Utility libraries
│   │   ├── utils.ts                   # cn() helper (shadcn standard)
│   │   └── constants.ts              # API_BASE_URL, WS_URL, etc.
│   │
│   └── types/                         # TypeScript type definitions
│       ├── api.ts                     # API response types (mirror Pydantic)
│       ├── chat.ts                    # Message, StreamState types
│       └── session.ts                # Session types
```

---

## 5. State Management (Zustand)

### 5.1 Chat Store — `stores/chat-store.ts`

```typescript
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  status: "sending" | "streaming" | "done" | "error";
  errorMessage?: string;
  thinkingContent?: string;  // Accumulated thinking text
}

interface StreamState {
  isStreaming: boolean;
  isThinking: boolean;
  thinkingText: string;
  partialContent: string;   // Token-by-token accumulator
}

interface ChatStore {
  // State
  messages: Message[];
  stream: StreamState;
  torDocument: TORDocument | null;
  sessionState: SessionState | null;
  escalationInfo: EscalationInfo | null;

  // Actions
  sendMessage: (text: string) => Promise<void>;
  retryMessage: (messageId: string) => Promise<void>;
  appendToken: (token: string) => void;
  setThinking: (active: boolean) => void;
  appendThinkingToken: (token: string) => void;
  finalizeStream: (data: HybridResponse) => void;
  setError: (messageId: string, error: string) => void;
  clearMessages: () => void;
}
```

**Retry Flow:**
```typescript
retryMessage: async (messageId: string) => {
  const { messages } = get();
  const failedMsg = messages.find(m => m.id === messageId);
  if (!failedMsg || failedMsg.role !== "assistant") return;

  // Cari pesan user sebelum assistant yang gagal
  const idx = messages.indexOf(failedMsg);
  const userMsg = messages.slice(0, idx).reverse().find(m => m.role === "user");
  if (!userMsg) return;

  // Hapus assistant message yang gagal
  set(state => ({
    messages: state.messages.filter(m => m.id !== messageId)
  }));

  // Kirim ulang
  await get().sendMessage(userMsg.content);
}
```

### 5.2 Session Store — `stores/session-store.ts`

```typescript
interface SessionStore {
  // State
  sessions: SessionListItem[];
  activeSessionId: string | null;
  isLoading: boolean;

  // Actions
  fetchSessions: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  createNewSession: () => void;
  setActiveSession: (id: string | null) => void;
}
```

### 5.3 Model Store — `stores/model-store.ts`

```typescript
interface ModelStore {
  models: ModelInfo[];
  activeModelId: string | null;
  chatMode: "local" | "gemini";
  isLoading: boolean;

  fetchModels: () => Promise<void>;
  setActiveModel: (id: string, type: string) => void;
}
```

### 5.4 UI Store — `stores/ui-store.ts`

```typescript
interface UIStore {
  sidebarOpen: boolean;
  settingsOpen: boolean;
  settingsSection: "umum" | "format_tor" | "lanjutan";
  theme: "system" | "dark" | "light";
  activeTool: "chat" | "generate_doc";

  toggleSidebar: () => void;
  openSettings: (section?: string) => void;
  closeSettings: () => void;
  setTheme: (theme: string) => void;
  setActiveTool: (tool: string) => void;
}
```

---

## 6. Backend — Endpoint WebSocket Baru

### 6.1 WebSocket Endpoint

```python
# app/api/routes/ws_chat.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json, logging

router = APIRouter()
logger = logging.getLogger("ai-agent-hybrid.ws")

@router.websocket("/ws/chat/{session_id}")
async def ws_chat(websocket: WebSocket, session_id: str | None = None):
    await websocket.accept()
    
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            
            if data["type"] == "message":
                user_text = data["text"]
                
                # Kirim thinking_start
                await websocket.send_json({"type": "thinking_start"})
                
                # Process via decision engine (dengan streaming callback)
                async for event in decision_engine.route_stream(
                    session_id=session_id,
                    message=user_text,
                ):
                    if event.type == "thinking_token":
                        await websocket.send_json({
                            "type": "thinking_token", "t": event.token
                        })
                    elif event.type == "thinking_end":
                        await websocket.send_json({"type": "thinking_end"})
                    elif event.type == "token":
                        await websocket.send_json({
                            "type": "token", "t": event.token
                        })
                    elif event.type == "done":
                        await websocket.send_json({
                            "type": "done",
                            "data": event.response.model_dump(),
                        })
                        # Update session_id if new
                        if event.response.session_id != session_id:
                            session_id = event.response.session_id
                    elif event.type == "error":
                        await websocket.send_json({
                            "type": "error",
                            "error": str(event.error),
                        })
                        
    except WebSocketDisconnect:
        logger.info(f"WS disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"WS error: {e}")
        await websocket.send_json({"type": "error", "error": str(e)})
```

### 6.2 Register di Router

```python
# app/api/router.py — tambah:
from app.api.routes import ws_chat
api_router.include_router(ws_chat.router, tags=["WebSocket"])
```

### 6.3 Skema Event WebSocket

| Direction | Event | Payload | Keterangan |
|-----------|-------|---------|------------|
| Client→Server | `message` | `{type:"message", text:"..."}` | User kirim pesan |
| Server→Client | `thinking_start` | `{type:"thinking_start"}` | AI mulai berpikir |
| Server→Client | `thinking_token` | `{type:"thinking_token", t:"..."}` | Token thinking (opsional) |
| Server→Client | `thinking_end` | `{type:"thinking_end"}` | Thinking selesai |
| Server→Client | `token` | `{type:"token", t:"..."}` | Token response |
| Server→Client | `done` | `{type:"done", data:{...}}` | Response complete + metadata |
| Server→Client | `error` | `{type:"error", error:"..."}` | Error occurred |
| Client→Server | `ping` | `{type:"ping"}` | Heartbeat |
| Server→Client | `pong` | `{type:"pong"}` | Heartbeat response |

---

## 7. WebSocket Manager (Frontend)

### 7.1 `ws/socket.ts`

```typescript
type WSStatus = "connecting" | "connected" | "disconnected" | "error";

class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnects = 5;
  private heartbeatInterval: NodeJS.Timer | null = null;

  public status: WSStatus = "disconnected";
  public onToken?: (token: string) => void;
  public onThinkingStart?: () => void;
  public onThinkingToken?: (token: string) => void;
  public onThinkingEnd?: () => void;
  public onDone?: (data: HybridResponse) => void;
  public onError?: (error: string) => void;
  public onStatusChange?: (status: WSStatus) => void;

  constructor(baseUrl: string) {
    this.url = baseUrl.replace("http", "ws");
  }

  connect(sessionId?: string): void {
    const path = sessionId ? `/ws/chat/${sessionId}` : "/ws/chat/new";
    this.ws = new WebSocket(`${this.url}${path}`);
    this.status = "connecting";

    this.ws.onopen = () => {
      this.status = "connected";
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.onStatusChange?.("connected");
    };

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      switch (msg.type) {
        case "thinking_start":  this.onThinkingStart?.(); break;
        case "thinking_token":  this.onThinkingToken?.(msg.t); break;
        case "thinking_end":    this.onThinkingEnd?.(); break;
        case "token":           this.onToken?.(msg.t); break;
        case "done":            this.onDone?.(msg.data); break;
        case "error":           this.onError?.(msg.error); break;
        case "pong":            /* heartbeat ok */ break;
      }
    };

    this.ws.onclose = () => {
      this.status = "disconnected";
      this.stopHeartbeat();
      this.onStatusChange?.("disconnected");
      this.tryReconnect(sessionId);
    };

    this.ws.onerror = () => {
      this.status = "error";
      this.onStatusChange?.("error");
    };
  }

  send(text: string): void {
    this.ws?.send(JSON.stringify({ type: "message", text }));
  }

  private tryReconnect(sessionId?: string): void {
    if (this.reconnectAttempts >= this.maxReconnects) {
      console.warn("Max reconnect attempts reached, falling back to HTTP");
      return;
    }
    const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000);
    this.reconnectAttempts++;
    setTimeout(() => this.connect(sessionId), delay);
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      this.ws?.send(JSON.stringify({ type: "ping" }));
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
  }

  disconnect(): void {
    this.stopHeartbeat();
    this.ws?.close();
    this.ws = null;
  }
}
```

### 7.2 Fallback HTTP Streaming — `ws/fallback.ts`

```typescript
async function sendMessageHTTP(
  text: string,
  sessionId: string | null,
  onToken: (token: string) => void,
  onDone: (data: HybridResponse) => void,
  onError: (error: string) => void,
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/hybrid`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        message: text,
      }),
    });

    if (!response.ok) {
      const err = await response.json();
      onError(err.error?.message || "Request gagal");
      return;
    }

    const data = await response.json();
    // Simulate streaming for consistent UX
    const words = data.message.split(" ");
    for (const word of words) {
      onToken(word + " ");
      await new Promise(r => setTimeout(r, 20));
    }
    onDone(data);
  } catch (e) {
    onError(e instanceof Error ? e.message : "Network error");
  }
}
```

---

## 8. Komponen Utama

### 8.1 ChatArea — Message List + Streaming

```tsx
// components/chat/ChatArea.tsx
function ChatArea() {
  const { messages, stream } = useChatStore();
  const scrollRef = useAutoScroll(messages, stream.isStreaming);

  return (
    <ScrollArea ref={scrollRef} className="flex-1 px-4">
      {messages.length === 0 && !stream.isStreaming && <EmptyState />}
      
      {messages.map(msg => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {stream.isThinking && (
        <ThinkingIndicator text={stream.thinkingText} />
      )}

      {stream.isStreaming && !stream.isThinking && (
        <MessageBubble
          message={{
            id: "streaming",
            role: "assistant",
            content: stream.partialContent,
            status: "streaming",
            timestamp: Date.now(),
          }}
        />
      )}
    </ScrollArea>
  );
}
```

### 8.2 MessageBubble — dengan Retry

```tsx
// components/chat/MessageBubble.tsx
function MessageBubble({ message }: { message: Message }) {
  const retryMessage = useChatStore(s => s.retryMessage);

  return (
    <div className={cn(
      "group flex gap-3 py-4",
      message.role === "user" ? "justify-end" : "justify-start"
    )}>
      {message.role === "assistant" && (
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
          <Bot className="w-4 h-4 text-primary" />
        </div>
      )}

      <div className={cn(
        "max-w-[80%] rounded-2xl px-4 py-3",
        message.role === "user"
          ? "bg-primary text-primary-foreground"
          : "bg-muted"
      )}>
        {message.status === "streaming" ? (
          <StreamingText text={message.content} />
        ) : (
          <MarkdownRenderer content={message.content} />
        )}

        {/* Error state + Retry */}
        {message.status === "error" && (
          <div className="mt-2 flex items-center gap-2 text-destructive text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>{message.errorMessage || "Gagal mendapat respons"}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => retryMessage(message.id)}
            >
              <RotateCcw className="w-3 h-3 mr-1" />
              Coba lagi
            </Button>
          </div>
        )}
      </div>

      {message.role === "user" && (
        <div className="w-8 h-8 rounded-full bg-foreground/10 flex items-center justify-center">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
}
```

### 8.3 ThinkingIndicator

```tsx
// components/chat/ThinkingIndicator.tsx
function ThinkingIndicator({ text }: { text: string }) {
  return (
    <div className="flex gap-3 py-4">
      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center animate-pulse">
        <Brain className="w-4 h-4 text-primary" />
      </div>
      <div className="bg-muted rounded-2xl px-4 py-3 max-w-[80%]">
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span>Sedang berpikir...</span>
        </div>
        {text && (
          <p className="text-xs text-muted-foreground/60 font-mono whitespace-pre-wrap">
            {text}
          </p>
        )}
      </div>
    </div>
  );
}
```

### 8.4 ChatInput — dengan Keyboard Shortcut

```tsx
// components/chat/ChatInput.tsx
function ChatInput() {
  const [text, setText] = useState("");
  const sendMessage = useChatStore(s => s.sendMessage);
  const isStreaming = useChatStore(s => s.stream.isStreaming);

  const handleSend = () => {
    if (!text.trim() || isStreaming) return;
    sendMessage(text.trim());
    setText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t p-4">
      <div className="relative max-w-3xl mx-auto flex items-end gap-2">
        <Textarea
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Tanyakan apa saja..."
          className="min-h-[44px] max-h-[200px] resize-none pr-12"
          rows={1}
        />
        <Button
          size="icon"
          onClick={handleSend}
          disabled={!text.trim() || isStreaming}
          className="absolute right-2 bottom-2"
        >
          {isStreaming ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </div>
    </div>
  );
}
```

---

## 9. Performa & Best Practice

### 9.1 Rendering

| Strategi | Detail |
|----------|--------|
| **React.memo** | `MessageBubble`, `SessionItem` — prevent re-render saat streaming |
| **Zustand selectors** | `useChatStore(s => s.stream.isStreaming)` — subscribe spesifik, bukan seluruh store |
| **Virtualized list** | Gunakan `@tanstack/react-virtual` jika messages > 100 |
| **useDeferredValue** | Untuk thinking text agar tidak block main thread |
| **Debounced auto-scroll** | Scroll hanya saat user di bottom, throttle 16ms |

### 9.2 Error Handling

```typescript
// Pattern: setiap API call wrapped dalam try/catch
// dengan state update yang jelas
async function apiCall<T>(fn: () => Promise<T>): Promise<T | null> {
  try {
    return await fn();
  } catch (error) {
    if (error instanceof Response) {
      const body = await error.json();
      // Handle structured error dari FastAPI
      const detail = body.error?.message || "Terjadi kesalahan";
      const retryAfter = body.error?.retry_after_seconds;
      
      if (retryAfter) {
        // Auto-retry setelah delay
        await new Promise(r => setTimeout(r, retryAfter * 1000));
        return apiCall(fn);
      }
      
      throw new Error(detail);
    }
    throw error;
  }
}
```

### 9.3 WebSocket Resilience

```
WS disconnect
      │
      ▼
Exponential backoff: 1s → 2s → 4s → 8s → 16s → 30s (cap)
      │
      ├─ Reconnect success → resume streaming
      │
      └─ Max 5 attempts → fallback ke HTTP
         └─ POST /api/v1/hybrid (full response, no streaming)
         └─ UI tetap berfungsi (simulate streaming dari full response)
```

---

## 10. Backend Changes Required

### 10.1 Files Baru

| File | Deskripsi |
|------|-----------|
| `app/api/routes/ws_chat.py` | WebSocket endpoint untuk streaming chat |
| `app/services/stream_service.py` | Async generator yang yield streaming events |

### 10.2 Modifikasi

| File | Perubahan |
|------|-----------|
| `app/api/router.py` | Tambah `ws_chat.router` |
| `app/services/chat_service.py` | Tambah method `process_message_stream()` yang yield tokens |
| `app/ai/ollama_provider.py` | Expose streaming dari Ollama native streaming |
| `app/ai/gemini_chat_provider.py` | Expose streaming dari Gemini streaming API |
| `app/main.py` | Update CORS untuk WebSocket origin |

### 10.3 CORS Update

```python
# app/main.py — update untuk support WS dari React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 11. Task Breakdown

| # | Task | Scope | Estimasi |
|---|------|-------|----------|
| 1 | **Project Setup** — Vite + React + TS + Tailwind + Shadcn init | Scaffold | Low |
| 2 | **TypeScript Types** — Mirror semua Pydantic models ke TS interfaces | Types | Low |
| 3 | **API Client Layer** — HTTP client per-endpoint (chat, sessions, models, health, styles, export) | API | Medium |
| 4 | **Zustand Stores** — chat-store, session-store, model-store, ui-store | State | Medium |
| 5 | **Layout Shell** — AppLayout, Sidebar, Header (tanpa konten) | UI | Medium |
| 6 | **Sidebar** — Model selector, new chat, session list + delete, tools | UI | High |
| 7 | **Chat Interface** — ChatArea, ChatInput, MessageBubble, EmptyState, MarkdownRenderer | UI | High |
| 8 | **Settings Dialog** — ChatGPT-style sidebar nav (Umum/Format TOR/Lanjutan) | UI | Medium |
| 9 | **Backend WebSocket** — ws_chat.py + stream_service.py + router registration | Backend | High |
| 10 | **Frontend WebSocket** — WebSocketManager + useWebSocket hook + chatStore integration | WS | High |
| 11 | **Streaming UI** — ThinkingIndicator, StreamingText, token-by-token render | UI | Medium |
| 12 | **Retry Mechanism** — Error state per-message + retry action + error UI | Logic | Medium |
| 13 | **Generate from Doc** — Upload form + result preview + export buttons | UI | Medium |
| 14 | **TOR Preview + Export** — Rendered TOR preview + download (DOCX/PDF/MD) | UI | Medium |
| 15 | **Polish & Testing** — Dark mode, responsive, keyboard shortcuts, final QA | Polish | Medium |

---

## 12. Batasan Scope

| Termasuk | Tidak Termasuk |
|----------|----------------|
| Chat interface + streaming | User authentication/login |
| Session management (CRUD) | Multi-user support |
| Model selector (Ollama + Gemini) | Admin panel |
| TOR preview + export (DOCX/PDF/MD) | Real-time collaboration |
| Settings (theme/format/advanced) | Internationalization penuh |
| WebSocket streaming | Push notifications |
| Retry failed messages | Offline mode / PWA |
| Dark/Light theme | Mobile app (hanya web responsive) |

---

## 13. Verification Plan

### Automated
- `npm run build` → zero TypeScript errors
- `npm run lint` → zero ESLint errors
- Vite dev server hot reload berfungsi

### Manual UI
- [ ] Chat: kirim pesan → streaming response muncul token-by-token
- [ ] Thinking: indicator muncul, lalu hilang saat response mulai
- [ ] Retry: klik retry pada pesan gagal → pesan dikirim ulang
- [ ] Session: klik riwayat → chat history ter-load
- [ ] Session: hapus session → session hilang dari list
- [ ] New chat: klik → reset chat, session baru
- [ ] Model: switch model → mode berubah
- [ ] Generate: upload doc → TOR muncul → export berfungsi
- [ ] Settings: buka → navigasi section → theme switch berfungsi
- [ ] WebSocket: disconnect WiFi → reconnect otomatis
- [ ] Fallback: matikan WS → chat masih berfungsi via HTTP
- [ ] Dark mode: toggle → seluruh UI berubah
- [ ] Keyboard: Enter = kirim, Shift+Enter = newline

---

## 14. Timeline Estimasi

| Fase | Durasi | Task |
|------|--------|------|
| **Fase 1: Foundation** | 2-3 hari | Task 1-4 (scaffold, types, API, stores) |
| **Fase 2: Core UI** | 3-4 hari | Task 5-8 (layout, sidebar, chat, settings) |
| **Fase 3: Streaming** | 3-4 hari | Task 9-12 (WS backend, WS frontend, streaming UI, retry) |
| **Fase 4: Features** | 2-3 hari | Task 13-14 (generate doc, TOR preview, export) |
| **Fase 5: Polish** | 1-2 hari | Task 15 (dark mode, responsive, testing) |
| **Total** | **~11-16 hari** | |
