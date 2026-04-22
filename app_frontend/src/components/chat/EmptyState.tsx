import { Sparkles } from "lucide-react";
import { useTranslation } from "@/i18n";

export function EmptyState() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-5">
      <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center">
        <Sparkles className="w-8 h-8 text-primary opacity-70" />
      </div>
      <div className="text-center space-y-1.5 max-w-sm">
        <h2 className="text-lg font-medium text-foreground">{t("chat.empty_title")}</h2>
        <p className="text-sm">
          {t("chat.empty_desc")}
        </p>
      </div>
    </div>
  );
}
