import { create } from "zustand";
import { sendMessage as apiSendMessage } from "@/api/chat";
import type { Message, StreamState } from "@/types/chat";
import type { HybridResponse, TORDocument, SessionState, EscalationInfo } from "@/types/api";

interface ChatStore {
  messages: Message[];
  stream: StreamState;
  torDocument: TORDocument | null;
  sessionState: SessionState | null;
  escalationInfo: EscalationInfo | null;

  // We use any to avoid circular strict typing before WSManager is created, but normally it's WebSocketManager
  wsManager: any | null;
  setWSManager: (ws: any) => void;

  sendMessage: (text: string, sessionId: string | null) => Promise<void>;
  retryMessage: (messageId: string, sessionId: string | null) => Promise<void>;
  appendToken: (token: string) => void;
  setThinking: (active: boolean) => void;
  appendThinkingToken: (token: string) => void;
  finalizeStream: (data: HybridResponse) => void;
  setError: (messageId: string, error: string) => void;
  clearMessages: () => void;
  loadMessages: (messages: Message[]) => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  stream: { isStreaming: false, isThinking: false, thinkingText: "", partialContent: "" },
  torDocument: null,
  sessionState: null,
  escalationInfo: null,
  wsManager: null,

  setWSManager: (ws) => set({ wsManager: ws }),

  sendMessage: async (text, sessionId) => {
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: Date.now(),
      status: "done",
    };

    set(state => ({ messages: [...state.messages, userMsg] }));

    const ws = get().wsManager;
    if (ws?.status === "connected") {
      set(state => ({
        stream: { ...state.stream, isStreaming: true },
      }));
      ws.send(text);
      return;
    }

    // fallback http
    const assistantId = crypto.randomUUID();
    const assistantMsg: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: Date.now(),
      status: "sending",
    };
    set(state => ({ messages: [...state.messages, assistantMsg] }));

    try {
      const response = await apiSendMessage({
        session_id: sessionId,
        message: text,
      });
      get().finalizeStream(response);
    } catch (error) {
      const errMsg = error instanceof Error ? error.message : "Terjadi kesalahan";
      get().setError(assistantId, errMsg);
    }
  },

  retryMessage: async (messageId, sessionId) => {
    const { messages } = get();
    const failedIdx = messages.findIndex(m => m.id === messageId);
    if (failedIdx === -1) return;

    const userMsg = messages.slice(0, failedIdx).reverse().find(m => m.role === "user");
    if (!userMsg) return;

    set(state => ({
      messages: state.messages.filter(m => m.id !== messageId),
    }));

    await get().sendMessage(userMsg.content, sessionId);
  },

  appendToken: (token) => {
    set(state => ({
      stream: { ...state.stream, partialContent: state.stream.partialContent + token },
    }));
  },

  setThinking: (active) => {
    set(state => ({
      stream: {
        ...state.stream,
        isThinking: active,
        isStreaming: active || state.stream.isStreaming,
        thinkingText: active ? "" : state.stream.thinkingText,
      },
    }));
  },

  appendThinkingToken: (token) => {
    set(state => ({
      stream: { ...state.stream, thinkingText: state.stream.thinkingText + token },
    }));
  },

  finalizeStream: (data) => {
    set(state => {
      const lastAssistant = [...state.messages].reverse().find(m => m.role === "assistant");
      const updatedMessages = state.messages.map(m =>
        m.id === lastAssistant?.id || m.status === 'sending'
          ? { ...m, content: data.message, status: "done" as const }
          : m,
      );

      // If WS is used, lastAssistant might not exist if it's currently stored in partialContent
      if (!lastAssistant && state.stream.isStreaming) {
         updatedMessages.push({
             id: crypto.randomUUID(),
             role: "assistant",
             content: data.message,
             timestamp: Date.now(),
             status: "done"
         });
      }

      return {
        messages: updatedMessages,
        stream: { isStreaming: false, isThinking: false, thinkingText: "", partialContent: "" },
        torDocument: data.tor_document ?? state.torDocument,
        sessionState: data.state,
        escalationInfo: data.escalation_info ?? null,
      };
    });
  },

  setError: (messageId, error) => {
    set(state => ({
      messages: state.messages.map(m =>
        m.id === messageId
          ? { ...m, status: "error" as const, errorMessage: error }
          : m,
      ),
      stream: { isStreaming: false, isThinking: false, thinkingText: "", partialContent: "" },
    }));
  },

  clearMessages: () => set({
    messages: [],
    stream: { isStreaming: false, isThinking: false, thinkingText: "", partialContent: "" },
    torDocument: null,
    sessionState: null,
    escalationInfo: null,
  }),

  loadMessages: (messages) => set({ messages }),
}));
