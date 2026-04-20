# Task 14: TOR Preview + Export (DOCX/PDF/MD)

## 1. Judul Task

Implementasi preview TOR di chat area dan export download ke DOCX/PDF/MD

## 2. Deskripsi

Saat AI menghasilkan TOR (baik dari chat maupun generate), tampilkan preview konten TOR dan tombol download ke format DOCX, PDF, atau MD menggunakan endpoint `/export/{session_id}`.

## 3. Tujuan Teknis

- `TORPreview.tsx` — card preview TOR dalam chat area
- Export button group (DOCX/PDF/MD)
- Download via blob + `downloadBlob()` helper

## 4. Scope

**Yang dikerjakan:**
- `src/components/chat/TORPreview.tsx`
- Update `ChatArea.tsx` — tampilkan TOR preview saat `torDocument != null`
- Update `GenerateResult.tsx` — enable export buttons
- Gunakan `exportDocument()` + `downloadBlob()` dari `src/api/export.ts`

**Yang tidak dikerjakan:**
- Print to PDF (hanya download file)
- Edit TOR inline

## 5. Langkah Implementasi

### 5.1 `src/components/chat/TORPreview.tsx`

```tsx
import { useState } from "react";
import { FileText, Download, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { exportDocument, downloadBlob } from "@/api/export";
import type { TORDocument } from "@/types/api";

interface Props {
  torDocument: TORDocument;
  sessionId: string;
}

export function TORPreview({ torDocument, sessionId }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);

  const handleExport = async (format: "docx" | "pdf" | "md") => {
    setDownloading(format);
    try {
      const blob = await exportDocument(sessionId, format);
      const ext = format;
      downloadBlob(blob, `TOR_${sessionId.slice(0, 8)}.${ext}`);
    } catch (e) {
      console.error("Export failed:", e);
    } finally {
      setDownloading(null);
    }
  };

  const preview = expanded
    ? torDocument.content
    : torDocument.content.slice(0, 500) + (torDocument.content.length > 500 ? "..." : "");

  return (
    <div className="bg-muted/30 border border-border rounded-lg p-4 my-4 space-y-3">
      <div className="flex items-center gap-2">
        <FileText className="w-5 h-5 text-primary" />
        <span className="font-semibold text-sm">TOR Dokumen</span>
        <span className="text-xs text-muted-foreground ml-auto">
          {torDocument.metadata.word_count} kata
        </span>
      </div>

      <div className="prose prose-sm dark:prose-invert max-w-none text-sm">
        <MarkdownRenderer content={preview} />
      </div>

      {torDocument.content.length > 500 && (
        <Button variant="ghost" size="sm" onClick={() => setExpanded(!expanded)}>
          {expanded ? <ChevronUp className="w-3 h-3 mr-1" /> : <ChevronDown className="w-3 h-3 mr-1" />}
          {expanded ? "Sembunyikan" : "Tampilkan semua"}
        </Button>
      )}

      <div className="flex gap-2 pt-2 border-t border-border">
        {(["docx", "pdf", "md"] as const).map(fmt => (
          <Button
            key={fmt}
            variant="outline"
            size="sm"
            onClick={() => handleExport(fmt)}
            disabled={downloading !== null}
          >
            {downloading === fmt ? (
              <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            ) : (
              <Download className="w-3 h-3 mr-1" />
            )}
            {fmt.toUpperCase()}
          </Button>
        ))}
      </div>
    </div>
  );
}
```

### 5.2 Update `ChatArea.tsx`

```tsx
const torDocument = useChatStore(s => s.torDocument);
const activeSessionId = useSessionStore(s => s.activeSessionId);

// After messages, before input:
{torDocument && activeSessionId && (
  <TORPreview torDocument={torDocument} sessionId={activeSessionId} />
)}
```

### 5.3 Update `GenerateResult.tsx` — enable export

Replace disabled export buttons with working ones using same `handleExport` pattern.

## 6. Output yang Diharapkan

TOR preview card di chat:
```
┌─────────────────────────────────────┐
│ [📄] TOR Dokumen           500 kata │
│                                     │
│ # Kerangka Acuan Kerja             │
│ ## Latar Belakang                   │
│ ...                                 │
│ [▼ Tampilkan semua]                 │
│ ─────────────────────               │
│ [DOCX] [PDF] [MD]                   │
└─────────────────────────────────────┘
```

## 7. Dependencies

- Task 03 (export API client)
- Task 07 (ChatArea)
- Task 13 (GenerateResult)

## 8. Acceptance Criteria

- [ ] TOR preview card muncul saat TOR ter-generate
- [ ] Expand/collapse konten berfungsi
- [ ] Export DOCX → download file berfungsi
- [ ] Export PDF → download file berfungsi
- [ ] Export MD → download file berfungsi
- [ ] Loading state saat downloading

## 9. Estimasi

Medium (1-2 jam)
