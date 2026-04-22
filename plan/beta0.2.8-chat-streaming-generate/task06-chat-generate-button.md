# Task 06 — Frontend: Tombol Manual "Buat TOR" di Chat

## 1. Judul Task

Menambahkan tombol manual "Buat TOR" di chat sebagai fallback jika auto-trigger gagal atau user ingin secara eksplisit memulai generate.

## 2. Deskripsi

Auto-trigger di task 04 akan menangani kasus *happy path*. Namun ada skenario di mana user perlu memulai generate secara manual:
- Auto-generate gagal di tengah jalan (error/timeout), user ingin re-trigger dari chat.
- Session sudah berstatus `READY` dari sesi sebelumnya yang tidak di-generate.
- User membuka session lama yang sudah pernah `READY_TO_GENERATE`.

Task ini menambahkan komponen button di area chat yang muncul saat `sessionState.status === "READY"` atau `"READY_TO_GENERATE"`.

## 3. Tujuan Teknis

- Menampilkan tombol "Buat TOR Sekarang" di area chat (misalnya di bawah pesan terakhir atau sebagai banner di bawah chat area).
- Klik tombol → panggil `generateFromChatStream(sessionId, mode)` dan switch tab.

## 4. Scope

### Yang dikerjakan
- Membuat komponen baru `ChatGeneratePrompt.tsx` di `src/components/chat/`.
- Menampilkan komponen ini di `ChatArea.tsx` berdasarkan kondisi `sessionState`.

### Yang tidak dikerjakan
- Perubahan backend.
- Perubahan logic auto-trigger (tetap di task 04).

## 5. Langkah Implementasi

### Step 1: Buat `src/components/chat/ChatGeneratePrompt.tsx`

```tsx
import { Button } from "@/components/ui/button";
import { FileText } from "lucide-react";
import { useGenerateStore } from "@/stores/generate-store";
import { useUIStore } from "@/stores/ui-store";
import { useSessionStore } from "@/stores/session-store";
import { useTranslation } from "@/i18n";

interface ChatGeneratePromptProps {
  sessionId: string;
  status: string; // "READY_TO_GENERATE" | "ESCALATE_TO_GEMINI" | "READY"
}

export function ChatGeneratePrompt({ sessionId, status }: ChatGeneratePromptProps) {
  const { t } = useTranslation();
  const isStreaming = useGenerateStore(s => s.isStreaming);

  const handleGenerate = () => {
    const mode = status === "ESCALATE_TO_GEMINI" ? "escalation" : "standard";

    // Switch tab ke generate
    useUIStore.getState().setActiveTool("generate_doc");

    // Mulai streaming
    setTimeout(() => {
      useGenerateStore.getState().generateFromChatStream(sessionId, mode);
    }, 100);
  };

  if (isStreaming) return null; // Jangan tampilkan jika sudah streaming

  return (
    <div className="flex justify-center py-3">
      <Button
        variant="default"
        size="sm"
        onClick={handleGenerate}
        className="gap-2"
      >
        <FileText className="w-4 h-4" />
        Buat TOR Sekarang
      </Button>
    </div>
  );
}
```

### Step 2: Integrasikan di `ChatArea.tsx`

Buka `src/components/chat/ChatArea.tsx` dan tambahkan:

1. Import komponen:
```typescript
import { ChatGeneratePrompt } from "./ChatGeneratePrompt";
import { useChatStore } from "@/stores/chat-store";
import { useSessionStore } from "@/stores/session-store";
```

2. Render komponen setelah daftar pesan, jika kondisi memenuhi:
```tsx
{sessionState && 
 (sessionState.status === "READY_TO_GENERATE" || 
  sessionState.status === "READY" ||
  sessionState.status === "ESCALATE_TO_GEMINI") && 
 activeSessionId && (
  <ChatGeneratePrompt 
    sessionId={activeSessionId} 
    status={sessionState.status} 
  />
)}
```

## 6. Output yang Diharapkan

### UI ketika session sudah READY tapi belum di-generate:
```
[Pesan-pesan chat...]
[AI] Semua informasi sudah lengkap!

    ┌─────────────────────────┐
    │ 📄 Buat TOR Sekarang    │
    └─────────────────────────┘
```

### Setelah klik:
- Tab berpindah ke Generate.
- `StreamingResult` tampil dengan token mengalir.

## 7. Dependencies

- **Task 03** harus selesai (`generateFromChatStream` tersedia).

## 8. Acceptance Criteria

- [ ] Komponen `ChatGeneratePrompt` muncul hanya saat `sessionState.status` adalah `READY_TO_GENERATE`, `READY`, atau `ESCALATE_TO_GEMINI`.
- [ ] Klik tombol → `generateFromChatStream()` terpanggil.
- [ ] Klik tombol → UI berpindah ke tab `generate_doc`.
- [ ] Tombol tidak tampil saat `isStreaming === true`.
- [ ] Tidak ada regresi pada chat flow biasa (status `NEED_MORE_INFO`).
- [ ] `npm run build` → zero errors.

## 9. Estimasi

**Low** — ~45 menit kerja.
