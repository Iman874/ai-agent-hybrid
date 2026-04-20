import { useState } from "react";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Download, Loader2 } from "lucide-react";
import { exportDocument, downloadBlob } from "@/api/export";
import { useTranslation } from "@/i18n";
import type { GenerateResponse } from "@/types/api";

interface Props {
  result: GenerateResponse;
  onBack: () => void;
}

export function GenerateResult({ result, onBack }: Props) {
  const { t } = useTranslation();
  const [downloading, setDownloading] = useState<string | null>(null);

  const handleExport = async (format: "docx" | "pdf" | "md") => {
    setDownloading(format);
    try {
      const blob = await exportDocument(result.session_id, format);
      const ext = format;
      downloadBlob(blob, `TOR_${result.session_id.slice(0, 8)}.${ext}`);
    } catch (e) {
      console.error("Export failed:", e);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-4 sm:p-8 space-y-4">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={onBack}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <h2 className="text-lg font-semibold">{t("generate.result_title")}</h2>
      </div>

      <div className="bg-muted/30 rounded-lg p-6">
        <MarkdownRenderer content={result.tor_document.content} />
      </div>

      {/* Export buttons */}
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

      <p className="text-xs text-muted-foreground">
        {result.tor_document.metadata.word_count} kata · 
        {result.tor_document.metadata.generation_time_ms}ms · 
        {result.tor_document.metadata.generated_by}
      </p>
    </div>
  );
}
