# Task 06: Sidebar — Model Selector, Session List, Tools, Status

## 1. Judul Task

Implementasi konten sidebar: model selector, session list + delete, tools radio, API status

## 2. Deskripsi

Mengisi sidebar shell (task 05) dengan komponen fungsional: dropdown model AI, list riwayat sesi dengan tombol hapus, radio alat (Obrolan/Generate Dokumen), tombol pengaturan, dan status API.

## 3. Tujuan Teknis

- Model selector dropdown (`nama · provider`)
- Session list (maks 4) + tombol delete per item
- Tools: Obrolan / Generate Dokumen
- Status API: dot hijau/merah + label
- New chat button

## 4. Scope

**Yang dikerjakan:**
- `src/components/layout/Sidebar.tsx` — rewrite konten
- `src/components/session/SessionList.tsx`
- `src/components/session/SessionItem.tsx`
- `src/components/shared/ModelSelector.tsx`
- `src/components/shared/StatusIndicator.tsx`
- `src/hooks/useHealth.ts` — periodic health check

**Yang tidak dikerjakan:**
- AllSessionsDialog (simplifikasi — bukan prioritas)
- Settings dialog content (task 08)

## 5. Langkah Implementasi

### 5.1 `src/components/shared/ModelSelector.tsx`

```tsx
import { useModelStore } from "@/stores/model-store";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"; // Shadcn — install jika belum

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
      <SelectTrigger className="w-full text-sm h-9">
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
```

### 5.2 `src/components/session/SessionItem.tsx`

```tsx
import { memo } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { SessionListItem } from "@/types/session";

interface Props {
  session: SessionListItem;
  isActive: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export const SessionItem = memo(function SessionItem({
  session, isActive, onSelect, onDelete,
}: Props) {
  const title = session.title || `Sesi ${session.id.slice(0, 8)}`;
  const displayTitle = title.length > 28 ? title.slice(0, 28) + "…" : title;

  return (
    <div className={cn(
      "group flex items-center gap-1 rounded-md pr-1",
      isActive && "bg-primary/10",
    )}>
      <Button
        variant="ghost"
        size="sm"
        className={cn(
          "flex-1 justify-start text-sm font-normal truncate h-8",
          isActive && "font-semibold text-foreground",
          !isActive && "text-muted-foreground",
        )}
        disabled={isActive}
        onClick={() => onSelect(session.id)}
      >
        {displayTitle}
      </Button>

      {!isActive && (
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => { e.stopPropagation(); onDelete(session.id); }}
        >
          <X className="w-3 h-3" />
        </Button>
      )}
    </div>
  );
});
```

### 5.3 `src/components/session/SessionList.tsx`

```tsx
import { useSessionStore } from "@/stores/session-store";
import { SessionItem } from "./SessionItem";
import { MessageSquare } from "lucide-react";

export function SessionList() {
  const sessions = useSessionStore(s => s.sessions);
  const activeSessionId = useSessionStore(s => s.activeSessionId);
  const loadSession = useSessionStore(s => s.loadSession);
  const deleteSession = useSessionStore(s => s.deleteSession);

  const displayed = sessions.slice(0, 4);

  if (displayed.length === 0) {
    return (
      <div className="text-center py-6 text-muted-foreground">
        <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-xs">Belum ada percakapan</p>
        <p className="text-xs">Mulai obrolan baru</p>
      </div>
    );
  }

  return (
    <div className="space-y-0.5">
      {displayed.map(s => (
        <SessionItem
          key={s.id}
          session={s}
          isActive={s.id === activeSessionId}
          onSelect={loadSession}
          onDelete={deleteSession}
        />
      ))}
    </div>
  );
}
```

### 5.4 `src/hooks/useHealth.ts`

```tsx
import { useState, useEffect } from "react";
import { checkHealth } from "@/api/health";
import type { HealthResponse } from "@/types/api";

export function useHealth(intervalMs = 30_000) {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const data = await checkHealth();
        setHealth(data);
      } catch {
        setHealth(null);
      }
    };
    fetch();
    const id = setInterval(fetch, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  return health;
}
```

### 5.5 `src/components/shared/StatusIndicator.tsx`

```tsx
import { useHealth } from "@/hooks/useHealth";
import { useSessionStore } from "@/stores/session-store";

export function StatusIndicator() {
  const health = useHealth();
  const activeSessionId = useSessionStore(s => s.activeSessionId);

  const ok = health?.status === "healthy";
  const label = ok ? "API Terhubung" : "API Terputus";
  const sid = activeSessionId ? ` · ${activeSessionId.slice(0, 8)}` : "";

  return (
    <p className="text-xs text-muted-foreground flex items-center gap-1.5">
      <span className={`w-1.5 h-1.5 rounded-full ${ok ? "bg-green-500" : "bg-red-500"}`} />
      {label}{sid}
    </p>
  );
}
```

### 5.6 Update `Sidebar.tsx` — full implementation

```tsx
import { useUIStore } from "@/stores/ui-store";
import { useSessionStore } from "@/stores/session-store";
import { Settings, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ModelSelector } from "@/components/shared/ModelSelector";
import { SessionList } from "@/components/session/SessionList";
import { StatusIndicator } from "@/components/shared/StatusIndicator";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const openSettings = useUIStore(s => s.openSettings);
  const activeTool = useUIStore(s => s.activeTool);
  const setActiveTool = useUIStore(s => s.setActiveTool);
  const createNewSession = useSessionStore(s => s.createNewSession);

  return (
    <div className="flex flex-col h-full p-3 gap-2">
      <ModelSelector />

      <Button className="w-full" size="sm" onClick={createNewSession}>
        <Plus className="w-4 h-4 mr-2" />
        Obrolan baru
      </Button>

      <Separator className="opacity-40" />

      <p className="text-[0.65rem] font-semibold uppercase tracking-wider text-muted-foreground">
        Riwayat
      </p>
      <div className="flex-1 overflow-y-auto min-h-0">
        <SessionList />
      </div>

      <Separator className="opacity-40" />

      <p className="text-[0.65rem] font-semibold uppercase tracking-wider text-muted-foreground">
        Alat
      </p>
      <div className="space-y-0.5">
        {(["chat", "generate_doc"] as const).map(tool => (
          <Button
            key={tool}
            variant="ghost"
            size="sm"
            className={cn(
              "w-full justify-start text-sm font-normal",
              activeTool === tool && "bg-primary/10 font-semibold",
            )}
            onClick={() => setActiveTool(tool)}
          >
            {tool === "chat" ? "Obrolan" : "Generate Dokumen"}
          </Button>
        ))}
      </div>

      <Separator className="opacity-40" />

      <Button
        variant="ghost"
        size="sm"
        className="w-full justify-start text-muted-foreground"
        onClick={() => openSettings()}
      >
        <Settings className="w-4 h-4 mr-2" />
        Pengaturan
      </Button>

      <StatusIndicator />
    </div>
  );
}
```

## 6. Output yang Diharapkan

Sidebar fungsional:
```
┌──────────────────────┐
│ gemma4:e2b · Ollama ▾│
│ [+] Obrolan baru     │
│ ─────────            │
│ RIWAYAT              │
│   Pengadaan la..  [×]│
│   Workshop AI..   [×]│
│ ─────────            │
│ ALAT                 │
│ ▌Obrolan             │
│   Generate Dokumen   │
│ ─────────            │
│ [⚙] Pengaturan       │
│ ● API Terhubung      │
└──────────────────────┘
```

## 7. Dependencies

- Task 04 (stores)
- Task 05 (layout shell)

## 8. Acceptance Criteria

- [ ] Model selector dropdown berfungsi
- [ ] Session list menampilkan maks 4 sesi
- [ ] Session delete button muncul on hover
- [ ] Empty state saat tidak ada sesi
- [ ] Tools switching berfungsi
- [ ] Health status auto-poll setiap 30 detik
- [ ] New chat button mereset state

## 9. Estimasi

High (2-3 jam)
