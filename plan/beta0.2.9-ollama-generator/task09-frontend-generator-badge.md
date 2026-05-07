# Task 09: Frontend — Generator Badge di StreamingResult

## Status
[ ] Belum dimulai

## Deskripsi
Tampilkan badge "Local" atau "Gemini" pada hasil generate TOR, sehingga user tahu provider mana yang menghasilkan TOR tersebut.

## File yang Diubah
- **MODIFY**: `app_frontend/src/components/generate/StreamingResult.tsx`
- **MODIFY**: `app_frontend/src/types/generate.ts`
- **MODIFY**: `app_frontend/src/i18n/` (tambah keys)

## Spesifikasi

### 1. Update StreamDoneData Type

Di `app_frontend/src/types/generate.ts`:

```typescript
export interface StreamDoneData {
  session_id: string;
  metadata: {
    generated_by: string;
    generator: string;       // NEW: "gemini" | "ollama"
    mode: string;
    word_count: number;
    has_assumptions: boolean;
  };
}
```

### 2. Generator Badge Component

Di `StreamingResult.tsx`, tambahkan badge di header atau footer hasil generate:

```tsx
// Setelah TOR selesai di-stream, tampilkan metadata
{streamMetadata && (
  <div className="flex items-center gap-2 mt-4 text-xs text-muted-foreground">
    <GeneratorBadge generator={streamMetadata.generator} />
    <span>{streamMetadata.word_count} kata</span>
    <span>{streamMetadata.generated_by}</span>
  </div>
)}

// Component badge
function GeneratorBadge({ generator }: { generator: string }) {
  if (generator === "ollama") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
        🖥️ Local
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
      ☁️ Gemini
    </span>
  );
}
```

### 3. Juga di Generate History

Jika ada tampilan history generate (daftar hasil generate sebelumnya), tambahkan badge generator di setiap item:

```tsx
// Di komponen list item
{item.metadata?.generator && (
  <GeneratorBadge generator={item.metadata.generator} />
)}
```

### 4. i18n Keys

```json
{
  "generate": {
    "badge_local": "Local",
    "badge_gemini": "Gemini",
    "generated_by": "Dihasilkan oleh {model}"
  }
}
```

## Catatan
- Badge Local: warna hijau, ikon 🖥️
- Badge Gemini: warna biru, ikon ☁️
- Juga tampilkan nama model (`generated_by`) sebagai informasi tambahan
