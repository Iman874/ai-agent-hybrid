import { useEffect } from "react";
import { useGenerateStore } from "@/stores/generate-store";
import { useTranslation } from "@/i18n";
import { Button } from "@/components/ui/button";
import { Eye, Trash2, Loader2, CheckCircle, XCircle, Clock } from "lucide-react";

export function GenerateHistory() {
  const { t } = useTranslation();
  const history = useGenerateStore(s => s.history);
  const isLoading = useGenerateStore(s => s.isLoadingHistory);
  const fetchHistory = useGenerateStore(s => s.fetchHistory);
  const viewResult = useGenerateStore(s => s.viewResult);
  const deleteGeneration = useGenerateStore(s => s.deleteGeneration);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  if (isLoading) {
    return (
      <div className="py-8 flex justify-center text-muted-foreground">
        <Loader2 className="w-5 h-5 animate-spin" />
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-6">
        {t("generate.no_history")}
      </p>
    );
  }

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "failed": return <XCircle className="w-4 h-4 text-destructive" />;
      default: return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
        {t("generate.history_title")}
      </h3>
      <div className="border rounded-lg divide-y bg-background/50 backdrop-blur">
        {history.map(item => (
          <div key={item.id} className="flex items-center justify-between px-4 py-3 hover:bg-muted/30 transition">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              {statusIcon(item.status)}
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">{item.filename}</p>
                <p className="text-xs text-muted-foreground">
                  {item.style_name ?? "-"} &middot; {item.word_count ? `${item.word_count} ${t("generate.words_label")}` : "-"} &middot; {formatDate(item.created_at)}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1 flex-shrink-0 ml-2">
              {item.status === "completed" && (
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => viewResult(item.id)}>
                  <Eye className="w-4 h-4" />
                </Button>
              )}
              <Button
                variant="ghost" size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-destructive transition-colors"
                onClick={() => {
                   if (confirm(t("generate.delete_confirm"))) {
                     deleteGeneration(item.id);
                   }
                }}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
