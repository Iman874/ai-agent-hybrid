# Task 04: API Client Extensions — apiPut, updateStyle, createStyle, extractStyle

## 1. Judul Task

Menambahkan fungsi API yang belum ada untuk CRUD Format TOR: `apiPut`, `updateStyle`, `createStyle`, `extractStyle`

## 2. Deskripsi

Frontend sudah punya beberapa fungsi styles API (`listStyles`, `activateStyle`, `deleteStyle`, `duplicateStyle`). Task ini menambahkan fungsi-fungsi yang belum ada agar CRUD lengkap.

## 3. Tujuan Teknis

- `apiPut` helper di `src/api/client.ts`
- `updateStyle(id, updates)` di `src/api/styles.ts`
- `createStyle(data)` di `src/api/styles.ts`
- `extractStyle(file)` di `src/api/styles.ts`

## 4. Scope

**Yang dikerjakan:**
- `src/api/client.ts` — tambah `apiPut`
- `src/api/styles.ts` — tambah 3 fungsi baru

**Yang tidak dikerjakan:**
- UI komponen (task 06-11)
- Backend endpoint (sudah ada)

## 5. Langkah Implementasi

### 5.1 Tambah `apiPut` di `src/api/client.ts`

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

### 5.2 Tambah fungsi di `src/api/styles.ts`

```typescript
import { apiGet, apiPost, apiPut, apiDelete, apiPostFormData } from "./client";
import type { TORStyle } from "@/types/api";

// ... existing functions ...

export async function updateStyle(
  styleId: string,
  updates: Record<string, unknown>,
): Promise<TORStyle> {
  return apiPut<TORStyle>(`/styles/${styleId}`, updates);
}

export async function createStyle(
  data: Record<string, unknown>,
): Promise<TORStyle> {
  return apiPost<TORStyle>("/styles", data);
}

export async function extractStyle(file: File): Promise<Record<string, unknown>> {
  const formData = new FormData();
  formData.append("file", file);
  return apiPostFormData<Record<string, unknown>>("/styles/extract", formData);
}
```

## 6. Output yang Diharapkan

- `updateStyle("abc", { name: "Baru" })` → `PUT /api/v1/styles/abc` → returns updated TORStyle
- `createStyle({ name: "Custom" })` → `POST /api/v1/styles` → returns new TORStyle
- `extractStyle(file)` → `POST /api/v1/styles/extract` → returns extracted style object

## 7. Dependencies

- Tidak ada (fungsi API mandiri)

## 8. Acceptance Criteria

- [ ] `apiPut` ada di `client.ts`
- [ ] `updateStyle` ada dan memanggil `PUT /styles/{id}`
- [ ] `createStyle` ada dan memanggil `POST /styles`
- [ ] `extractStyle` ada dan memanggil `POST /styles/extract` dengan FormData
- [ ] Import paths benar
- [ ] `npm run build` sukses

## 9. Estimasi

Low (30 menit — 1 jam)
