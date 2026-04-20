import { useEffect } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { SettingsDialog } from "@/components/settings/SettingsDialog";
import { useModelStore } from "@/stores/model-store";
import { useSessionStore } from "@/stores/session-store";
import { useUIStore } from "@/stores/ui-store";

function App() {
  const fetchModels = useModelStore(s => s.fetchModels);
  const fetchSessions = useSessionStore(s => s.fetchSessions);
  const theme = useUIStore(s => s.theme);

  // Bootstrap: fetch models + sessions on mount
  useEffect(() => {
    fetchModels();
    fetchSessions();
  }, [fetchModels, fetchSessions]);

  // Apply theme on mount
  useEffect(() => {
    useUIStore.getState().setTheme(theme);
  }, [theme]);

  // Provide the global variables for shadcn UI components via index.css and tailwind configs.
  return (
    <>
      <AppLayout />
      <SettingsDialog />
    </>
  );
}

export default App;
