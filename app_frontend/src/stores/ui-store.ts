import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Language } from "@/i18n/types";

type Theme = "system" | "dark" | "light";
type Tool = "chat" | "generate_doc";
type SettingsSection = "umum" | "format_tor" | "lanjutan";

interface UIStore {
  sidebarOpen: boolean;
  settingsOpen: boolean;
  settingsSection: SettingsSection;
  theme: Theme;
  language: Language;
  activeTool: Tool;

  toggleSidebar: () => void;
  openSettings: (section?: SettingsSection) => void;
  closeSettings: () => void;
  setTheme: (theme: Theme) => void;
  setLanguage: (lang: Language) => void;
  setActiveTool: (tool: Tool) => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      settingsOpen: false,
      settingsSection: "umum",
      theme: "system",
      language: "id",
      activeTool: "chat",

      toggleSidebar: () => set(state => ({ sidebarOpen: !state.sidebarOpen })),
      openSettings: (section = "umum") => set({ settingsOpen: true, settingsSection: section }),
      closeSettings: () => set({ settingsOpen: false }),
      setTheme: (theme) => {
        set({ theme });
        const root = document.documentElement;
        root.classList.remove("dark", "light");
        
        if (theme === "dark") {
             root.classList.add("dark");
        } else if (theme === "system") {
            if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
              root.classList.add("dark");
            }
        }
      },
      setLanguage: (language) => set({ language }),
      setActiveTool: (tool) => set({ activeTool: tool }),
    }),
    { name: "tor-ui-settings", partialize: (state) => ({ theme: state.theme, language: state.language }) },
  ),
);
