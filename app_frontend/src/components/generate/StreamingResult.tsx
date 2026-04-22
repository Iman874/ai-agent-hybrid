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
  Play,
} from "lucide-react";

export function StreamingResult() {
  const { t } = useTranslation();

  // Store state
  const streamingContent = useGenerateStore(s => s.streamingContent);
  const streamingStatus = useGenerateStore(s => s.streamingStatus);
  const isStreaming = useGenerateStore(s => s.isStreaming);
  const streamError = useGenerateStore(s => s.streamError);
  const streamSessionId = useGenerateStore(s => s.streamSessionId);
  const sourceGenId = useGenerateStore(s => s._sourceGenId);
  const streamSource = useGenerateStore(s => s.streamSource);
  const cancelStream = useGenerateStore(s => s.cancelStream);
  const clearStreamState = useGenerateStore(s => s.clearStreamState);
  const continueGeneration = useGenerateStore(s => s.continueGeneration);
  const retryGeneration = useGenerateStore(s => s.retryGeneration);

  // Throttled rendering: dinamis berdasarkan panjang konten untuk performa
  const [renderedContent, setRenderedContent] = useState("");
  useEffect(() => {
    // Makin panjang markdown, makin berat re-render AST-nya
    const delay = streamingContent.length > 50000 ? 1000 : streamingContent.length > 10000 ? 500 : 150;
    const timer = setTimeout(() => {
      setRenderedContent(streamingContent);
    }, delay);
    return () => clearTimeout(timer);
  }, [streamingContent]);

  // Elapsed time counter
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef<number | null>(null);
  
  useEffect(() => {
    if (!isStreaming) return;
    
    // Inisialisasi startRef hanya saat mulai streaming
    if (!startRef.current) {
        startRef.current = Date.now();
    }
    
    const interval = setInterval(() => {
      if (startRef.current) {
        setElapsed(Math.floor((Date.now() - startRef.current) / 1000));
      }
    }, 1000);
    
    return () => {
        clearInterval(interval);
        startRef.current = null;
    };
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

  // ID yang bisa dipakai untuk continue/retry — prioritas: streamSessionId > sourceGenId
  const effectiveGenId = streamSessionId || sourceGenId;

  // Handler: lanjutkan generate IN-PLACE (tetap di halaman ini)
  const handleContinue = () => {
    if (effectiveGenId && streamingContent) {
      continueGeneration(effectiveGenId, streamingContent);
    }
  };

  // Handler: generate ulang dari awal
  const handleRetry = () => {
    if (effectiveGenId) {
      retryGeneration(effectiveGenId);
    } else {
      clearStreamState();
    }
  };

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
                {streamSource === "chat" && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {t("generate.source_chat") || "Source: Chat session"}
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
        <div className="bg-muted/30 rounded-lg p-6 max-h-[60vh] overflow-y-auto relative">
          <MarkdownRenderer content={renderedContent} />
          {/* Blinking cursor saat streaming */}
          {isStreaming && (
            <span className="inline-block w-2 h-5 bg-primary animate-pulse ml-0.5 rounded-sm align-middle" />
          )}
          <div ref={bottomRef} className="h-4" />
        </div>
      )}

      {/* Empty state saat belum ada content */}
      {!hasContent && isStreaming && (
        <div className="flex items-center justify-center h-40 text-muted-foreground">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      )}

      {/* Error state tanpa content (retry/continue langsung gagal) */}
      {!hasContent && !isStreaming && streamError && (
        <div className="flex flex-col items-center justify-center text-center text-muted-foreground space-y-3 py-10">
          <AlertTriangle className="w-10 h-10 text-yellow-500/60" />
          <div className="space-y-1">
            <p className="font-medium">{t("generate.source_unavailable")}</p>
            <p className="text-xs text-destructive max-w-sm mx-auto">{streamError}</p>
          </div>
          <Button variant="outline" className="mt-2" onClick={clearStreamState}>
            {t("generate.retry_upload")}
          </Button>
        </div>
      )}

      {/* Partial warning */}
      {isPartial && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-sm text-yellow-600 dark:text-yellow-400">
          {t("generate.partial_warning")}
        </div>
      )}

      {/* Footer: stats + action buttons */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div>
          {hasContent && (
            <span>
              {renderedContent.length} chars
              {isStreaming && ` · ${elapsed}s`}
            </span>
          )}
        </div>

        {/* Action buttons saat error/cancel */}
        {streamError && !isStreaming && (
          <div className="flex gap-2">
            {/* Tombol sekunder: Generate Ulang */}
            <Button variant="outline" size="sm" onClick={handleRetry}>
              <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
              {t("generate.retry_generate")}
            </Button>
            {/* Tombol utama: Lanjutkan Generate (hanya kalau ada partial content) */}
            {isPartial && effectiveGenId && (
              <Button variant="default" size="sm" onClick={handleContinue}>
                <Play className="w-3.5 h-3.5 mr-1.5" />
                {t("generate.continue_generate")}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
