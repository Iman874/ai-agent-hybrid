# Task 13: Generate from Document — Upload Form + Result

## 1. Judul Task

Implementasi halaman Generate TOR dari Dokumen: upload form + result preview

## 2. Deskripsi

Membuat mode "Generate Dokumen" yang muncul saat user memilih alat tersebut di sidebar. Berisi form upload file (PDF/DOCX/TXT/MD), input konteks tambahan, dan preview hasil TOR yang di-generate.

## 3. Tujuan Teknis

- `UploadForm.tsx` — drag-drop file + context input + style selector + submit
- `GenerateResult.tsx` — TOR content preview + export buttons
- Integration: form submit → `POST /generate/from-document` → show result

## 4. Scope

**Yang dikerjakan:**
- `src/components/generate/UploadForm.tsx`
- `src/components/generate/GenerateResult.tsx`
- Update `AppLayout.tsx` — render generate mode

**Yang tidak dikerjakan:**
- Style CRUD (basic selector saja)
- Export logic (task 14)

## 5. Langkah Implementasi

### 5.1 `src/components/generate/UploadForm.tsx`

```tsx
import { useState, useRef } from "react";
import { Upload, FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { generateFromDocument } from "@/api/generate";
import type { GenerateResponse } from "@/types/api";

interface Props {
  onResult: (result: GenerateResponse) => void;
}

export function UploadForm({ onResult }: Props) {
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
      const result = await generateFromDocument(file, context || undefined);
      onResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Gagal generate TOR");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8 space-y-6">
      <div>
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Upload className="w-5 h-5 text-primary" />
          Generate TOR dari Dokumen
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Upload dokumen sumber, AI otomatis membuat TOR.
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
            <p className="text-sm text-muted-foreground">Klik untuk upload PDF, DOCX, TXT, atau MD</p>
          </>
        )}
      </div>

      <Textarea
        value={context}
        onChange={e => setContext(e.target.value)}
        placeholder="Konteks tambahan (opsional)..."
        rows={3}
      />

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Button onClick={handleSubmit} disabled={!file || loading} className="w-full">
        {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
        {loading ? "Sedang memproses..." : "Generate TOR"}
      </Button>
    </div>
  );
}
```

### 5.2 `src/components/generate/GenerateResult.tsx`

```tsx
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Download } from "lucide-react";
import type { GenerateResponse } from "@/types/api";

interface Props {
  result: GenerateResponse;
  onBack: () => void;
}

export function GenerateResult({ result, onBack }: Props) {
  return (
    <div className="max-w-3xl mx-auto p-8 space-y-4">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={onBack}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <h2 className="text-lg font-semibold">Hasil TOR</h2>
      </div>

      <div className="prose prose-sm dark:prose-invert max-w-none bg-muted/30 rounded-lg p-6">
        <MarkdownRenderer content={result.tor_document.content} />
      </div>

      {/* Export buttons — task 14 */}
      <div className="flex gap-2">
        <Button variant="outline" size="sm" disabled>
          <Download className="w-4 h-4 mr-1" /> DOCX (task 14)
        </Button>
        <Button variant="outline" size="sm" disabled>
          <Download className="w-4 h-4 mr-1" /> PDF (task 14)
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">
        {result.tor_document.metadata.word_count} kata · 
        {result.tor_document.metadata.generation_time_ms}ms · 
        {result.tor_document.metadata.generated_by}
      </p>
    </div>
  );
}
```

## 6. Output yang Diharapkan

Mode Generate Dokumen:
1. Upload form → pilih file → tambah konteks → klik Generate
2. Loading spinner → TOR result muncul
3. Back button → kembali ke upload form

## 7. Dependencies

- Task 03 (API client: generateFromDocument)
- Task 05 (AppLayout: activeTool === "generate_doc")

## 8. Acceptance Criteria

- [ ] Upload file berfungsi (PDF/DOCX/TXT/MD)
- [ ] Context input opsional
- [ ] Submit → API call → result tampil
- [ ] Error handling tampil
- [ ] Back button kembali ke form
- [ ] TOR content di-render sebagai markdown

## 9. Estimasi

Medium (2 jam)
