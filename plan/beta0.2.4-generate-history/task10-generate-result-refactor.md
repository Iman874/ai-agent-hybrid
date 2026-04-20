# Task 10: `GenerateResult.tsx` Refactor

## 1. Judul Task
Update `GenerateResult` agar bisa render dari dua sumber data: response langsung (generate baru) dan detail dari riwayat.

## 2. Deskripsi
Saat ini `GenerateResult` hanya menerima `GenerateResponse` prop. Setelah refactor, komponen ini juga bisa menampilkan `DocGenDetail` (dari riwayat). Ini memerlukan dual-source rendering karena kedua tipe berisi data TOR dengan struktur sedikit berbeda.

## 3. Tujuan Teknis
- Props bisa menerima `result: GenerateResponse` ATAU `resultFromHistory: DocGenDetail`
- Normalize ke satu format internal
- Export PDF/DOCX/MD tetap berfungsi

## 4. Scope
### Yang dikerjakan
- Modifikasi `src/components/generate/GenerateResult.tsx`

### Yang tidak dikerjakan
- Tidak mengubah store atau API
- Tidak mengubah export logic

## 5. Langkah Implementasi

### Step 1: Update interface dan logic

```tsx
import { useState } from "react";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Download, Loader2 } from "lucide-react";
import { exportDocument, downloadBlob } from "@/api/export";
import { useTranslation } from "@/i18n";
import type { GenerateResponse, TORMetadata } from "@/types/api";
import type { DocGenDetail } from "@/types/generate";

interface Props {
  result?: GenerateResponse;
  resultFromHistory?: DocGenDetail;
  onBack: () => void;
}

export function GenerateResult({ result, resultFromHistory, onBack }: Props) {
  const { t } = useTranslation();
  const [downloading, setDownloading] = useState<string | null>(null);

  // Normalize data from either source
  const sessionId = result?.session_id ?? resultFromHistory?.id ?? "";
  const torContent = result?.tor_document?.content ?? resultFromHistory?.tor_content ?? "";
  const metadata: TORMetadata | null = result?.tor_document?.metadata ?? resultFromHistory?.metadata ?? null;
  const filename = resultFromHistory?.filename;

  const handleExport = async (format: "docx" | "pdf" | "md") => {
    setDownloading(format);
    try {
      const blob = await exportDocument(sessionId, format);
      const name = filename
        ? `${filename.replace(/\.[^.]+$/, "")}.${format}`
        : `TOR_${sessionId.slice(0, 8)}.${format}`;
      downloadBlob(blob, name);
    } catch (e) {
      console.error("Export failed:", e);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-4 sm:p-8 space-y-4">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={onBack}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h2 className="text-lg font-semibold">{t("generate.result_title")}</h2>
          {filename && (
            <p className="text-xs text-muted-foreground">{filename}</p>
          )}
        </div>
      </div>

      <div className="bg-muted/30 rounded-lg p-6">
        <MarkdownRenderer content={torContent} />
      </div>

      {/* Export buttons */}
      <div className="flex gap-2">
        {(["docx", "pdf", "md"] as const).map(fmt => (
          <Button
            key={fmt} variant="outline" size="sm"
            onClick={() => handleExport(fmt)}
            disabled={downloading !== null}
          >
            {downloading === fmt ? (
              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
            ) : (
              <Download className="w-4 h-4 mr-1" />
            )}
            {fmt.toUpperCase()}
          </Button>
        ))}
      </div>

      {metadata && (
        <p className="text-xs text-muted-foreground">
          {metadata.word_count} {t("generate.words_label")} · 
          {metadata.generation_time_ms}ms · 
          {metadata.generated_by}
        </p>
      )}
    </div>
  );
}
```

## 6. Output yang Diharapkan

Tampilan identik baik dari generate baru maupun dari riwayat:
```
← Hasil TOR
  proposal.docx

  ┌──────────────────────────┐
  │  # TOR Kegiatan ...      │
  │  ## Latar Belakang       │
  │  ...                     │
  └──────────────────────────┘

  [DOCX] [PDF] [MD]

  1.240 kata · 3200ms · gemini-2.5-pro
```

## 7. Dependencies
- Task 6 (types `DocGenDetail`)
- Task 9 (GenerateContainer passes correct props)

## 8. Acceptance Criteria
- [ ] Render dari `result` (GenerateResponse) berfungsi
- [ ] Render dari `resultFromHistory` (DocGenDetail) berfungsi
- [ ] Export buttons berfungsi dari kedua sumber
- [ ] Filename asli ditampilkan jika dari history
- [ ] Metadata (word count, time, model) ditampilkan jika ada
- [ ] `npm run build` sukses

## 9. Estimasi
**Low** (~30 menit)
