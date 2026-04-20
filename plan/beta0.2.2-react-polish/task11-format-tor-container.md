# Task 11: FormatTOR Container Rewrite — Wire All Sub-Components

## 1. Judul Task

Rewrite `FormatTORSettings.tsx` untuk menggabungkan semua sub-komponen Style menjadi halaman CRUD fungsional

## 2. Deskripsi

Mengganti skeleton statis `FormatTORSettings.tsx` saat ini (2 entries hardcoded) dengan container yang mengorchestrasi semua sub-komponen: StyleSelector, StyleReadonlyView, StyleActions, StyleEditForm, dan StyleExtractForm.

## 3. Tujuan Teknis

- Rewrite `src/components/settings/FormatTORSettings.tsx`
- Fetch styles list dari API on-mount
- State: selectedId, isEditing, styles[]
- Layout: Selector → Detail → Actions → (EditForm) → ExtractForm

## 4. Scope

**Yang dikerjakan:**
- Full rewrite `FormatTORSettings.tsx`
- Data fetching + loading state + error state
- Wiring semua sub-komponen (task 06–10)

**Yang tidak dikerjakan:**
- Sub-komponen individual (sudah dibuat di task 06–10)

## 5. Langkah Implementasi

### 5.1 Rewrite `src/components/settings/FormatTORSettings.tsx`

```tsx
import { useEffect, useState, useCallback } from "react";
import { Loader2 } from "lucide-react";
import { listStyles } from "@/api/styles";
import { useTranslation } from "@/i18n";
import { StyleSelector } from "./StyleSelector";
import { StyleReadonlyView } from "./StyleReadonlyView";
import { StyleActions } from "./StyleActions";
import { StyleEditForm } from "./StyleEditForm";
import { StyleExtractForm } from "./StyleExtractForm";
import type { TORStyle } from "@/types/api";

export function FormatTORSettings() {
  const { t } = useTranslation();
  const [styles, setStyles] = useState<TORStyle[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string>("");
  const [isEditing, setIsEditing] = useState(false);

  const fetchStyles = useCallback(async () => {
    setLoading(true);
    try {
      const result = await listStyles();
      setStyles(result);
      // Auto-select active or first
      if (!selectedId || !result.find(s => s.id === selectedId)) {
        const activeId = result.find(s => s.is_active)?.id ?? result[0]?.id;
        setSelectedId(activeId ?? "");
      }
    } catch (e) {
      console.error("Failed to load styles:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchStyles(); }, [fetchStyles]);

  const handleRefresh = () => {
    setIsEditing(false);
    fetchStyles();
  };

  const selectedStyle = styles.find(s => s.id === selectedId);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <h3 className="text-lg font-medium mb-1">{t("format.title")}</h3>
        <p className="text-sm text-muted-foreground">{t("format.desc")}</p>
      </div>

      {/* Selector */}
      <StyleSelector
        styles={styles}
        selectedId={selectedId}
        onSelect={(id) => { setSelectedId(id); setIsEditing(false); }}
        onRefresh={handleRefresh}
      />

      {selectedStyle && (
        <>
          {/* Divider */}
          <div className="border-t" />

          {/* Detail Header */}
          <div>
            <h4 className="text-sm font-semibold">{selectedStyle.name}</h4>
            <p className="text-xs text-muted-foreground">{selectedStyle.description}</p>
          </div>

          {/* Readonly View */}
          <StyleReadonlyView style={selectedStyle} />

          {/* Divider */}
          <div className="border-t" />

          {/* Actions */}
          <StyleActions
            style={selectedStyle}
            isEditing={isEditing}
            onToggleEdit={() => setIsEditing(!isEditing)}
            onRefresh={handleRefresh}
          />

          {/* Edit Form (conditional) */}
          {isEditing && !selectedStyle.is_default && (
            <>
              <div className="border-t" />
              <StyleEditForm style={selectedStyle} onSave={handleRefresh} />
            </>
          )}
        </>
      )}

      {/* Divider */}
      <div className="border-t" />

      {/* Extract Form */}
      <StyleExtractForm onSaved={handleRefresh} />
    </div>
  );
}
```

## 6. Output yang Diharapkan

Halaman Format TOR lengkap:
1. Header "Format TOR" + deskripsi
2. Dropdown style selector + tombol Activate
3. Detail readonly (tabel + metrik)
4. Action buttons (Edit/Clone/Delete) — mengikuti aturan proteksi
5. Edit form (muncul saat klik Edit)
6. Extraction form (selalu muncul di bawah)

## 7. Dependencies

- Task 01 (i18n)
- Task 06 (StyleSelector)
- Task 07 (StyleReadonlyView)
- Task 08 (StyleActions)
- Task 09 (StyleEditForm)
- Task 10 (StyleExtractForm)

## 8. Acceptance Criteria

- [ ] Styles list di-fetch dari API on-mount
- [ ] Loading spinner saat fetching
- [ ] Select style → detail berubah
- [ ] Activate style → badge pindah
- [ ] Edit → form muncul → simpan → refresh
- [ ] Clone → style baru muncul
- [ ] Delete → style hilang
- [ ] Default style → tidak bisa edit/delete
- [ ] Extract form selalu tampil di bawah
- [ ] `npm run build` sukses

## 9. Estimasi

Medium (1 jam)
