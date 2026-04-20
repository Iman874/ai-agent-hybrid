# Task 02: TypeScript Types — Mirror Pydantic Models

## 1. Judul Task

Definisikan semua TypeScript interfaces yang mirror Pydantic models backend

## 2. Deskripsi

Membuat file type definitions di `src/types/` yang merepresentasikan semua API request/response models dari backend FastAPI. Ini menjadi kontrak tipe antara frontend dan backend.

## 3. Tujuan Teknis

- Semua API response types terdefinisi
- Semua request body types terdefinisi
- Type safety end-to-end

## 4. Scope

**Yang dikerjakan:**
- `src/types/api.ts` — response types umum
- `src/types/chat.ts` — chat/message types
- `src/types/session.ts` — session types
- `src/types/ws.ts` — WebSocket message types

**Yang tidak dikerjakan:**
- API client functions (task 03)
- Store implementations (task 04)

## 5. Langkah Implementasi

### 5.1 Buat `src/types/api.ts`

```typescript
// Mirror dari app/models/api.py + app/models/responses.py

export interface SessionState {
  status: string;
  turn_count: number;
  completeness_score: number;
  filled_fields: string[];
  missing_fields: string[];
}

export interface TORMetadata {
  generated_by: string;
  mode: string;
  word_count: number;
  generation_time_ms: number;
  has_assumptions: boolean;
  prompt_tokens: number;
  completion_tokens: number;
}

export interface TORDocument {
  content: string;
  metadata: TORMetadata;
}

export interface EscalationInfo {
  reason: string;
  trigger: string;
  auto_escalated: boolean;
}

export interface TORData {
  judul_kegiatan: string | null;
  latar_belakang: string | null;
  tujuan: string | null;
  sasaran: string | null;
  target_peserta: string | null;
  waktu_pelaksanaan: string | null;
  tempat: string | null;
  anggaran: string | null;
  penanggung_jawab: string | null;
  narasumber: string | null;
  metode: string | null;
  output_kegiatan: string | null;
}

export interface HybridRequest {
  session_id: string | null;
  message: string;
  options?: {
    force_generate?: boolean;
    model_preference?: string;
  };
}

export interface HybridResponse {
  session_id: string;
  type: "chat" | "generate";
  message: string;
  state: SessionState;
  extracted_data?: TORData | null;
  tor_document?: TORDocument | null;
  escalation_info?: EscalationInfo | null;
  cached?: boolean;
}

export interface ComponentHealth {
  status: "up" | "down" | "degraded";
  details?: Record<string, unknown>;
  latency_ms?: number;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  uptime_seconds: number;
  components: Record<string, ComponentHealth>;
}

export interface ModelInfo {
  id: string;
  type: "local" | "gemini";
  provider: string;
  status: "available" | "offline";
}

export interface ModelsResponse {
  models: ModelInfo[];
  default_chat_mode: string;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details?: string | null;
  retry_after_seconds?: number | null;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

export interface TORStyle {
  id: string;
  name: string;
  description: string;
  is_default: boolean;
  is_active: boolean;
  sections: Record<string, unknown>[];
  config: Record<string, unknown>;
}

export interface GenerateDocRequest {
  file: File;
  context?: string;
  style_id?: string;
}

export interface GenerateResponse {
  session_id: string;
  message: string;
  tor_document: TORDocument;
  cached: boolean;
}
```

### 5.2 Buat `src/types/session.ts`

```typescript
export interface SessionListItem {
  id: string;
  title: string | null;
  state: string;
  turn_count: number;
  created_at: string;
  updated_at: string;
  has_tor: boolean;
}

export interface ChatHistoryMessage {
  role: "user" | "assistant";
  content: string;
  parsed_status: string | null;
  timestamp: string;
}

export interface SessionDetailResponse {
  id: string;
  created_at: string;
  updated_at: string;
  state: string;
  turn_count: number;
  completeness_score: number;
  extracted_data: import("./api").TORData;
  chat_history: ChatHistoryMessage[];
  generated_tor: string | null;
  metadata: {
    gemini_calls_count: number;
    total_tokens_local: number;
    total_tokens_gemini: number;
  };
}
```

### 5.3 Buat `src/types/chat.ts`

```typescript
export type MessageStatus = "sending" | "streaming" | "done" | "error";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  status: MessageStatus;
  errorMessage?: string;
  thinkingContent?: string;
}

export interface StreamState {
  isStreaming: boolean;
  isThinking: boolean;
  thinkingText: string;
  partialContent: string;
}
```

### 5.4 Buat `src/types/ws.ts`

```typescript
// WebSocket message types — Client → Server
export interface WSClientMessage {
  type: "message" | "ping";
  text?: string;
}

// WebSocket message types — Server → Client
export type WSServerMessage =
  | { type: "thinking_start" }
  | { type: "thinking_token"; t: string }
  | { type: "thinking_end" }
  | { type: "token"; t: string }
  | { type: "done"; data: import("./api").HybridResponse }
  | { type: "error"; error: string }
  | { type: "pong" };
```

## 6. Output yang Diharapkan

- 4 file type definitions di `src/types/`
- Semua types bisa di-import: `import type { HybridResponse } from "@/types/api"`
- TypeScript compiler tidak error

## 7. Dependencies

- Task 01 (project setup)

## 8. Acceptance Criteria

- [ ] `src/types/api.ts` — semua API response/request types
- [ ] `src/types/session.ts` — session list + detail types
- [ ] `src/types/chat.ts` — Message + StreamState types
- [ ] `src/types/ws.ts` — WebSocket message types (client + server)
- [ ] `npm run build` tanpa TypeScript errors
- [ ] Types match Pydantic models di backend

## 9. Estimasi

Low (30 menit)
