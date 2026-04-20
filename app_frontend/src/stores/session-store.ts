import { create } from "zustand";
import * as sessionsApi from "@/api/sessions";
import { useChatStore } from "./chat-store";
import type { SessionListItem } from "@/types/session";

interface SessionStore {
  sessions: SessionListItem[];
  activeSessionId: string | null;
  isLoading: boolean;

  fetchSessions: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  createNewSession: () => void;
  setActiveSession: (id: string | null) => void;
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  isLoading: false,

  fetchSessions: async () => {
    set({ isLoading: true });
    try {
      const sessions = await sessionsApi.listSessions(50);
      set({ sessions, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  loadSession: async (sessionId) => {
    set({ isLoading: true });
    try {
      const detail = await sessionsApi.getSession(sessionId);
      const messages = detail.chat_history.map((msg, i) => ({
        id: `hist-${i}`,
        role: msg.role as "user" | "assistant",
        content: msg.content,
        timestamp: new Date(msg.timestamp).getTime(),
        status: "done" as const,
      }));
      useChatStore.getState().loadMessages(messages);
      set({ activeSessionId: sessionId, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  deleteSession: async (sessionId) => {
    await sessionsApi.deleteSession(sessionId);
    set(state => ({
      sessions: state.sessions.filter(s => s.id !== sessionId),
      activeSessionId: state.activeSessionId === sessionId ? null : state.activeSessionId,
    }));
    if (get().activeSessionId === null) {
      useChatStore.getState().clearMessages();
    }
  },

  createNewSession: () => {
    useChatStore.getState().clearMessages();
    set({ activeSessionId: null });
  },

  setActiveSession: (id) => set({ activeSessionId: id }),
}));
