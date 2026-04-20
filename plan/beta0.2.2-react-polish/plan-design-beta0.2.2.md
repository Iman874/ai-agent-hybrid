# Beta 0.2.2 — React Frontend Polish: i18n + Format TOR CRUD + Style Extraction

## 1. Ringkasan

Version ini berfokus pada **3 pilar perbaikan** frontend React SPA:

1. **i18n (Internationalization)** — Menambahkan dukungan bahasa Inggris dan sistem terjemahan yang konsisten di seluruh komponen.
2. **Format TOR CRUD** — Mengubah halaman Format TOR dari skeleton statis menjadi halaman fungsional penuh: list, activate, edit, clone, delete — dengan aturan proteksi format default.
3. **Ekstraksi Format dari Dokumen** — Form upload dokumen TOR referensi agar AI menganalisis struktur dan gaya bahasa untuk disimpan sebagai style baru.

---

## 2. Referensi Arsitektur

### 2.1 Backend API Endpoints (Sudah Ada)

Semua endpoint di bawah sudah tersedia dari backend FastAPI dan sudah dikonsumsi oleh Streamlit. React hanya perlu memanggil endpoint yang sama melalui `api/client.ts`.

| Method   | Endpoint                         | Fungsi                        |
|----------|----------------------------------|-------------------------------|
| `GET`    | `/styles`                        | List semua styles             |
| `GET`    | `/styles/active`                 | Ambil style aktif             |
| `POST`   | `/styles/{id}/activate`          | Set style aktif               |
| `PUT`    | `/styles/{id}`                   | Update style (non-default)    |
| `DELETE` | `/styles/{id}`                   | Hapus style (non-default)     |
| `POST`   | `/styles/{id}/duplicate`         | Kloning style                 |
| `POST`   | `/styles`                        | Buat style baru               |
| `POST`   | `/styles/extract`               | Ekstrak style dari dokumen    |

### 2.2 Frontend API Client (`src/api/styles.ts` — Sudah Parsial)

Fungsi yang **sudah ada**: `listStyles`, `getActiveStyle`, `activateStyle`, `deleteStyle`, `duplicateStyle`.

Fungsi yang **belum ada**:
- `updateStyle(id, updates)` — `PUT /styles/{id}`
- `createStyle(data)` — `POST /styles`
- `extractStyle(file)` — `POST /styles/extract` (FormData upload)

### 2.3 Referensi UX: Streamlit `format_tab.py`

Streamlit sudah memiliki implementasi lengkap yang menjadi acuan:
- **Style selector** — dropdown + tombol "Jadikan Aktif"
- **Readonly view** — tabel seksi + metrik konfigurasi (bahasa, formalitas, voice, min/max kata, penomoran)
- **Edit form** — hanya untuk non-default styles (nama, deskripsi, seksi, konfigurasi penulisan)
- **Actions** — Edit / Clone / Delete (delete diblokir jika `is_active` atau `is_default`)
- **Extraction** — upload file → AI analyze → simpan sebagai style baru

---

## 3. Aturan Bisnis Format TOR

> [!IMPORTANT]
> **Aturan proteksi wajib ditegakkan di frontend:**

| Kondisi                          | Edit | Delete | Clone | Activate |
|----------------------------------|------|--------|-------|----------|
| `is_default === true`            | NO   | NO     | YES   | YES      |
| `is_default === false`           | YES  | YES*   | YES   | YES      |

*Delete diblokir jika style sedang aktif (`is_active`). User harus ganti style aktif terlebih dahulu.

---

## 4. Modul 1: Sistem i18n (Internationalization)

### 4.1 Arsitektur

Mengadopsi pola yang sama dari Streamlit (`utils/i18n.py`) ke React:

```
src/
├── i18n/
│   ├── index.ts          # useTranslation hook + provider
│   ├── locales/
│   │   ├── id.ts         # Bahasa Indonesia translations
│   │   └── en.ts         # English translations
│   └── types.ts          # TranslationKey type
```

### 4.2 Approach

- **Hook-based**: `useTranslation()` → `{ t, language, setLanguage }`
- **Zustand-persisted**: Bahasa disimpan di `ui-store` (sudah ada `theme`, tambah `language`)
- **Compile-time safe**: TypeScript type untuk semua translation keys
- **Fallback chain**: `selected language → id → key`

### 4.3 Translation Coverage

Mengambil semua string dari komponen yang ada:

| Komponen            | Strings |
|---------------------|---------|
| Sidebar             | ~12     |
| Header              | ~3      |
| ChatArea + Bubbles  | ~8      |
| Settings Dialog     | ~15     |
| Format TOR          | ~35     |
| Generate Document   | ~10     |
| **Total**           | **~83** |

### 4.4 Update GeneralSettings

```tsx
// Bahasa selector — dari statis ke fungsional
<RadioGroup value={language} onValueChange={setLanguage}>
  <RadioGroupItem value="id" /> Bahasa Indonesia
  <RadioGroupItem value="en" /> English
</RadioGroup>
```

---

## 5. Modul 2: Format TOR CRUD Full

### 5.1 Komponen Baru

```
src/components/settings/
├── FormatTORSettings.tsx     # [REWRITE] Container utama
├── StyleSelector.tsx         # [NEW] Dropdown + Activate button
├── StyleReadonlyView.tsx     # [NEW] Tabel seksi + metrik config
├── StyleEditForm.tsx         # [NEW] Form edit inline (non-default only)
├── StyleActions.tsx          # [NEW] Edit/Clone/Delete buttons
├── StyleExtractForm.tsx      # [NEW] Upload + extract via AI
```

### 5.2 FormatTORSettings (Container)

Flow utama:
1. Fetch styles dari API (`listStyles()`)
2. Render `<StyleSelector>` — user pilih style, tombol "Aktifkan"
3. Render `<StyleReadonlyView>` — tampilkan detail readonly
4. Render `<StyleActions>` — tombol Edit / Clone / Delete  
5. Jika editing & non-default → render `<StyleEditForm>`
6. Render `<StyleExtractForm>` — di section "Pengaturan Lanjutan"

### 5.3 StyleSelector

```tsx
// Select style + Activate
<Select value={selectedId} onValueChange={setSelectedId}>
  {styles.map(s => (
    <SelectItem key={s.id} value={s.id}>
      {s.name} {s.is_active ? "(Aktif)" : ""}
    </SelectItem>
  ))}
</Select>
{selectedId !== activeId && (
  <Button onClick={() => activateStyle(selectedId)}>Jadikan Aktif</Button>
)}
```

### 5.4 StyleReadonlyView

Menampilkan:
- **Struktur Seksi** — tabel: No, Nama Seksi, Tipe (Wajib/Opsional), Format, Min Paragraf
- **Gaya Penulisan** — grid metrik: Bahasa, Formalitas, Voice, Min/Max Kata, Penomoran
- **Instruksi Kustom** — collapsible text

### 5.5 StyleEditForm

Form inline (hanya muncul jika `is_default === false` dan user klik "Edit"):
- **Informasi Umum**: nama, deskripsi
- **Gaya Penulisan**: bahasa, formalitas, voice, perspektif, min/max kata, penomoran, instruksi kustom
- **Edit Seksi**: accordion per-section — judul, instruksi AI, wajib/tidak, format hint, min paragraf
- **Tombol Simpan**: `PUT /styles/{id}` → refresh list

### 5.6 StyleActions

```tsx
<div className="flex gap-2">
  {!isDefault && <Button onClick={toggleEdit}>Edit Style</Button>}
  <ClonePopover styleId={id} styleName={name} />
  {!isDefault && !isActive && <DeleteConfirmPopover styleId={id} />}
</div>
```

### 5.7 StyleExtractForm

```tsx
// Upload TOR referensi → AI extract → save as new style
<input type="file" accept=".pdf,.docx,.txt,.md" />
<Input placeholder="Nama style baru (opsional)" />
<Button onClick={handleExtract}>Ekstrak dengan AI</Button>
// → POST /styles/extract → POST /styles (save)
```

---

## 6. Modul 3: API Client Extensions

### 6.1 Fungsi Baru di `src/api/styles.ts`

```typescript
// UPDATE style
export async function updateStyle(styleId: string, updates: Record<string, unknown>): Promise<TORStyle> {
  return apiPut<TORStyle>(`/styles/${styleId}`, updates);
}

// CREATE new style  
export async function createStyle(data: Record<string, unknown>): Promise<TORStyle> {
  return apiPost<TORStyle>(`/styles`, data);
}

// EXTRACT style from document
export async function extractStyle(file: File): Promise<Record<string, unknown>> {
  return apiPostFormData<Record<string, unknown>>(`/styles/extract`, formData);
}
```

### 6.2 `apiPut` Helper di `client.ts`

Fungsi `apiPut` belum ada di client — perlu ditambahkan:

```typescript
export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<T>(response);
}
```

---

## 7. Type Extensions (`src/types/api.ts`)

Perlu ditambahkan/diperbaiki:

```typescript
export interface TORStyleSection {
  title: string;
  description: string;
  required: boolean;
  format_hint: string;
  min_paragraphs: number;
}

export interface TORStyleConfig {
  language: "id" | "en";
  formality: "formal" | "semi_formal" | "informal";
  voice: "active" | "passive";
  perspective: "first_person" | "third_person";
  min_word_count: number;
  max_word_count: number;
  numbering_style: "numeric" | "roman" | "none";
  custom_instructions: string;
}

// Update TORStyle existing
export interface TORStyle {
  id: string;
  name: string;
  description: string;
  is_default: boolean;
  is_active: boolean;
  sections: TORStyleSection[];
  config: TORStyleConfig;
}
```

---

## 8. Task Breakdown

| #   | Task                          | Scope                                        | Estimasi |
|-----|-------------------------------|----------------------------------------------|----------|
| T01 | i18n System Setup             | `src/i18n/`, hook, locales ID+EN, ui-store   | 2 jam    |
| T02 | i18n Integration              | Apply `t()` ke semua 15+ komponen            | 2 jam    |
| T03 | Language Selector             | Update `GeneralSettings.tsx` — radio EN/ID   | 30 min   |
| T04 | API Client Extensions         | `apiPut`, `updateStyle`, `createStyle`, `extractStyle` | 1 jam |
| T05 | Type Extensions               | `TORStyleSection`, `TORStyleConfig`          | 30 min   |
| T06 | StyleSelector Component       | Dropdown + activate button                   | 1 jam    |
| T07 | StyleReadonlyView Component   | Section table + config metrics               | 1.5 jam  |
| T08 | StyleActions Component        | Edit/Clone/Delete buttons + popovers         | 1.5 jam  |
| T09 | StyleEditForm Component       | Full inline edit form                        | 2 jam    |
| T10 | StyleExtractForm Component    | Upload + AI extract + save                   | 1.5 jam  |
| T11 | FormatTOR Container Rewrite   | Wire all sub-components together             | 1 jam    |
| T12 | QA + Build Verification       | `npm run build`, dark mode, responsive       | 1 jam    |

**Total: ~15 jam kerja**

---

## 9. Dependency Graph

```
T01 → T02 → T03
T04 → T05 → T06 → T07 → T08 → T09 → T10 → T11
T11 + T03 → T12
```

T01-T03 (i18n) dan T04-T11 (Format TOR) bisa dikerjakan **paralel** karena tidak saling bergantung, lalu digabung di T12 (QA).

---

## 10. Verification Plan

### Automated
- `npm run build` → zero errors
- Semua tipe TypeScript valid

### Manual
- Switch bahasa ID ↔ EN → semua string berubah
- List styles dari backend → muncul di selector
- Activate style → badge "Aktif" pindah
- Edit custom style → simpan → data terpersistens
- Clone style → duplikat muncul di list
- Delete non-default + non-active → berhasil
- Delete default → tombol delete tidak muncul
- Delete active → tombol delete disabled + pesan warning
- Extract dari PDF → AI analyze → style baru tersimpan
- Dark mode → semua komponen baru konsisten
