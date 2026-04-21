import { create } from "zustand";
import { listModels } from "@/api/models";
import type { ModelInfo, ModelCapabilities } from "@/types/api";

const DEFAULT_CAPABILITIES: ModelCapabilities = {
  supports_text: true,
  supports_image_input: false,
  supports_streaming: true,
};

interface ModelStore {
  models: ModelInfo[];
  activeModelId: string | null;
  activeCapabilities: ModelCapabilities;
  chatMode: "local" | "gemini";
  isLoading: boolean;

  fetchModels: () => Promise<void>;
  setActiveModel: (id: string, type: string) => void;
}

export const useModelStore = create<ModelStore>((set, get) => ({
  models: [],
  activeModelId: null,
  activeCapabilities: DEFAULT_CAPABILITIES,
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
      
      const firstModel = available[0];
      const caps = firstModel?.capabilities ?? DEFAULT_CAPABILITIES;

      set({
        models: available,
        isLoading: false,
        activeModelId: firstModel?.id ?? null,
        activeCapabilities: caps,
        chatMode: firstModel?.type === "local" ? "local" : "gemini",
      });
    } catch {
      set({ isLoading: false });
    }
  },

  setActiveModel: (id, type) => {
    const { models } = get();
    const model = models.find(m => m.id === id);
    set({
      activeModelId: id,
      activeCapabilities: model?.capabilities ?? DEFAULT_CAPABILITIES,
      chatMode: type === "local" ? "local" : "gemini",
    });
  },
}));
