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
  const isGenerating = useGenerateStore(s => s.isGenerating);
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

  // View: Showing immediate generate result
  if (lastResponse) {
    return (
      <GenerateResult
        result={lastResponse}
        onBack={clearLastResponse}
      />
    );
  }

  // View: Streaming aktif ATAU error/cancel (dengan atau tanpa content)
  if (isStreaming || streamError) {
    return <StreamingResult />;
  }

  // View: Generating spinner
  if (isGenerating) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="text-sm">{t("generate.processing")}</p>
      </div>
    );
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
