# Beta 0.2.4 — Generate Document History & Persistence

## 1. Ringkasan

Version ini berfokus pada **persistensi dan riwayat** fitur "Generate TOR dari Dokumen":

1. **Bug Fix** — State di halaman "Generate Dokumen" hidup sepenuhnya dalam `useState` (`GenerateContainer.tsx`). Begitu user reload, pindah tab, atau navigasi — semua data hilang: file yang diupload, hasil TOR, metadata. Tidak ada yang tersimpan di database maupun store.
2. **Fitur Baru: Riwayat Generate** — Menyediakan tabel riwayat semua dokumen yang pernah di-generate, lengkap dengan nama file sumber, tanggal, status, dan akses cepat ke hasil TOR + export.

Cakupan perubahan: **Database** (migration baru), **Backend** (API endpoints baru), **Frontend** (Zustand store + UI komponen baru).

---

## 2. Analisis Masalah Saat Ini

### 2.1 Arsitektur Sekarang (Broken)

```
┌──────────────────────────────┐
│   GenerateContainer.tsx      │
│   useState<GenerateResponse> │  ← Ephemeral! Hilang saat reload
│   ┌───────────┐ ┌──────────┐│
│   │UploadForm │→│GenResult ││
│   └───────────┘ └──────────┘│
└──────────────────────────────┘
         ↓ POST /generate/from-document
┌──────────────────────────────┐
│   Backend generate_doc.py    │
│   - Parse file               │
│   - Call Gemini              │
│   - Store di tor_cache       │  ← Hanya cache by session_id (volatile "doc-xxx")
│   - Return GenerateResponse  │
└──────────────────────────────┘
```

**Masalah:**
1. Frontend: `GenerateContainer` menggunakan `useState` lokal → reload = state hilang
2. Backend: session_id di-generate sebagai `doc-{uuid}` tetapi **tidak** disimpan ke tabel `sessions` → tidak ada record tetap
3. `tor_cache` memiliki FK ke `sessions(id)` tetapi `doc-xxx` bukan session yang valid → data cache bisa hilang
4. Tidak ada endpoint untuk list/view riwayat generate dokumen
5. Nama file sumber, konteks tambahan, dan style yang digunakan tidak tersimpan

### 2.2 Arsitektur Target

```
┌──────────────────────────────────────────────────────┐
│   GenerateContainer.tsx                              │
│   ┌──────────────────────────────────────────────────┤
│   │ GenerateHistoryList  ← Daftar riwayat dari API   │
│   │ UploadForm           ← Upload dokumen baru        │
│   │ GenerateResult       ← Lihat hasil TOR            │
│   │ (state via generate-store.ts)                     │
│   └──────────────────────────────────────────────────┤
└──────────────────────────────────────────────────────┘
         ↓ POST /generate/from-document (IMPROVED)
         ↓ GET  /generate/history          (NEW)
         ↓ GET  /generate/{id}             (NEW)
         ↓ DELETE /generate/{id}           (NEW)
┌──────────────────────────────────────────────────────┐
│   Backend                                            │
│   ┌────────────────────────────────────────┐         │
│   │ Tabel: document_generations (NEW)      │         │
│   │ - id, filename, context, style_id      │         │
│   │ - status, tor_content, metadata_json   │         │
│   │ - created_at                           │         │
│   └────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────┘
```

---

## 3. Database: Migration Baru

### 3.1 Tabel `document_generations`

```sql
-- Migration 006: Document generation history
CREATE TABLE IF NOT EXISTS document_generations (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    context TEXT DEFAULT '',
    style_id TEXT,
    style_name TEXT,
    status TEXT DEFAULT 'processing'
        CHECK(status IN ('processing','completed','failed')),
    tor_content TEXT,
    metadata_json TEXT DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_docgen_created ON document_generations(created_at DESC);
```

**Penjelasan kolom:**
| Kolom | Tipe | Fungsi |
|-------|------|--------|
| `id` | TEXT PK | UUID, contoh `doc-a2184d4d` |
| `filename` | TEXT | Nama file asli yang diupload |
| `file_size` | INT | Ukuran file dalam bytes |
| `context` | TEXT | Konteks tambahan dari user |
| `style_id` | TEXT | ID style TOR yang digunakan |
| `style_name` | TEXT | Nama style (snapshot, agar tetap ada walau style dihapus) |
| `status` | TEXT | `processing` → `completed` / `failed` |
| `tor_content` | TEXT | Hasil TOR markdown (null saat processing) |
| `metadata_json` | TEXT | JSON metadata: model, tokens, word_count, dll |
| `error_message` | TEXT | Pesan error jika failed |
| `created_at` | TIMESTAMP | Kapan di-generate |

> [!IMPORTANT]
> Tabel ini **terpisah** dari `sessions` dan `tor_cache`. Generate-from-document adalah fitur mandiri, bukan chat session. Ini menghindari polusi data di `sessions` table.

---

## 4. Backend: API Changes

### 4.1 Update `POST /generate/from-document` (`generate_doc.py`)

**Perubahan:**
1. Sebelum proses, insert record ke `document_generations` dengan `status='processing'`
2. Setelah berhasil, update record: `status='completed'`, simpan `tor_content` + `metadata_json`
3. Jika gagal, update: `status='failed'`, simpan `error_message`
4. Return `id` di response agar frontend bisa mereferensi

### 4.2 Endpoint Baru: `GET /generate/history`

```python
@router.get("/generate/history")
async def list_generations(limit: int = 30):
    """List riwayat generate dari dokumen, urut terbaru."""
    # SELECT id, filename, file_size, style_name, status, 
    #        created_at, metadata_json
    # FROM document_generations
    # ORDER BY created_at DESC LIMIT ?
```

**Response:** List of `DocGenerationListItem`:
```python
class DocGenerationListItem(BaseModel):
    id: str
    filename: str
    file_size: int
    style_name: str | None
    status: str  # "completed" | "failed" | "processing"
    word_count: int | None
    created_at: str
```

### 4.3 Endpoint Baru: `GET /generate/{id}`

```python
@router.get("/generate/{gen_id}")
async def get_generation(gen_id: str):
    """Ambil detail satu generate result beserta TOR content."""
```

**Response:** `DocGenerationDetail`:
```python
class DocGenerationDetail(BaseModel):
    id: str
    filename: str
    file_size: int
    context: str
    style_name: str | None
    status: str
    tor_content: str | None
    metadata: TORMetadata | None
    error_message: str | None
    created_at: str
```

### 4.4 Endpoint Baru: `DELETE /generate/{id}`

```python
@router.delete("/generate/{gen_id}")
async def delete_generation(gen_id: str):
    """Hapus record riwayat generate."""
```

### 4.5 Repository: `doc_generation_repo.py`

Kelas baru di `app/db/repositories/`:
```python
class DocGenerationRepo:
    async def create(self, id, filename, file_size, context, style_id, style_name) -> None
    async def update_completed(self, id, tor_content, metadata_json) -> None
    async def update_failed(self, id, error_message) -> None
    async def list_all(self, limit=30) -> list[dict]
    async def get(self, id) -> dict | None
    async def delete(self, id) -> bool
```

---

## 5. Frontend: Store + API + UI

### 5.1 API Client Baru: `src/api/generate.ts` (Extend)

```typescript
// Existing
export async function generateFromDocument(...): Promise<GenerateResponse> { ... }

// NEW
export async function listGenerations(limit?: number): Promise<DocGenListItem[]> { ... }
export async function getGeneration(id: string): Promise<DocGenDetail> { ... }
export async function deleteGeneration(id: string): Promise<void> { ... }
```

### 5.2 Type Baru: `src/types/generate.ts`

```typescript
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

### 5.3 Zustand Store: `src/stores/generate-store.ts`

```typescript
interface GenerateStore {
  // History list
  history: DocGenListItem[];
  isLoadingHistory: boolean;
  fetchHistory: () => Promise<void>;

  // Active result (viewing)
  activeResult: DocGenDetail | null;
  isLoadingResult: boolean;
  viewResult: (id: string) => Promise<void>;
  clearActiveResult: () => void;

  // Generate flow  
  isGenerating: boolean;
  generateFromDoc: (file: File, context?: string, styleId?: string) => Promise<void>;

  // Delete
  deleteGeneration: (id: string) => Promise<void>;
}
```

### 5.4 UI: Komponen Baru & Refactor

```
src/components/generate/
├── GenerateContainer.tsx   # [REWRITE] Orchestrator dengan 3 view states
├── UploadForm.tsx          # [KEEP] Minor: tambah style selector
├── GenerateResult.tsx      # [MODIFY] Render dari store, bukan prop
├── GenerateHistory.tsx     # [NEW] Tabel riwayat generate
```

#### `GenerateContainer.tsx` — Rewrite

Tiga view states:
1. **`idle`** = Tampilkan `UploadForm` + `GenerateHistory` (di bawah form)
2. **`generating`** = Spinner loading (saat proses AI)
3. **`viewing`** = Tampilkan `GenerateResult` (dari store `activeResult`)

```tsx
export function GenerateContainer() {
  const { activeResult, isGenerating, ... } = useGenerateStore();

  if (isGenerating) return <GenerateSpinner />;
  if (activeResult) return <GenerateResult onBack={clearActiveResult} />;
  return (
    <>
      <UploadForm onSubmit={generateFromDoc} />
      <GenerateHistory />
    </>
  );
}
```

#### `GenerateHistory.tsx` — New

Tabel minimal menampilkan riwayat generate:

| Nama File | Style | Status | Kata | Tanggal | Aksi |
|-----------|-------|--------|------|---------|------|
| TOR_a2184d4d.docx | Standar Pemerintah | ✓ Selesai | 1.240 | 20 Apr | 👁 Lihat · 🗑 |

- Klik "Lihat" → `viewResult(id)` → pindah ke view `GenerateResult`
- Klik "🗑" → `deleteGeneration(id)` → refresh list
- Fetch on mount + setelah generate baru berhasil

---

## 6. Aturan Bisnis

> [!IMPORTANT]
> **Persistensi**: Setiap generate HARUS membuat record di `document_generations` sebelum proses dimulai (status=processing), lalu update setelah selesai. Ini menjamin data tidak hilang bahkan jika proses gagal.

> [!IMPORTANT]
> **Isolasi**: Generate-from-document TIDAK boleh membuat entry di tabel `sessions`. Kedua fitur (Chat + Generate) harus independen.

> [!WARNING]
> **File asli tidak disimpan**: Kita TIDAK menyimpan binary file asli ke database. Hanya nama file & ukuran sebagai metadata. Jika suatu hari butuh re-generate, user harus re-upload.

---

## 7. File yang Diubah/Ditambah

### Backend
| File | Status | Fungsi |
|------|--------|--------|
| `app/db/migrations/006_doc_generations.sql` | **NEW** | Tabel baru |
| `app/db/repositories/doc_generation_repo.py` | **NEW** | CRUD repository |
| `app/models/generate.py` | **MODIFY** | Pydantic models baru |
| `app/api/routes/generate_doc.py` | **MODIFY** | Persist ke DB + return id |
| `app/api/routes/generate_doc.py` | **MODIFY** | 3 endpoint baru |
| `app/api/router.py` | **MODIFY** | Register endpoint baru |
| `app/main.py` | **MODIFY** | Init DocGenerationRepo |

### Frontend
| File | Status | Fungsi |
|------|--------|--------|
| `src/types/generate.ts` | **NEW** | Types untuk history |
| `src/api/generate.ts` | **MODIFY** | API client functions baru |
| `src/stores/generate-store.ts` | **NEW** | Zustand store |
| `src/components/generate/GenerateContainer.tsx` | **REWRITE** | Orchestrator |
| `src/components/generate/GenerateResult.tsx` | **MODIFY** | Baca dari store |
| `src/components/generate/GenerateHistory.tsx` | **NEW** | Tabel riwayat |
| `src/i18n/locales/id.ts` | **MODIFY** | Translation keys baru |
| `src/i18n/locales/en.ts` | **MODIFY** | Translation keys baru |

---

## 8. Task Breakdown

| #   | Task                                  | Layer     | Estimasi |
|-----|---------------------------------------|-----------|----------|
| T01 | DB Migration: tabel `document_generations` | Database | 30 min |
| T02 | Repository: `DocGenerationRepo` CRUD | Backend | 1 jam |
| T03 | Pydantic Response Models | Backend | 30 min |
| T04 | Update `POST /generate/from-document` — persist ke DB | Backend | 1 jam |
| T05 | Endpoint `GET /history`, `GET /{id}`, `DELETE /{id}` | Backend | 1 jam |
| T06 | Frontend Types + API Client | Frontend | 30 min |
| T07 | Zustand `generate-store.ts` | Frontend | 1 jam |
| T08 | `GenerateHistory.tsx` komponen tabel | Frontend | 1.5 jam |
| T09 | `GenerateContainer.tsx` rewrite (3 states) | Frontend | 1 jam |
| T10 | `GenerateResult.tsx` refactor (baca dari store) | Frontend | 30 min |
| T11 | i18n keys + QA + Build | Frontend | 45 min |
| T12 | Fix TOR Cache Mode Constraint | Backend | 5 min |

**Total: ~9 jam kerja**

---

## 9. Dependency Graph

```
T01 → T02 → T03 → T04 → T05       (Backend sequential)
                          ↓
T06 → T07 → T08 → T09 → T10 → T11 (Frontend sequential, depends on T05)
```

Backend HARUS selesai dulu sebelum frontend bisa ditest end-to-end.

---

## 10. Verification Plan

### Automated
- `npm run build` → zero errors
- Backend startup → migration 006 applied tanpa error

### Manual Test Scenarios

**Skenario 1: Generate + Persist**
1. Buka halaman Generate Dokumen
2. Upload file → Generate TOR → hasil muncul
3. Klik "Back" → riwayat menampilkan entry baru dengan status ✓
4. Refresh browser → riwayat masih ada
5. Klik item riwayat → hasil TOR ditampilkan kembali

**Skenario 2: Generate Failed**
1. Upload file yang bermasalah → generate gagal
2. Riwayat menampilkan entry dengan status ✗ Failed
3. Error message tersimpan

**Skenario 3: Delete**
1. Klik 🗑 di riwayat → item hilang
2. Refresh → item tetap tidak ada

**Skenario 4: Export dari Riwayat**
1. Buka hasil dari riwayat
2. Klik Download DOCX / PDF / MD → berhasil
