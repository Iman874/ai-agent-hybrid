import { useSessionStore } from "@/stores/session-store";
import { SessionItem } from "./SessionItem";
import { MessageSquare } from "lucide-react";

export function SessionList() {
  const sessions = useSessionStore(s => s.sessions);
  const activeSessionId = useSessionStore(s => s.activeSessionId);
  const loadSession = useSessionStore(s => s.loadSession);
  const deleteSession = useSessionStore(s => s.deleteSession);

  const displayed = sessions.slice(0, 4);

  if (displayed.length === 0) {
    return (
      <div className="text-center py-6 text-muted-foreground flex flex-col items-center">
        <MessageSquare className="w-6 h-6 mb-2 opacity-30" />
        <p className="text-xs">Belum ada percakapan</p>
      </div>
    );
  }

  return (
    <>
      {displayed.map(s => (
        <SessionItem
          key={s.id}
          session={s}
          isActive={s.id === activeSessionId}
          onSelect={loadSession}
          onDelete={deleteSession}
        />
      ))}
    </>
  );
}
