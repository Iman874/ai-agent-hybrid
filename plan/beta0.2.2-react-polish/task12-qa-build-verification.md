# Task 12: QA + Build Verification — Dark Mode, Responsive, Final Testing

## 1. Judul Task

Verifikasi akhir: build production, dark mode konsistensi, responsive, dan validasi semua fitur baru

## 2. Deskripsi

Task terakhir: memastikan semua fitur baru (i18n, Format TOR CRUD, Extraction) berfungsi end-to-end tanpa regresi, lolos `npm run build`, dan tampil konsisten di dark/light mode.

## 3. Tujuan Teknis

- `npm run build` → zero errors
- Semua komponen baru dark-mode compatible
- i18n switching ID ↔ EN → zero broken strings
- Format TOR CRUD full cycle tested

## 4. Scope

**Yang dikerjakan:**
- Build verification
- Dark mode audit untuk komponen baru (StyleSelector, StyleReadonlyView, StyleEditForm, StyleActions, StyleExtractForm)
- i18n completeness check — tidak ada hardcoded string yang tertinggal
- Update `src/lib/constants.ts` — bump version ke 0.2.2

**Yang tidak dikerjakan:**
- Automated tests (future versioning)

## 5. Langkah Implementasi

### 5.1 Run `npm run build`

Pastikan zero TypeScript errors dan zero Vite build errors.

### 5.2 Dark Mode Audit

Checklist komponen baru:
- [ ] `StyleSelector` — select input, button styles
- [ ] `StyleReadonlyView` — table header, metric cards, collapsible
- [ ] `StyleActions` — popover backgrounds, button variants
- [ ] `StyleEditForm` — input fields, select dropdowns, accordion
- [ ] `StyleExtractForm` — upload zone, success/error messages

Semua harus menggunakan semantic colors:
- `bg-background`, `bg-muted`, `bg-muted/40`
- `text-foreground`, `text-muted-foreground`
- `border-border`
- Tidak ada hardcoded hex colors kecuali code block (#1e1e1e)

### 5.3 i18n Coverage Check

- Buka Settings → switch EN
- Navigasi ke setiap section (Umum, Format TOR, Lanjutan)
- Verify semua text sudah dalam English
- Switch back ke ID → semua text kembali ke Indonesia
- Check: sidebar, header, chat area, generate page

### 5.4 Format TOR Full Cycle Test

1. List styles → minimal 2 styles muncul
2. Select style → detail tampil
3. Activate non-active style → berhasil
4. Clone style → duplikat muncul
5. Edit custom style → simpan → data terupdate
6. Delete custom non-active style → berhasil
7. Try delete default → tombol TIDAK ada
8. Try delete active → warning message
9. Extract from document → upload → AI process → new style saved

### 5.5 Version Bump

Update `src/lib/constants.ts`:

```typescript
export const APP_VERSION = "0.2.2";
```

## 6. Output yang Diharapkan

- `npm run build` → `✓ built in XXXms` tanpa error
- Semua fitur baru berfungsi end-to-end
- Dark/light mode konsisten
- Tidak ada console errors

## 7. Dependencies

- Task 01–11 (semua task sebelumnya)

## 8. Acceptance Criteria

- [ ] `npm run build` → zero errors
- [ ] Dark mode → semua komponen Format TOR konsisten
- [ ] Light mode → semua komponen Format TOR konsisten
- [ ] i18n ID ↔ EN → semua string berubah tanpa break
- [ ] Format TOR CRUD: list, activate, edit, clone, delete → semua berfungsi
- [ ] Default protection: edit/delete blocked untuk default styles
- [ ] Active protection: delete blocked untuk active style
- [ ] Style extraction dari dokumen berfungsi
- [ ] Version bumped ke 0.2.2
- [ ] No console errors di production build

## 9. Estimasi

Medium (1 jam)
