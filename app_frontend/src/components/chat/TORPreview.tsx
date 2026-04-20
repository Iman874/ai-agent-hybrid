import { useState } from "react";
import { FileText, Download, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { exportDocument, downloadBlob } from "@/api/export";
import { useTranslation } from "@/i18n";
import type { TORDocument } from "@/types/api";

interface Props {
  torDocument: TORDocument;
  sessionId: string;
}

export function TORPreview({ torDocument, sessionId }: Props) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);

  const handleExport = async (format: "docx" | "pdf" | "md") => {
    setDownloading(format);
    try {
      const blob = await exportDocument(sessionId, format);
      const ext = format;
      downloadBlob(blob, `TOR_${sessionId.slice(0, 8)}.${ext}`);
    } catch (e) {
      console.error("Export failed:", e);
    } finally {
      setDownloading(null);
    }
  };

  const preview = expanded
    ? torDocument.content
    : torDocument.content.slice(0, 500) + (torDocument.content.length > 500 ? "..." : "");

  return (
    <div className="bg-muted/40 border border-border rounded-xl p-5 my-6 space-y-4 shadow-sm">
      <div className="flex items-center gap-2">
        <FileText className="w-5 h-5 text-primary" />
        <span className="font-semibold text-sm">{t("chat.tor_available")}</span>
        <span className="text-xs text-muted-foreground ml-auto bg-muted px-2 py-0.5 rounded">
          {torDocument.metadata?.word_count ?? 0} {t("format.metric_word_count") || "kata"}
        </span>
      </div>

      <div className="bg-background/80 rounded-md p-4 max-h-[400px] overflow-y-auto">
        <MarkdownRenderer content={preview} />
      </div>

      {torDocument.content.length > 500 && (
        <Button variant="ghost" size="sm" onClick={() => setExpanded(!expanded)} className="w-full text-xs text-muted-foreground">
          {expanded ? <ChevronUp className="w-4 h-4 mr-1" /> : <ChevronDown className="w-4 h-4 mr-1" />}
          {expanded ? t("chat.hide") : t("chat.show_all")}
        </Button>
      )}

      <div className="flex gap-2 pt-3 border-t border-border/60">
        {(["docx", "pdf", "md"] as const).map(fmt => (
          <Button
            key={fmt}
            variant="outline"
            size="sm"
            onClick={() => handleExport(fmt)}
            disabled={downloading !== null}
            className="flex-1 text-xs"
          >
            {downloading === fmt ? (
              <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
            ) : (
              <Download className="w-3.5 h-3.5 mr-1.5" />
            )}
            {t("export.download")} {fmt.toUpperCase()}
          </Button>
        ))}
      </div>
    </div>
  );
}
