import { memo } from "react";
import { Bot, User, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { StreamingText } from "./StreamingText";
import { RetryButton } from "./RetryButton";
import { useChatStore } from "@/stores/chat-store";
import { useSessionStore } from "@/stores/session-store";
import { useTranslation } from "@/i18n";
import type { Message } from "@/types/chat";

interface Props {
  message: Message;
}

export const MessageBubble = memo(function MessageBubble({ message }: Props) {
  const { t } = useTranslation();
  const isUser = message.role === "user";
  const hasReasoning = !isUser && !!message.thinkingContent?.trim();
  const isReasoningVisible = !!message.thinkingVisible;
  const isReasoningExpanded = !!message.thinkingExpanded;

  const toggleThinkingVisible = useChatStore(s => s.toggleThinkingVisible);
  const toggleThinkingExpanded = useChatStore(s => s.toggleThinkingExpanded);

  return (
    <div className={cn("flex gap-3 py-4", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Bot className="w-4 h-4 text-primary" />
        </div>
      )}

      <div className={cn(
        "max-w-[85%] sm:max-w-[80%] rounded-2xl px-5 py-3.5 shadow-sm min-w-0 box-border text-sm overflow-hidden",
        isUser ? "bg-primary text-primary-foreground" : 
        message.status === "error" ? "bg-destructive/10 border-destructive/20 border text-destructive" :
        "bg-muted",
      )}>
        {/* Render Attached Images */}
        {message.images && message.images.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {message.images.map((imgBase64, idx) => (
              <img
                key={idx}
                src={`data:image/jpeg;base64,${imgBase64}`}
                alt={`attachment ${idx + 1}`}
                className="max-h-48 max-w-full object-contain rounded-lg border border-primary/20 bg-background/50"
                loading="lazy"
              />
            ))}
          </div>
        )}

        {/* Message Content */}
        {message.status === "sending" ? (
          <div className="flex items-center gap-2 text-sm h-5">
            <div className="flex gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-current opacity-60 animate-[bounce_1.4s_infinite_.2s]" />
              <div className="w-1.5 h-1.5 rounded-full bg-current opacity-60 animate-[bounce_1.4s_infinite_.4s]" />
              <div className="w-1.5 h-1.5 rounded-full bg-current opacity-60 animate-[bounce_1.4s_infinite_.6s]" />
            </div>
          </div>
        ) : message.status === "streaming" ? (
          <StreamingText text={message.content} />
        ) : (
          <MarkdownRenderer content={message.content} />
        )}

        {hasReasoning && (
          <div className="mt-3 pt-2 border-t border-border/60">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold text-foreground/90 mr-1">
                {t("chat.reasoning_title")}
              </span>
              <button
                type="button"
                onClick={() => toggleThinkingVisible(message.id)}
                className="text-xs font-medium text-primary hover:underline"
              >
                {isReasoningVisible ? t("chat.reasoning_hide") : t("chat.reasoning_show")}
              </button>

              {isReasoningVisible && (
                <button
                  type="button"
                  onClick={() => toggleThinkingExpanded(message.id)}
                  className="text-xs font-medium text-muted-foreground hover:text-foreground hover:underline"
                >
                  {isReasoningExpanded ? t("chat.reasoning_collapse") : t("chat.reasoning_expand")}
                </button>
              )}
            </div>

            <div
              className={cn(
                "mt-2 rounded-xl border border-border/60 bg-background/60 px-3 py-2 relative transition-all duration-200 ease-out",
                isReasoningVisible
                  ? "opacity-100"
                  : "opacity-0 max-h-0 py-0 px-3 border-transparent",
                isReasoningVisible && !isReasoningExpanded && "max-h-28 overflow-hidden",
              )}
              aria-hidden={!isReasoningVisible}
            >
              <p className="text-[11px] leading-relaxed text-muted-foreground whitespace-pre-wrap font-mono">
                {message.thinkingContent}
              </p>
              {isReasoningVisible && !isReasoningExpanded && (
                <div className="pointer-events-none absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-background/95 to-transparent" />
              )}
            </div>
          </div>
        )}

        {message.status === "error" && (
            <div className="mt-2 flex items-center gap-2 text-destructive text-sm pt-2 border-t border-destructive/20">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span className="flex-1 text-xs font-semibold">{message.errorMessage || t("chat.error_default")}</span>
                <RetryButton onClick={() => {
                   const sessionId = useSessionStore.getState().activeSessionId;
                   useChatStore.getState().retryMessage(message.id, sessionId);
                }} />
            </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
          <User className="w-4 h-4 text-primary" />
        </div>
      )}
    </div>
  );
});
