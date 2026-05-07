# Task 08: Frontend — Generator Selector UI

## Status
[ ] Belum dimulai

## Deskripsi
Buat UI selector untuk memilih generator mode. Ada di dua tempat: **Settings dialog** dan **Chat area** (dropdown cepat).

## File yang Diubah
- **NEW/EDIT**: `app_frontend/src/components/settings/GeneratorSelector.tsx`
- **NEW/EDIT**: `app_frontend/src/components/chat/ChatGeneratorSelector.tsx`
- **MODIFY**: `app_frontend/src/components/settings/SettingsDialog.tsx`
- **MODIFY**: `app_frontend/src/components/chat/ChatInput.tsx` (atau area sekitar)
- **MODIFY**: `app_frontend/src/i18n/` (tambah keys)

## Spesifikasi

### 1. GeneratorSelector Component (Settings)

File: `app_frontend/src/components/settings/GeneratorSelector.tsx`

```tsx
interface GeneratorSelectorProps {
  value: "auto" | "gemini" | "ollama";
  onChange: (mode: "auto" | "gemini" | "ollama") => void;
}

function GeneratorSelector({ value, onChange }: GeneratorSelectorProps) {
  return (
    <div className="space-y-2">
      <Label>{t("settings.generator.label")}</Label>
      <RadioGroup value={value} onValueChange={onChange}>
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="auto" id="gen-auto" />
          <Label htmlFor="gen-auto">
            {t("settings.generator.auto")}
            <p className="text-sm text-muted-foreground">
              {t("settings.generator.auto_desc")}
            </p>
          </Label>
        </div>
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="ollama" id="gen-ollama" />
          <Label htmlFor="gen-ollama">
            {t("settings.generator.local")}
            <p className="text-sm text-muted-foreground">
              {t("settings.generator.local_desc")}
            </p>
          </Label>
        </div>
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="gemini" id="gen-gemini" />
          <Label htmlFor="gen-gemini">
            {t("settings.generator.gemini")}
            <p className="text-sm text-muted-foreground">
              {t("settings.generator.gemini_desc")}
            </p>
          </Label>
        </div>
      </RadioGroup>
    </div>
  );
}
```

### 2. ChatGeneratorSelector Component (Chat Area)

File: `app_frontend/src/components/chat/ChatGeneratorSelector.tsx`

Dropdown kecil di dekat input chat (misal di samping tombol send atau di atas input):

```tsx
function ChatGeneratorSelector() {
  const { generatorMode, setGeneratorMode } = useModelStore();
  
  return (
    <Select value={generatorMode} onValueChange={setGeneratorMode}>
      <SelectTrigger className="w-[130px] h-8 text-xs">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="auto">⚡ Auto</SelectItem>
        <SelectItem value="ollama">🖥️ Local</SelectItem>
        <SelectItem value="gemini">☁️ Gemini</SelectItem>
      </SelectContent>
    </Select>
  );
}
```

### 3. Integrasi di SettingsDialog

Di `SettingsDialog.tsx`, tambahkan section baru:

```tsx
// Di dalam dialog, setelah section model atau sebelum section format
<GeneratorSelector
  value={generatorMode}
  onChange={(mode) => useModelStore.getState().setGeneratorMode(mode)}
/>
```

### 4. Integrasi di ChatInput

Di `ChatInput.tsx` (atau container chat), tambahkan `ChatGeneratorSelector` di atas input area atau di samping tombol:

```tsx
<div className="flex items-center gap-2 px-4 py-1">
  <ChatGeneratorSelector />
  {/* ... existing controls ... */}
</div>
```

### 5. i18n Keys

Tambah keys:

```json
{
  "settings": {
    "generator": {
      "label": "Generator TOR",
      "auto": "Auto (Rekomendasi)",
      "auto_desc": "Sistem memilih generator terbaik berdasarkan data",
      "local": "Local (Ollama)",
      "local_desc": "Gratis, offline, cocok untuk TOR sederhana",
      "gemini": "Cloud (Gemini)",
      "gemini_desc": "Kualitas tinggi, butuh koneksi internet"
    }
  }
}
```

## Catatan
- Settings selector menggunakan RadioGroup (pilihan jelas)
- Chat area selector menggunakan Select (dropdown compact)
- Keduanya sinkron ke store yang sama (`model-store.generatorMode`)
- Default: "auto"
