import { memo } from "react";
import { X, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { SessionListItem } from "@/types/session";

interface Props {
  session: SessionListItem;
  isActive: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export const SessionItem = memo(function SessionItem({
  session, isActive, onSelect, onDelete,
}: Props) {
  const title = session.title || `Sesi ${session.id.slice(0, 8)}`;
  const displayTitle = title.length > 28 ? title.slice(0, 28) + "…" : title;

  return (
    <div className={cn(
      "group flex items-center gap-1 rounded-md pr-1",
      isActive && "bg-primary/10",
    )}>
      <Button
        variant="ghost"
        size="sm"
        className={cn(
          "flex-1 justify-start text-sm font-normal truncate h-8",
          isActive && "font-semibold text-foreground",
          !isActive && "text-muted-foreground",
        )}
        disabled={isActive}
        onClick={() => onSelect(session.id)}
      >
        <MessageSquare className="w-3.5 h-3.5 mr-2 opacity-70" />
        {displayTitle}
      </Button>

      {!isActive && (
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
          onClick={(e) => { e.stopPropagation(); onDelete(session.id); }}
        >
          <X className="w-3 h-3 text-muted-foreground hover:text-destructive" />
        </Button>
      )}
    </div>
  );
});
