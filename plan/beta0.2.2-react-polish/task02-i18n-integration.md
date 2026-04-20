# Task 02: i18n Integration — Apply `t()` ke Semua Komponen

## 1. Judul Task

Mengganti semua hardcoded string di komponen React dengan `t()` translation calls

## 2. Deskripsi

Setelah sistem i18n siap (task 01), task ini mengintegrasikan `useTranslation()` ke seluruh komponen UI yang ada. Setiap string teks yang tampil ke user harus diganti dari hardcoded ke `t("key")`.

## 3. Tujuan Teknis

- Semua komponen menggunakan `t()` untuk menampilkan string
- Tidak ada lagi hardcoded Indonesian string di JSX

## 4. Scope

**Yang dikerjakan:**
- `Sidebar.tsx` — semua label navigasi, tools, session
- `Header.tsx` — title
- `ChatArea.tsx` — empty state text
- `ChatInput.tsx` — placeholder
- `EmptyState.tsx` — title, description
- `ThinkingIndicator.tsx` — "Sedang berpikir..."
- `RetryButton.tsx` — "Coba lagi"
- `MessageBubble.tsx` — error default text
- `SettingsDialog.tsx` — navigation labels
- `GeneralSettings.tsx` — section titles
- `FormatTORSettings.tsx` — semua label (akan di-rewrite di task 11, tapi label dasar tetap)
- `UploadForm.tsx` — title, subtitle, button text
- `GenerateResult.tsx` — title
- `TORPreview.tsx` — header text

**Yang tidak dikerjakan:**
- Language selector UI (task 03)
- Menambah key baru yang belum ada di locale (jika perlu, tambahkan)

## 5. Langkah Implementasi

### 5.1 Pattern umum per komponen

```tsx
// BEFORE
export function EmptyState() {
  return (
    <h2>Ceritakan kebutuhan TOR Anda</h2>
    <p>Mulai chat untuk menyusun...</p>
  );
}

// AFTER
import { useTranslation } from "@/i18n";

export function EmptyState() {
  const { t } = useTranslation();
  return (
    <h2>{t("chat.empty_title")}</h2>
    <p>{t("chat.empty_desc")}</p>
  );
}
```

### 5.2 Daftar komponen dan string yang harus diganti

| Komponen | Strings to replace |
|---|---|
| `Sidebar.tsx` | "Obrolan baru", "RIWAYAT", "ALAT", "Obrolan", "Generate Dokumen", "Pengaturan", "API Terhubung/Terputus" |
| `Header.tsx` | "Generator TOR" |
| `EmptyState.tsx` | title, description |
| `ChatInput.tsx` | placeholder |
| `ThinkingIndicator.tsx` | "Sedang berpikir..." |
| `RetryButton.tsx` | "Coba lagi" |
| `MessageBubble.tsx` | "Gagal mendapat respons" |
| `SettingsDialog.tsx` | "Pengaturan", nav labels |
| `GeneralSettings.tsx` | "Umum", "Pengaturan tampilan...", "Tema", "Bahasa" |
| `UploadForm.tsx` | title, subtitle, button, placeholder |
| `GenerateResult.tsx` | "Hasil TOR" |
| `TORPreview.tsx` | "Dokumen TOR Tersedia" |

### 5.3 Tambahkan key baru ke locale files jika ditemukan string yang belum ada

## 6. Output yang Diharapkan

- Switch bahasa di store → semua UI text berubah secara reaktif
- Tidak ada Indonesian string yang hardcoded di JSX (kecuali placeholder komponen yang belum di-build)

## 7. Dependencies

- Task 01 (i18n system setup)

## 8. Acceptance Criteria

- [ ] Semua 14+ komponen menggunakan `t()` untuk teks
- [ ] Ganti bahasa di store → UI berubah tanpa reload
- [ ] Tidak ada regresi visual (layout tetap sama)
- [ ] `npm run build` sukses

## 9. Estimasi

High (2 jam)
