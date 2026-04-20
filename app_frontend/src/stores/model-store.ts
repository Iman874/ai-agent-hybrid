import { create } from "zustand";
import { listModels } from "@/api/models";
import type { ModelInfo } from "@/types/api";

interface ModelStore {
  models: ModelInfo[];
  activeModelId: string | null;
  chatMode: "local" | "gemini";
  isLoading: boolean;

  fetchModels: () => Promise<void>;
  setActiveModel: (id: string, type: string) => void;
}

export const useModelStore = create<ModelStore>((set) => ({
  models: [],
  activeModelId: null,
  chatMode: "local",
  isLoading: false,

  fetchModels: async () => {
    set({ isLoading: true });
    try {
      const data = await listModels();
      const available = data.models.filter((m: ModelInfo) =>
        m.status === "available" &&
        !m.id.toLowerCase().includes("embed") &&
        !m.id.toLowerCase().includes("nomic")
      );
      set({
        models: available,
        isLoading: false,
        activeModelId: available[0]?.id ?? null,
        chatMode: available[0]?.type === "local" ? "local" : "gemini",
      });
    } catch {
      set({ isLoading: false });
    }
  },

  setActiveModel: (id, type) => set({
    activeModelId: id,
    chatMode: type === "local" ? "local" : "gemini",
  }),
}));
