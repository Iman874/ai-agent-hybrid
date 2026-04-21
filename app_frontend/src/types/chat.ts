export type MessageStatus = "sending" | "streaming" | "done" | "error";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  images?: string[];
  timestamp: number;
  status: MessageStatus;
  errorMessage?: string;
  thinkingContent?: string;
  thinkingVisible?: boolean;
  thinkingExpanded?: boolean;
}

export interface StreamState {
  isStreaming: boolean;
  isThinking: boolean;
  thinkingText: string;
  partialContent: string;
  thinkingVisible: boolean;
}
