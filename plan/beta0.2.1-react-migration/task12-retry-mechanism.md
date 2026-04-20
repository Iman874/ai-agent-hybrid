# Task 12: Retry Mechanism — Error State + Retry Button

## 1. Judul Task

Implementasi error state per-message dan tombol retry untuk pesan yang gagal

## 2. Deskripsi

Menambahkan error state visual pada pesan assistant yang gagal, dengan tombol "Coba lagi" yang mengirim ulang pesan user sebelumnya. Ini fitur kritis yang tidak ada di Streamlit.

## 3. Tujuan Teknis

- Error state visual di `MessageBubble`
- `RetryButton.tsx` component
- `retryMessage()` action di chat store (sudah ada — verify)
- Error dari WS dan HTTP ter-handle

## 4. Scope

**Yang dikerjakan:**
- `src/components/chat/RetryButton.tsx`
- Update `src/components/chat/MessageBubble.tsx` — error UI
- Verify `retryMessage` di chat-store

**Yang tidak dikerjakan:**
- Auto-retry (hanya manual retry via button)
- Retry limit/counter

## 5. Langkah Implementasi

### 5.1 `src/components/chat/RetryButton.tsx`

```tsx
import { RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  onClick: () => void;
}

export function RetryButton({ onClick }: Props) {
  return (
    <Button
      variant="ghost"
      size="sm"
      className="text-destructive hover:text-destructive h-7 text-xs"
      onClick={onClick}
    >
      <RotateCcw className="w-3 h-3 mr-1" />
      Coba lagi
    </Button>
  );
}
```

### 5.2 Update `MessageBubble.tsx`

Add error state rendering after message content:

```tsx
import { AlertCircle } from "lucide-react";
import { RetryButton } from "./RetryButton";
import { useChatStore } from "@/stores/chat-store";
import { useSessionStore } from "@/stores/session-store";

// Inside MessageBubble:
{message.status === "error" && (
  <div className="mt-2 flex items-center gap-2 text-destructive text-sm">
    <AlertCircle className="w-4 h-4 flex-shrink-0" />
    <span className="flex-1 text-xs">{message.errorMessage || "Gagal mendapat respons"}</span>
    <RetryButton onClick={() => {
      const sessionId = useSessionStore.getState().activeSessionId;
      useChatStore.getState().retryMessage(message.id, sessionId);
    }} />
  </div>
)}
```

## 6. Output yang Diharapkan

Error state:
```
[Bot] ⚠ Gagal mendapat respons  [↻ Coba lagi]
```

Klik "Coba lagi" → pesan error dihapus → pesan user dikirim ulang.

## 7. Dependencies

- Task 07 (MessageBubble)
- Task 04 (retryMessage action)

## 8. Acceptance Criteria

- [ ] Pesan error tampilkan icon warning + pesan error
- [ ] Tombol "Coba lagi" muncul pada pesan error
- [ ] Klik retry → pesan error hilang → pesan dikirim ulang
- [ ] Retry berfungsi via HTTP dan WS
- [ ] Multiple errors bisa di-retry secara independen

## 9. Estimasi

Medium (1 jam)
