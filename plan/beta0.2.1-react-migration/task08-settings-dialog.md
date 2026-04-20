# Task 08: Settings Dialog — ChatGPT-Style Sidebar Nav

## 1. Judul Task

Implementasi dialog pengaturan dengan navigasi sidebar (Umum / Format TOR / Lanjutan)

## 2. Deskripsi

Membuat dialog pengaturan terinspirasi ChatGPT: kolom navigasi kiri + konten kanan. 3 sections: Umum (tema + bahasa), Format TOR (style management), Lanjutan (API + cache).

## 3. Tujuan Teknis

- Dialog dengan Shadcn `Dialog` component
- Layout 2 kolom
- 3 sections navigasi
- Theme switch berfungsi
- Integrasi dengan `useUIStore`

## 4. Scope

**Yang dikerjakan:**
- `src/components/settings/SettingsDialog.tsx`
- `src/components/settings/GeneralSettings.tsx`
- `src/components/settings/FormatTORSettings.tsx`
- `src/components/settings/AdvancedSettings.tsx`

**Yang tidak dikerjakan:**
- Implementasi bahasa aktif (placeholder)
- CRUD style TOR lengkap (basic list saja)

## 5. Langkah Implementasi

### 5.1 `src/components/settings/SettingsDialog.tsx`

```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useUIStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";
import { GeneralSettings } from "./GeneralSettings";
import { FormatTORSettings } from "./FormatTORSettings";
import { AdvancedSettings } from "./AdvancedSettings";

const NAV_ITEMS = [
  { key: "umum" as const, label: "Umum" },
  { key: "format_tor" as const, label: "Format TOR" },
  { key: "lanjutan" as const, label: "Lanjutan" },
];

export function SettingsDialog() {
  const open = useUIStore(s => s.settingsOpen);
  const section = useUIStore(s => s.settingsSection);
  const closeSettings = useUIStore(s => s.closeSettings);
  const openSettings = useUIStore(s => s.openSettings);

  return (
    <Dialog open={open} onOpenChange={(v) => !v && closeSettings()}>
      <DialogContent className="max-w-2xl h-[500px] p-0 gap-0">
        <div className="flex h-full">
          {/* Nav sidebar */}
          <div className="w-44 border-r border-border p-3 space-y-1 flex-shrink-0">
            <DialogHeader className="pb-3">
              <DialogTitle className="text-sm">Pengaturan</DialogTitle>
            </DialogHeader>
            {NAV_ITEMS.map(item => (
              <Button
                key={item.key}
                variant="ghost"
                size="sm"
                className={cn(
                  "w-full justify-start text-sm font-normal",
                  section === item.key && "bg-primary/10 font-semibold",
                )}
                onClick={() => openSettings(item.key)}
              >
                {item.label}
              </Button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {section === "umum" && <GeneralSettings />}
            {section === "format_tor" && <FormatTORSettings />}
            {section === "lanjutan" && <AdvancedSettings />}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

### 5.2 `GeneralSettings.tsx`, `FormatTORSettings.tsx`, `AdvancedSettings.tsx`

(Implementasi lengkap dengan theme radio, bahasa placeholder, style list, cache clear — lihat plan design section 8)

## 6. Output yang Diharapkan

Dialog 2 kolom — nav kiri, konten kanan. Switch section tanpa close.

## 7. Dependencies

- Task 05 (layout — dialog trigger di sidebar)
- Task 04 (ui-store: settingsOpen, settingsSection)

## 8. Acceptance Criteria

- [ ] Dialog buka/tutup berfungsi
- [ ] 3 sections navigasi
- [ ] Theme switch (dark/light/system) berfungsi
- [ ] Dialog TIDAK close saat switch section

## 9. Estimasi

Medium (1-2 jam)
