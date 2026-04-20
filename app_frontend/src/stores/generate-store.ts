import { create } from "zustand";
import * as genApi from "@/api/generate";
import type { DocGenListItem, DocGenDetail } from "@/types/generate";
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
}));
