import { useUIStore } from "@/stores/ui-store";
import { PanelLeftClose, PanelLeft, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/i18n";

export function Header() {
  const sidebarOpen = useUIStore(s => s.sidebarOpen);
  const toggleSidebar = useUIStore(s => s.toggleSidebar);
  const activeTool = useUIStore(s => s.activeTool);

  const { t } = useTranslation();

  return (
    <header className="h-12 border-b border-border flex items-center px-4 gap-3 flex-shrink-0">
      <Button variant="ghost" size="icon" onClick={toggleSidebar}>
        {sidebarOpen ? (
          <PanelLeftClose className="w-4 h-4" />
        ) : (
          <PanelLeft className="w-4 h-4" />
        )}
      </Button>

      {activeTool === "chat" && (
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-primary" />
          <span className="font-semibold text-lg hover:text-primary transition-colors">{t("header.title")}</span>
        </div>
      )}
    </header>
  );
}
