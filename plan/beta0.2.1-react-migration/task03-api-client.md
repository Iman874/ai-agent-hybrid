# Task 03: API Client Layer — HTTP Client per Endpoint

## 1. Judul Task

Buat HTTP API client layer untuk semua backend endpoints

## 2. Deskripsi

Membuat modul API client di `src/api/` yang meng-wrap semua HTTP calls ke FastAPI backend. Setiap endpoint punya function tersendiri dengan type safety penuh.

## 3. Tujuan Teknis

- Base client dengan error handling + interceptors
- Function per endpoint: chat, sessions, models, health, styles, generate, export
- Error handling terstruktur (map ErrorResponse dari backend)

## 4. Scope

**Yang dikerjakan:**
- `src/api/client.ts` — base fetch wrapper
- `src/api/chat.ts` — POST /hybrid
- `src/api/sessions.ts` — GET/DELETE sessions
- `src/api/models.ts` — GET /models
- `src/api/health.ts` — GET /health
- `src/api/styles.ts` — CRUD /styles
- `src/api/generate.ts` — POST /generate/from-document
- `src/api/export.ts` — GET /export/{id}

**Yang tidak dikerjakan:**
- WebSocket (task 10)
- Store integration (task 04)

## 5. Langkah Implementasi

### 5.1 Base Client — `src/api/client.ts`

```typescript
import { API_BASE_URL } from "@/lib/constants";
import type { ErrorResponse } from "@/types/api";

export class ApiError extends Error {
  code: string;
  details?: string;
  retryAfterSeconds?: number;

  constructor(error: ErrorResponse["error"]) {
    super(error.message);
    this.code = error.code;
    this.details = error.details ?? undefined;
    this.retryAfterSeconds = error.retry_after_seconds ?? undefined;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    try {
      const body = await response.json() as ErrorResponse;
      throw new ApiError(body.error);
    } catch (e) {
      if (e instanceof ApiError) throw e;
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  }
  return response.json() as Promise<T>;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  return handleResponse<T>(response);
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<T>(response);
}

export async function apiDelete<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "DELETE",
  });
  return handleResponse<T>(response);
}

export async function apiPostFormData<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<T>(response);
}
```

### 5.2 Chat API — `src/api/chat.ts`

```typescript
import { apiPost } from "./client";
import type { HybridRequest, HybridResponse } from "@/types/api";

export async function sendMessage(req: HybridRequest): Promise<HybridResponse> {
  return apiPost<HybridResponse>("/hybrid", req);
}
```

### 5.3 Sessions API — `src/api/sessions.ts`

```typescript
import { apiGet, apiDelete } from "./client";
import type { SessionListItem } from "@/types/session";
import type { SessionDetailResponse } from "@/types/session";

export async function listSessions(limit = 50): Promise<SessionListItem[]> {
  return apiGet<SessionListItem[]>(`/sessions?limit=${limit}`);
}

export async function getSession(sessionId: string): Promise<SessionDetailResponse> {
  return apiGet<SessionDetailResponse>(`/session/${sessionId}`);
}

export async function deleteSession(sessionId: string): Promise<{ status: string }> {
  return apiDelete<{ status: string }>(`/sessions/${sessionId}`);
}
```

### 5.4 Models API — `src/api/models.ts`

```typescript
import { apiGet } from "./client";
import type { ModelsResponse } from "@/types/api";

export async function listModels(): Promise<ModelsResponse> {
  return apiGet<ModelsResponse>("/models");
}
```

### 5.5 Health API — `src/api/health.ts`

```typescript
import { apiGet } from "./client";
import type { HealthResponse } from "@/types/api";

export async function checkHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health");
}
```

### 5.6 Styles API — `src/api/styles.ts`

```typescript
import { apiGet, apiPost, apiDelete } from "./client";
import type { TORStyle } from "@/types/api";

export async function listStyles(): Promise<TORStyle[]> {
  return apiGet<TORStyle[]>("/styles/");
}

export async function getActiveStyle(): Promise<TORStyle> {
  return apiGet<TORStyle>("/styles/active");
}

export async function activateStyle(styleId: string): Promise<void> {
  await apiPost(`/styles/${styleId}/activate`, {});
}

export async function deleteStyle(styleId: string): Promise<void> {
  await apiDelete(`/styles/${styleId}`);
}

export async function duplicateStyle(styleId: string, newName: string): Promise<TORStyle> {
  return apiPost<TORStyle>(`/styles/${styleId}/duplicate`, { new_name: newName });
}
```

### 5.7 Generate API — `src/api/generate.ts`

```typescript
import { apiPostFormData } from "./client";
import type { GenerateResponse } from "@/types/api";

export async function generateFromDocument(
  file: File,
  context?: string,
  styleId?: string,
): Promise<GenerateResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (context) formData.append("context", context);
  if (styleId) formData.append("style_id", styleId);

  return apiPostFormData<GenerateResponse>("/generate/from-document", formData);
}
```

### 5.8 Export API — `src/api/export.ts`

```typescript
import { API_BASE_URL } from "@/lib/constants";

export async function exportDocument(
  sessionId: string,
  format: "docx" | "pdf" | "md" = "docx",
): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/export/${sessionId}?format=${format}`,
  );
  if (!response.ok) throw new Error(`Export failed: ${response.statusText}`);
  return response.blob();
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
```

## 6. Output yang Diharapkan

```typescript
// Contoh usage:
import { sendMessage } from "@/api/chat";
import { listSessions } from "@/api/sessions";

const response = await sendMessage({ session_id: null, message: "Hello" });
console.log(response.session_id, response.message);

const sessions = await listSessions(10);
```

## 7. Dependencies

- Task 01 (project setup)
- Task 02 (TypeScript types)

## 8. Acceptance Criteria

- [ ] `src/api/client.ts` — base client dengan error handling
- [ ] Semua 7 endpoint files dibuat
- [ ] Semua function return typed responses
- [ ] `ApiError` class bisa di-catch dan punya `.code`, `.message`
- [ ] `npm run build` tanpa error
- [ ] Vite proxy memforward `/api/v1/*` ke `localhost:8000`

## 9. Estimasi

Medium (1-2 jam)
