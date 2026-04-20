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
