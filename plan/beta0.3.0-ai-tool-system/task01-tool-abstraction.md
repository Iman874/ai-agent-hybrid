# Task 01 — Tool Abstraction (BaseTool, ToolSpec, ToolResult)

## Deskripsi

Membangun fondasi abstraksi untuk seluruh Tool System. Task ini mendefinisikan kontrak interface yang **WAJIB** dipatuhi oleh setiap tool/skill dalam sistem. Tiga komponen utama dibuat:

1. **`ToolSpec`** — Pydantic model yang mendeskripsikan tool ke LLM (nama, deskripsi, parameter JSON Schema)
2. **`ToolResult`** — Pydantic model untuk hasil eksekusi tool (sukses/gagal, data, error, metadata)
3. **`BaseTool`** — Abstract base class yang memaksa setiap tool mengimplementasikan `spec` dan `execute()`

Tanpa task ini, tool-tool akan memiliki interface yang tidak konsisten dan sulit diintegrasikan.

---

## Tujuan Teknis

- Mendefinisikan kontrak interface yang ketat menggunakan ABC (Abstract Base Class) Python
- Memastikan setiap tool memiliki spesifikasi yang bisa dikirim ke LLM dalam format JSON Schema
- Memastikan hasil eksekusi tool memiliki format standar yang bisa diproses oleh ToolHandler, ChatService, dan frontend
- Menggunakan Pydantic V2 untuk validasi data secara otomatis
- Menyediakan type hints yang lengkap untuk memudahkan developer dan IDE autocompletion

---

## Scope

### Termasuk

- Membuat direktori `app/tools/` dengan `__init__.py`
- Membuat `app/tools/base.py` berisi:
  - **`ToolSpec`** — Pydantic model dengan field:
    - `name: str` — Nama tool (snake_case, contoh: `web_search`)
    - `description: str` — Deskripsi untuk LLM tentang kapan dan bagaimana menggunakan tool
    - `parameters: dict` — JSON Schema object yang mendefinisikan parameter yang diterima tool
  - **`ToolResult`** — Pydantic model dengan field:
    - `tool_name: str` — Nama tool yang dieksekusi
    - `success: bool` — Status eksekusi
    - `data: str` — Data hasil (string, siap di-inject ke konteks LLM)
    - `error: str | None` — Pesan error jika gagal
    - `metadata: dict` — Informasi tambahan (durasi, jumlah hasil, sumber, dll)
  - **`BaseTool`** — Abstract class dengan:
    - `@property @abstractmethod def spec(self) -> ToolSpec`
    - `@abstractmethod async def execute(self, **kwargs) -> ToolResult`
- Validasi Pydantic: `ToolSpec.parameters` harus memiliki struktur JSON Schema yang valid
- Docstrings lengkap untuk setiap class, property, dan method
- Type hints yang ketat sesuai standar project (Python 3.10+)

### Tidak Termasuk

- Implementasi tool spesifik (WebSearchTool — task terpisah)
- ToolRegistry (task terpisah)
- Error handling khusus tool (task terpisah)
- Logging (akan ditambahkan di task implementasi tool)

---

## Langkah Implementasi

### Langkah 1: Buat struktur direktori

Buat folder `app/tools/` dan file `__init__.py` kosong di dalamnya.

### Langkah 2: Buat `app/tools/base.py` — ToolSpec

```python
from pydantic import BaseModel, Field
from typing import Any


class ToolSpec(BaseModel):
    """Spesifikasi tool yang dikirim ke LLM.

    Setiap tool WAJIB memiliki spec yang mendeskripsikan:
    - nama tool (untuk dipanggil LLM)
    - deskripsi (kapan tool ini digunakan)
    - parameter (JSON Schema agar LLM tahu arguments apa yang diperlukan)

    Contoh:
        ToolSpec(
            name="web_search",
            description="Cari informasi terbaru dari internet...",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Kata kunci pencarian",
                    },
                },
                "required": ["query"],
            },
        )
    """

    name: str = Field(
        ...,
        description="Nama tool dalam format snake_case. Contoh: web_search",
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    description: str = Field(
        ...,
        description="Deskripsi untuk LLM tentang kapan dan bagaimana menggunakan tool ini",
        max_length=1000,
    )
    parameters: dict[str, Any] = Field(
        ...,
        description="JSON Schema object yang mendefinisikan parameter tool",
    )

    class Config:
        frozen = True  # Immutable setelah dibuat
```

### Langkah 3: Buat `app/tools/base.py` — ToolResult

```python
class ToolResult(BaseModel):
    """Hasil eksekusi tool.

    Format standar yang dikembalikan oleh setiap tool setelah dieksekusi.
    Field `data` berisi string yang siap di-inject ke konteks LLM.

    Jika `success=True`:
        - `data` berisi hasil tool yang sudah diformat
        - `error` harus None
        - `metadata` berisi info tambahan (result_count, duration_ms, dll)

    Jika `success=False`:
        - `data` harus string kosong
        - `error` berisi pesan error human-readable
        - `metadata` tetap bisa diisi untuk debugging
    """

    tool_name: str = Field(..., description="Nama tool yang dieksekusi")
    success: bool = Field(..., description="True jika eksekusi berhasil")
    data: str = Field(
        default="",
        description="Data hasil tool dalam format string, siap di-inject ke LLM",
    )
    error: str | None = Field(
        default=None,
        description="Pesan error jika eksekusi gagal",
        max_length=2000,
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata tambahan: query, result_count, duration_ms, source, dll",
    )

    class Config:
        frozen = True
```

### Langkah 4: Buat `app/tools/base.py` — BaseTool

```python
from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Abstract base class untuk semua tool/skill dalam sistem.

    Setiap tool WAJIB mengimplementasi:
    1. `spec` — property yang mengembalikan ToolSpec (deskripsi tool untuk LLM)
    2. `execute()` — async method yang mengeksekusi tool dan mengembalikan ToolResult

    Contoh implementasi:
        class WebSearchTool(BaseTool):
            @property
            def spec(self) -> ToolSpec:
                return ToolSpec(
                    name="web_search",
                    description="...",
                    parameters={...},
                )

            async def execute(self, query: str, max_results: int = 5) -> ToolResult:
                # Implementasi pencarian
                ...
    """

    @property
    @abstractmethod
    def spec(self) -> ToolSpec:
        """Spesifikasi tool yang dikirim ke LLM.

        Returns:
            ToolSpec: Berisi name, description, dan parameters JSON Schema.
        """
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Eksekusi tool dengan arguments dari LLM.

        Args:
            **kwargs: Arguments sesuai dengan spec.parameters.
                      Contoh: execute(query="AI Indonesia", max_results=5)

        Returns:
            ToolResult: Hasil eksekusi — sukses atau gagal.

        Notes:
            - Method ini TIDAK BOLEH throw exception.
            - Semua error harus di-catch dan dikembalikan sebagai ToolResult(success=False).
            - Tool TIDAK BOLEH memiliki side effect ke session/state.
        """
        ...
```

### Langkah 5: Validasi

Pastikan file bisa di-import tanpa error dengan menjalankan:

```python
from app.tools.base import BaseTool, ToolSpec, ToolResult

# Test ToolSpec
spec = ToolSpec(
    name="web_search",
    description="Cari informasi di internet",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Kata kunci"},
        },
        "required": ["query"],
    },
)

# Test ToolResult sukses
result_ok = ToolResult(
    tool_name="web_search",
    success=True,
    data="Hasil pencarian...",
    metadata={"query": "test", "result_count": 5},
)

# Test ToolResult gagal
result_fail = ToolResult(
    tool_name="web_search",
    success=False,
    data="",
    error="Search API timeout",
)

# Test BaseTool tidak bisa diinstansiasi
try:
    tool = BaseTool()  # Harus raise TypeError
    assert False, "BaseTool harus abstract!"
except TypeError:
    pass
```

---

## Output yang Diharapkan

```
app/tools/
├── __init__.py          # File kosong
└── base.py              # Berisi ToolSpec, ToolResult, BaseTool
```

- `ToolSpec` bisa diinstansiasi dengan validasi otomatis
- `ToolResult` bisa diinstansiasi untuk sukses dan error cases
- `BaseTool` tidak bisa diinstansiasi langsung (abstract)
- Semua type hints terdefinisi dengan baik
- Docstrings lengkap untuk dokumentasi otomatis

---

## Dependencies

- **Tidak ada** — task ini adalah fondasi paling dasar
- Hanya membutuhkan: `pydantic>=2.0`, `abc` (standard library)

---

## Acceptance Criteria

### Functional
- [ ] `ToolSpec` bisa diinstansiasi dengan `name`, `description`, `parameters`
- [ ] `ToolSpec.name` hanya menerima snake_case (regex `^[a-z][a-z0-9_]*$`)
- [ ] `ToolSpec.description` dibatasi maksimal 1000 karakter
- [ ] `ToolSpec` immutable setelah dibuat (`frozen=True`)
- [ ] `ToolResult` bisa diinstansiasi dengan `success=True` dan `data`
- [ ] `ToolResult` bisa diinstansiasi dengan `success=False` dan `error`
- [ ] `ToolResult.data` default ke string kosong
- [ ] `ToolResult.error` bisa None (saat sukses)
- [ ] `ToolResult.metadata` default ke dict kosong
- [ ] `BaseTool` tidak bisa diinstansiasi langsung (raise `TypeError`)
- [ ] Class turunan `BaseTool` WAJIB mengimplementasi `spec` dan `execute()`

### Code Quality
- [ ] Semua class menggunakan Pydantic V2 (`BaseModel`)
- [ ] Semua method memiliki type hints lengkap
- [ ] Semua class dan method memiliki docstrings
- [ ] Tidak ada `# type: ignore` atau `Any` yang tidak perlu
- [ ] Import hanya dari standard library + pydantic

### Edge Cases
- [ ] `ToolSpec` dengan parameters kosong (`{}`) tetap valid
- [ ] `ToolResult` dengan `data=""` dan `success=True` valid (tool tidak menemukan hasil)
- [ ] `ToolResult` dengan `metadata={"custom": ["list", "values"]}` valid

---

## Estimasi

**Low** (~1 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Membuat struktur direktori | 5 menit |
| Implementasi ToolSpec | 15 menit |
| Implementasi ToolResult | 10 menit |
| Implementasi BaseTool | 15 menit |
| Validasi & testing manual | 15 menit |
