import { useState, useRef } from "react";
import { Upload, FileText, Loader2, Wand2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createStyle, extractStyle } from "@/api/styles";
import { useTranslation } from "@/i18n";

interface Props {
  onSuccess: () => void;
  onCancel: () => void;
}

export function StyleExtractForm({ onSuccess, onCancel }: Props) {
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleExtract = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      // 1. Extract JSON from document
      const extractedData = await extractStyle(file);
      
      // 2. Wrap it into a Style creation payload
      // Provide generic fallbacks in case AI extraction misses some base properties
      const payload = {
        name: extractedData?.name || `Format - ${file.name.replace(/\.[^/.]+$/, "")}`,
        description: extractedData?.description || t("format.extracted_desc", { name: file.name }),
        sections: extractedData?.sections || [],
        config: extractedData?.config || {
          language: "id",
          formality: "formal",
          voice: "active",
          perspective: "third_person",
          min_word_count: 500,
          max_word_count: 1500,
          numbering_style: "numeric",
          custom_instructions: "Extracted automatically."
        }
      };

      await createStyle(payload);
      onSuccess();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("format.extract_failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-300 border border-border p-5 rounded-xl bg-muted/10">
      
      <div>
        <h4 className="text-sm font-semibold flex items-center gap-1.5">
          <Wand2 className="w-4 h-4 text-primary" />
          {t("format.extract_title")}
        </h4>
        <p className="text-xs text-muted-foreground mt-1">
          {t("format.extract_subtitle")}
        </p>
      </div>

      <div
        className="border-2 border-dashed border-border rounded-lg p-6 text-center hover:border-primary/50 transition cursor-pointer bg-background"
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={e => setFile(e.target.files?.[0] ?? null)}
        />
        {file ? (
          <div className="flex flex-col items-center gap-2">
            <FileText className="w-6 h-6 text-primary" />
            <span className="font-medium text-sm truncate max-w-[200px]">{file.name}</span>
            <span className="text-xs text-muted-foreground">({(file.size / 1024).toFixed(0)} KB)</span>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <Upload className="w-6 h-6 text-muted-foreground mb-2" />
            <p className="text-xs text-muted-foreground">{t("format.upload_hint")}</p>
          </div>
        )}
      </div>

      {error && <p className="text-xs text-destructive bg-destructive/10 p-2 rounded">{error}</p>}

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="ghost" size="sm" onClick={onCancel} disabled={loading}>
          {t("common.cancel")}
        </Button>
        <Button size="sm" onClick={handleExtract} disabled={!file || loading}>
          {loading ? <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <Wand2 className="w-3.5 h-3.5 mr-1.5" />}
          {loading ? t("format.extracting") : t("format.extract")}
        </Button>
      </div>
    </div>
  );
}
