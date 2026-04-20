import { useUIStore } from "@/stores/ui-store";
import { useSessionStore } from "@/stores/session-store";
import { Settings, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ModelSelector } from "@/components/shared/ModelSelector";
import { SessionList } from "@/components/session/SessionList";
import { StatusIndicator } from "@/components/shared/StatusIndicator";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/i18n";

export function Sidebar() {
  const openSettings = useUIStore(s => s.openSettings);
  const activeTool = useUIStore(s => s.activeTool);
  const setActiveTool = useUIStore(s => s.setActiveTool);
  const createNewSession = useSessionStore(s => s.createNewSession);
  const { t } = useTranslation();

  return (
    <div className="flex flex-col h-full p-3 gap-2">
      <div className="pt-2 pb-1">
        <ModelSelector />
      </div>

      <Button className="w-full justify-start text-sm" size="sm" onClick={createNewSession}>
        <Plus className="w-4 h-4 mr-2" />
        {t("sidebar.new_chat")}
      </Button>

      <Separator className="my-2 opacity-40 mx-2 w-auto" />

      <p className="text-[0.65rem] font-semibold uppercase tracking-wider text-muted-foreground px-2">
        {t("sidebar.history")}
      </p>
      <div className="flex-1 overflow-y-auto min-h-0 px-2 space-y-0.5">
        <SessionList />
      </div>

      <Separator className="my-2 opacity-40 mx-2 w-auto" />

      <p className="text-[0.65rem] font-semibold uppercase tracking-wider text-muted-foreground px-2">
        {t("sidebar.tools")}
      </p>
      <div className="space-y-0.5 px-2">
        {(["chat", "generate_doc"] as const).map(tool => (
          <Button
            key={tool}
            variant="ghost"
            size="sm"
            className={cn(
              "w-full justify-start text-sm font-normal",
              activeTool === tool && "bg-primary/10 font-semibold",
            )}
            onClick={() => setActiveTool(tool)}
          >
            {tool === "chat" ? t("sidebar.tool.chat") : t("sidebar.tool.generate_doc")}
          </Button>
        ))}
      </div>

      <div className="mt-auto pt-2 px-2 flex flex-col gap-2">
        <Separator className="opacity-40" />

        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start text-muted-foreground"
          onClick={() => openSettings()}
        >
          <Settings className="w-4 h-4 mr-2" />
          {t("sidebar.settings")}
        </Button>

        <StatusIndicator />
      </div>
    </div>
  );
}
