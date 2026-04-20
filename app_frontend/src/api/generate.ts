import { apiPostFormData, apiGet, apiDelete, apiPost } from "./client";
import { API_BASE_URL } from "@/lib/constants";
import type { GenerateResponse } from "@/types/api";
import type { DocGenListItem, DocGenDetail, StreamDoneData } from "@/types/generate";

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

export async function listGenerations(limit = 30): Promise<DocGenListItem[]> {
  return apiGet<DocGenListItem[]>(`/generate/history?limit=${limit}`);
}

export async function getGeneration(id: string): Promise<DocGenDetail> {
  return apiGet<DocGenDetail>(`/generate/${id}`);
}

export async function deleteGeneration(id: string): Promise<void> {
  await apiDelete(`/generate/${id}`);
}

export interface StreamCallbacks {
  onStatus: (msg: string, sessionId?: string) => void;
  onToken: (text: string) => void;
  onDone: (data: StreamDoneData) => void;
  onError: (msg: string) => void;
}

export async function streamGenerateFromDocument(
  file: File,
  context: string | undefined,
  styleId: string | undefined,
  callbacks: StreamCallbacks,
  abortSignal?: AbortSignal,
): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);
  if (context) formData.append("context", context);
  if (styleId) formData.append("style_id", styleId);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/generate/from-document/stream`, {
      method: "POST",
      body: formData,
      signal: abortSignal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") return;
    callbacks.onError(e instanceof Error ? e.message : "Network error");
    return;
  }

  await consumeStream(response, callbacks);
}

export async function retryStream(
  genId: string,
  callbacks: StreamCallbacks,
  abortSignal?: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/generate/${genId}/retry-stream`, {
      method: "POST",
      signal: abortSignal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") return;
    callbacks.onError(e instanceof Error ? e.message : "Network error");
    return;
  }

  await consumeStream(response, callbacks);
}

export async function continueStream(
  genId: string,
  callbacks: StreamCallbacks,
  abortSignal?: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/generate/${genId}/continue-stream`, {
      method: "POST",
      signal: abortSignal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") return;
    callbacks.onError(e instanceof Error ? e.message : "Network error");
    return;
  }

  await consumeStream(response, callbacks);
}

async function consumeStream(response: Response, callbacks: StreamCallbacks): Promise<void> {

  if (!response.ok) {
    // Coba baca error message dari backend (JSON: {detail: "..."})
    try {
      const errBody = await response.json();
      const detail = errBody?.detail || `HTTP ${response.status}: ${response.statusText}`;
      callbacks.onError(detail);
    } catch {
      callbacks.onError(`HTTP ${response.status}: ${response.statusText}`);
    }
    return;
  }

  if (!response.body) {
    callbacks.onError("Response body is null");
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;

        let data: Record<string, unknown>;
        try {
          data = JSON.parse(line.slice(6));
        } catch {
          continue;
        }

        switch (data.type) {
          case "status":
            callbacks.onStatus(data.msg as string, data.session_id as string | undefined);
            break;
          case "token":
            callbacks.onToken(data.t as string);
            break;
          case "done":
            callbacks.onDone(data as unknown as StreamDoneData);
            break;
          case "error":
            callbacks.onError(data.msg as string);
            break;
        }
      }
    }
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") return;
    callbacks.onError("Koneksi terputus saat streaming");
  }
}

/** Simpan partial content ke backend saat stream dibatalkan */
export async function savePartialContent(
  sessionId: string,
  content: string,
  error: string = "Dibatalkan oleh user",
): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/generate/${sessionId}/save-partial`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, error }),
    });
  } catch {
    console.error("Failed to save partial content");
  }
}
