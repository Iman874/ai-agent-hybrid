# Task 9: `GenerateContainer.tsx` Rewrite — 3 View States

## 1. Judul Task
Rewrite `GenerateContainer.tsx` untuk menggunakan `generate-store` dan menampilkan 3 view states: idle, generating, viewing.

## 2. Deskripsi
Container saat ini menggunakan `useState` lokal yang hilang saat reload. Setelah rewrite, semua state berasal dari Zustand store. Container mengorkestrasi 3 view:
1. **Idle** — `UploadForm` + `GenerateHistory`
2. **Generating** — Spinner loading
3. **Viewing** — `GenerateResult` (dari store)

## 3. Tujuan Teknis
- Hapus `useState<GenerateResponse>` lokal
- Baca semua state dari `useGenerateStore`
- Integrasi `UploadForm` onResult dengan `generateFromDoc` store
- Render `GenerateHistory` di bawah upload form

## 4. Scope
### Yang dikerjakan
- Rewrite `src/components/generate/GenerateContainer.tsx`

### Yang tidak dikerjakan
- Tidak mengubah `UploadForm` secara drastis (minor callback change)
- Tidak mengubah `GenerateResult` (task 10)

## 5. Langkah Implementasi

### Step 1: Rewrite `GenerateContainer.tsx`

```tsx
import { useGenerateStore } from "@/stores/generate-store";
import { UploadForm } from "./UploadForm";
import { GenerateResult } from "./GenerateResult";
import { GenerateHistory } from "./GenerateHistory";
import { Loader2 } from "lucide-react";
import { useTranslation } from "@/i18n";

export function GenerateContainer() {
  const { t } = useTranslation();
  const isGenerating = useGenerateStore(s => s.isGenerating);
  const lastResponse = useGenerateStore(s => s.lastGenerateResponse);
  const activeResult = useGenerateStore(s => s.activeResult);
  const isLoadingResult = useGenerateStore(s => s.isLoadingResult);
  const clearActiveResult = useGenerateStore(s => s.clearActiveResult);
  const clearLastResponse = useGenerateStore(s => s.clearLastResponse);

  // View: Loading detail from history
  if (isLoadingResult) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  // View: Showing result from history click
  if (activeResult) {
    return (
      <GenerateResult
        resultFromHistory={activeResult}
        onBack={clearActiveResult}
      />
    );
  }

  // View: Showing immediate generate result
  if (lastResponse) {
    return (
      <GenerateResult
        result={lastResponse}
        onBack={clearLastResponse}
      />
    );
  }

  // View: Generating spinner
  if (isGenerating) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="text-sm">{t("generate.processing")}</p>
      </div>
    );
  }

  // View: Idle — upload form + history
  return (
    <div className="space-y-8 pb-8">
      <UploadForm />
      <div className="max-w-2xl mx-auto px-8">
        <GenerateHistory />
      </div>
    </div>
  );
}
```

### Step 2: Update `UploadForm.tsx` — Gunakan store

Modify `UploadForm` agar menggunakan `generateFromDoc` dari store alih-alih callback prop:

```tsx
// Hapus interface Props dan onResult prop
// Import dan gunakan store:
import { useGenerateStore } from "@/stores/generate-store";

export function UploadForm() {
  const { t } = useTranslation();
  const generateFromDoc = useGenerateStore(s => s.generateFromDoc);
  // ... state lokal tetap (file, context, loading, error)

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

  // ... rest of JSX
}
```

## 6. Output yang Diharapkan

**Idle state:**
```
┌─────────────────────────────────────┐
│  📤 Generate TOR dari Dokumen       │
│  [Upload area]                      │
│  [Context textarea]                 │
│  [Generate TOR button]              │
│                                     │
│  RIWAYAT GENERATE                   │
│  ┌──────────────────────────────┐   │
│  │ ✓ TOR_abc.docx  · 👁 🗑     │   │
│  │ ✓ proposal.pdf  · 👁 🗑     │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

## 7. Dependencies
- Task 7 (generate-store)
- Task 8 (GenerateHistory component)

## 8. Acceptance Criteria
- [ ] Tidak ada `useState<GenerateResponse>` lokal di GenerateContainer
- [ ] All state berasal dari `useGenerateStore`
- [ ] Idle: Upload form + history tampil
- [ ] Generating: Spinner tampil
- [ ] After generate: Result tampil, klik back → kembali ke idle
- [ ] History click: Result detail tampil dari API
- [ ] Browser reload → history masih tampil (dari API)
- [ ] `npm run build` sukses

## 9. Estimasi
**Medium** (~1 jam)
