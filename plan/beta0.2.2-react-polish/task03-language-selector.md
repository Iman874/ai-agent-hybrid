# Task 03: Language Selector — Bahasa Radio di General Settings

## 1. Judul Task

Mengubah static text "Bahasa Indonesia (Default)" menjadi radio selector fungsional ID/EN

## 2. Deskripsi

Di `GeneralSettings.tsx`, section Bahasa saat ini hanya menampilkan teks statis. Task ini menggantinya dengan `RadioGroup` yang fungsional untuk memilih antara Bahasa Indonesia dan English.

## 3. Tujuan Teknis

- RadioGroup dengan opsi "Bahasa Indonesia" dan "English"
- Terhubung ke `ui-store.language` via `useTranslation()`
- Perubahan bahasa langsung re-render semua teks

## 4. Scope

**Yang dikerjakan:**
- Update `src/components/settings/GeneralSettings.tsx` — replace static text dengan RadioGroup

**Yang tidak dikerjakan:**
- Locale file content (task 01)
- Komponen lain (task 02)

## 5. Langkah Implementasi

### 5.1 Update `GeneralSettings.tsx`

```tsx
import { useTranslation } from "@/i18n";

export function GeneralSettings() {
  const { t, language, setLanguage } = useTranslation();
  const theme = useUIStore(s => s.theme);
  const setTheme = useUIStore(s => s.setTheme);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Theme section - existing */}
      ...

      {/* Language section - UPDATED */}
      <div className="space-y-4 pt-4 border-t">
        <div className="flex flex-col gap-2">
          <Label className="text-base">{t("settings.language")}</Label>
          <RadioGroup
            value={language}
            onValueChange={(val) => setLanguage(val as "id" | "en")}
            className="flex gap-4 mt-2"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="id" id="lang-id" />
              <Label htmlFor="lang-id" className="font-normal cursor-pointer">
                Bahasa Indonesia
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="en" id="lang-en" />
              <Label htmlFor="lang-en" className="font-normal cursor-pointer">
                English
              </Label>
            </div>
          </RadioGroup>
        </div>
      </div>
    </div>
  );
}
```

## 6. Output yang Diharapkan

- Buka Settings → Umum → section Bahasa menampilkan 2 radio: ID dan EN
- Klik English → semua teks di dialog langsung berubah ke English
- Klik Bahasa Indonesia → kembali ke Indonesia
- Refresh page → bahasa tetap tersimpan

## 7. Dependencies

- Task 01 (i18n hook + store)
- Task 02 (i18n applied to GeneralSettings labels)

## 8. Acceptance Criteria

- [ ] Radio group menampilkan 2 opsi bahasa
- [ ] Switch ID ↔ EN berfungsi real-time
- [ ] Preferensi bahasa persist setelah reload
- [ ] Nama bahasa tidak diterjemahkan (tetap "Bahasa Indonesia" dan "English")

## 9. Estimasi

Low (30 menit)
