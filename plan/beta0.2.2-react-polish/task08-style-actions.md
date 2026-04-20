# Task 08: StyleActions Component — Edit / Clone / Delete Buttons

## 1. Judul Task

Membuat komponen action buttons: Edit, Clone (dengan popover nama), dan Delete (dengan konfirmasi) — dengan proteksi aturan default

## 2. Deskripsi

Komponen ini menampilkan row tombol aksi untuk style yang dipilih. Aturan proteksi format default ditegakkan di sini: style default tidak bisa diedit/dihapus, style aktif tidak bisa dihapus.

## 3. Tujuan Teknis

- `src/components/settings/StyleActions.tsx`
- Tombol Edit: toggle edit mode (hanya non-default)
- Tombol Clone: popover input nama → `duplicateStyle()`
- Tombol Delete: popover konfirmasi → `deleteStyle()` (non-default + non-active)

## 4. Scope

**Yang dikerjakan:**
- `StyleActions.tsx` dengan Edit, Clone popover, Delete popover
- Aturan bisnis: default → hide Edit/Delete, active → disable Delete

**Yang tidak dikerjakan:**
- Edit form content (task 09)

## 5. Langkah Implementasi

### 5.1 Buat `src/components/settings/StyleActions.tsx`

```tsx
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import { Pencil, Copy, Trash2, Loader2, AlertTriangle } from "lucide-react";
import { duplicateStyle, deleteStyle } from "@/api/styles";
import { useTranslation } from "@/i18n";
import type { TORStyle } from "@/types/api";

interface Props {
  style: TORStyle;
  isEditing: boolean;
  onToggleEdit: () => void;
  onRefresh: () => void;
}

export function StyleActions({ style, isEditing, onToggleEdit, onRefresh }: Props) {
  const { t } = useTranslation();
  const isDefault = style.is_default;
  const isActive = style.is_active;

  return (
    <div className="flex gap-2 flex-wrap">
      {/* Edit — non-default only */}
      {!isDefault && (
        <Button variant="outline" size="sm" onClick={onToggleEdit}>
          <Pencil className="w-3.5 h-3.5 mr-1.5" />
          {isEditing ? t("format.done_edit") : t("format.edit")}
        </Button>
      )}

      {/* Clone — always available */}
      <ClonePopover styleId={style.id} styleName={style.name} onRefresh={onRefresh} />

      {/* Delete — non-default + non-active only */}
      {!isDefault && (
        <DeletePopover
          styleId={style.id}
          isActive={isActive}
          onRefresh={onRefresh}
        />
      )}
    </div>
  );
}

function ClonePopover({ styleId, styleName, onRefresh }: {
  styleId: string; styleName: string; onRefresh: () => void;
}) {
  const { t } = useTranslation();
  const [name, setName] = useState(`Salinan ${styleName}`);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const handleClone = async () => {
    setLoading(true);
    try {
      await duplicateStyle(styleId, name);
      setOpen(false);
      onRefresh();
    } catch (e) {
      console.error("Clone failed:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm">
          <Copy className="w-3.5 h-3.5 mr-1.5" />
          {t("format.clone")}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72 space-y-3">
        <label className="text-sm font-medium">{t("format.clone_name")}</label>
        <Input value={name} onChange={e => setName(e.target.value)} />
        <Button onClick={handleClone} disabled={loading || !name.trim()} size="sm" className="w-full">
          {loading && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
          {t("format.clone_button")}
        </Button>
      </PopoverContent>
    </Popover>
  );
}

function DeletePopover({ styleId, isActive, onRefresh }: {
  styleId: string; isActive: boolean; onRefresh: () => void;
}) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const handleDelete = async () => {
    setLoading(true);
    try {
      await deleteStyle(styleId);
      setOpen(false);
      onRefresh();
    } catch (e) {
      console.error("Delete failed:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="text-destructive hover:text-destructive">
          <Trash2 className="w-3.5 h-3.5 mr-1.5" />
          {t("format.delete")}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72 space-y-3">
        <div className="flex items-center gap-2 text-destructive text-sm font-medium">
          <AlertTriangle className="w-4 h-4" />
          {t("format.delete_warning")}
        </div>
        {isActive ? (
          <p className="text-xs text-destructive">{t("format.delete_active_block")}</p>
        ) : (
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={loading}
            size="sm"
            className="w-full"
          >
            {loading && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
            {t("format.delete_confirm")}
          </Button>
        )}
      </PopoverContent>
    </Popover>
  );
}
```

## 6. Output yang Diharapkan

- Style default: hanya tombol "Tiru (Klon)" tampil
- Style custom non-aktif: Edit + Klon + Hapus semua muncul
- Style custom aktif: Edit + Klon muncul, Hapus ada tapi isinya warning "ubah aktif dulu"
- Klik Clone → popover input nama → "Buat Salinan" → list refresh
- Klik Delete → popover konfirmasi → "Ya, Hapus Sekarang" → list refresh

## 7. Dependencies

- Task 01 (i18n)
- Task 04 (API: duplicateStyle, deleteStyle)
- Shadcn `Popover`, `Input` components sudah ada

## 8. Acceptance Criteria

- [ ] Style `is_default=true` → tombol Edit dan Delete TIDAK muncul
- [ ] Style `is_active=true` → tombol Delete menampilkan warning, bukan tombol hapus
- [ ] Clone popover berfungsi → style baru muncul di list
- [ ] Delete popover berfungsi → style hilang dari list
- [ ] Loading states di semua async actions

## 9. Estimasi

Medium (1.5 jam)
