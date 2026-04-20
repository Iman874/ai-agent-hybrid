import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useChatStore } from "@/stores/chat-store";
import { useSessionStore } from "@/stores/session-store";
import { useTranslation } from "@/i18n";

export function ChatInput() {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Use specific selectors to avoid re-renders
  const sendMessage = useChatStore(s => s.sendMessage);
  const isStreaming = useChatStore(s => s.stream.isStreaming);
  const activeSessionId = useSessionStore(s => s.activeSessionId);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 200) + "px";
    }
  }, [text]);

  const handleSend = () => {
    if (!text.trim() || isStreaming) return;
    sendMessage(text.trim(), activeSessionId);
    setText("");
    
    // Reset height
    if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 bg-background px-4 sm:px-8 max-w-4xl mx-auto w-full">
      <div className="relative shadow-sm rounded-xl border bg-background focus-within:ring-1 focus-within:ring-ring transition-shadow">
        <Textarea
          ref={textareaRef}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t("chat.input_placeholder")}
          className="min-h-[52px] max-h-[200px] resize-none pr-12 border-0 focus-visible:ring-0 shadow-none rounded-xl py-3.5 text-[0.95rem] leading-relaxed"
          rows={1}
        />
        <div className="absolute right-2 bottom-2">
            <Button
              size="icon"
              className="h-8 w-8 rounded-lg"
              onClick={handleSend}
              disabled={!text.trim() || isStreaming}
            >
              {isStreaming ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4 ml-0.5" />
              )}
            </Button>
        </div>
      </div>
      <p className="text-center text-[0.65rem] text-muted-foreground mt-2">
        {t("chat.disclaimer")}
      </p>
    </div>
  );
}
