# Task 4: Frontend Types — `StreamDoneData`

## 1. Judul Task
Tambah TypeScript interface `StreamDoneData` untuk data yang diterima dari SSE `done` event.

## 2. Deskripsi
Frontend butuh type-safe interface untuk data yang dikirim backend saat streaming selesai (event `done`). Interface ini digunakan oleh API client, store, dan komponen UI.

## 3. Tujuan Teknis
- Interface `StreamDoneData` di `src/types/generate.ts`
- Matching dengan backend `sse_event("done", {...})` structure

## 4. Scope
### Yang dikerjakan
- Tambah `StreamDoneData` di `src/types/generate.ts`

### Yang tidak dikerjakan
- Tidak membuat API client (task 5)
- Tidak memodifikasi store (task 6)

## 5. Langkah Implementasi

### Step 1: Buka `src/types/generate.ts` dan tambahkan di akhir file

```typescript
export interface StreamDoneData {
  session_id: string;
  metadata: {
    generated_by: string;
    mode: string;
    word_count: number;
    has_assumptions: boolean;
  };
}
```

## 6. Output yang Diharapkan

```typescript
import type { StreamDoneData } from "@/types/generate";

const data: StreamDoneData = {
  session_id: "doc-abc123",
  metadata: {
    generated_by: "gemini-2.0-flash",
    mode: "standard",
    word_count: 1240,
    has_assumptions: false,
  },
};
```

## 7. Dependencies
- Tidak ada (bisa dikerjakan paralel dengan backend tasks)

## 8. Acceptance Criteria
- [ ] `StreamDoneData` ada di `src/types/generate.ts`
- [ ] `session_id: string` field ada
- [ ] `metadata` object dengan field: `generated_by`, `mode`, `word_count`, `has_assumptions`
- [ ] `npm run build` sukses

## 9. Estimasi
**Low** (~15 menit)
