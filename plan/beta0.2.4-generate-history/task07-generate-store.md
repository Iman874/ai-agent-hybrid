# Task 7: Zustand Store — `generate-store.ts`

## 1. Judul Task
Buat Zustand store untuk mengelola state halaman Generate Document.

## 2. Deskripsi
Semua state untuk halaman Generate Document saat ini ada di `useState` lokal (`GenerateContainer`), menyebabkan data hilang saat reload. Store ini memindahkan state ke Zustand agar persisten dan bisa diakses dari komponen manapun.

## 3. Tujuan Teknis
- Store mengelola: history list, active result, generating state
- Actions: `fetchHistory`, `viewResult`, `clearActiveResult`, `generateFromDoc`, `deleteGeneration`
- Fetch history on mount, refresh setelah generate/delete

## 4. Scope
### Yang dikerjakan
- Buat `src/stores/generate-store.ts`

### Yang tidak dikerjakan
- Tidak mengubah UI (task 8-10)

## 5. Langkah Implementasi

### Step 1: Buat `src/stores/generate-store.ts`

```typescript
import { create } from "zustand";
import * as genApi from "@/api/generate";
import type { DocGenListItem, DocGenDetail } from "@/types/generate";
import type { GenerateResponse } from "@/types/api";

interface GenerateStore {
  // History
  history: DocGenListItem[];
  isLoadingHistory: boolean;
  fetchHistory: () => Promise<void>;

  // Active result (viewing detail)
  activeResult: DocGenDetail | null;
  isLoadingResult: boolean;
  viewResult: (id: string) => Promise<void>;
  clearActiveResult: () => void;

  // Last generate response (immediate result after generate)
  lastGenerateResponse: GenerateResponse | null;
  isGenerating: boolean;
  generateFromDoc: (file: File, context?: string, styleId?: string) => Promise<void>;
  clearLastResponse: () => void;

  // Delete
  deleteGeneration: (id: string) => Promise<void>;
}

export const useGenerateStore = create<GenerateStore>((set, get) => ({
  history: [],
  isLoadingHistory: false,

  fetchHistory: async () => {
    set({ isLoadingHistory: true });
    try {
      const data = await genApi.listGenerations(30);
      set({ history: data, isLoadingHistory: false });
    } catch {
      set({ isLoadingHistory: false });
    }
  },

  activeResult: null,
  isLoadingResult: false,

  viewResult: async (id) => {
    set({ isLoadingResult: true });
    try {
      const detail = await genApi.getGeneration(id);
      set({ activeResult: detail, isLoadingResult: false, lastGenerateResponse: null });
    } catch {
      set({ isLoadingResult: false });
    }
  },

  clearActiveResult: () => set({ activeResult: null }),

  lastGenerateResponse: null,
  isGenerating: false,

  generateFromDoc: async (file, context, styleId) => {
    set({ isGenerating: true, lastGenerateResponse: null });
    try {
      const result = await genApi.generateFromDocument(file, context, styleId);
      set({ lastGenerateResponse: result, isGenerating: false });
      // Refresh history
      get().fetchHistory();
    } catch (e) {
      set({ isGenerating: false });
      // Refresh to show failed entry
      get().fetchHistory();
      throw e;
    }
  },

  clearLastResponse: () => set({ lastGenerateResponse: null }),

  deleteGeneration: async (id) => {
    await genApi.deleteGeneration(id);
    set(state => ({
      history: state.history.filter(h => h.id !== id),
      activeResult: state.activeResult?.id === id ? null : state.activeResult,
    }));
  },
}));
```

## 6. Output yang Diharapkan

```typescript
const { history, fetchHistory, generateFromDoc, viewResult } = useGenerateStore();

// Fetch history on mount
useEffect(() => { fetchHistory(); }, []);

// Generate from document
await generateFromDoc(myFile, "konteks", "style-123");
// → lastGenerateResponse is set, history is refreshed

// View past result
await viewResult("doc-abc");
// → activeResult is set with full detail
```

## 7. Dependencies
- Task 6 (types + API client)

## 8. Acceptance Criteria
- [ ] Store di `src/stores/generate-store.ts` dengan semua states dan actions
- [ ] `fetchHistory()` memanggil `listGenerations()` dari API
- [ ] `generateFromDoc()` memanggil `generateFromDocument()` → set `lastGenerateResponse` → refresh history
- [ ] `viewResult()` memanggil `getGeneration()` → set `activeResult`
- [ ] `deleteGeneration()` memanggil `deleteGeneration()` → remove dari local list
- [ ] `npm run build` sukses

## 9. Estimasi
**Medium** (~1 jam)
