# Task 07: Chat Interface — ChatArea, ChatInput, MessageBubble, EmptyState

## 1. Judul Task

Implementasi chat interface: area pesan, input bar, message bubbles, empty state, markdown renderer

## 2. Deskripsi

Membuat core chat UI yang mirip ChatGPT: message list yang scrollable, bubble per pesan (user/assistant), input bar dengan Enter=kirim, empty state saat belum ada pesan, dan markdown rendering untuk response AI.

## 3. Tujuan Teknis

- `ChatArea.tsx` — scrollable message list
- `ChatInput.tsx` — textarea + send button
- `MessageBubble.tsx` — user/assistant bubble dengan markdown
- `EmptyState.tsx` — welcome screen
- `MarkdownRenderer.tsx` — render AI response markdown

## 4. Scope

**Yang dikerjakan:**
- `src/components/chat/ChatArea.tsx`
- `src/components/chat/ChatInput.tsx`
- `src/components/chat/MessageBubble.tsx`
- `src/components/chat/EmptyState.tsx`
- `src/components/shared/MarkdownRenderer.tsx`
- `src/hooks/useAutoScroll.ts`
- Update `AppLayout.tsx` — integrate ChatArea

**Yang tidak dikerjakan:**
- Streaming UI / ThinkingIndicator (task 11)
- Retry button (task 12)
- TOR preview (task 14)

## 5. Langkah Implementasi

### 5.1 `src/hooks/useAutoScroll.ts`

```tsx
import { useEffect, useRef } from "react";

export function useAutoScroll(deps: unknown[]) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    // Only auto-scroll if user is near bottom
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    if (isNearBottom) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, deps);

  return ref;
}
```

### 5.2 `src/components/shared/MarkdownRenderer.tsx`

```tsx
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function MarkdownRenderer({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      className="prose prose-sm dark:prose-invert max-w-none"
      components={{
        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
        ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
        code: ({ className, children, ...props }) => {
          const isInline = !className;
          return isInline ? (
            <code className="bg-muted px-1 py-0.5 rounded text-xs" {...props}>{children}</code>
          ) : (
            <pre className="bg-muted p-3 rounded-md overflow-x-auto text-xs mb-2">
              <code {...props}>{children}</code>
            </pre>
          );
        },
      }}
    />
  );
}
```

### 5.3 `src/components/chat/EmptyState.tsx`

```tsx
import { MessageSquare } from "lucide-react";

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-4">
      <MessageSquare className="w-16 h-16 opacity-30" />
      <div className="text-center space-y-1">
        <h2 className="text-lg font-medium text-foreground">Ceritakan kebutuhan TOR Anda</h2>
        <p className="text-sm">Mulai chat untuk menyusun Term of Reference.</p>
      </div>
    </div>
  );
}
```

### 5.4 `src/components/chat/MessageBubble.tsx`

```tsx
import { memo } from "react";
import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import type { Message } from "@/types/chat";

interface Props {
  message: Message;
}

export const MessageBubble = memo(function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3 py-4", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
          <Bot className="w-4 h-4 text-primary" />
        </div>
      )}

      <div className={cn(
        "max-w-[80%] rounded-2xl px-4 py-3",
        isUser ? "bg-primary text-primary-foreground" : "bg-muted",
      )}>
        {message.status === "sending" ? (
          <div className="flex items-center gap-2 text-sm">
            <div className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
            Mengirim...
          </div>
        ) : (
          <MarkdownRenderer content={message.content} />
        )}

        {/* Error + retry placeholder — task 12 */}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-foreground/10 flex items-center justify-center flex-shrink-0">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
});
```

### 5.5 `src/components/chat/ChatInput.tsx`

```tsx
import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useChatStore } from "@/stores/chat-store";
import { useSessionStore } from "@/stores/session-store";

export function ChatInput() {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
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
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-border p-4 bg-background">
      <div className="relative max-w-3xl mx-auto">
        <Textarea
          ref={textareaRef}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Tanyakan apa saja..."
          className="min-h-[44px] max-h-[200px] resize-none pr-12"
          rows={1}
        />
        <Button
          size="icon"
          variant="ghost"
          className="absolute right-2 bottom-2 h-8 w-8"
          onClick={handleSend}
          disabled={!text.trim() || isStreaming}
        >
          {isStreaming ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </div>
    </div>
  );
}
```

### 5.6 `src/components/chat/ChatArea.tsx`

```tsx
import { useChatStore } from "@/stores/chat-store";
import { useAutoScroll } from "@/hooks/useAutoScroll";
import { MessageBubble } from "./MessageBubble";
import { EmptyState } from "./EmptyState";
import { ChatInput } from "./ChatInput";

export function ChatArea() {
  const messages = useChatStore(s => s.messages);
  const isStreaming = useChatStore(s => s.stream.isStreaming);
  const scrollRef = useAutoScroll([messages.length, isStreaming]);

  return (
    <div className="flex flex-col h-full">
      {/* Message list */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 ? (
            <EmptyState />
          ) : (
            messages.map(msg => (
              <MessageBubble key={msg.id} message={msg} />
            ))
          )}
        </div>
      </div>

      {/* Input */}
      <ChatInput />
    </div>
  );
}
```

### 5.7 Update `AppLayout.tsx`

Replace chat placeholder:
```tsx
import { ChatArea } from "@/components/chat/ChatArea";

// In render:
{activeTool === "chat" ? (
  <ChatArea />
) : (
  <div className="...">Generate from document (task 13)</div>
)}
```

## 6. Output yang Diharapkan

- Empty state: icon + "Ceritakan kebutuhan TOR Anda"
- Kirim pesan → bubble user (kanan, primary color)
- Response AI → bubble assistant (kiri, muted bg, markdown rendered)
- Enter = kirim, Shift+Enter = newline
- Auto-scroll ke bawah saat pesan baru
- Textarea auto-resize

## 7. Dependencies

- Task 04 (chat store)
- Task 05 (layout)

## 8. Acceptance Criteria

- [ ] Empty state tampil saat tidak ada pesan
- [ ] Kirim pesan → bubble user muncul
- [ ] Response AI ter-render dengan markdown (bold, list, code)
- [ ] Enter = kirim, Shift+Enter = newline
- [ ] Auto-scroll ke bottom
- [ ] Textarea auto-resize
- [ ] `React.memo` pada MessageBubble untuk performa
- [ ] `npm run build` tanpa error

## 9. Estimasi

High (2-3 jam)
