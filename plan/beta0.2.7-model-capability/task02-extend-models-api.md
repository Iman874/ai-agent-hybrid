# Task 2: Backend — Extend `GET /models` Response + Pydantic

## Deskripsi

Menambahkan field `capabilities` di response endpoint `GET /models` dan membuat Pydantic model yang sesuai agar frontend bisa mengetahui kemampuan setiap model.

## Tujuan Teknis

- Pydantic model `ModelCapabilitiesSchema` di `app/models/api.py`
- Endpoint `GET /models` return `capabilities` per model
- Response backward-compatible (field baru, bukan breaking change)

## Scope

**Dikerjakan:**
- Pydantic schema di `app/models/api.py`
- Update `app/api/routes/models.py` untuk include capabilities
- Instansiasi `ModelCapabilityResolver` di endpoint

**Tidak dikerjakan:**
- Frontend type update (Task 5)
- Image validation (Task 4)

## Langkah Implementasi

### Step 1: Tambah Pydantic schema

File: `app/models/api.py`

```python
from pydantic import BaseModel

class ModelCapabilitiesSchema(BaseModel):
    supports_text: bool = True
    supports_image_input: bool = False
    supports_streaming: bool = True

class ModelInfoSchema(BaseModel):
    id: str
    type: str  # "local" | "gemini"
    provider: str
    status: str  # "available" | "offline"
    capabilities: ModelCapabilitiesSchema
```

### Step 2: Update endpoint `GET /models`

File: `app/api/routes/models.py`

```python
from app.core.capability_resolver import ModelCapabilityResolver

resolver = ModelCapabilityResolver()

@router.get("/models")
async def list_models(request: Request):
    settings = request.app.state.settings
    models = []

    # Ollama models
    try:
        import ollama as ollama_lib
        client = ollama_lib.AsyncClient(host=settings.ollama_base_url)
        result = await client.list()
        for m in result.models:
            caps = resolver.resolve(m.model, "ollama")
            models.append({
                "id": m.model,
                "type": "local",
                "provider": "ollama",
                "status": "available",
                "capabilities": {
                    "supports_text": caps.supports_text,
                    "supports_image_input": caps.supports_image_input,
                    "supports_streaming": caps.supports_streaming,
                },
            })
    except Exception as e:
        logger.warning(f"Ollama not available: {e}")
        caps = resolver.resolve(settings.ollama_chat_model, "ollama")
        models.append({
            "id": settings.ollama_chat_model,
            "type": "local",
            "provider": "ollama",
            "status": "offline",
            "capabilities": {
                "supports_text": caps.supports_text,
                "supports_image_input": caps.supports_image_input,
                "supports_streaming": caps.supports_streaming,
            },
        })

    # Gemini
    if settings.gemini_api_key:
        caps = resolver.resolve(settings.gemini_model, "google")
        models.append({
            "id": settings.gemini_model,
            "type": "gemini",
            "provider": "google",
            "status": "available",
            "capabilities": {
                "supports_text": caps.supports_text,
                "supports_image_input": caps.supports_image_input,
                "supports_streaming": caps.supports_streaming,
            },
        })

    return {"models": models, "default_chat_mode": "local"}
```

### Step 3: Test endpoint

```bash
curl http://localhost:8000/models | python -m json.tool
```

## Output yang Diharapkan

```json
{
  "models": [
    {
      "id": "qwen2.5:7b-instruct",
      "type": "local",
      "provider": "ollama",
      "status": "available",
      "capabilities": {
        "supports_text": true,
        "supports_image_input": false,
        "supports_streaming": true
      }
    },
    {
      "id": "gemini-2.0-flash",
      "type": "gemini",
      "provider": "google",
      "status": "available",
      "capabilities": {
        "supports_text": true,
        "supports_image_input": true,
        "supports_streaming": true
      }
    }
  ],
  "default_chat_mode": "local"
}
```

## Dependencies

- Task 1: `ModelCapabilityResolver` harus sudah ada

## Acceptance Criteria

- [ ] Pydantic `ModelCapabilitiesSchema` dibuat di `app/models/api.py`
- [ ] `GET /models` mengembalikan `capabilities` per model
- [ ] Ollama text model → `supports_image_input: false`
- [ ] Gemini → `supports_image_input: true`
- [ ] Offline model tetap punya capabilities (resolve dari nama)
- [ ] `uvicorn --reload` tanpa error
- [ ] `curl /models` menunjukkan field baru

## Estimasi

Low (30 menit - 1 jam)
