# Task 08 — Frontend: i18n Keys untuk Chat-to-Generate Streaming

## 1. Judul Task

Menambahkan translation keys baru untuk fitur Chat-to-Generate di file i18n Indonesia dan Inggris.

## 2. Deskripsi

Fitur baru ini menampilkan beberapa teks baru di UI yang perlu diterjemahkan ke dua bahasa (Indonesia dan Inggris). Task ini menambahkan semua keys yang dibutuhkan oleh komponen-komponen di task 05 dan 06.

## 3. Tujuan Teknis

- Menambahkan keys baru di `src/i18n/locales/id.ts` dan `src/i18n/locales/en.ts`.
- Semua teks hardcoded di task sebelumnya diganti dengan `t("key")`.

## 4. Scope

### Yang dikerjakan
- Tambahkan keys di file `id.ts` dan `en.ts`.
- Ganti teks hardcoded di `ChatGeneratePrompt.tsx`, `StreamingResult.tsx`, dan `chat-store.ts`.

### Yang tidak dikerjakan
- Menambahkan bahasa baru selain ID dan EN.
- Refactor i18n structure.

## 5. Langkah Implementasi

### Step 1: Identifikasi semua teks baru
  
| Lokasi | Teks ID | Key |
|--------|---------|-----|
| `ChatGeneratePrompt` | "Buat TOR Sekarang" | `chat.generate_now` |
| `chat-store.ts` (transisi) | "✅ Semua informasi sudah lengkap! Memulai pembuatan dokumen TOR..." | `chat.ready_generating` |
| `StreamingResult` (source) | "Sumber: Sesi chat" | `generate.source_chat` |
| `StreamingResult` (source) | "Sumber: Upload dokumen" | `generate.source_document` |

### Step 2: Tambahkan keys di `src/i18n/locales/id.ts`

Dalam section `chat`:
```typescript
generate_now: "Buat TOR Sekarang",
ready_generating: "✅ Semua informasi sudah lengkap! Memulai pembuatan dokumen TOR...",
```

Dalam section `generate`:
```typescript
source_chat: "Sumber: Sesi chat",
source_document: "Sumber: Upload dokumen",
```

### Step 3: Tambahkan keys di `src/i18n/locales/en.ts`

Dalam section `chat`:
```typescript
generate_now: "Generate TOR Now",
ready_generating: "✅ All information is complete! Starting TOR document generation...",
```

Dalam section `generate`:
```typescript
source_chat: "Source: Chat session",
source_document: "Source: Document upload",
```

### Step 4: Ganti hardcoded text di komponen

Di `ChatGeneratePrompt.tsx`:
```tsx
// Ganti "Buat TOR Sekarang":
{t("chat.generate_now")}
```

Di `chat-store.ts` (finalizeStream):
```typescript
// Untuk teks transisi, simpan key dan resolve di komponen, 
// ATAU gunakan teks statis karena store tidak bisa akses hook t()
// Solusi pragmatis: gunakan teks Indonesia sebagai default 
// (karena ini system message, bukan label UI)
content: "✅ Semua informasi sudah lengkap! Memulai pembuatan dokumen TOR...",
```

Di `StreamingResult.tsx`:
```tsx
{streamSource === "chat" && (
  <p className="text-xs text-muted-foreground mt-0.5">
    {t("generate.source_chat")}
  </p>
)}
```

## 6. Output yang Diharapkan

Semua teks UI terkait fitur baru tersedia dalam bahasa Indonesia dan Inggris. Switching bahasa via Settings menampilkan teks yang tepat.

## 7. Dependencies

- **Task 05** dan **Task 06** harus selesai (komponen yang menggunakan teks ini harus sudah ada).

## 8. Acceptance Criteria

- [ ] Keys `chat.generate_now` dan `chat.ready_generating` tersedia di `id.ts` dan `en.ts`.
- [ ] Keys `generate.source_chat` dan `generate.source_document` tersedia di `id.ts` dan `en.ts`.
- [ ] Semua teks UI menggunakan `t("key")` bukan hardcoded string.
- [ ] Switching bahasa ID ↔ EN menampilkan teks yang benar.
- [ ] `npm run build` → zero TypeScript errors.

## 9. Estimasi

**Low** — ~20 menit kerja.
