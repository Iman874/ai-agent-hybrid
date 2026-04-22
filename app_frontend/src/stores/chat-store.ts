import { create } from "zustand";
import { sendMessage as apiSendMessage, sendMessageStream } from "@/api/chat";
import { useSessionStore } from "./session-store";
import { useModelStore } from "./model-store";
import { useGenerateStore } from "./generate-store";
import { useUIStore } from "./ui-store";
import { getTranslation } from "@/i18n";
import type { Message, StreamState } from "@/types/chat";
import type { HybridResponse, TORDocument, SessionState, EscalationInfo } from "@/types/api";

const LIVE_THINKING_VISIBILITY_KEY = "chat.liveThinkingVisible";

function getInitialLiveThinkingVisible(): boolean {
  if (typeof window === "undefined") return true;

  const raw = window.localStorage.getItem(LIVE_THINKING_VISIBILITY_KEY);
  if (raw === "false") return false;
  if (raw === "true") return true;
  return true;
}

function persistLiveThinkingVisible(value: boolean): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(LIVE_THINKING_VISIBILITY_KEY, String(value));
}

const initialLiveThinkingVisible = getInitialLiveThinkingVisible();

interface ChatStore {
  messages: Message[];
  stream: StreamState;
  torDocument: TORDocument | null;
  sessionState: SessionState | null;
  escalationInfo: EscalationInfo | null;

  // We use any to avoid circular strict typing before WSManager is created, but normally it's WebSocketManager
  wsManager: any | null;
  _abortController: AbortController | null;
  setWSManager: (ws: any) => void;

  sendMessage: (text: string, sessionId: string | null, images?: string[]) => Promise<void>;
  retryMessage: (messageId: string, sessionId: string | null) => Promise<void>;
  appendToken: (token: string) => void;
  setThinking: (active: boolean) => void;
  appendThinkingToken: (token: string) => void;
  toggleLiveThinkingVisible: () => void;
  toggleThinkingVisible: (messageId: string) => void;
  toggleThinkingExpanded: (messageId: string) => void;
  finalizeStream: (data: HybridResponse) => void;
  setError: (messageId: string, error: string) => void;
  clearMessages: () => void;
  loadMessages: (messages: Message[]) => void;
  setTorDocument: (doc: TORDocument) => void;
  clearTorDocument: () => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  stream: {
    isStreaming: false,
    isThinking: false,
    thinkingText: "",
    partialContent: "",
    thinkingVisible: initialLiveThinkingVisible,
  },
  torDocument: null,
  sessionState: null,
  escalationInfo: null,
  wsManager: null,
  _abortController: null,

  setWSManager: (ws) => set({ wsManager: ws }),

  sendMessage: async (text, sessionId, images) => {
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      images: images,
      timestamp: Date.now(),
      status: "done",
    };

    set(state => ({ messages: [...state.messages, userMsg] }));

    const { chatMode, activeModelId } = useModelStore.getState();
    const requestBody = {
      session_id: sessionId,
      message: text,
      images: images,
      options: {
        chat_mode: chatMode,
        model_preference: activeModelId ?? undefined,
      },
    };

    // PRIMARY: SSE stream
    const abortController = new AbortController();
    let sseDone = false;
    let sseError = "";

    set(state => ({
      _abortController: abortController,
      stream: {
        isStreaming: false,
        isThinking: false,
        thinkingText: "",
        partialContent: "",
        thinkingVisible: state.stream.thinkingVisible,
      },
    }));

    await sendMessageStream(
      requestBody,
      {
        onStatus: (_msg, sid) => {
          if (sid) {
            const currentActiveId = useSessionStore.getState().activeSessionId;
            if (!currentActiveId) {
              useSessionStore.getState().setActiveSession(sid);
              useSessionStore.getState().fetchSessions();
            }
          }
        },
        onThinkingStart: () => get().setThinking(true),
        onThinking: (token) => get().appendThinkingToken(token),
        onThinkingEnd: () => get().setThinking(false),
        onToken: (token) => {
          set(state => ({
            stream: { ...state.stream, isStreaming: true },
          }));
          get().appendToken(token);
        },
        onDone: (data) => {
          sseDone = true;
          get().finalizeStream(data);
        },
        onError: (msg) => {
          sseError = msg;
        },
      },
      abortController.signal,
    );

    set({ _abortController: null });

    if (sseDone || abortController.signal.aborted) {
      return;
    }

    // Reset UI stream state sebelum fallback.
    set(state => ({
      stream: {
        isStreaming: false,
        isThinking: false,
        thinkingText: "",
        partialContent: "",
        thinkingVisible: state.stream.thinkingVisible,
      },
    }));

    // FALLBACK 1: WebSocket
    const ws = get().wsManager;
    if (ws?.status === "connected") {
      set(state => ({
        stream: { ...state.stream, isStreaming: true },
      }));
      ws.send(text);
      return;
    }

    // FALLBACK 2: HTTP blocking
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
      const response = await apiSendMessage(requestBody);
      get().finalizeStream(response);
    } catch (error) {
      const errMsg = error instanceof Error
        ? error.message
        : (sseError || "Terjadi kesalahan");
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

  toggleLiveThinkingVisible: () => {
    set(state => {
      const nextVisible = !state.stream.thinkingVisible;
      persistLiveThinkingVisible(nextVisible);

      return {
        stream: {
          ...state.stream,
          thinkingVisible: nextVisible,
        },
      };
    });
  },

  toggleThinkingVisible: (messageId) => {
    set(state => ({
      messages: state.messages.map(m =>
        m.id === messageId
          ? { ...m, thinkingVisible: !(m.thinkingVisible ?? false) }
          : m,
      ),
    }));
  },

  toggleThinkingExpanded: (messageId) => {
    set(state => ({
      messages: state.messages.map(m =>
        m.id === messageId
          ? { ...m, thinkingExpanded: !(m.thinkingExpanded ?? false) }
          : m,
      ),
    }));
  },

  finalizeStream: (data) => {
    set(state => {
      const finalThinking = state.stream.thinkingText.trim() || undefined;
      const lastAssistant = [...state.messages].reverse().find(m => m.role === "assistant");
      const updatedMessages = state.messages.map(m =>
        m.id === lastAssistant?.id || m.status === 'sending'
          ? {
              ...m,
              content: data.message,
              status: "done" as const,
              thinkingContent: finalThinking,
              thinkingVisible: false,
              thinkingExpanded: false,
            }
          : m,
      );

      // If WS is used, lastAssistant might not exist if it's currently stored in partialContent
      if (!lastAssistant && state.stream.isStreaming) {
         updatedMessages.push({
             id: crypto.randomUUID(),
             role: "assistant",
             content: data.message,
             timestamp: Date.now(),
             status: "done",
             thinkingContent: finalThinking,
             thinkingVisible: false,
             thinkingExpanded: false,
         });
      }

      return {
        messages: updatedMessages,
        stream: {
          isStreaming: false,
          isThinking: false,
          thinkingText: "",
          partialContent: "",
          thinkingVisible: state.stream.thinkingVisible,
        },
        torDocument: data.tor_document ?? state.torDocument,
        sessionState: data.state,
        escalationInfo: data.escalation_info ?? null,
      };
    });

    const status = data.state?.status;
    if (
      status === "READY_TO_GENERATE" ||
      status === "ESCALATE_TO_GEMINI"
    ) {
      const mode = status === "ESCALATE_TO_GEMINI" ? "escalation" : "standard";
      const sessionId = data.session_id;

      if (sessionId) {
        // Task 05: Tambahkan pesan transisi di chat
        set(state => ({
          messages: [
            ...state.messages,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: getTranslation("chat.ready_generating"),
              timestamp: Date.now(),
              status: "done",
            },
          ],
        }));

        // 1. Switch UI ke tab "generate_doc" agar StreamingResult tampil
        useUIStore.getState().setActiveTool("generate_doc");

        // 2. Panggil generate store untuk mulai streaming TOR
        // Sedikit delay agar React sempat merender tab switch
        setTimeout(() => {
          useGenerateStore.getState().generateFromChatStream(sessionId, mode);
        }, 100);
      }
    }

    // Sync session_id ke session store
    const currentActiveId = useSessionStore.getState().activeSessionId;
    if (data.session_id && !currentActiveId) {
      useSessionStore.getState().setActiveSession(data.session_id);
      useSessionStore.getState().fetchSessions();
    }
  },

  setError: (messageId, error) => {
    set(state => ({
      messages: state.messages.map(m =>
        m.id === messageId
          ? { ...m, status: "error" as const, errorMessage: error }
          : m,
      ),
      stream: {
        isStreaming: false,
        isThinking: false,
        thinkingText: "",
        partialContent: "",
        thinkingVisible: state.stream.thinkingVisible,
      },
    }));
  },

  clearMessages: () => set({
    messages: [],
    stream: {
      isStreaming: false,
      isThinking: false,
      thinkingText: "",
      partialContent: "",
      thinkingVisible: getInitialLiveThinkingVisible(),
    },
    torDocument: null,
    sessionState: null,
    escalationInfo: null,
  }),

  loadMessages: (messages) => set({ messages }),
  setTorDocument: (doc) => set({ torDocument: doc }),
  clearTorDocument: () => set({ torDocument: null }),
}));
