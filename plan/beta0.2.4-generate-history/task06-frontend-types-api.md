# Task 6: Frontend Types + API Client

## 1. Judul Task
Buat TypeScript types dan API client functions untuk generate history.

## 2. Deskripsi
Frontend butuh TypeScript interfaces matching response backend dan fungsi-fungsi API untuk memanggil endpoint-endpoint baru.

## 3. Tujuan Teknis
- File `src/types/generate.ts` dengan interfaces `DocGenListItem` dan `DocGenDetail`
- Extend `src/api/generate.ts` dengan 3 fungsi baru

## 4. Scope
### Yang dikerjakan
- Buat `src/types/generate.ts`
- Tambah fungsi di `src/api/generate.ts`

### Yang tidak dikerjakan
- Tidak membuat store (task 7)
- Tidak mengubah UI (task 8-10)

## 5. Langkah Implementasi

### Step 1: Buat `src/types/generate.ts`

```typescript
import type { TORMetadata } from "./api";

export interface DocGenListItem {
  id: string;
  filename: string;
  file_size: number;
  style_name: string | null;
  status: "completed" | "failed" | "processing";
  word_count: number | null;
  created_at: string;
}

export interface DocGenDetail {
  id: string;
  filename: string;
  file_size: number;
  context: string;
  style_name: string | null;
  status: string;
  tor_content: string | null;
  metadata: TORMetadata | null;
  error_message: string | null;
  created_at: string;
}
```

### Step 2: Extend `src/api/generate.ts`

Tambahkan import dan 3 fungsi baru:

```typescript
import { apiGet, apiDelete } from "./client";
import type { DocGenListItem, DocGenDetail } from "@/types/generate";

// Existing generateFromDocument stays

export async function listGenerations(limit = 30): Promise<DocGenListItem[]> {
  return apiGet<DocGenListItem[]>(`/generate/history?limit=${limit}`);
}

export async function getGeneration(id: string): Promise<DocGenDetail> {
  return apiGet<DocGenDetail>(`/generate/${id}`);
}

export async function deleteGeneration(id: string): Promise<void> {
  await apiDelete(`/generate/${id}`);
}
```

## 6. Output yang Diharapkan

```typescript
import { listGenerations, getGeneration } from "@/api/generate";
const history = await listGenerations();     // DocGenListItem[]
const detail = await getGeneration("doc-abc"); // DocGenDetail
```

## 7. Dependencies
- Task 5 (backend endpoints harus ada untuk test)

## 8. Acceptance Criteria
- [ ] `src/types/generate.ts` berisi `DocGenListItem` dan `DocGenDetail`
- [ ] `listGenerations()`, `getGeneration()`, `deleteGeneration()` di `src/api/generate.ts`
- [ ] `npm run build` sukses

## 9. Estimasi
**Low** (~30 menit)
