# Task 10: StyleExtractForm Component — Upload + AI Extract + Save

## 1. Judul Task

Membuat form untuk mengekstrak format TOR dari dokumen referensi menggunakan AI

## 2. Deskripsi

User upload contoh dokumen TOR (PDF/DOCX/TXT/MD), AI menganalisis struktur dan gaya bahasa, lalu hasilnya disimpan sebagai style baru. Referensi: `streamlit_app/components/format_tab.py` → `_render_extraction_section()`.

## 3. Tujuan Teknis

- `src/components/settings/StyleExtractForm.tsx`
- Upload file → `extractStyle(file)` → result
- Optional: user input nama style
- Save → `createStyle(data)` → refresh parent

## 4. Scope

**Yang dikerjakan:**
- `StyleExtractForm.tsx` — file upload, optional name input, extract button, save flow
- 2-step flow: extract → review → save

**Yang tidak dikerjakan:**
- Preview/edit extracted style sebelum save (future enhancement)

## 5. Langkah Implementasi

### 5.1 Buat `src/components/settings/StyleExtractForm.tsx`

```tsx
import { useState, useRef } from "react";
import { Sparkles, Upload, FileText, Loader2, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { extractStyle, createStyle } from "@/api/styles";
import { useTranslation } from "@/i18n";

interface Props {
  onSaved: () => void;
}

export function StyleExtractForm({ onSaved }: Props) {
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [styleName, setStyleName] = useState("");
  const [extracting, setExtracting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleExtract = async () => {
    if (!file) return;
    setExtracting(true);
    setError("");
    setSuccess("");

    try {
      // Step 1: Extract style from document via AI
      const extractedData = await extractStyle(file);

      // Step 2: Override name if user provided one
      if (styleName.trim()) {
        extractedData.name = styleName.trim();
      }

      // Step 3: Save as new style
      setSaving(true);
      await createStyle(extractedData);

      setSuccess(t("format.extract_saved"));
      setFile(null);
      setStyleName("");
      onSaved(); // refresh parent style list
    } catch (e) {
      setError(e instanceof Error ? e.message : t("common.error"));
    } finally {
      setExtracting(false);
      setSaving(false);
    }
  };

  const isProcessing = extracting || saving;

  return (
    <div className="space-y-4 border rounded-lg p-4 bg-muted/20">
      <div className="flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-primary" />
        <h4 className="text-sm font-semibold">{t("format.extract_title")}</h4>
      </div>
      <p className="text-xs text-muted-foreground">{t("format.extract_caption")}</p>

      {/* File upload */}
      <div
        className="border border-dashed rounded-md p-4 text-center cursor-pointer hover:border-primary/50 transition"
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
          <div className="flex items-center justify-center gap-2 text-sm">
            <FileText className="w-4 h-4 text-primary" />
            <span className="font-medium">{file.name}</span>
            <span className="text-xs text-muted-foreground">
              ({(file.size / 1024).toFixed(0)} KB)
            </span>
          </div>
        ) : (
          <div className="text-xs text-muted-foreground">
            <Upload className="w-5 h-5 mx-auto mb-1" />
            {t("format.extract_upload")}
          </div>
        )}
      </div>

      {/* Optional style name */}
      <Input
        value={styleName}
        onChange={e => setStyleName(e.target.value)}
        placeholder={t("format.extract_placeholder")}
        className="text-sm"
      />

      {/* Error / Success */}
      {error && <p className="text-xs text-destructive">{error}</p>}
      {success && (
        <p className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
          <Check className="w-3.5 h-3.5" /> {success}
        </p>
      )}

      {/* Extract button */}
      <Button
        onClick={handleExtract}
        disabled={!file || isProcessing}
        size="sm"
        className="w-full"
      >
        {isProcessing ? (
          <>
            <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
            {extracting ? t("format.extract_spinner") : t("common.saving")}
          </>
        ) : (
          <>
            <Sparkles className="w-3.5 h-3.5 mr-1.5" />
            {t("format.extract_button")}
          </>
        )}
      </Button>
    </div>
  );
}
```

## 6. Output yang Diharapkan

Flow:
1. User klik area upload → pilih file PDF
2. (Optional) ketik nama style baru
3. Klik "Ekstrak dengan AI"
4. Spinner "AI sedang menganalisis..." (15-30 detik)
5. Selesai → pesan sukses hijau "Style berhasil diekstrak dan disimpan!"
6. Style baru muncul di dropdown selector

## 7. Dependencies

- Task 01 (i18n)
- Task 04 (API: extractStyle, createStyle)

## 8. Acceptance Criteria

- [ ] Upload file berfungsi (PDF/DOCX/TXT/MD)
- [ ] Nama style opsional (AI auto-name jika kosong)
- [ ] Extract → spinner → save → success message
- [ ] Error handling jika extract/save gagal
- [ ] Parent list ter-refresh setelah save
- [ ] File bisa diganti tanpa reload

## 9. Estimasi

Medium (1.5 jam)
