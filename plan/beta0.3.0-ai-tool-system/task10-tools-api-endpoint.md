# Task 10 — Tools API Endpoint

## Deskripsi

Membuat endpoint REST `GET /api/v1/tools` yang mengembalikan daftar tool yang tersedia beserta spesifikasinya. Frontend menggunakan endpoint ini untuk mengetahui tool apa yang aktif, menampilkan statusnya ke user, dan menampilkan parameter yang dibutuhkan.

---

## Tujuan Teknis

- Frontend bisa query tool yang tersedia via API
- Response mencakup: nama, deskripsi, status enabled, dan parameter schema
- Endpoint terintegrasi dengan `ToolRegistry` dari `app.state`
- Jika tidak ada tool terdaftar, return empty list (bukan error)

---

## Scope

### Termasuk

- Membuat `app/api/routes/tools.py`
- Pydantic models untuk response:
  ```python
  class ToolInfoResponse(BaseModel):
      """Informasi satu tool untuk frontend."""
      name: str
      description: str
      enabled: bool
      parameters: dict

  class ToolsListResponse(BaseModel):
      """Response GET /tools."""
      tools: list[ToolInfoResponse]
  ```

- Endpoint `GET /tools`:
  - Ambil `tool_registry` dari `request.app.state`
  - Jika tidak ada → return `{"tools": []}`
  - Iterate `tool_registry.get_specs()`
  - Return list tool info dengan `enabled: True` (semua tool yang terdaftar aktif)

- Registrasi router di `app/api/router.py`:
  ```python
  from app.api.routes import tools
  api_router.include_router(tools.router, tags=["Tools"])
  ```

- Error handling:
  - Jika `tool_registry` tidak ada di `app.state` → return empty list (jangan crash)
  - Jika registry kosong → return `{"tools": []}`

### Tidak Termasuk

- Tool execution (Task 04)
- Frontend API client (Task 13)
- Tool toggle UI (Task 16)
- Endpoint untuk enable/disable tool secara individual

---

## Langkah Implementasi

### Langkah 1: Buat `app/api/routes/tools.py`

```python
"""Tools API endpoint — mengembalikan daftar tool yang tersedia."""

import logging
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.tools.base import ToolSpec

logger = logging.getLogger("ai-agent-hybrid.api.tools")

router = APIRouter()


class ToolInfoResponse(BaseModel):
    """Informasi satu tool untuk frontend."""
    name: str
    description: str
    enabled: bool = True
    parameters: dict


class ToolsListResponse(BaseModel):
    """Response GET /tools."""
    tools: list[ToolInfoResponse]


@router.get("/tools", response_model=ToolsListResponse)
async def list_tools(request: Request):
    """Daftar semua tool yang tersedia.

    Mengembalikan tool specs dari ToolRegistry.
    Jika ToolRegistry tidak tersedia atau kosong, return empty list.

    Returns:
        ToolsListResponse: Daftar tool dengan nama, deskripsi, status, dan parameter.
    """
    tool_registry = getattr(request.app.state, "tool_registry", None)
    if tool_registry is None:
        logger.warning("ToolRegistry not available in app.state")
        return ToolsListResponse(tools=[])

    try:
        specs = tool_registry.get_specs()
        tools = [
            ToolInfoResponse(
                name=spec.name,
                description=spec.description,
                enabled=True,
                parameters=spec.parameters,
            )
            for spec in specs
        ]
        logger.debug(f"Returning {len(tools)} tool(s): {[t.name for t in tools]}")
        return ToolsListResponse(tools=tools)
    except Exception as e:
        logger.error(f"Failed to list tools: {e}", exc_info=True)
        return ToolsListResponse(tools=[])
```

### Langkah 2: Registrasi di Router

```python
# Di app/api/router.py
from app.api.routes import tools

api_router = APIRouter()

# ... existing routers ...
api_router.include_router(tools.router, tags=["Tools"])  # NEW
```

### Langkah 3: Validasi

```bash
# Test endpoint
curl http://localhost:8000/api/v1/tools

# Response yang diharapkan (jika WebSearchTool terdaftar):
# {
#   "tools": [
#     {
#       "name": "web_search",
#       "description": "Cari informasi terbaru dari internet...",
#       "enabled": true,
#       "parameters": {
#         "type": "object",
#         "properties": {
#           "query": {"type": "string", "description": "Kata kunci pencarian"},
#           "max_results": {"type": "integer", "description": "...", "default": 5}
#         },
#         "required": ["query"]
#       }
#     }
#   ]
# }

# Test dengan registry kosong
# Response: {"tools": []}
```

---

## Output yang Diharapkan

```
app/api/routes/
├── tools.py           # Baru — endpoint GET /tools
└── ... (existing)
```

- `GET /api/v1/tools` mengembalikan daftar tool yang terdaftar
- Response format sesuai dengan yang diharapkan frontend
- Terintegrasi dengan API router

---

## Dependencies

- **Task 02 (Tool Registry)** — `ToolRegistry`
- **Task 11 (Config Settings)** — inisialisasi registry di `main.py`

---

## Acceptance Criteria

### Functional
- [ ] `GET /tools` mengembalikan response dengan format `{"tools": [...]}`
- [ ] Setiap tool memiliki: `name`, `description`, `enabled`, `parameters`
- [ ] Jika tidak ada tool terdaftar, return `{"tools": []}`
- [ ] Jika `tool_registry` tidak tersedia di app state, return `{"tools": []}`
- [ ] Endpoint terdaftar di router dan bisa diakses di `/api/v1/tools`
- [ ] Response menggunakan Pydantic models (validasi otomatis)

### Error Handling
- [ ] Registry tidak tersedia → log warning, return empty list
- [ ] Registry kosong → return empty list
- [ ] Exception di get_specs() → log error, return empty list

---

## Estimasi

**Low** (~30 menit)

| Aktivitas | Durasi |
|-----------|--------|
| Membuat file tools.py + models | 15 menit |
| Registrasi di router | 5 menit |
| Validasi & testing | 10 menit |
