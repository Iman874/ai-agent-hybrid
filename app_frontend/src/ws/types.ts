export type WSStatus = "connecting" | "connected" | "disconnected" | "error";

export interface WSCallbacks {
  onToken: (token: string) => void;
  onThinkingStart: () => void;
  onThinkingToken: (token: string) => void;
  onThinkingEnd: () => void;
  onDone: (data: any) => void;
  onError: (error: string) => void;
  onStatusChange: (status: WSStatus) => void;
}
