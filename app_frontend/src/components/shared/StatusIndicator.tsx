import { useHealth } from "@/hooks/useHealth";
import { useSessionStore } from "@/stores/session-store";
import { useTranslation } from "@/i18n";

export function StatusIndicator() {
  const { t } = useTranslation();
  const health = useHealth();
  const activeSessionId = useSessionStore(s => s.activeSessionId);

  const ok = health?.status === "healthy";
  const label = ok ? t("sidebar.api_connected") : t("sidebar.api_disconnected");
  const sid = activeSessionId ? ` · ${t("sidebar.session_prefix") || "Session"} ${activeSessionId.slice(0, 8)}` : "";

  return (
    <p className="text-[0.65rem] text-muted-foreground flex items-center gap-1.5 px-2 mt-1 mb-2">
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${ok ? "bg-green-500" : "bg-red-500"}`} />
      <span className="truncate">{label}{sid}</span>
    </p>
  );
}
