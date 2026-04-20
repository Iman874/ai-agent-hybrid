# Task 06: StyleSelector Component — Dropdown + Activate Button

## 1. Judul Task

Membuat komponen StyleSelector yang menampilkan dropdown pemilih style dan tombol "Aktifkan"

## 2. Deskripsi

Komponen ini menampilkan list semua styles dari backend sebagai dropdown (`Select`). Style yang sedang aktif ditandai suffix "(Aktif)". Jika user memilih style berbeda dari yang aktif, muncul tombol "Jadikan Aktif".

## 3. Tujuan Teknis

- `src/components/settings/StyleSelector.tsx`
- Fetch styles via `listStyles()` dari `src/api/styles.ts`
- Activate via `activateStyle()` dari `src/api/styles.ts`

## 4. Scope

**Yang dikerjakan:**
- `StyleSelector.tsx`
- Menggunakan Shadcn `Select` atau native HTML select

**Yang tidak dikerjakan:**
- Detail view (task 07)
- Edit form (task 09)

## 5. Langkah Implementasi

### 5.1 Buat `src/components/settings/StyleSelector.tsx`

```tsx
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { activateStyle } from "@/api/styles";
import { useTranslation } from "@/i18n";
import { Loader2, Check } from "lucide-react";
import type { TORStyle } from "@/types/api";

interface Props {
  styles: TORStyle[];
  selectedId: string;
  onSelect: (id: string) => void;
  onRefresh: () => void;
}

export function StyleSelector({ styles, selectedId, onSelect, onRefresh }: Props) {
  const { t } = useTranslation();
  const [activating, setActivating] = useState(false);
  const activeId = styles.find(s => s.is_active)?.id;

  const handleActivate = async () => {
    setActivating(true);
    try {
      await activateStyle(selectedId);
      onRefresh();
    } catch (e) {
      console.error("Activate failed:", e);
    } finally {
      setActivating(false);
    }
  };

  return (
    <div className="flex gap-3 items-end">
      <div className="flex-1">
        <label className="text-sm font-medium mb-1.5 block">{t("format.available")}</label>
        <select
          className="w-full rounded-md border bg-background px-3 py-2 text-sm"
          value={selectedId}
          onChange={e => onSelect(e.target.value)}
        >
          {styles.map(s => (
            <option key={s.id} value={s.id}>
              {s.name} {s.is_active ? `(${t("format.active")})` : ""}
            </option>
          ))}
        </select>
      </div>
      {selectedId !== activeId && (
        <Button onClick={handleActivate} disabled={activating} size="sm">
          {activating ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Check className="w-4 h-4 mr-1" />}
          {t("format.activate")}
        </Button>
      )}
    </div>
  );
}
```

## 6. Output yang Diharapkan

- Dropdown menampilkan list styles: "Standar Akademik (Aktif)", "Proyek Nasional"
- Pilih "Proyek Nasional" → muncul tombol "Aktifkan"
- Klik "Aktifkan" → spinner → refetch → badge aktif pindah

## 7. Dependencies

- Task 01 (i18n)
- Task 04 (API: activateStyle sudah ada)

## 8. Acceptance Criteria

- [ ] Dropdown menampilkan semua styles dari backend
- [ ] Style aktif ditandai "(Aktif)" di label
- [ ] Tombol Activate muncul hanya jika selected ≠ active
- [ ] Klik Activate → API call → refresh list
- [ ] Loading state saat activate

## 9. Estimasi

Medium (1 jam)
