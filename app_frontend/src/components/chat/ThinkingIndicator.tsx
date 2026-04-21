import { Brain, Loader2 } from "lucide-react";
import { useTranslation } from "@/i18n";

interface ThinkingIndicatorProps {
  text: string;
  visible: boolean;
  onToggleVisible: () => void;
}

export function ThinkingIndicator({
  text,
  visible,
  onToggleVisible,
}: ThinkingIndicatorProps) {
  const { t } = useTranslation();
  return (
    <div className="flex gap-3 py-4">
      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center animate-pulse flex-shrink-0 mt-0.5">
        <Brain className="w-4 h-4 text-primary" />
      </div>
      <div className="bg-muted rounded-2xl px-5 py-3 max-w-[85%] sm:max-w-[80%] shadow-sm overflow-hidden">
        <div className="flex items-center gap-2 text-sm text-foreground font-medium mb-1 flex-wrap">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          <span>{t("chat.thinking")}</span>
          <button
            type="button"
            onClick={onToggleVisible}
            className="text-xs text-primary hover:underline ml-auto"
          >
            {visible ? t("chat.reasoning_hide") : t("chat.reasoning_show")}
          </button>
        </div>

        {visible && text && (
          <p className="text-xs text-muted-foreground font-mono whitespace-pre-wrap mt-2 overflow-x-auto w-full">
            {text}
          </p>
        )}
      </div>
    </div>
  );
}
