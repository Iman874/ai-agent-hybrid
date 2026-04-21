# Task 8: Frontend — ModelSelector Capability Badges

## Deskripsi

Menambahkan badge/icon kecil di dropdown ModelSelector untuk menunjukkan kemampuan setiap model — vision atau text-only.

## Tujuan Teknis

- Setiap model di dropdown memiliki badge visual
- Vision model: ikon 👁 (Eye) + label "Vision"
- Text-only model: ikon 📝 (FileText) + label "Text"
- Tooltip menjelaskan arti badge

## Scope

**Dikerjakan:**
- Update `app_frontend/src/components/shared/ModelSelector.tsx`

**Tidak dikerjakan:**
- Model store logic (Task 5)
- ChatInput (Task 6)

## Langkah Implementasi

### Step 1: Update ModelSelector

File: `app_frontend/src/components/shared/ModelSelector.tsx`

```tsx
import { useModelStore } from "@/stores/model-store";
import { useTranslation } from "@/i18n";
import { Eye, FileText } from "lucide-react";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Tooltip, TooltipContent, TooltipTrigger, TooltipProvider,
} from "@/components/ui/tooltip";

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
        {models.map(m => {
          const isVision = m.capabilities?.supports_image_input ?? false;
          return (
            <SelectItem key={m.id} value={m.id}>
              <div className="flex items-center gap-2 w-full">
                <span className="truncate flex-1">
                  {m.id} · {m.provider === "ollama" ? "Ollama" : "Gemini"}
                </span>
                <TooltipProvider delayDuration={300}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className={`flex items-center gap-0.5 text-[0.65rem] px-1.5 py-0.5 rounded-full flex-shrink-0 ${
                        isVision
                          ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                          : "bg-muted text-muted-foreground"
                      }`}>
                        {isVision ? (
                          <><Eye className="w-3 h-3" /> Vision</>
                        ) : (
                          <><FileText className="w-3 h-3" /> Text</>
                        )}
                      </span>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      {isVision
                        ? t("sidebar.model_vision_tooltip", "Mendukung input gambar")
                        : t("sidebar.model_text_tooltip", "Hanya mendukung teks")}
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  );
}
```

### Step 2: Tambah i18n keys (jika perlu)

File: `app_frontend/src/i18n/locales/id.ts` dan `en.ts`

```typescript
sidebar: {
  // existing...
  model_vision_tooltip: "Mendukung input gambar",
  model_text_tooltip: "Hanya mendukung teks",
}
```

## Output yang Diharapkan

Dropdown model menampilkan:
```
┌──────────────────────────────────────────┐
│  qwen2.5:7b-instruct · Ollama   [Text]  │
│  gemini-2.0-flash · Gemini    [Vision]   │  ← badge hijau
│  llava:13b · Ollama            [Vision]  │  ← badge hijau
│  mistral:7b · Ollama             [Text]  │
└──────────────────────────────────────────┘
```

Badge Vision berwarna hijau emerald, badge Text berwarna muted.

## Dependencies

- Task 5: `ModelInfo.capabilities` harus ada di store

## Acceptance Criteria

- [ ] Setiap model di dropdown punya badge (Vision / Text)
- [ ] Badge Vision: ikon Eye + teks "Vision" + warna emerald
- [ ] Badge Text: ikon FileText + teks "Text" + warna muted
- [ ] Tooltip muncul saat hover badge
- [ ] i18n keys ditambahkan (id + en)
- [ ] Layout tidak rusak dengan badge tambahan
- [ ] `npm run build` clean

## Estimasi

Low (30 menit - 1 jam)
