import { useEffect } from "react";
import { useUIStore } from "@/stores/ui-store";
import { useChatStore } from "@/stores/chat-store";
import { useSessionStore } from "@/stores/session-store";

export function useKeyboard() {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Esc = close settings
      if (e.key === "Escape") {
        useUIStore.getState().closeSettings();
      }
      
      // Ctrl+Shift+N = new chat
      if (e.key === "N" && e.ctrlKey && e.shiftKey) {
        e.preventDefault();
        useSessionStore.getState().setActiveSession(null);
        useChatStore.getState().clearMessages();
        useUIStore.getState().setActiveTool("chat");
      }
    };
    
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
}
