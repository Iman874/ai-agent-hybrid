import { WS_BASE_URL } from "@/lib/constants";
import type { WSCallbacks, WSStatus } from "./types";
import type { WSServerMessage } from "@/types/ws";

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private urlPath: string;
  private reconnectInterval = 1000;
  private maxReconnectAttempts = 5;
  private attempt = 0;
  private heartbeatIntervalObj: number | null = null;
  public status: WSStatus = "disconnected";
  private currentSessionId?: string;

  public onToken?: WSCallbacks["onToken"];
  public onThinkingStart?: WSCallbacks["onThinkingStart"];
  public onThinkingToken?: WSCallbacks["onThinkingToken"];
  public onThinkingEnd?: WSCallbacks["onThinkingEnd"];
  public onDone?: WSCallbacks["onDone"];
  public onError?: WSCallbacks["onError"];
  public onStatusChange?: WSCallbacks["onStatusChange"];

  constructor(urlPath: string) {
    this.urlPath = urlPath;
  }

  connect(sessionId?: string) {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    if (sessionId !== undefined) {
      this.currentSessionId = sessionId;
    }

    const sid = this.currentSessionId || "null";
    const fullUrl = `${WS_BASE_URL}${this.urlPath}/${sid}`;

    this.setStatus("connecting");
    try {
      this.ws = new WebSocket(fullUrl);
      this.setupListeners();
    } catch (e) {
      this.handleError(e as Error);
    }
  }

  private setupListeners() {
    if (!this.ws) return;

    this.ws.onopen = () => {
      this.setStatus("connected");
      this.attempt = 0;
      this.reconnectInterval = 1000;
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WSServerMessage;
        this.handleMessage(data);
      } catch (e) {
        console.error("Failed to parse WS msg", e);
      }
    };

    this.ws.onclose = () => {
      this.stopHeartbeat();
      if (this.status !== "disconnected") {
        this.handleDisconnect();
      }
    };

    this.ws.onerror = (e) => {
      console.error("WS Error:", e);
    };
  }

  private handleMessage(data: WSServerMessage) {
    switch (data.type) {
      case "thinking_start":
        this.onThinkingStart?.();
        break;
      case "thinking_token":
        this.onThinkingToken?.(data.t);
        break;
      case "thinking_end":
        this.onThinkingEnd?.();
        break;
      case "token":
        this.onToken?.(data.t);
        break;
      case "done":
        this.onDone?.(data.data);
        break;
      case "error":
        this.onError?.(data.error);
        break;
      case "pong":
        break; // Heartbeat ack
    }
  }

  send(text: string) {
    if (this.status === "connected" && this.ws) {
      this.ws.send(JSON.stringify({ type: "message", text }));
    }
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    // @ts-ignore
    this.heartbeatIntervalObj = setInterval(() => {
      if (this.status === "connected" && this.ws) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000);
  }

  private stopHeartbeat() {
    if (this.heartbeatIntervalObj) {
      clearInterval(this.heartbeatIntervalObj);
      this.heartbeatIntervalObj = null;
    }
  }

  private handleDisconnect() {
    this.setStatus("disconnected");
    if (this.attempt < this.maxReconnectAttempts) {
      this.attempt++;
      setTimeout(() => {
        this.connect(); // Try reconnect
      }, this.reconnectInterval);
      this.reconnectInterval = Math.min(this.reconnectInterval * 2, 30000);
    } else {
      this.setStatus("error");
      this.onError?.("Koneksi WebSocket terputus permanen. Menggunakan HTTP fallback.");
    }
  }

  private handleError(e: Error) {
    console.error("WS error:", e);
    this.handleDisconnect();
  }

  private setStatus(status: WSStatus) {
    this.status = status;
    this.onStatusChange?.(status);
  }

  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.onclose = null; // Prevent reconnect loop
      this.ws.close();
      this.ws = null;
    }
    this.setStatus("disconnected");
  }
}
