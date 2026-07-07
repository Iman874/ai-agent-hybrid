# Task 02 — Tool Registry

## Deskripsi

Membangun `ToolRegistry` — central registry yang menjadi **single source of truth** untuk semua tool dalam sistem. Registry ini bertanggung jawab untuk:

1. **Mendaftarkan** tool instances yang tersedia
2. **Menyediakan spesifikasi** semua tool untuk dikirim ke LLM (via `get_specs()`)
3. **Mengeksekusi** tool berdasarkan nama yang dipanggil LLM (via `execute(name, **kwargs)`)
4. **Validasi** bahwa hanya object `BaseTool` yang bisa didaftarkan

Registry adalah jembatan antara LLM (yang hanya tahu nama tool) dan implementasi tool (yang melakukan pekerjaan sebenarnya). Tanpa registry, sistem tidak tahu tool apa yang tersedia dan bagaimana memanggilnya.

---

## Tujuan Teknis

- Menyediakan mekanisme registrasi tool yang seragam dengan validasi tipe ketat
- Memungkinkan sistem mengambil spesifikasi semua tool untuk dikirim ke LLM (native tool calling maupun prompt injection)
- Menyediakan eksekusi tool by-name dengan error handling lengkap
- Memastikan thread-safe operation (registry diakses dari multiple coroutines)
- Logging setiap registrasi dan eksekusi untuk debugging dan audit

---

## Scope

### Termasuk

- Membuat `app/tools/registry.py`
- Implementasi class `ToolRegistry` dengan method berikut:

  **`__init__(self)`**
  - Inisialisasi dictionary internal `_tools: dict[str, BaseTool]`
  - Inisialisasi logger: `logging.getLogger("ai-agent-hybrid.tools.registry")`

  **`register(self, tool: BaseTool) -> None`**
  - Validasi: `tool` harus instance dari `BaseTool`
  - Jika valid: simpan ke `_tools[tool.spec.name] = tool`
  - Jika nama sudah terdaftar: **overwrite** dengan warning log
  - Log: `"Tool '{name}' registered successfully"`

  **`get_specs(self) -> list[ToolSpec]`**
  - Iterate semua tool di `_tools.values()`
  - Kumpulkan `tool.spec` ke dalam list
  - Return list (urut sesuai urutan registrasi)

  **`async execute(self, name: str, **kwargs) -> ToolResult`**
  - Cari tool by name di `_tools`
  - Jika tidak ditemukan: return `ToolResult(tool_name=name, success=False, error=f"Tool '{name}' not found")`
  - Jika ditemukan: panggil `await tool.execute(**kwargs)`
  - Wrap dengan try/except: jika exception, return `ToolResult` error
  - Log: `"Executing tool '{name}' with args: {kwargs}"` dan `"Tool '{name}' completed: success={result.success}"`

  **`get_tool(self, name: str) -> BaseTool | None`**
  - Return tool instance by name
  - Return None jika tidak ditemukan (untuk frontend query)

  **`list_tools(self) -> list[str]`**
  - Return list of tool names yang terdaftar

  **`count(self) -> int`**
  - Return jumlah tool yang terdaftar

- Error handling komprehensif:
  - `register()` dengan non-BaseTool → raise `TypeError` dengan pesan jelas
  - `execute()` dengan nama tidak dikenal → return `ToolResult(success=False)` — **tidak throw**
  - `execute()` dengan exception di tool → catch, log, return `ToolResult(success=False)`
- Thread safety: registry adalah in-memory, operasi dict adalah atomic di Python

### Tidak Termasuk

- Implementasi tool individual (task terpisah)
- Inisialisasi registry di `main.py` (task terpisah — Task 11)
- API endpoint untuk tools (task terpisah — Task 10)
- Persistence (registry di-reset setiap restart aplikasi)

---

## Langkah Implementasi

### Langkah 1: Buat `app/tools/registry.py`

```python
"""Tool Registry — central registry untuk semua tool/skill dalam sistem.

Registry ini adalah single source of truth untuk:
- Daftar tool yang tersedia
- Spesifikasi tool (untuk dikirim ke LLM)
- Eksekusi tool by name

Usage:
    registry = ToolRegistry()
    registry.register(web_search_tool)
    specs = registry.get_specs()  # Untuk dikirim ke LLM
    result = await registry.execute("web_search", query="AI Indonesia")
"""

import logging
from typing import Any

from app.tools.base import BaseTool, ToolSpec, ToolResult

logger = logging.getLogger("ai-agent-hybrid.tools.registry")


class ToolRegistry:
    """Central registry untuk semua tool/skill.

    Attributes:
        _tools: Dictionary mapping tool name → BaseTool instance.
    """

    def __init__(self) -> None:
        """Inisialisasi registry kosong."""
        self._tools: dict[str, BaseTool] = {}
        logger.debug("ToolRegistry initialized")

    def register(self, tool: BaseTool) -> None:
        """Daftarkan tool ke registry.

        Args:
            tool: Instance BaseTool yang akan didaftarkan.

        Raises:
            TypeError: Jika tool bukan instance BaseTool.

        Notes:
            - Jika nama tool sudah terdaftar, akan di-overwrite dengan warning.
            - Nama tool diambil dari `tool.spec.name`.
        """
        if not isinstance(tool, BaseTool):
            raise TypeError(
                f"Expected BaseTool instance, got {type(tool).__name__}"
            )

        name = tool.spec.name
        if name in self._tools:
            logger.warning(f"Tool '{name}' already registered. Overwriting.")

        self._tools[name] = tool
        logger.info(f"Tool '{name}' registered successfully")

    def get_specs(self) -> list[ToolSpec]:
        """Kembalikan spesifikasi semua tool yang terdaftar.

        Returns:
            list[ToolSpec]: List spesifikasi tool, urut sesuai registrasi.
                           Empty list jika tidak ada tool terdaftar.
        """
        return [tool.spec for tool in self._tools.values()]

    async def execute(self, name: str, **kwargs: Any) -> ToolResult:
        """Eksekusi tool by name.

        Args:
            name: Nama tool yang akan dieksekusi.
            **kwargs: Arguments yang akan diteruskan ke tool.execute().

        Returns:
            ToolResult: Hasil eksekusi. Jika tool tidak ditemukan atau error,
                       return ToolResult dengan success=False.
        """
        tool = self._tools.get(name)
        if tool is None:
            logger.warning(f"Tool '{name}' not found in registry")
            return ToolResult(
                tool_name=name,
                success=False,
                data="",
                error=f"Tool '{name}' tidak ditemukan. Tool yang tersedia: {', '.join(self._tools.keys())}",
            )

        logger.debug(f"Executing tool '{name}' with args: {kwargs}")
        try:
            result = await tool.execute(**kwargs)
            logger.info(
                f"Tool '{name}' completed: success={result.success}, "
                f"data_len={len(result.data)}, error={result.error}"
            )
            return result
        except Exception as e:
            logger.error(f"Tool '{name}' execution failed with exception: {e}", exc_info=True)
            return ToolResult(
                tool_name=name,
                success=False,
                data="",
                error=f"Tool '{name}' gagal dieksekusi: {str(e)[:500]}",
            )

    def get_tool(self, name: str) -> BaseTool | None:
        """Ambil tool instance by name.

        Args:
            name: Nama tool yang dicari.

        Returns:
            BaseTool | None: Tool instance jika ditemukan, None jika tidak.
        """
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """Daftar nama semua tool yang terdaftar.

        Returns:
            list[str]: List nama tool (sorted alphabetically).
        """
        return sorted(self._tools.keys())

    def count(self) -> int:
        """Jumlah tool yang terdaftar.

        Returns:
            int: Jumlah tool di registry.
        """
        return len(self._tools)
```

### Langkah 2: Validasi

Jalankan script validasi berikut:

```python
from app.tools.base import BaseTool, ToolSpec, ToolResult
from app.tools.registry import ToolRegistry


# Buat mock tool untuk testing
class MockTool(BaseTool):
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="mock_tool",
            description="Mock tool untuk testing",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                },
                "required": ["input"],
            },
        )

    async def execute(self, input: str = "") -> ToolResult:
        return ToolResult(
            tool_name="mock_tool",
            success=True,
            data=f"Processed: {input}",
        )


# Test registry
registry = ToolRegistry()

# Test register
tool = MockTool()
registry.register(tool)
assert registry.count() == 1
assert registry.list_tools() == ["mock_tool"]

# Test get_specs
specs = registry.get_specs()
assert len(specs) == 1
assert specs[0].name == "mock_tool"

# Test execute
result = await registry.execute("mock_tool", input="hello")
assert result.success is True
assert result.data == "Processed: hello"

# Test execute with unknown tool
result = await registry.execute("unknown_tool")
assert result.success is False
assert "tidak ditemukan" in result.error

# Test register non-BaseTool
try:
    registry.register("not_a_tool")  # Harus raise TypeError
    assert False, "Should have raised TypeError"
except TypeError:
    pass

print("All validations passed!")
```

---

## Output yang Diharapkan

```
app/tools/
├── __init__.py
├── base.py              # Dari Task 01
└── registry.py          # Baru — class ToolRegistry
```

- `ToolRegistry` bisa menerima registrasi tool, query specs, dan eksekusi
- Error handling untuk tool tidak ditemukan, exception, dan invalid type
- Logging untuk setiap operasi penting

---

## Dependencies

- **Task 01 (Tool Abstraction)** — `BaseTool`, `ToolSpec`, `ToolResult`
- Standard library: `logging`, `typing`

---

## Acceptance Criteria

### Functional
- [ ] `register(tool)` menerima instance `BaseTool` dan menyimpannya
- [ ] `register(tool)` dengan nama yang sudah ada meng-overwrite dengan warning
- [ ] `register("string")` raise `TypeError` dengan pesan jelas
- [ ] `get_specs()` mengembalikan list `ToolSpec` sesuai urutan registrasi
- [ ] `get_specs()` mengembalikan empty list jika belum ada tool
- [ ] `execute(name, **kwargs)` memanggil tool yang benar dengan arguments yang benar
- [ ] `execute("unknown", ...)` mengembalikan `ToolResult(success=False)` — tidak throw
- [ ] `execute()` aman dari exception tool — catch dan return `ToolResult(success=False)`
- [ ] `get_tool(name)` mengembalikan `BaseTool | None`
- [ ] `list_tools()` mengembalikan sorted list of names
- [ ] `count()` mengembalikan jumlah tool yang terdaftar

### Logging
- [ ] Registrasi tool di-log dengan level INFO
- [ ] Overwrite tool di-log dengan level WARNING
- [ ] Eksekusi tool di-log dengan args (DEBUG)
- [ ] Hasil eksekusi di-log dengan success status (INFO)
- [ ] Tool tidak ditemukan di-log dengan level WARNING
- [ ] Exception di tool execution di-log dengan level ERROR + traceback

### Edge Cases
- [ ] Registry kosong: `get_specs()` return `[]`, `execute()` return error
- [ ] Multiple tool dengan nama sama: overwrite dengan warning
- [ ] Tool dengan arguments kompleks (nested dict, list) tetap bisa dieksekusi
- [ ] Concurrent execute dari multiple coroutines tidak corrupt state

---

## Estimasi

**Low** (~1 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Implementasi class ToolRegistry | 30 menit |
| Implementasi error handling | 15 menit |
| Logging setup | 10 menit |
| Validasi & testing manual | 15 menit |
