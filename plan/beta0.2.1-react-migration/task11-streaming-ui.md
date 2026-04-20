# Task 11: Streaming UI — ThinkingIndicator + StreamingText

## 1. Judul Task

Implementasi komponen visual untuk streaming: thinking indicator dan token-by-token text render

## 2. Deskripsi

Membuat komponen yang menampilkan status thinking AI (animasi "Sedang berpikir...") dan teks response yang muncul token-by-token saat streaming aktif.

## 3. Tujuan Teknis

- `ThinkingIndicator.tsx` — animasi pulsing + teks thinking
- `StreamingText.tsx` — render partial text dengan cursor blink
- Update `ChatArea.tsx` — integrate streaming state

## 4. Scope

**Yang dikerjakan:**
- `src/components/chat/ThinkingIndicator.tsx`
- `src/components/chat/StreamingText.tsx`
- Update `src/components/chat/ChatArea.tsx`

**Yang tidak dikerjakan:**
- WS logic (task 10)
- Retry (task 12)

## 5. Langkah Implementasi

### 5.1 `ThinkingIndicator.tsx`

```tsx
import { Brain, Loader2 } from "lucide-react";

export function ThinkingIndicator({ text }: { text: string }) {
  return (
    <div className="flex gap-3 py-4">
      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center animate-pulse flex-shrink-0">
        <Brain className="w-4 h-4 text-primary" />
      </div>
      <div className="bg-muted rounded-2xl px-4 py-3 max-w-[80%]">
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span>Sedang berpikir...</span>
        </div>
        {text && (
          <p className="text-xs text-muted-foreground/60 font-mono whitespace-pre-wrap">
            {text}
          </p>
        )}
      </div>
    </div>
  );
}
```

### 5.2 `StreamingText.tsx`

```tsx
export function StreamingText({ text }: { text: string }) {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <span>{text}</span>
      <span className="inline-block w-0.5 h-4 bg-foreground animate-pulse ml-0.5" />
    </div>
  );
}
```

### 5.3 Update `ChatArea.tsx`

Add thinking + streaming bubbles after message list:

```tsx
{stream.isThinking && <ThinkingIndicator text={stream.thinkingText} />}
{stream.isStreaming && !stream.isThinking && stream.partialContent && (
  <MessageBubble
    message={{
      id: "streaming",
      role: "assistant",
      content: stream.partialContent,
      status: "streaming",
      timestamp: Date.now(),
    }}
  />
)}
```

Update `MessageBubble.tsx` to use `StreamingText` when `status === "streaming"`.

## 6. Output yang Diharapkan

- Thinking: pulsing brain icon + "Sedang berpikir..." + optional thinking text
- Streaming: tokens accumulate with blinking cursor
- Done: cursor disappears, full markdown rendered

## 7. Dependencies

- Task 07 (ChatArea, MessageBubble)
- Task 10 (WS integration)

## 8. Acceptance Criteria

- [ ] Thinking indicator muncul saat thinking_start
- [ ] Thinking indicator hilang saat thinking_end
- [ ] Token-by-token text accumulation berfungsi
- [ ] Blinking cursor selama streaming
- [ ] Cursor hilang saat streaming selesai
- [ ] Smooth auto-scroll selama streaming

## 9. Estimasi

Medium (1-2 jam)
