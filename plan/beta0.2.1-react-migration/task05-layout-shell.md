# Task 05: Layout Shell — AppLayout, Sidebar, Header

## 1. Judul Task

Buat layout shell: AppLayout (sidebar + main), Sidebar skeleton, Header bar

## 2. Deskripsi

Membuat struktur layout utama aplikasi: sidebar kiri yang bisa collapse + area utama kanan. Belum ada konten — hanya shell/skeleton untuk diisi di task selanjutnya.

## 3. Tujuan Teknis

- `AppLayout.tsx` — grid 2 kolom (sidebar + main)
- `Sidebar.tsx` — container sidebar dengan toggle
- `Header.tsx` — top bar di area utama
- React Router setup dengan single route `/`
- Responsive: sidebar auto-hide di mobile

## 4. Scope

**Yang dikerjakan:**
- `src/components/layout/AppLayout.tsx`
- `src/components/layout/Sidebar.tsx`
- `src/components/layout/Header.tsx`
- `src/App.tsx` — setup router + layout
- `src/main.tsx` — wrap dengan BrowserRouter

**Yang tidak dikerjakan:**
- Sidebar content/session list (task 06)
- Chat content (task 07)
- Settings dialog (task 08)

## 5. Langkah Implementasi

### 5.1 `src/App.tsx`

```tsx
import { useEffect } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useModelStore } from "@/stores/model-store";
import { useSessionStore } from "@/stores/session-store";
import { useUIStore } from "@/stores/ui-store";

function App() {
  const fetchModels = useModelStore(s => s.fetchModels);
  const fetchSessions = useSessionStore(s => s.fetchSessions);
  const theme = useUIStore(s => s.theme);

  // Bootstrap: fetch models + sessions on mount
  useEffect(() => {
    fetchModels();
    fetchSessions();
  }, [fetchModels, fetchSessions]);

  // Apply theme on mount
  useEffect(() => {
    useUIStore.getState().setTheme(theme);
  }, [theme]);

  return <AppLayout />;
}

export default App;
```

### 5.2 `src/components/layout/AppLayout.tsx`

```tsx
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { useUIStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";

export function AppLayout() {
  const sidebarOpen = useUIStore(s => s.sidebarOpen);
  const activeTool = useUIStore(s => s.activeTool);

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <aside
        className={cn(
          "flex-shrink-0 border-r border-border bg-sidebar transition-all duration-300",
          sidebarOpen ? "w-64" : "w-0"
        )}
      >
        {sidebarOpen && <Sidebar />}
      </aside>

      {/* Main area */}
      <main className="flex-1 flex flex-col min-w-0">
        <Header />
        <div className="flex-1 overflow-hidden">
          {activeTool === "chat" ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              Chat area (task 07)
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              Generate from document (task 13)
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
```

### 5.3 `src/components/layout/Sidebar.tsx`

```tsx
import { useUIStore } from "@/stores/ui-store";
import { Settings, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

export function Sidebar() {
  const openSettings = useUIStore(s => s.openSettings);

  return (
    <div className="flex flex-col h-full p-3 gap-2">
      {/* Model selector placeholder */}
      <div className="h-10 rounded-md border border-border bg-muted/50 flex items-center px-3 text-sm text-muted-foreground">
        Model selector (task 06)
      </div>

      {/* New chat button */}
      <Button className="w-full" size="sm">
        <Plus className="w-4 h-4 mr-2" />
        Obrolan baru
      </Button>

      <Separator />

      {/* Session list placeholder */}
      <div className="flex-1 overflow-y-auto">
        <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider mb-2">
          Riwayat
        </p>
        <p className="text-sm text-muted-foreground text-center py-4">
          Session list (task 06)
        </p>
      </div>

      <Separator />

      {/* Tools placeholder */}
      <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">
        Alat
      </p>
      <p className="text-sm text-muted-foreground">Tools radio (task 06)</p>

      <Separator />

      {/* Bottom: settings + status */}
      <Button
        variant="ghost"
        size="sm"
        className="w-full justify-start"
        onClick={() => openSettings()}
      >
        <Settings className="w-4 h-4 mr-2" />
        Pengaturan
      </Button>

      <p className="text-xs text-muted-foreground">
        ● API Status (task 06)
      </p>
    </div>
  );
}
```

### 5.4 `src/components/layout/Header.tsx`

```tsx
import { useUIStore } from "@/stores/ui-store";
import { PanelLeftClose, PanelLeft, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Header() {
  const sidebarOpen = useUIStore(s => s.sidebarOpen);
  const toggleSidebar = useUIStore(s => s.toggleSidebar);
  const activeTool = useUIStore(s => s.activeTool);

  return (
    <header className="h-12 border-b border-border flex items-center px-4 gap-3 flex-shrink-0">
      <Button variant="ghost" size="icon" onClick={toggleSidebar}>
        {sidebarOpen ? (
          <PanelLeftClose className="w-4 h-4" />
        ) : (
          <PanelLeft className="w-4 h-4" />
        )}
      </Button>

      {activeTool === "chat" && (
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-primary" />
          <span className="font-semibold">Generator TOR</span>
        </div>
      )}
    </header>
  );
}
```

### 5.5 Tambah CSS token sidebar di `src/index.css`

```css
@import "tailwindcss";

@custom-variant dark (&:where(.dark, .dark *));

@layer base {
  :root {
    --sidebar: 0 0% 98%;
  }
  .dark {
    --sidebar: 224 12% 11%;
  }
}
```

Dan tambah di `tailwind.config.ts` (jika perlu extend):
```typescript
// Shadcn sudah generate config — tambah:
sidebar: "hsl(var(--sidebar))",
```

## 6. Output yang Diharapkan

Layout visual:
```
┌──────────────┬────────────────────────────────┐
│ Sidebar      │ [≡] [Bot] Generator TOR        │
│              │────────────────────────────────│
│ [Model ▾]    │                                │
│ [+ Obrolan]  │       Chat area placeholder    │
│ ──────       │                                │
│ RIWAYAT      │                                │
│  (empty)     │                                │
│ ──────       │                                │
│ ALAT         │                                │
│ ──────       │                                │
│ [⚙] Pengaturan                               │
│ ● API Status │                                │
└──────────────┴────────────────────────────────┘
```

## 7. Dependencies

- Task 01 (project, shadcn components)
- Task 04 (stores: useUIStore, useModelStore, useSessionStore)

## 8. Acceptance Criteria

- [ ] Layout 2 kolom: sidebar (w-64) + main area
- [ ] Sidebar toggle: klik → sidebar collapse/expand
- [ ] Header: sidebar toggle button + brand name
- [ ] Brand name hanya tampil di mode chat (bukan generate_doc)
- [ ] Placeholders untuk semua bagian yang belum diimplementasi
- [ ] Dark mode styling berfungsi
- [ ] `npm run build` tanpa error

## 9. Estimasi

Medium (1-2 jam)
