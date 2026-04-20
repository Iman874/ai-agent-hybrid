# Task 7: Komponen `StreamingResult.tsx` + Throttle + Partial

## 1. Judul Task
Buat komponen `StreamingResult.tsx` yang menampilkan TOR secara live saat streaming, dengan throttled rendering, cursor berkedip, stop button, dan partial result preservation.

## 2. Deskripsi
Komponen ini adalah jantung UX streaming. Menampilkan teks markdown yang terus bertambah secara real-time, dilengkapi status bar, counter, auto-scroll, tombol stop, dan kemampuan menampilkan partial result saat error/cancel.

## 3. Tujuan Teknis
- Komponen `StreamingResult.tsx` yang reads dari `generate-store`
- **Throttled rendering**: Markdown hanya di-render max 10 FPS (100ms interval)
- **Cursor berkedip**: CSS animation di akhir teks saat streaming aktif
- **Counter**: Jumlah chars + elapsed time
- **Auto-scroll**: `scrollIntoView` saat teks bertambah
- **Stop button**: Memanggil `cancelStream()` dari store
- **Partial result**: Saat error/cancel, teks tetap tampil + warning label
- **Retry button**: Muncul saat error, untuk coba lagi

## 4. Scope
### Yang dikerjakan
- Buat `src/components/generate/StreamingResult.tsx`

### Yang tidak dikerjakan
- Tidak mengubah `GenerateContainer` (task 8)
- Tidak mengubah store (task 6)

## 5. Langkah Implementasi

### Step 1: Buat `src/components/generate/StreamingResult.tsx`

```tsx
import { useState, useEffect, useRef } from "react";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { Button } from "@/components/ui/button";
import { useGenerateStore } from "@/stores/generate-store";
import { useTranslation } from "@/i18n";
import {
  Loader2,
  Square,
  ArrowLeft,
  RotateCcw,
  AlertTriangle,
} from "lucide-react";

export function StreamingResult() {
  const { t } = useTranslation();

  // Store state
  const streamingContent = useGenerateStore(s => s.streamingContent);
  const streamingStatus = useGenerateStore(s => s.streamingStatus);
  const isStreaming = useGenerateStore(s => s.isStreaming);
  const streamError = useGenerateStore(s => s.streamError);
  const cancelStream = useGenerateStore(s => s.cancelStream);
  const clearStreamState = useGenerateStore(s => s.clearStreamState);

  // Throttled rendering: render max setiap 100ms
  const [renderedContent, setRenderedContent] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => {
      setRenderedContent(streamingContent);
    }, 100);
    return () => clearTimeout(timer);
  }, [streamingContent]);

  // Elapsed time counter
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef(Date.now());
  useEffect(() => {
    if (!isStreaming) return;
    startRef.current = Date.now();
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startRef.current) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [isStreaming]);

  // Auto-scroll
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (isStreaming && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [renderedContent, isStreaming]);

  const hasContent = renderedContent.length > 0;
  const isPartial = !isStreaming && streamError && hasContent;

  return (
    <div className="max-w-3xl mx-auto p-4 sm:p-8 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {isStreaming ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin text-primary" />
              <div>
                <h2 className="text-lg font-semibold">
                  {t("generate.streaming_title")}
                </h2>
                {streamingStatus && (
                  <p className="text-xs text-muted-foreground">
                    {streamingStatus}
                  </p>
                )}
              </div>
            </>
          ) : streamError ? (
            <>
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              <div>
                <h2 className="text-lg font-semibold">
                  {t("generate.partial_title")}
                </h2>
                <p className="text-xs text-destructive">{streamError}</p>
              </div>
            </>
          ) : null}
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {isStreaming && (
            <Button
              variant="outline"
              size="sm"
              onClick={cancelStream}
              className="text-destructive border-destructive/50 hover:bg-destructive/10"
            >
              <Square className="w-3.5 h-3.5 mr-1.5 fill-current" />
              {t("generate.stop")}
            </Button>
          )}
          {!isStreaming && (
            <Button variant="ghost" size="icon" onClick={clearStreamState}>
              <ArrowLeft className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Content area */}
      {hasContent && (
        <div className="bg-muted/30 rounded-lg p-6 max-h-[60vh] overflow-y-auto">
          <MarkdownRenderer content={renderedContent} />
          {/* Blinking cursor saat streaming */}
          {isStreaming && (
            <span className="inline-block w-2 h-5 bg-primary animate-pulse ml-0.5 rounded-sm" />
          )}
          <div ref={bottomRef} />
        </div>
      )}

      {/* Empty state saat belum ada content */}
      {!hasContent && isStreaming && (
        <div className="flex items-center justify-center h-40 text-muted-foreground">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      )}

      {/* Partial warning */}
      {isPartial && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-sm text-yellow-600 dark:text-yellow-400">
          {t("generate.partial_warning")}
        </div>
      )}

      {/* Footer: stats + retry */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div>
          {hasContent && (
            <span>
              {renderedContent.length} chars
              {isStreaming && ` · ${elapsed}s`}
            </span>
          )}
        </div>

        {/* Retry button saat error */}
        {streamError && !isStreaming && (
          <Button variant="outline" size="sm" onClick={clearStreamState}>
            <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
            {t("generate.retry")}
          </Button>
        )}
      </div>
    </div>
  );
}
```

## 6. Output yang Diharapkan

**Saat streaming aktif:**
```
┌──────────────────────────────────────────┐
│ ⏳ Menghasilkan TOR...   [Stop Generating]│
│    Menghasilkan TOR...                    │
│                                           │
│ ┌───────────────────────────────────────┐ │
│ │ # TOR Kegiatan Pelatihan AI          │ │
│ │                                       │ │
│ │ ## 1. Latar Belakang                  │ │
│ │ Berdasarkan hasil evaluasi...         │ │
│ │ █                                     │ │
│ └───────────────────────────────────────┘ │
│ 847 chars · 12s                           │
└──────────────────────────────────────────┘
```

**Setelah error/cancel:**
```
┌──────────────────────────────────────────┐
│ ⚠ Hasil belum lengkap           [← Back] │
│   Dibatalkan oleh user                    │
│                                           │
│ ┌───────────────────────────────────────┐ │
│ │ # TOR Kegiatan Pelatihan AI          │ │
│ │ ## 1. Latar Belakang                  │ │
│ │ Berdasarkan hasil evalua              │ │
│ └───────────────────────────────────────┘ │
│                                           │
│ ⚠ Hasil ini belum lengkap karena proses   │
│   dihentikan sebelum selesai.             │
│                                           │
│                              [🔄 Coba Lagi]│
└──────────────────────────────────────────┘
```

## 7. Dependencies
- Task 6 (store streaming state)

## 8. Acceptance Criteria
- [ ] Komponen membaca `streamingContent` dari store
- [ ] **Throttled rendering**: `renderedContent` di-update max setiap 100ms, bukan setiap token
- [ ] **Cursor berkedip**: elemen `<span>` dengan `animate-pulse` saat `isStreaming=true`
- [ ] **Counter**: chars count + elapsed time (seconds)
- [ ] **Auto-scroll**: `scrollIntoView` saat content bertambah
- [ ] **Stop button**: memanggil `cancelStream()`, hanya tampil saat `isStreaming=true`
- [ ] **Partial result**: content tetap tampil saat error/cancel + warning banner
- [ ] **Retry button**: tampil saat error, memanggil `clearStreamState()` (kembali ke form)
- [ ] **Back button**: tampil saat tidak streaming, kembali ke form
- [ ] `npm run build` sukses

## 9. Estimasi
**High** (~2 jam)
