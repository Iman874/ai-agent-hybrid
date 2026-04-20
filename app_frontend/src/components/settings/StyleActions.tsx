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
  const [name, setName] = useState(`${t("format.clone_name")}: ${styleName}`);
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
