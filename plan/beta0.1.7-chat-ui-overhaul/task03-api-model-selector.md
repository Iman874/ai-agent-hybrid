# Task 03: API — Tambah chat_mode di HybridOptions & Endpoint /models

## Deskripsi
Menambahkan field `chat_mode` pada model `HybridOptions` agar frontend bisa mengirim pilihan model, dan membuat endpoint baru `GET /api/v1/models` untuk list model yang tersedia.

## Tujuan Teknis
1. Tambah field `chat_mode: str = "local"` di `HybridOptions` (`app/models/routing.py`)
2. Buat endpoint `GET /api/v1/models` yang return daftar model available
3. Register route baru di `app/api/router.py`

## Scope
- **Dikerjakan**:
  - Modifikasi `app/models/routing.py` — tambah `chat_mode`
  - Buat `app/api/routes/models.py` — endpoint list models
  - Modifikasi `app/api/router.py` — register route baru
- **Tidak dikerjakan**:
  - Perubahan di DecisionEngine (task04)
  - UI changes

## Langkah Implementasi

### Step 1: Update `HybridOptions`

```python
# app/models/routing.py

class HybridOptions(BaseModel):
    force_generate: bool = False
    language: str = "id"
    chat_mode: str = "local"  # NEW: "local" | "gemini"
```

### Step 2: Buat endpoint `/models`

```python
# app/api/routes/models.py

import logging
from fastapi import APIRouter, Request

logger = logging.getLogger("ai-agent-hybrid.api.models")
router = APIRouter()


@router.get("/models")
async def list_models(request: Request):
    """Return daftar model yang tersedia untuk chat."""
    settings = request.app.state.settings
    models = []

    # Check Ollama availability
    try:
        ollama_provider = request.app.state.chat_service.ollama
        # Simple health check — try list models
        import ollama as ollama_lib
        client = ollama_lib.AsyncClient(host=settings.ollama_base_url)
        model_list = await client.list()
        for m in model_list.get("models", []):
            models.append({
                "id": m["name"],
                "type": "local",
                "provider": "ollama",
                "status": "available",
            })
    except Exception as e:
        logger.warning(f"Ollama not available: {e}")
        models.append({
            "id": settings.ollama_chat_model,
            "type": "local",
            "provider": "ollama",
            "status": "offline",
        })

    # Gemini — always available if API key set
    if settings.gemini_api_key:
        models.append({
            "id": settings.gemini_model,
            "type": "gemini",
            "provider": "google",
            "status": "available",
        })

    return {"models": models, "default_chat_mode": "local"}
```

### Step 3: Register di router

```python
# app/api/router.py
from app.api.routes import health, chat, session, rag, generate, hybrid, generate_doc, models

api_router.include_router(models.router, tags=["Models"])
```

## Output yang Diharapkan

**GET /api/v1/models** response:
```json
{
  "models": [
    {"id": "qwen2.5:3b", "type": "local", "provider": "ollama", "status": "available"},
    {"id": "gemini-2.5-flash", "type": "gemini", "provider": "google", "status": "available"}
  ],
  "default_chat_mode": "local"
}
```

**POST /api/v1/hybrid** request sekarang bisa:
```json
{
  "message": "Buatkan TOR...",
  "options": {"chat_mode": "gemini"}
}
```

## Dependencies
- Tidak ada (bisa paralel dengan Task 01-02)

## Acceptance Criteria
- [ ] `HybridOptions.chat_mode` ada dengan default `"local"`
- [ ] `GET /api/v1/models` return list models dengan status
- [ ] Ollama offline → status `"offline"` (bukan error 500)
- [ ] Gemini model muncul jika `GEMINI_API_KEY` ada di env
- [ ] Route ter-register dan muncul di `/docs`

## Estimasi
Low
