import { useState } from "react";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Download, Loader2, XCircle, RotateCcw, Play } from "lucide-react";
import { exportDocument, downloadBlob } from "@/api/export";
import { useTranslation } from "@/i18n";
import { useGenerateStore } from "@/stores/generate-store";
import type { GenerateResponse, TORMetadata } from "@/types/api";
import type { DocGenDetail } from "@/types/generate";

interface Props {
  result?: GenerateResponse;
  resultFromHistory?: DocGenDetail;
  onBack: () => void;
}

export function GenerateResult({ result, resultFromHistory, onBack }: Props) {
  const { t } = useTranslation();
  const [downloading, setDownloading] = useState<string | null>(null);
  
  const retryGeneration = useGenerateStore(s => s.retryGeneration);
  const continueGeneration = useGenerateStore(s => s.continueGeneration);

  // Normalize data from either source
  const sessionId = result?.session_id ?? resultFromHistory?.id ?? "";
  const torContent = result?.tor_document?.content ?? resultFromHistory?.tor_content ?? "";
  const metadata: TORMetadata | null = result?.tor_document?.metadata ?? resultFromHistory?.metadata ?? null;
  const filename = resultFromHistory?.filename;

  const handleExport = async (format: "docx" | "pdf" | "md") => {
    setDownloading(format);
    try {
      const blob = await exportDocument(sessionId, format);
      const name = filename
        ? `${filename.replace(/\.[^.]+$/, "")}.${format}`
        : `TOR_${sessionId.slice(0, 8)}.${format}`;
      downloadBlob(blob, name);
    } catch (e) {
      console.error("Export failed:", e);
    } finally {
      setDownloading(null);
    }
  };

  const handleRetry = () => {
    if (resultFromHistory?.id) {
      retryGeneration(resultFromHistory.id);
    }
  };

  const handleContinue = () => {
    if (resultFromHistory?.id && torContent) {
      continueGeneration(resultFromHistory.id, torContent);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-4 sm:p-8 space-y-4">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={onBack}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h2 className="text-lg font-semibold">{t("generate.result_title")}</h2>
          {filename && (
            <p className="text-xs text-muted-foreground">{filename}</p>
          )}
        </div>
      </div>

      <div className="bg-muted/30 rounded-lg p-6 min-h-[150px]">
        {torContent ? (
          <MarkdownRenderer content={torContent} />
        ) : (
          <div className="flex flex-col items-center justify-center text-center h-full text-muted-foreground space-y-3 py-6">
            <XCircle className="w-10 h-10 text-muted-foreground/50 opacity-50" />
            <div className="space-y-1">
              <p className="font-medium">{t("generate.no_content") ?? "Result unavailable"}</p>
              {resultFromHistory?.error_message && (
                <p className="text-sm text-destructive max-w-sm mx-auto">{resultFromHistory.error_message}</p>
              )}
            </div>
            
            {(resultFromHistory?.status === "failed" || resultFromHistory?.status === "processing") && (
              <div className="flex gap-2 mt-4 flex-wrap justify-center">
                <Button variant="outline" onClick={onBack}>
                  {t("generate.retry_upload") ?? "Go Back & Retry Upload"}
                </Button>
                {resultFromHistory?.status === "failed" && (
                  <Button variant="default" onClick={handleRetry}>
                    <RotateCcw className="w-4 h-4 mr-1.5" />
                    {t("generate.retry_generate") ?? "Regenerate"}
                  </Button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {resultFromHistory?.status === "failed" && torContent && (
        <div className="flex gap-2 justify-end mb-4">
          <Button variant="outline" onClick={handleRetry}>
            <RotateCcw className="w-4 h-4 mr-1.5" />
            {t("generate.retry_generate") ?? "Regenerate"}
          </Button>
          <Button variant="default" onClick={handleContinue}>
            <Play className="w-4 h-4 mr-1.5" />
            {t("generate.continue_generate") ?? "Continue"}
          </Button>
        </div>
      )}

      {/* Export buttons */}
      {torContent && (
      <div className="flex gap-2">
        {(["docx", "pdf", "md"] as const).map(fmt => (
          <Button
            key={fmt}
            variant="outline"
            size="sm"
            onClick={() => handleExport(fmt)}
            disabled={downloading !== null}
          >
            {downloading === fmt ? (
              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
            ) : (
              <Download className="w-4 h-4 mr-1" />
            )}
            {fmt.toUpperCase()}
          </Button>
        ))}
      </div>
      )}

      {metadata && (
        <p className="text-xs text-muted-foreground">
          {metadata.word_count} {t("generate.words_label")} · 
          {metadata.generation_time_ms}ms · 
          {metadata.generated_by}
        </p>
      )}
    </div>
  );
}
