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
