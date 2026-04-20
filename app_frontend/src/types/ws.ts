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
