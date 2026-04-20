# Task 4: ModelSelector i18n + Polish

## 1. Judul Task
Terapkan terjemahan i18n pada komponen `ModelSelector` dan tambahkan translation keys baru.

## 2. Deskripsi
`ModelSelector.tsx` masih memiliki string hardcoded dalam Bahasa Indonesia (`"Model tidak tersedia"`, `"Pilih model..."`). Perlu diganti dengan `t()` hook agar ikut berubah saat user ganti bahasa.

## 3. Tujuan Teknis
- Import `useTranslation` di `ModelSelector.tsx`
- Ganti semua hardcoded string dengan `t()` calls
- Tambahkan translation keys baru di `id.ts` dan `en.ts`

## 4. Scope
### Yang dikerjakan
- Modifikasi `src/components/shared/ModelSelector.tsx`
- Tambah keys di `src/i18n/locales/id.ts` dan `src/i18n/locales/en.ts`

### Yang tidak dikerjakan
- Tidak mengubah logic pemilihan model
- Tidak mengubah styling

## 5. Langkah Implementasi

### Step 1: Tambah translation keys di `src/i18n/locales/id.ts`

Di bagian Sidebar section, tambahkan:
```typescript
"sidebar.model_unavailable": "Model tidak tersedia",
"sidebar.model_placeholder": "Pilih model...",
```

### Step 2: Tambah translation keys di `src/i18n/locales/en.ts`

```typescript
"sidebar.model_unavailable": "No models available",
"sidebar.model_placeholder": "Select model...",
```

### Step 3: Update `ModelSelector.tsx`

```typescript
import { useModelStore } from "@/stores/model-store";
import { useTranslation } from "@/i18n";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export function ModelSelector() {
  const { t } = useTranslation();
  const models = useModelStore(s => s.models);
  const activeModelId = useModelStore(s => s.activeModelId);
  const setActiveModel = useModelStore(s => s.setActiveModel);

  if (models.length === 0) {
    return (
      <p className="text-xs text-destructive px-2">{t("sidebar.model_unavailable")}</p>
    );
  }

  return (
    <Select
      value={activeModelId ?? undefined}
      onValueChange={(val) => {
        const model = models.find(m => m.id === val);
        if (model) setActiveModel(model.id, model.type);
      }}
    >
      <SelectTrigger className="w-full text-sm h-9 border-none bg-muted/50 focus:ring-0 focus:ring-offset-0">
        <SelectValue placeholder={t("sidebar.model_placeholder")} />
      </SelectTrigger>
      <SelectContent>
        {models.map(m => (
          <SelectItem key={m.id} value={m.id}>
            {m.id} · {m.provider === "ollama" ? "Ollama" : "Gemini"}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
```

## 6. Output yang Diharapkan

**Bahasa Indonesia:**  
- Jika model kosong: "Model tidak tersedia"
- Placeholder: "Pilih model..."

**English:**
- Jika model kosong: "No models available"
- Placeholder: "Select model..."

## 7. Dependencies
- Task 1-3 (opsional, tapi sebaiknya dikerjakan setelah bugs selesai)

## 8. Acceptance Criteria
- [ ] `ModelSelector` menggunakan `t()` untuk semua string
- [ ] Ganti bahasa di settings → teks di ModelSelector ikut berubah
- [ ] Tidak ada string hardcoded tersisa di komponen
- [ ] `npm run build` sukses tanpa error

## 9. Estimasi
**Low** (~15 menit)
