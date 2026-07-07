# Task 03 — WebSearchTool (DuckDuckGo)

## Deskripsi

Mengimplementasikan tool pertama dalam Tool System: **`WebSearchTool`** yang memungkinkan AI mencari informasi dari internet secara real-time. Menggunakan DuckDuckGo sebagai search engine default karena **gratis, tanpa API key, dan tanpa rate limit ketat**.

Tool ini adalah "skill" pertama yang bisa dipanggil oleh LLM. Ketika AI membutuhkan informasi yang tidak ada di training data (berita terbaru, statistik terkini, regulasi, dll), AI bisa memanggil `web_search(query="...")` dan mendapatkan hasil real-time dari internet.

---

## Tujuan Teknis

- Menyediakan kemampuan pencarian internet real-time untuk LLM (Ollama & Gemini)
- Menggunakan DuckDuckGo sebagai search engine default (gratis, tanpa registrasi)
- Hasil pencarian diformat secara terstruktur agar mudah diproses oleh LLM
- Error handling untuk: timeout, network error, rate limiting, empty results
- Metadata lengkap untuk setiap pencarian (query, jumlah hasil, durasi, sumber)
- Tool mengikuti kontrak `BaseTool` yang sudah didefinisikan

---

## Scope

### Termasuk

- Install library `duckduckgo_search>=6.0.0`
- Membuat `app/tools/web_search.py`
- Implementasi class `WebSearchTool(BaseTool)`:

  **`spec` property**
  ```python
  ToolSpec(
      name="web_search",
      description="Cari informasi terbaru dari internet. "
                  "Gunakan ketika kamu membutuhkan data real-time, "
                  "berita terbaru, statistik terkini, regulasi, "
                  "atau informasi yang mungkin tidak ada di training data-mu.",
      parameters={
          "type": "object",
          "properties": {
              "query": {
                  "type": "string",
                  "description": "Kata kunci pencarian. Gunakan bahasa Indonesia untuk hasil lokal.",
              },
              "max_results": {
                  "type": "integer",
                  "description": "Jumlah hasil maksimal yang diinginkan (1-10)",
                  "default": 5,
              },
          },
          "required": ["query"],
      },
  )
  ```

  **`async execute(self, query: str, max_results: int = 5) -> ToolResult`**
  - Validasi input: `query` minimal 3 karakter, `max_results` antara 1-10
  - Panggil `_search_web(query, max_results)`
  - Format hasil via `_format_results(results)`
  - Return `ToolResult` dengan data terformat

  **`_search_web(self, query: str, max_results: int = 5) -> list[dict]`**
  - Async wrapper untuk DuckDuckGo API menggunakan `asyncio.to_thread()`
  - Timeout: 15 detik per pencarian
  - Return list of dict: `[{"title": ..., "snippet": ..., "url": ...}, ...]`

  **`_format_results(self, results: list[dict]) -> str`**
  - Format output dengan marker dan separator yang jelas untuk LLM

- Format output standar:
  ```
  === HASIL PENCARIAN INTERNET ===
  Query: "regulasi AI kesehatan Indonesia 2025"
  
  Sumber 1: [Kemenkes RI - Kebijakan AI Kesehatan 2025]
  URL: https://kemenkes.go.id/...
  Konten: Menteri Kesehatan meluncurkan kebijakan AI untuk layanan kesehatan...
  ──────────────────────────────────────
  Sumber 2: [DetikHealth - AI di RS Indonesia]
  URL: https://health.detik.com/...
  Konten: 5 rumah sakit di Indonesia sudah mengadopsi AI untuk diagnosis...
  ──────────────────────────────────────
  ...
  === AKHIR HASIL PENCARIAN ===
  ```

- Error handling:
  - `asyncio.TimeoutError` → return `ToolResult(success=False, error="Pencarian timeout setelah 15 detik")`
  - `ConnectionError` → return `ToolResult(success=False, error="Gagal terhubung ke layanan pencarian")`
  - `RateLimitError` → return `ToolResult(success=False, error="Terlalu banyak permintaan, coba lagi nanti")`
  - Empty results → return `ToolResult(success=True, data="Pencarian tidak menemukan hasil.")` (tetap success, tapi data kosong)
  - Exception umum → catch all, return `ToolResult(success=False, error=str(e)[:500])`

- Metadata:
  - `query`: query yang digunakan
  - `result_count`: jumlah hasil
  - `source`: "duckduckgo"
  - `duration_ms`: waktu eksekusi dalam milidetik

### Tidak Termasuk

- Search engine alternatif (Bing, SerpAPI, Google) — future
- Caching hasil search — future (bisa ditambahkan sebagai enhancement)
- Content filtering / URL blocklist — future
- Web scraping (mengambil konten lengkap dari URL) — future tool terpisah

---

## Langkah Implementasi

### Langkah 1: Install library

```bash
pip install duckduckgo_search>=6.0.0
```

### Langkah 2: Buat `app/tools/web_search.py`

```python
"""WebSearchTool — pencarian internet real-time via DuckDuckGo.

Tool ini memungkinkan LLM mencari informasi terbaru dari internet.
Menggunakan DuckDuckGo sebagai search engine (gratis, tanpa API key).

Usage:
    tool = WebSearchTool()
    result = await tool.execute(query="AI Indonesia 2025", max_results=5)
    if result.success:
        print(result.data)  # Formatted search results
"""

import asyncio
import logging
import time
from typing import Any

from duckduckgo_search import DDGS

from app.tools.base import BaseTool, ToolSpec, ToolResult

logger = logging.getLogger("ai-agent-hybrid.tools.web_search")

SEARCH_TIMEOUT = 15  # detik
MAX_RESULTS_MAX = 10
MAX_RESULTS_MIN = 1
QUERY_MIN_LENGTH = 3


class WebSearchTool(BaseTool):
    """Mencari informasi dari internet via DuckDuckGo.

    Tool ini memberikan LLM akses ke informasi real-time dari web.
    Hasil pencarian diformat dengan marker dan separator agar mudah diproses LLM.
    """

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="web_search",
            description=(
                "Cari informasi terbaru dari internet. "
                "Gunakan ketika kamu membutuhkan data real-time, "
                "berita terbaru, statistik terkini, regulasi, "
                "atau informasi yang mungkin tidak ada di training data-mu."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Kata kunci pencarian. Gunakan bahasa Indonesia untuk hasil lokal.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Jumlah hasil maksimal yang diinginkan (1-10)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        )

    async def execute(  # type: ignore[override]
        self,
        query: str,
        max_results: int = 5,
    ) -> ToolResult:
        """Eksekusi pencarian internet.

        Args:
            query: Kata kunci pencarian (min 3 karakter).
            max_results: Jumlah hasil maksimal (1-10, default 5).

        Returns:
            ToolResult: Hasil pencarian yang sudah diformat.
        """
        # Validasi input
        if not query or len(query.strip()) < QUERY_MIN_LENGTH:
            return ToolResult(
                tool_name="web_search",
                success=False,
                data="",
                error=f"Query harus minimal {QUERY_MIN_LENGTH} karakter",
            )

        max_results = max(MAX_RESULTS_MIN, min(max_results, MAX_RESULTS_MAX))
        query = query.strip()

        start_time = time.monotonic()

        try:
            results = await self._search_web(query, max_results)
            duration_ms = int((time.monotonic() - start_time) * 1000)

            if not results:
                logger.info(f"Search returned no results: query='{query}'")
                return ToolResult(
                    tool_name="web_search",
                    success=True,
                    data="Pencarian tidak menemukan hasil yang relevan.",
                    metadata={
                        "query": query,
                        "result_count": 0,
                        "source": "duckduckgo",
                        "duration_ms": duration_ms,
                    },
                )

            formatted = self._format_results(query, results)
            logger.info(
                f"Search completed: query='{query}', "
                f"results={len(results)}, duration={duration_ms}ms"
            )

            return ToolResult(
                tool_name="web_search",
                success=True,
                data=formatted,
                metadata={
                    "query": query,
                    "result_count": len(results),
                    "source": "duckduckgo",
                    "duration_ms": duration_ms,
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Search timeout: query='{query}'")
            return ToolResult(
                tool_name="web_search",
                success=False,
                data="",
                error=f"Pencarian timeout setelah {SEARCH_TIMEOUT} detik. Coba dengan query yang lebih spesifik.",
                metadata={"query": query, "source": "duckduckgo"},
            )
        except ConnectionError as e:
            logger.error(f"Search connection error: {e}")
            return ToolResult(
                tool_name="web_search",
                success=False,
                data="",
                error="Gagal terhubung ke layanan pencarian. Periksa koneksi internet.",
                metadata={"query": query, "source": "duckduckgo"},
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Search failed: {error_msg}", exc_info=True)

            # Detect rate limiting
            if "ratelimit" in error_msg.lower() or "rate" in error_msg.lower():
                return ToolResult(
                    tool_name="web_search",
                    success=False,
                    data="",
                    error="Terlalu banyak permintaan pencarian. Tunggu beberapa saat dan coba lagi.",
                    metadata={"query": query, "source": "duckduckgo"},
                )

            return ToolResult(
                tool_name="web_search",
                success=False,
                data="",
                error=f"Pencarian gagal: {error_msg[:500]}",
                metadata={"query": query, "source": "duckduckgo"},
            )

    async def _search_web(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """Async wrapper untuk DuckDuckGo search.

        Args:
            query: Kata kunci pencarian.
            max_results: Jumlah hasil maksimal.

        Returns:
            list[dict]: List of {title, snippet, url}.

        Raises:
            asyncio.TimeoutError: Jika search melebihi batas waktu.
            ConnectionError: Jika gagal terhubung.
        """
        def _sync_search() -> list[dict[str, Any]]:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))
                return [
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", ""),
                    }
                    for r in raw_results
                    if r.get("body")  # Skip results without content
                ]

        return await asyncio.wait_for(
            asyncio.to_thread(_sync_search),
            timeout=SEARCH_TIMEOUT,
        )

    def _format_results(self, query: str, results: list[dict[str, Any]]) -> str:
        """Format hasil pencarian untuk konsumsi LLM.

        Args:
            query: Query pencarian (untuk ditampilkan).
            results: List hasil pencarian.

        Returns:
            str: String terformat dengan marker dan separator.
        """
        lines = [f"=== HASIL PENCARIAN INTERNET ==="]
        lines.append(f'Query: "{query}"')
        lines.append("")

        for i, r in enumerate(results, start=1):
            title = r.get("title", "Tanpa judul")
            url = r.get("url", "")
            snippet = r.get("snippet", "")

            lines.append(f"Sumber {i}: [{title}]")
            lines.append(f"URL: {url}")
            lines.append(f"Konten: {snippet}")
            lines.append("──────────────────────────────────────")

        lines.append("=== AKHIR HASIL PENCARIAN ===")
        return "\n".join(lines)
```

### Langkah 3: Validasi

Jalankan script validasi:

```python
import asyncio
from app.tools.web_search import WebSearchTool


async def test():
    tool = WebSearchTool()

    # Test spec
    spec = tool.spec
    assert spec.name == "web_search"
    assert "query" in spec.parameters["required"]
    assert spec.parameters["properties"]["max_results"]["default"] == 5

    # Test execute with real search (butuh internet)
    result = await tool.execute(query="AI Indonesia 2025", max_results=3)
    if result.success:
        print("Search results:")
        print(result.data[:500])
        print(f"\nMetadata: {result.metadata}")
    else:
        print(f"Search failed (maybe no internet): {result.error}")

    # Test execute with empty query
    result = await tool.execute(query="")
    assert result.success is False
    assert "minimal" in result.error

    # Test execute with max_results out of range
    result = await tool.execute(query="test", max_results=100)
    # Should be clamped to 10
    assert result.metadata.get("result_count", 0) <= 10

    print("\nAll validations passed!")


asyncio.run(test())
```

---

## Output yang Diharapkan

```
app/tools/
├── __init__.py
├── base.py              # Dari Task 01
├── registry.py          # Dari Task 02
└── web_search.py        # Baru — class WebSearchTool
```

- `WebSearchTool` bisa mencari informasi dari DuckDuckGo
- Hasil terformat rapi dengan marker `=== HASIL PENCARIAN INTERNET ===`
- Error handling untuk semua skenario kegagalan
- Metadata lengkap untuk setiap pencarian

---

## Dependencies

- **Task 01 (Tool Abstraction)** — `BaseTool`, `ToolSpec`, `ToolResult`
- **Library**: `duckduckgo_search>=6.0.0`
- **Python**: `asyncio`, `logging`, `time` (standard library)

---

## Acceptance Criteria

### Functional
- [ ] `WebSearchTool` mengimplementasi `BaseTool` dengan benar
- [ ] `spec.name == "web_search"`
- [ ] `spec.parameters` memiliki `query` (required, string) dan `max_results` (optional, integer, default 5)
- [ ] `execute("query")` mengembalikan `ToolResult` dengan `success=True` dan `data` terformat
- [ ] Hasil pencarian memiliki marker `=== HASIL PENCARIAN INTERNET ===` di awal
- [ ] Hasil pencarian memiliki marker `=== AKHIR HASIL PENCARIAN ===` di akhir
- [ ] Setiap sumber memiliki format: `Sumber N: [Judul]`, `URL: ...`, `Konten: ...`
- [ ] Setiap sumber dipisah dengan `──────────────────────────────────────`
- [ ] Metadata berisi `query`, `result_count`, `source`, `duration_ms`

### Error Handling
- [ ] Query kosong → `ToolResult(success=False)` dengan pesan error
- [ ] Query < 3 karakter → `ToolResult(success=False)`
- [ ] `max_results` < 1 → di-clamp ke 1
- [ ] `max_results` > 10 → di-clamp ke 10
- [ ] Timeout → `ToolResult(success=False)` — tidak throw exception
- [ ] Connection error → `ToolResult(success=False)` — tidak throw exception
- [ ] Rate limit → `ToolResult(success=False)` dengan pesan spesifik
- [ ] Empty results → `ToolResult(success=True)` dengan data "Pencarian tidak menemukan hasil"
- [ ] Exception umum → catch, log, return `ToolResult(success=False)`

### Logging
- [ ] Setiap pencarian di-log dengan query dan max_results (DEBUG)
- [ ] Hasil pencarian di-log dengan jumlah hasil dan durasi (INFO)
- [ ] Timeout di-log dengan level ERROR
- [ ] Connection error di-log dengan level ERROR
- [ ] Rate limit di-log dengan level WARNING

---

## Estimasi

**Medium** (~2 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Install library | 5 menit |
| Implementasi WebSearchTool | 45 menit |
| Implementasi _search_web async wrapper | 20 menit |
| Implementasi _format_results | 15 menit |
| Error handling | 20 menit |
| Validasi & testing | 15 menit |
