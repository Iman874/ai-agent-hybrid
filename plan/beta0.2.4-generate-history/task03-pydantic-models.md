# Task 3: Pydantic Response Models

## 1. Judul Task
Tambah Pydantic models untuk response API generate history: `DocGenListItem` dan `DocGenDetail`.

## 2. Deskripsi
Backend memerlukan Pydantic models untuk memvalidasi dan serialize response dari endpoint-endpoint riwayat generate yang baru.

## 3. Tujuan Teknis
- `DocGenListItem` — model ringkas untuk list riwayat
- `DocGenDetail` — model lengkap untuk detail satu generate result
- Ditambahkan di `app/models/generate.py`

## 4. Scope
### Yang dikerjakan
- Tambah 2 Pydantic models di `app/models/generate.py`

### Yang tidak dikerjakan
- Tidak mengubah model `GenerateResponse` yang sudah ada
- Tidak membuat endpoints (task 4-5)

## 5. Langkah Implementasi

### Step 1: Buka `app/models/generate.py` dan tambahkan di akhir file

```python
class DocGenListItem(BaseModel):
    """Item ringkas untuk list riwayat generate."""
    id: str
    filename: str
    file_size: int
    style_name: str | None = None
    status: str  # "completed" | "failed" | "processing"
    word_count: int | None = None
    created_at: str


class DocGenDetail(BaseModel):
    """Detail lengkap satu generate result."""
    id: str
    filename: str
    file_size: int
    context: str = ""
    style_name: str | None = None
    status: str
    tor_content: str | None = None
    metadata: TORMetadata | None = None
    error_message: str | None = None
    created_at: str
```

## 6. Output yang Diharapkan

```python
from app.models.generate import DocGenListItem, DocGenDetail

item = DocGenListItem(
    id="doc-abc", filename="TOR.docx", file_size=43000,
    style_name="Standar", status="completed",
    word_count=1240, created_at="2026-04-21T03:00:00"
)
# → valid Pydantic model
```

## 7. Dependencies
- Tidak ada (models bisa dibuat kapan saja)

## 8. Acceptance Criteria
- [ ] `DocGenListItem` memiliki field: id, filename, file_size, style_name, status, word_count, created_at
- [ ] `DocGenDetail` memiliki field: id, filename, file_size, context, style_name, status, tor_content, metadata, error_message, created_at
- [ ] `DocGenDetail.metadata` menggunakan `TORMetadata | None` (tipe yang sudah ada)
- [ ] Backend startup tanpa error import

## 9. Estimasi
**Low** (~20 menit)
