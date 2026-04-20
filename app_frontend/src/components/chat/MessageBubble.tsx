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
