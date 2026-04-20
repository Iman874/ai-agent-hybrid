# Task 05: Type Extensions — TORStyleSection, TORStyleConfig

## 1. Judul Task

Memperbarui tipe TypeScript `TORStyle`, menambah `TORStyleSection` dan `TORStyleConfig` yang strongly-typed

## 2. Deskripsi

Tipe `TORStyle` saat ini menggunakan `Record<string, unknown>` untuk `sections` dan `config`. Task ini mengganti ke tipe yang spesifik agar edit form type-safe.

## 3. Tujuan Teknis

- `TORStyleSection` interface — title, description, required, format_hint, min_paragraphs
- `TORStyleConfig` interface — language, formality, voice, perspective, word counts, numbering, custom_instructions
- Update `TORStyle` — replace `Record<string, unknown>[]` dengan `TORStyleSection[]` dan `TORStyleConfig`

## 4. Scope

**Yang dikerjakan:**
- `src/types/api.ts` — tambah dan update types

**Yang tidak dikerjakan:**
- UI komponen
- API functions

## 5. Langkah Implementasi

### 5.1 Tambahkan di `src/types/api.ts`

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
```

### 5.2 Update `TORStyle` yang sudah ada

```typescript
// BEFORE
export interface TORStyle {
  id: string;
  name: string;
  description: string;
  is_default: boolean;
  is_active: boolean;
  sections: Record<string, unknown>[];
  config: Record<string, unknown>;
}

// AFTER
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

## 6. Output yang Diharapkan

- Autocomplete di editor untuk `style.config.language`, `style.sections[0].title`, dll.
- Type error jika field salah

## 7. Dependencies

- Tidak ada

## 8. Acceptance Criteria

- [ ] `TORStyleSection` dan `TORStyleConfig` terdefinisi
- [ ] `TORStyle.sections` bertipe `TORStyleSection[]`
- [ ] `TORStyle.config` bertipe `TORStyleConfig`
- [ ] `npm run build` sukses

## 9. Estimasi

Low (30 menit)
