import { useModelStore } from "@/stores/model-store";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

export function ModelSelector() {
  const models = useModelStore(s => s.models);
  const activeModelId = useModelStore(s => s.activeModelId);
  const setActiveModel = useModelStore(s => s.setActiveModel);

  if (models.length === 0) {
    return (
      <p className="text-xs text-destructive px-2">Model tidak tersedia</p>
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
        <SelectValue placeholder="Pilih model..." />
      </SelectTrigger>
      <SelectContent>
        {models.map(m => (
          <SelectItem key={m.id} value={m.id}>
            {m.id} · {m.provider === "ollama" ? "Ollama" : "Gemini"}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
