# Task 4: Backend — Validasi Image + ChatService Images

## Deskripsi

Menambahkan validasi image attachment di endpoint dan meneruskan images melalui ChatService ke provider.

## Tujuan Teknis

- `HybridRequest` extended dengan field `images: list[str] | None`
- Endpoint `/hybrid` dan `/hybrid/stream` validasi: reject gambar jika model text-only
- `ChatService.process_message()` dan `process_message_stream()` menerima parameter `images`
- Images diteruskan ke prompt builder → messages → provider

## Scope

**Dikerjakan:**
- Extend `HybridRequest` di `app/models/api.py`
- Validasi di `app/api/routes/hybrid.py`  
- Update `ChatService` di `app/services/chat_service.py`
- Update `PromptBuilder` di `app/core/prompt_builder.py` (jika perlu)

**Tidak dikerjakan:**
- Provider update (Task 3)
- Frontend (Task 5+)

## Langkah Implementasi

### Step 1: Extend `HybridRequest`

File: `app/models/api.py`

```python
class HybridRequest(BaseModel):
    session_id: str | None = None
    message: str
    images: list[str] | None = None  # NEW — base64 encoded images
    options: HybridOptions | None = None
```

### Step 2: Tambah validasi di `/hybrid` endpoint

File: `app/api/routes/hybrid.py`

```python
from app.core.capability_resolver import ModelCapabilityResolver

resolver = ModelCapabilityResolver()

@router.post("/hybrid", response_model=HybridAPIResponse)
async def hybrid_endpoint(request: Request, body: HybridRequest):
    # Validasi image support
    if body.images and len(body.images) > 0:
        model_id = body.options.model_preference if body.options and body.options.model_preference else None
        settings = request.app.state.settings
        
        # Determine active model
        if body.options and body.options.chat_mode == "gemini":
            active_model = settings.gemini_model
            provider = "google"
        else:
            active_model = model_id or settings.ollama_chat_model
            provider = "ollama"
        
        caps = resolver.resolve(active_model, provider)
        if not caps.supports_image_input:
            raise HTTPException(
                status_code=400,
                detail="Model ini tidak mendukung input gambar. Pilih model vision untuk mengirim gambar.",
            )
    
    # ... existing routing logic ...
    decision_engine = request.app.state.decision_engine
    result = await decision_engine.route(
        session_id=body.session_id,
        message=body.message,
        options=body.options,
        images=body.images,  # NEW — teruskan images
    )
    return _convert_to_api_response(result)
```

### Step 3: Tambah validasi yang sama di `/hybrid/stream` (jika ada dari beta 0.2.6)

Sama seperti Step 2 tapi untuk SSE endpoint.

### Step 4: Update `DecisionEngine.route()` 

File: `app/core/decision_engine.py`

Tambah parameter `images`:

```python
async def route(
    self,
    session_id: str | None,
    message: str,
    options: HybridOptions | None = None,
    images: list[str] | None = None,  # NEW
) -> RoutingResult:
    # ... existing logic ...
    
    # Step 4: Chat with LLM — teruskan images
    chat_result = await self.chat.process_message(
        session_id=session_id,
        message=message,
        rag_context=rag_context,
        chat_mode=chat_mode,
        think=options.think,
        images=images,  # NEW
    )
```

### Step 5: Update `ChatService.process_message()`

File: `app/services/chat_service.py`

```python
async def process_message(
    self,
    session_id: str | None,
    message: str,
    rag_context: str | None = None,
    chat_mode: str = "local",
    think: bool = True,
    images: list[str] | None = None,  # NEW
) -> ChatResult:
    # ... existing Step 1-2 ...
    
    # Step 3: Build prompt — tambah images di message terakhir
    messages = self.prompt_builder.build_chat_messages(
        chat_history=history,
        user_message=message,
        rag_context=rag_context,
    )
    
    # Inject images ke message user terakhir
    if images and len(images) > 0:
        # Message terakhir harusnya user message
        for msg in reversed(messages):
            if msg["role"] == "user":
                msg["images"] = images
                break
    
    # ... rest of processing ...
```

### Step 6: Update `process_message_stream()` (jika ada dari beta 0.2.6)

Sama seperti Step 5 tapi untuk streaming version.

## Output yang Diharapkan

```bash
# Kirim gambar ke text-only model → error
curl -X POST http://localhost:8000/hybrid \
  -H "Content-Type: application/json" \
  -d '{"message": "Apa ini?", "images": ["base64data"], "options": {"chat_mode": "local"}}'
# → 400: "Model ini tidak mendukung input gambar..."

# Kirim gambar ke Gemini → sukses
curl -X POST http://localhost:8000/hybrid \
  -H "Content-Type: application/json" \
  -d '{"message": "Apa ini?", "images": ["base64data"], "options": {"chat_mode": "gemini"}}'
# → 200: response vision
```

## Dependencies

- Task 1: `ModelCapabilityResolver`
- Task 3: Provider multimodal support

## Acceptance Criteria

- [ ] `HybridRequest.images` field ditambahkan (optional, default None)
- [ ] Validasi: images + text-only model → HTTP 400 dengan pesan jelas
- [ ] Validasi: images + vision model → diteruskan ke provider
- [ ] `DecisionEngine.route()` menerima dan meneruskan `images`
- [ ] `ChatService.process_message()` menerima dan inject images ke messages
- [ ] `process_message_stream()` juga updated (jika ada)
- [ ] Backward-compatible: request tanpa images tetap berfungsi
- [ ] `uvicorn --reload` tanpa error

## Estimasi

Medium (1-2 jam)
