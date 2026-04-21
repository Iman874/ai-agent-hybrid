import { useModelStore } from "@/stores/model-store";
import { useTranslation } from "@/i18n";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

export function ModelSelector() {
  const { t } = useTranslation();
  const models = useModelStore(s => s.models);
  const activeModelId = useModelStore(s => s.activeModelId);
  const setActiveModel = useModelStore(s => s.setActiveModel);

  if (models.length === 0) {
    return (
      <p className="text-xs text-destructive px-2">{t("sidebar.model_unavailable")}</p>
    );
  }

  return (
    <Select
      value={activeModelId ?? undefined}
      onValueChange={(val) => {
        const model = models.find(m => m.id === val);
        if (model) setActiveModel(model.id, model.type);
      }}
    >
      <SelectTrigger className="w-full text-sm h-9 border-none bg-muted/50 focus:ring-0 focus:ring-offset-0">
        <SelectValue placeholder={t("sidebar.model_placeholder")} />
      </SelectTrigger>
      <SelectContent>
        {models.map(m => (
          <SelectItem key={m.id} value={m.id}>
            <div className="flex items-center gap-2">
              <span className="truncate">{m.id}</span>
              <span className="text-[10px] text-muted-foreground opacity-60">
                · {m.provider === "ollama" ? "Ollama" : "Gemini"}
              </span>
              {m.capabilities?.supports_image_input && (
                <span className="px-1.5 py-0.5 rounded-md bg-primary/10 text-primary text-[9px] font-medium tracking-wider">
                  VISION
                </span>
              )}
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
