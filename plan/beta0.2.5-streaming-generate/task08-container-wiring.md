# Task 8: Container + UploadForm Wiring

## 1. Judul Task
Update `GenerateContainer.tsx` dan `UploadForm.tsx` untuk mendukung view state streaming dan memanggil stream API.

## 2. Deskripsi
Container mendapat dua view state baru: `streaming` (saat stream aktif) dan `partial` (saat error/cancel tapi ada content). UploadForm diubah agar memanggil `generateFromDocStream()` dari store, bukan `generateFromDoc()`.

## 3. Tujuan Teknis
- `GenerateContainer.tsx`: 5 view states (idle, streaming, partial, viewing, loading)
- `UploadForm.tsx`: memanggil `generateFromDocStream` dari store
- Transisi otomatis: setelah `done` event + session_id tersedia → auto-view result

## 4. Scope
### Yang dikerjakan
- Modifikasi `src/components/generate/GenerateContainer.tsx`
- Modifikasi `src/components/generate/UploadForm.tsx`

### Yang tidak dikerjakan
- Tidak mengubah `StreamingResult.tsx` (task 7)
- Tidak mengubah store (task 6)

## 5. Langkah Implementasi

### Step 1: Update `GenerateContainer.tsx`

```tsx
import { useEffect } from "react";
import { useGenerateStore } from "@/stores/generate-store";
import { UploadForm } from "./UploadForm";
import { GenerateResult } from "./GenerateResult";
import { GenerateHistory } from "./GenerateHistory";
import { StreamingResult } from "./StreamingResult";
import { Loader2 } from "lucide-react";
import { useTranslation } from "@/i18n";

export function GenerateContainer() {
  const { t } = useTranslation();
  const isStreaming = useGenerateStore(s => s.isStreaming);
  const streamingContent = useGenerateStore(s => s.streamingContent);
  const streamError = useGenerateStore(s => s.streamError);
  const streamSessionId = useGenerateStore(s => s.streamSessionId);
  const lastResponse = useGenerateStore(s => s.lastGenerateResponse);
  const activeResult = useGenerateStore(s => s.activeResult);
  const isLoadingResult = useGenerateStore(s => s.isLoadingResult);
  const clearActiveResult = useGenerateStore(s => s.clearActiveResult);
  const clearLastResponse = useGenerateStore(s => s.clearLastResponse);
  const viewResult = useGenerateStore(s => s.viewResult);

  // Auto-transition: setelah stream selesai dan session_id tersedia, view result
  useEffect(() => {
    if (!isStreaming && streamSessionId && !streamError) {
      // Stream selesai sukses → view detail result setelah delay kecil
      const timer = setTimeout(() => {
        viewResult(streamSessionId);
        // Reset stream state setelah transisi
        useGenerateStore.getState().clearStreamState();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [isStreaming, streamSessionId, streamError, viewResult]);

  // View: Loading detail from history
  if (isLoadingResult) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  // View: Showing result from history click
  if (activeResult) {
    return (
      <GenerateResult
        resultFromHistory={activeResult}
        onBack={clearActiveResult}
      />
    );
  }

  // View: Showing immediate generate result (fallback blocking)
  if (lastResponse) {
    return (
      <GenerateResult
        result={lastResponse}
        onBack={clearLastResponse}
      />
    );
  }

  // View: Streaming aktif ATAU partial result (error/cancel tapi ada content)
  if (isStreaming || (streamError && streamingContent)) {
    return <StreamingResult />;
  }

  // View: Idle — upload form + history
  return (
    <div className="space-y-8 pb-8">
      <UploadForm />
      <div className="max-w-3xl mx-auto px-4 sm:px-8">
        <GenerateHistory />
      </div>
    </div>
  );
}
```

### Step 2: Update `UploadForm.tsx`

Ganti `generateFromDoc` menjadi `generateFromDocStream`:

```tsx
import { useState, useRef } from "react";
import { Upload, FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useGenerateStore } from "@/stores/generate-store";
import { useTranslation } from "@/i18n";

export function UploadForm() {
  const { t } = useTranslation();
  const generateFromDocStream = useGenerateStore(s => s.generateFromDocStream);
  const isStreaming = useGenerateStore(s => s.isStreaming);
  
  const [file, setFile] = useState<File | null>(null);
  const [context, setContext] = useState("");
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    if (!file) return;
    setError("");
    try {
      await generateFromDocStream(file, context || undefined);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("common.error"));
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8 space-y-6">
      {/* ... same JSX as before ... */}
      
      <Button 
        onClick={handleSubmit} 
        disabled={!file || isStreaming}
        className="w-full"
      >
        {isStreaming ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
        {isStreaming ? t("generate.processing") : t("generate.submit")}
      </Button>
    </div>
  );
}
```

## 6. Output yang Diharapkan

**Flow:**
1. User di idle → melihat UploadForm + History
2. User klik Generate → `generateFromDocStream()` dipanggil
3. Container mendeteksi `isStreaming=true` → render `StreamingResult`
4. Streaming selesai → `streamSessionId` tersedia → auto `viewResult(id)`
5. Container mendeteksi `activeResult` → render `GenerateResult`
6. User klik Back → kembali ke idle

**Error flow:**
1. Streaming error/cancel → `streamError` set + `streamingContent` preserved
2. Container mendeteksi `streamError && streamingContent` → render `StreamingResult` (partial mode)
3. User klik "Coba Lagi" → `clearStreamState()` → kembali ke idle

## 7. Dependencies
- Task 7 (`StreamingResult` component)
- Task 6 (store streaming actions)

## 8. Acceptance Criteria
- [ ] Container renders `StreamingResult` saat `isStreaming=true`
- [ ] Container renders `StreamingResult` saat `streamError && streamingContent` (partial)
- [ ] Auto-transition: `done` → `viewResult(sessionId)` → `GenerateResult`
- [ ] `UploadForm` memanggil `generateFromDocStream` (bukan `generateFromDoc`)
- [ ] Generate button disabled saat `isStreaming=true`
- [ ] Existing flows (history view, blocking result) masih berfungsi
- [ ] `npm run build` sukses

## 9. Estimasi
**Medium** (~45 menit)
