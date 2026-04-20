import { useState, useRef } from "react";
import { Upload, FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useGenerateStore } from "@/stores/generate-store";
import { useTranslation } from "@/i18n";

export function UploadForm() {
  const { t } = useTranslation();
  const generateFromDoc = useGenerateStore(s => s.generateFromDoc);
  
  const [file, setFile] = useState<File | null>(null);
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      await generateFromDoc(file, context || undefined);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("common.error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8 space-y-6">
      <div>
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Upload className="w-5 h-5 text-primary" />
          {t("generate.title")}
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          {t("generate.subtitle")}
        </p>
      </div>

      {/* Drop zone */}
      <div
        className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/50 transition cursor-pointer"
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          className="hidden"
          onChange={e => setFile(e.target.files?.[0] ?? null)}
        />
        {file ? (
          <div className="flex items-center justify-center gap-2">
            <FileText className="w-5 h-5 text-primary" />
            <span className="font-medium">{file.name}</span>
            <span className="text-xs text-muted-foreground">({(file.size / 1024).toFixed(0)} KB)</span>
          </div>
        ) : (
          <>
            <Upload className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">{t("generate.upload_hint")}</p>
          </>
        )}
      </div>

      <Textarea
        value={context}
        onChange={e => setContext(e.target.value)}
        placeholder={t("generate.context_placeholder")}
        rows={3}
      />

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Button onClick={handleSubmit} disabled={!file || loading} className="w-full">
        {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
        {loading ? t("generate.processing") : t("generate.submit")}
      </Button>
    </div>
  );
}
