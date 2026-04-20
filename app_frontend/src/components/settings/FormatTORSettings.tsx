import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Plus, Loader2 } from "lucide-react";
import { listStyles } from "@/api/styles";
import { useTranslation } from "@/i18n";
import type { TORStyle } from "@/types/api";

import { StyleSelector } from "./StyleSelector";
import { StyleReadonlyView } from "./StyleReadonlyView";
import { StyleActions } from "./StyleActions";
import { StyleEditForm } from "./StyleEditForm";
import { StyleExtractForm } from "./StyleExtractForm";

export function FormatTORSettings() {
  const { t } = useTranslation();
  const [styles, setStyles] = useState<TORStyle[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [selectedId, setSelectedId] = useState<string>("");
  const [isEditing, setIsEditing] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);

  const fetchStyles = async () => {
    try {
      const data = await listStyles();
      setStyles(data);
      if (!selectedId || !data.find(s => s.id === selectedId)) {
        const active = data.find(s => s.is_active) || data[0];
        if (active) setSelectedId(active.id);
      }
    } catch (e) {
      console.error("Failed to load styles", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStyles();
  }, []);

  const handleRefresh = async () => {
    setIsEditing(false);
    setIsExtracting(false);
    await fetchStyles();
  };

  const selectedStyle = styles.find(s => s.id === selectedId);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium mb-1">{t("settings.format_title")}</h3>
          <p className="text-sm text-muted-foreground">{t("settings.format_desc")}</p>
        </div>
        {!isExtracting && !isEditing && (
          <Button size="sm" onClick={() => setIsExtracting(true)}>
            <Plus className="w-4 h-4 mr-1.5" /> {t("format.new_format")}
          </Button>
        )}
      </div>

      {loading ? (
        <div className="py-10 flex justify-center text-muted-foreground">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : styles.length === 0 ? (
        <p className="text-sm text-muted-foreground">Tidak ada format.</p>
      ) : (
        <div className="space-y-6">
          {/* Main View state */}
          {!isExtracting && !isEditing && selectedStyle && (
            <>
              <StyleSelector
                styles={styles}
                selectedId={selectedId}
                onSelect={id => setSelectedId(id)}
                onRefresh={handleRefresh}
              />
              <div className="border border-border rounded-xl p-5 bg-background shadow-sm space-y-5">
                <div className="border-b pb-4">
                  <h4 className="font-semibold text-lg">{selectedStyle.name}</h4>
                  <p className="text-sm text-muted-foreground mt-1">{selectedStyle.description}</p>
                </div>
                
                <StyleReadonlyView style={selectedStyle} />
                
                <div className="pt-2 border-t">
                  <StyleActions 
                    style={selectedStyle}
                    isEditing={false}
                    onToggleEdit={() => setIsEditing(true)}
                    onRefresh={handleRefresh}
                  />
                </div>
              </div>
            </>
          )}

          {/* Edit State */}
          {isEditing && selectedStyle && (
            <StyleEditForm 
              style={selectedStyle} 
              onSave={handleRefresh} 
            />
          )}

          {/* Extract State */}
          {isExtracting && (
            <StyleExtractForm
              onSuccess={handleRefresh}
              onCancel={() => setIsExtracting(false)}
            />
          )}
        </div>
      )}
    </div>
  );
}
