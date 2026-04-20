# Task 01: i18n System Setup — Hook, Locales, Store Integration

## 1. Judul Task

Setup sistem internationalization (i18n) dengan translation hook, locale files, dan persistensi bahasa di Zustand

## 2. Deskripsi

Membuat fondasi sistem multi-bahasa untuk React frontend. Sistem ini menyimpan preferensi bahasa user di Zustand store (persisted ke localStorage), menyediakan hook `useTranslation()` yang bisa dipakai di semua komponen, dan menyiapkan dua file locale (ID dan EN).

## 3. Tujuan Teknis

- `src/i18n/types.ts` — Type-safe translation keys
- `src/i18n/locales/id.ts` — Bahasa Indonesia translations
- `src/i18n/locales/en.ts` — English translations
- `src/i18n/index.ts` — `useTranslation()` hook
- Update `src/stores/ui-store.ts` — tambah `language` state + `setLanguage` action

## 4. Scope

**Yang dikerjakan:**
- Struktur folder `src/i18n/`
- Hook `useTranslation()` → `{ t, language, setLanguage }`
- Locale files ID + EN (minimal 20 key untuk testing, sisanya task 02)
- Persistensi bahasa di `ui-store`

**Yang tidak dikerjakan:**
- Integrasi ke komponen (task 02)
- Language selector UI (task 03)

## 5. Langkah Implementasi

### 5.1 Buat `src/i18n/types.ts`

```typescript
export type Language = "id" | "en";
export type TranslationKey = keyof typeof import("./locales/id").default;
```

### 5.2 Buat `src/i18n/locales/id.ts`

File berisi object dengan semua string UI dalam Bahasa Indonesia. Contoh key yang wajib ada di awal:

```typescript
const id = {
  // Header
  "header.title": "Generator TOR",

  // Sidebar
  "sidebar.new_chat": "Obrolan baru",
  "sidebar.history": "RIWAYAT",
  "sidebar.tools": "ALAT",
  "sidebar.tool.chat": "Obrolan",
  "sidebar.tool.generate_doc": "Generate Dokumen",
  "sidebar.settings": "Pengaturan",
  "sidebar.api_connected": "API Terhubung",
  "sidebar.api_disconnected": "API Terputus",
  "sidebar.empty_conversations": "Belum ada percakapan",
  "sidebar.model_label": "Model AI",

  // Settings
  "settings.title": "Pengaturan",
  "settings.nav.general": "Umum",
  "settings.nav.format_tor": "Format TOR",
  "settings.nav.advanced": "Lanjutan",
  "settings.theme": "Tema",
  "settings.language": "Bahasa",
  "settings.general_title": "Umum",
  "settings.general_desc": "Pengaturan tampilan dan pengalaman pengguna.",

  // Chat
  "chat.input_placeholder": "Tanyakan apa saja...",
  "chat.empty_title": "Ceritakan kebutuhan TOR Anda",
  "chat.empty_desc": "Mulai chat untuk menyusun Term of Reference dengan bantuan AI secara interaktif.",
  "chat.thinking": "Sedang berpikir...",
  "chat.retry": "Coba lagi",
  "chat.error_default": "Gagal mendapat respons",

  // Generate
  "generate.title": "Generate TOR dari Dokumen",
  "generate.subtitle": "Upload dokumen sumber, AI otomatis membuat TOR.",
  "generate.upload_hint": "Klik untuk upload PDF, DOCX, TXT, atau MD",
  "generate.context_placeholder": "Konteks tambahan (opsional)...",
  "generate.submit": "Generate TOR",
  "generate.processing": "Sedang memproses...",
  "generate.result_title": "Hasil TOR",

  // Format TOR
  "format.title": "Format TOR",
  "format.desc": "Manajemen gaya dan struktur Term of Reference.",
  "format.new": "Format Baru",
  "format.active": "Aktif",
  "format.activate": "Aktifkan",
  "format.default_readonly": "Format bawaan sistem — read only, tidak bisa diedit.",
  "format.edit": "Edit Style",
  "format.done_edit": "Selesai Edit",
  "format.clone": "Tiru (Klon)",
  "format.clone_name": "Nama Format Baru",
  "format.clone_button": "Buat Salinan",
  "format.delete": "Hapus",
  "format.delete_warning": "Tindakan ini tidak bisa dibatalkan.",
  "format.delete_active_block": "Ubah style aktif ke format lain sebelum menghapus!",
  "format.delete_confirm": "Ya, Hapus Sekarang",
  "format.sections_title": "Struktur Seksi",
  "format.writing_style": "Gaya Penulisan",
  "format.required": "Wajib",
  "format.optional": "Opsional",
  "format.metric_language": "Bahasa",
  "format.metric_formality": "Formalitas",
  "format.metric_voice": "Voice",
  "format.metric_min_words": "Min. Kata",
  "format.metric_max_words": "Maks. Kata",
  "format.metric_numbering": "Penomoran",
  "format.custom_instruction_view": "Lihat Instruksi Kustom",
  "format.custom_instruction_empty": "(Tidak ada instruksi khusus)",
  "format.save_changes": "Simpan Perubahan",
  "format.save_success": "Style berhasil disimpan!",
  "format.save_failed": "Gagal menyimpan",
  "format.extract_title": "Ekstrak Format dari Dokumen",
  "format.extract_caption": "Upload contoh dokumen TOR lalu AI menganalisis struktur dan gaya bahasa untuk disimpan sebagai style baru.",
  "format.extract_upload": "Upload Dokumen TOR Referensi",
  "format.extract_name": "Nama style baru (opsional)",
  "format.extract_placeholder": "AI akan memberi nama otomatis jika kosong",
  "format.extract_button": "Ekstrak dengan AI",
  "format.extract_spinner": "AI sedang menganalisis gaya bahasa dan struktur...",
  "format.extract_saved": "Style berhasil diekstrak dan disimpan!",

  // Export
  "export.download": "Download",

  // Common
  "common.cancel": "Batal",
  "common.save": "Simpan",
  "common.loading": "Memuat...",
  "common.error": "Terjadi kesalahan",
} as const;

export default id;
```

### 5.3 Buat `src/i18n/locales/en.ts`

Mirror dari `id.ts` dalam bahasa Inggris. Referensi: `streamlit_app/utils/i18n.py` blok `en`.

### 5.4 Buat `src/i18n/index.ts`

```typescript
import { useUIStore } from "@/stores/ui-store";
import type { Language } from "./types";
import id from "./locales/id";
import en from "./locales/en";

const locales: Record<Language, Record<string, string>> = { id, en };

export function useTranslation() {
  const language = useUIStore(s => s.language);
  const setLanguage = useUIStore(s => s.setLanguage);

  function t(key: string, params?: Record<string, string | number>): string {
    let text = locales[language]?.[key] ?? locales.id[key] ?? key;
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        text = text.replace(`{${k}}`, String(v));
      });
    }
    return text;
  }

  return { t, language, setLanguage };
}
```

### 5.5 Update `src/stores/ui-store.ts`

Tambah `language: Language` ke state dan `setLanguage` ke actions. Persist di localStorage bersama `theme`.

```typescript
// Tambah ke interface UIStore
language: Language;
setLanguage: (lang: Language) => void;

// Tambah ke create
language: "id",
setLanguage: (language) => set({ language }),

// Update partialize
partialize: (state) => ({ theme: state.theme, language: state.language }),
```

## 6. Output yang Diharapkan

- `useTranslation()` hook bisa dipanggil di komponen manapun
- `t("header.title")` → "Generator TOR" (ID) atau "TOR Generator" (EN)
- `t("format.clone_name", { name: "Akademik" })` → "Salinan Akademik"
- Bahasa tersimpan di localStorage dan survive page reload

## 7. Dependencies

- Tidak ada (task pertama)

## 8. Acceptance Criteria

- [ ] Folder `src/i18n/` terbuat dengan struktur benar
- [ ] `id.ts` berisi minimal 70 translation keys
- [ ] `en.ts` berisi terjemahan English untuk semua key yang sama
- [ ] `useTranslation()` hook berfungsi dan return `{ t, language, setLanguage }`
- [ ] `t()` mendukung parameter interpolation `{name}`
- [ ] `ui-store` menyimpan `language` dan persist ke localStorage
- [ ] `npm run build` sukses tanpa error

## 9. Estimasi

High (2 jam)
