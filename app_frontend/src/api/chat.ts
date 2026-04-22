import { apiPost } from "./client";
import { API_BASE_URL } from "@/lib/constants";
import type { HybridRequest, HybridResponse } from "@/types/api";

export async function sendMessage(req: HybridRequest): Promise<HybridResponse> {
  return apiPost<HybridResponse>("/hybrid", req);
}

export interface ChatStreamCallbacks {
  onStatus: (msg: string, sessionId?: string) => void;
  onThinkingStart: () => void;
  onThinking: (text: string) => void;
  onThinkingEnd: () => void;
  onToken: (text: string) => void;
  onDone: (data: HybridResponse) => void;
  onError: (msg: string) => void;
}

export async function sendMessageStream(
  req: HybridRequest,
  callbacks: ChatStreamCallbacks,
  abortSignal?: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/hybrid/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal: abortSignal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") return;
    callbacks.onError(e instanceof Error ? e.message : "Network error");
    return;
  }

  if (!response.ok) {
    try {
      const errBody = await response.json();
      callbacks.onError(errBody?.detail || `HTTP ${response.status}: ${response.statusText}`);
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
            callbacks.onStatus(
              data.msg as string,
              data.session_id as string | undefined,
            );
            break;
          case "thinking_start":
            callbacks.onThinkingStart();
            break;
          case "thinking":
            callbacks.onThinking(data.t as string);
            break;
          case "thinking_end":
            callbacks.onThinkingEnd();
            break;
          case "token":
            callbacks.onToken(data.t as string);
            break;
          case "done":
            callbacks.onDone(data as unknown as HybridResponse);
            break;
          case "error":
            callbacks.onError(data.msg as string);
            break;
        }
      }
    }
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") return;
    callbacks.onError("Connection lost during streaming");
  }
}
