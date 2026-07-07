# Task 17 — i18n Translations for Tool Features

## Deskripsi

Menambahkan key-value translations untuk fitur tool system di file i18n bahasa Indonesia dan Inggris. Semua teks yang muncul di UI terkait tool system harus menggunakan i18n keys agar aplikasi bisa mendukung multi-bahasa.

---

## Tujuan Teknis

- Semua teks terkait tool system bisa diterjemahkan (ID + EN)
- ToolCallIndicator, settings toggle, dan error messages menggunakan i18n keys
- Konsisten dengan pattern i18n yang sudah ada di project
- Tipe `ToolTranslation` terdefinisi di types.ts

---

## Scope

### Termasuk

- Modifikasi `app_frontend/src/i18n/types.ts` — tambah interface:
  ```typescript
  export interface ToolTranslation {
    search_title: string;
    search_running: string;
    search_success: string;
    search_error: string;
    tool_call: string;
    web_search: string;
    settings_label: string;
    settings_description: string;
    settings_active: string;
    settings_inactive: string;
    no_tools: string;
    tool_available: string;
    tool_unavailable: string;
  }
  ```

- Modifikasi `app_frontend/src/i18n/locales/id.ts`:
  ```typescript
  tool: {
    search_title: "Mencari informasi di internet",
    search_running: "Mencari...",
    search_success: "Mendapatkan {count} hasil",
    search_error: "Pencarian gagal",
    tool_call: "Memanggil {tool}",
    web_search: "Pencarian internet",
    settings_label: "Izinkan AI mencari informasi di internet",
    settings_description: "AI bisa mencari data real-time dari web jika diperlukan",
    settings_active: "Aktif",
    settings_inactive: "Nonaktif",
    no_tools: "Tidak ada tool yang tersedia",
    tool_available: "{count} tool tersedia",
    tool_unavailable: "Tool tidak tersedia",
  }
  ```

- Modifikasi `app_frontend/src/i18n/locales/en.ts`:
  ```typescript
  tool: {
    search_title: "Searching the internet",
    search_running: "Searching...",
    search_success: "Got {count} results",
    search_error: "Search failed",
    tool_call: "Calling {tool}",
    web_search: "Web search",
    settings_label: "Allow AI to search the internet",
    settings_description: "AI can fetch real-time data from the web when needed",
    settings_active: "Active",
    settings_inactive: "Inactive",
    no_tools: "No tools available",
    tool_available: "{count} tool(s) available",
    tool_unavailable: "Tool unavailable",
  }
  ```

- Update komponen yang menggunakan teks tool:
  - `ToolCallIndicator.tsx` — ganti string hardcoded dengan `getTranslation()`
  - Settings toggle — ganti string hardcoded dengan `getTranslation()`

### Tidak Termasuk

- ToolCallIndicator component (Task 14)
- Tool toggle UI (Task 16)
- Logic tool calling

---

## Langkah Implementasi

### Langkah 1: Update `app_frontend/src/i18n/types.ts`

Tambah `ToolTranslation` interface dan tambahkan ke main translation interface.

### Langkah 2: Update `app_frontend/src/i18n/locales/id.ts`

Tambah section `tool` dengan nilai bahasa Indonesia.

### Langkah 3: Update `app_frontend/src/i18n/locales/en.ts`

Tambah section `tool` dengan nilai bahasa Inggris.

### Langkah 4: Update `ToolCallIndicator.tsx`

```tsx
import { getTranslation } from "@/i18n";

// Ganti string hardcoded
function getStatusConfig(status: ToolCallEvent["status"]) {
  const t = getTranslation();
  
  switch (status) {
    case "running":
      return {
        // ... styling ...
        text: t.tool.search_running,  // "Mencari informasi..."
      };
    case "success":
      return {
        // ... styling ...
        text: t.tool.search_success.replace("{count}", String(call.resultCount ?? 0)),
        // "Mendapatkan 5 hasil"
      };
    case "error":
      return {
        // ... styling ...
        text: call.error || t.tool.search_error,  // "Pencarian gagal"
      };
  }
}
```

### Langkah 5: Update Settings Toggle

```tsx
const t = getTranslation();

<Label>{t.tool.settings_label}</Label>
<p>{t.tool.settings_description}</p>
<span>{toolsEnabled ? t.tool.settings_active : t.tool.settings_inactive}</span>
```

---

## Output yang Diharapkan

- Semua teks tool system menggunakan i18n keys
- Bahasa Indonesia dan Inggris tersedia
- Komponen menggunakan `getTranslation()` untuk teks

---

## Dependencies

- **Task 14 (ToolCallIndicator)** — komponen yang perlu di-update
- **Task 16 (Tool Toggle UI)** — settings yang perlu di-update

---

## Acceptance Criteria

- [ ] `ToolTranslation` interface terdefinisi di types.ts
- [ ] Semua teks tool system ada di file i18n `id.ts`
- [ ] Semua teks tool system ada di file i18n `en.ts`
- [ ] `ToolCallIndicator` menggunakan `getTranslation()` untuk teks
- [ ] Settings toggle menggunakan `getTranslation()` untuk label
- [ ] Tidak ada string hardcoded untuk teks tool system
- [ ] Format `{count}` dan `{tool}` bisa di-replace dengan nilai dinamis

---

## Estimasi

**Low** (~30 menit)

| Aktivitas | Durasi |
|-----------|--------|
| Update types.ts | 5 menit |
| Update id.ts | 10 menit |
| Update en.ts | 10 menit |
| Update komponen | 10 menit |
