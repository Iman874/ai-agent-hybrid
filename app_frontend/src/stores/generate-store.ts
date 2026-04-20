import { create } from "zustand";
import * as genApi from "@/api/generate";
import { streamGenerateFromDocument, savePartialContent, retryStream, continueStream } from "@/api/generate";
import type { DocGenListItem, DocGenDetail, StreamDoneData } from "@/types/generate";
import type { GenerateResponse } from "@/types/api";

interface GenerateStore {
  // History
  history: DocGenListItem[];
  isLoadingHistory: boolean;
  fetchHistory: () => Promise<void>;

  // Active result (viewing detail)
  activeResult: DocGenDetail | null;
  isLoadingResult: boolean;
  viewResult: (id: string) => Promise<void>;
  clearActiveResult: () => void;

  // Last generate response (immediate result after generate)
  lastGenerateResponse: GenerateResponse | null;
  isGenerating: boolean;
  generateFromDoc: (file: File, context?: string, styleId?: string) => Promise<void>;
  clearLastResponse: () => void;

  // Delete
  deleteGeneration: (id: string) => Promise<void>;

  // Streaming
  streamingContent: string;
  streamingStatus: string;
  isStreaming: boolean;
  streamError: string | null;
  streamSessionId: string | null;
  streamMetadata: StreamDoneData["metadata"] | null;
  
  generateFromDocStream: (file: File, context?: string, styleId?: string) => Promise<void>;
  retryGeneration: (genId: string) => Promise<void>;
  continueGeneration: (genId: string, existingContent: string) => Promise<void>;
  cancelStream: () => Promise<void>;
  clearStreamState: () => void;

  // Internal (non-reactive)
  _abortController: AbortController | null;
  _sourceGenId: string | null; // ID record asal untuk retry/continue fallback
}

export const useGenerateStore = create<GenerateStore>((set, get) => ({
  history: [],
  isLoadingHistory: false,

  fetchHistory: async () => {
    set({ isLoadingHistory: true });
    try {
      const data = await genApi.listGenerations(30);
      set({ history: data, isLoadingHistory: false });
    } catch {
      set({ isLoadingHistory: false });
    }
  },

  activeResult: null,
  isLoadingResult: false,

  viewResult: async (id) => {
    set({ isLoadingResult: true });
    try {
      const detail = await genApi.getGeneration(id);
      set({ activeResult: detail, isLoadingResult: false, lastGenerateResponse: null });
    } catch {
      set({ isLoadingResult: false });
    }
  },

  clearActiveResult: () => set({ activeResult: null }),

  lastGenerateResponse: null,
  isGenerating: false,

  generateFromDoc: async (file, context, styleId) => {
    set({ isGenerating: true, lastGenerateResponse: null });
    try {
      const result = await genApi.generateFromDocument(file, context, styleId);
      set({ lastGenerateResponse: result, isGenerating: false });
      // Refresh history
      get().fetchHistory();
    } catch (e) {
      set({ isGenerating: false });
      // Refresh to show failed entry
      get().fetchHistory();
      throw e;
    }
  },

  clearLastResponse: () => set({ lastGenerateResponse: null }),

  deleteGeneration: async (id) => {
    await genApi.deleteGeneration(id);
    set(state => ({
      history: state.history.filter(h => h.id !== id),
      activeResult: state.activeResult?.id === id ? null : state.activeResult,
    }));
  },

  // Streaming initial state
  streamingContent: "",
  streamingStatus: "",
  isStreaming: false,
  streamError: null,
  streamSessionId: null,
  streamMetadata: null,
  _abortController: null,
  _sourceGenId: null,

  generateFromDocStream: async (file, context, styleId) => {
    const abortController = new AbortController();
    set({
      isStreaming: true,
      streamingContent: "",
      streamingStatus: "",
      streamError: null,
      streamSessionId: null,
      streamMetadata: null,
      _abortController: abortController,
      _sourceGenId: null,
      lastGenerateResponse: null,
    });

    // Safety timeout: 300 detik (5 menit) max
    const safetyTimeout = setTimeout(() => {
      const state = get();
      if (state.isStreaming) {
        abortController.abort();
        set({
          isStreaming: false,
          streamError: "Timeout: generate melebihi batas waktu (300 detik)",
        });
      }
    }, 300_000);

    try {
      await streamGenerateFromDocument(file, context, styleId, {
        onStatus: (msg, sessionId) => {
          const updates: Partial<GenerateStore> = { streamingStatus: msg };
          if (sessionId) updates.streamSessionId = sessionId;
          set(updates);
        },
        onToken: (t) => set(s => ({ streamingContent: s.streamingContent + t })),
        onDone: (data) => {
          clearTimeout(safetyTimeout);
          set({
            isStreaming: false,
            streamSessionId: data.session_id,
            streamMetadata: data.metadata,
            streamingStatus: "",
            _abortController: null,
          });
          get().fetchHistory();
        },
        onError: async (msg) => {
          clearTimeout(safetyTimeout);
          const currentSessionId = get().streamSessionId;
          const currentContent = get().streamingContent;
          // PARTIAL PRESERVATION: streamingContent TIDAK di-reset
          set({
            isStreaming: false,
            streamError: msg,
            _abortController: null,
          });
          // Simpan partial content ke backend jika ada
          if (currentSessionId && currentContent) {
            await savePartialContent(currentSessionId, currentContent, msg);
          }
          get().fetchHistory();
        },
      }, abortController.signal);
    } catch {
      clearTimeout(safetyTimeout);
      set({ isStreaming: false, _abortController: null });
    }
  },

  retryGeneration: async (genId) => {
    const abortController = new AbortController();
    set({
      isStreaming: true,
      streamingContent: "",
      streamingStatus: "",
      streamError: null,
      streamSessionId: null,
      streamMetadata: null,
      _abortController: abortController,
      _sourceGenId: genId,        // simpan ID asal
      lastGenerateResponse: null,
      activeResult: null,         // close detail view
    });

    const safetyTimeout = setTimeout(() => {
      if (get().isStreaming) {
        abortController.abort();
        set({ isStreaming: false, streamError: "Timeout: melebihi batas waktu 5 menit" });
      }
    }, 300_000);

    try {
      await retryStream(genId, {
        onStatus: (msg, sessionId) => {
          const updates: Partial<GenerateStore> = { streamingStatus: msg };
          if (sessionId) updates.streamSessionId = sessionId;
          set(updates);
        },
        onToken: (t) => set(s => ({ streamingContent: s.streamingContent + t })),
        onDone: (data) => {
          clearTimeout(safetyTimeout);
          set({
            isStreaming: false,
            streamSessionId: data.session_id,
            streamMetadata: data.metadata,
            streamingStatus: "",
            _abortController: null,
          });
          get().fetchHistory();
        },
        onError: async (msg) => {
          clearTimeout(safetyTimeout);
          const sessionId = get().streamSessionId;
          const content = get().streamingContent;
          set({ isStreaming: false, streamError: msg, _abortController: null });
          if (sessionId && content) await savePartialContent(sessionId, content, msg);
          get().fetchHistory();
        },
      }, abortController.signal);
    } catch {
      clearTimeout(safetyTimeout);
      set({ isStreaming: false, _abortController: null });
    }
  },

  continueGeneration: async (genId, existingContent) => {
    const abortController = new AbortController();
    set({
      isStreaming: true,
      streamingContent: existingContent, // START WITH EXISTING CONTENT
      streamingStatus: "",
      streamError: null,
      // JANGAN reset streamSessionId — biarkan tetap untuk fallback
      streamMetadata: null,
      _abortController: abortController,
      _sourceGenId: genId,        // simpan ID asal
      lastGenerateResponse: null,
      activeResult: null,         // close detail view jika dari history
    });

    const safetyTimeout = setTimeout(() => {
      if (get().isStreaming) {
        abortController.abort();
        set({ isStreaming: false, streamError: "Timeout: melebihi batas waktu 5 menit" });
      }
    }, 300_000);

    try {
      await continueStream(genId, {
        onStatus: (msg, sessionId) => {
          const updates: Partial<GenerateStore> = { streamingStatus: msg };
          if (sessionId) updates.streamSessionId = sessionId;
          set(updates);
        },
        // Token baru di-append ke existing content — seamless continuation
        onToken: (t) => set(s => ({ streamingContent: s.streamingContent + t })),
        onDone: (data) => {
          clearTimeout(safetyTimeout);
          set({
            isStreaming: false,
            streamSessionId: data.session_id,
            streamMetadata: data.metadata,
            streamingStatus: "",
            _abortController: null,
          });
          get().fetchHistory();
        },
        onError: async (msg) => {
          clearTimeout(safetyTimeout);
          const sessionId = get().streamSessionId;
          const content = get().streamingContent;
          set({ isStreaming: false, streamError: msg, _abortController: null });
          if (sessionId && content) await savePartialContent(sessionId, content, msg);
          get().fetchHistory();
        },
      }, abortController.signal);
    } catch {
      clearTimeout(safetyTimeout);
      set({ isStreaming: false, _abortController: null });
    }
  },

  cancelStream: async () => {
    const ctrl = get()._abortController;
    const sessionId = get().streamSessionId;
    const content = get().streamingContent;
    if (ctrl) ctrl.abort();
    // PARTIAL PRESERVATION: content tetap, error message set
    set({
      isStreaming: false,
      streamError: "Dibatalkan oleh user",
      _abortController: null,
    });
    // Simpan partial content ke backend via explicit API call
    if (sessionId && content) {
      await savePartialContent(sessionId, content, "Dibatalkan oleh user");
    }
    get().fetchHistory();
  },

  clearStreamState: () => set({
    streamingContent: "",
    streamingStatus: "",
    streamError: null,
    streamSessionId: null,
    streamMetadata: null,
    isStreaming: false,
    _abortController: null,
    _sourceGenId: null,
  }),

}));
