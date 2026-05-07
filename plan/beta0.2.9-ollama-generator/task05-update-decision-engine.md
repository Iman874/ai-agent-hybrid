# Task 05: Update DecisionEngine — Generator Routing + Fallback

## Status
[ ] Belum dimulai

## Deskripsi
Update `DecisionEngine.route()` untuk mendukung generator mode ("auto", "gemini", "ollama") dan fallback chain. Juga update model HybridOptions.

## File yang Diubah
- **MODIFY**: `app/core/decision_engine.py`
- **MODIFY**: `app/models/routing.py`
- **MODIFY**: `app/models/api.py`

## Spesifikasi

### 1. Update HybridOptions (`app/models/routing.py`)

```python
class HybridOptions(BaseModel):
    force_generate: bool = False
    language: str = "id"
    chat_mode: str = "local"       # "local" | "gemini"
    think: bool = True
    generator: str = "auto"        # NEW: "auto" | "gemini" | "ollama"
```

### 2. Update HybridRequest API Model (`app/models/api.py`)

Tambah field yang sama di `HybridRequest.options` (jika belum ada, pastikan `generator` bisa di-pass dari frontend).

### 3. Update DecisionEngine.route()

Di bagian STEP 6 (post-routing decision), saat `READY_TO_GENERATE`:

```python
# === STEP 6: Post-routing decision ===
if chat_result.status == "READY_TO_GENERATE":
    # Tentukan generator mode dari options
    generator = options.generator if options else "auto"
    
    # Edge case: LLM says READY but score is low → escalation
    if chat_result.completeness_score < 0.5:
        mode = "escalation"
    else:
        mode = "standard"
    
    try:
        gen_result = await self.generate.generate_tor(
            session_id,
            mode=mode,
            generator=generator,  # NEW: pass generator mode
        )
        action = "GENERATE_STANDARD"
        if mode == "escalation":
            action = "GENERATE_ESCALATION"
        elif gen_result.tor_document.metadata.generator == "ollama":
            action = "GENERATE_LOCAL"
        
        return RoutingResult(
            session_id=session_id,
            action_taken=action,
            chat_response=chat_result,
            generate_response=gen_result,
        )
    except (GeminiTimeoutError, RateLimitError, GeminiAPIError,
            OllamaConnectionError, OllamaTimeoutError, NoProviderAvailableError) as e:
        logger.error(f"Generate failed after READY: {e}")
        await self.session_mgr.update(session_id, state="CHATTING")
        return RoutingResult(
            session_id=session_id,
            action_taken="CHAT",
            chat_response=ChatResult(
                session_id=session_id,
                status="NEED_MORE_INFO",
                message=f"Maaf, sistem generate sedang bermasalah: {str(e)[:100]}. "
                        "Coba lagi nanti atau ganti generator.",
                ...
            ),
        )
```

### 4. Update RoutingResult Action Types

```python
class RoutingResult(BaseModel):
    action_taken: Literal[
        "CHAT",
        "GENERATE_STANDARD",
        "GENERATE_ESCALATION",
        "GENERATE_LOCAL",     # NEW
        "FORCE_GENERATE",
    ]
    ...
```

### 5. Update _handle_escalation()

```python
async def _handle_escalation(self, ...) -> RoutingResult:
    ...
    try:
        gen_result = await self.generate.generate_tor(
            session_id,
            mode="escalation",
            generator=options.generator if options else "auto",  # NEW
        )
    except ...
```

## Catatan
- `GENERATE_LOCAL` adalah action baru untuk menandai bahwa TOR dihasilkan oleh Ollama
- Fallback chain sudah di-handle oleh `GenerateService._resolve_provider()`
- Error handling mencakup error dari kedua provider
