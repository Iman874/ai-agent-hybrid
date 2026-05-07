# Task 04: Refactor GenerateService untuk Multi-Provider

## Status
[ ] Belum dimulai

## Deskripsi
Update `GenerateService` agar bisa menerima multiple generator provider (Gemini + Ollama) dan memilih provider berdasarkan mode routing.

## File yang Diubah
- **MODIFY**: `app/services/generate_service.py`
- **MODIFY**: `app/models/generate.py` (tambah field `generator`)

## Spesifikasi

### 1. Update GenerateRequest / GenerateResult Model

Di `app/models/generate.py`:

```python
class GenerateRequest(BaseModel):
    session_id: str
    mode: Literal["standard", "escalation"] = "standard"
    generator: Literal["auto", "gemini", "ollama"] = "auto"  # NEW
    force_regenerate: bool = False
```

Tambah field di metadata:

```python
class TORMetadata(BaseModel):
    generated_by: str                    # "gemini-2.0-flash" | "qwen2.5:7b"
    generator: str = "gemini"            # NEW: "gemini" | "ollama"
    mode: str                            # "standard" | "escalation"
    ...
```

### 2. Update GenerateService Constructor

```python
class GenerateService:
    def __init__(
        self,
        gemini_provider: BaseGeneratorProvider,
        ollama_provider: BaseGeneratorProvider,
        session_mgr: SessionManager,
        rag_pipeline: RAGPipeline | None,
        gemini_prompt_builder: GeminiPromptBuilder,
        ollama_prompt_builder: OllamaPromptBuilder,  # NEW
        post_processor: PostProcessor,
        cache: TORCache,
        cost_ctrl: CostController,
        style_manager: StyleManager,
    ):
        self.providers = {
            "gemini": gemini_provider,
            "ollama": ollama_provider,
        }
        self.prompt_builders = {
            "gemini": gemini_prompt_builder,
            "ollama": ollama_prompt_builder,
        }
        ...
```

### 3. Update generate_tor() Method

```python
async def generate_tor(
    self,
    session_id: str,
    mode: str = "standard",
    generator: str = "auto",  # NEW: "auto" | "gemini" | "ollama"
    data_override: TORData | None = None,
    force_regenerate: bool = False,
) -> GenerateResult:
    # Step 1: Tentukan provider
    provider_name = await self._resolve_provider(session_id, generator, mode)
    provider = self.providers[provider_name]
    prompt_builder = self.prompt_builders[provider_name]
    
    # Step 2: Cost check (hanya untuk Gemini)
    if provider_name == "gemini":
        await self.cost_ctrl.check(session_id)
    
    # Step 3: Cache check
    if not force_regenerate and provider_name == "gemini" and mode == "standard":
        cached = await self.cache.get(session_id)
        if cached:
            return GenerateResult(session_id=session_id, tor_document=cached, cached=True)
    
    # Step 4: Get session data
    session = await self.session_mgr.get(session_id)
    data = data_override or session.extracted_data
    
    # Step 5: Build prompt (pilih builder sesuai provider)
    if mode == "standard":
        prompt = prompt_builder.build_standard(data=data, ...)
    else:
        prompt = prompt_builder.build_escalation(...)
    
    # Step 6: Call provider
    if provider_name == "gemini":
        response = await self._call_gemini_with_retry(prompt, session_id, mode)
        raw_text = response.text
    else:
        raw_text = await self._call_ollama(prompt, session_id, mode)
    
    # Step 7: Post-process (sama untuk kedua provider)
    processed = self.post_processor.process(raw_text, style=active_style)
    
    # Step 8: Build result
    tor_doc = TORDocument(
        content=processed.content,
        metadata=TORMetadata(
            generated_by=provider.model_name if hasattr(provider, 'model_name') else provider.model,
            generator=provider_name,
            mode=mode,
            ...
        )
    )
    
    # Step 9: Cache & persist
    ...
```

### 4. Provider Resolution Logic

```python
async def _resolve_provider(
    self, session_id: str, generator: str, mode: str
) -> str:
    """Tentukan provider mana yang dipakai."""
    
    if generator == "gemini":
        if await self.providers["gemini"].is_available():
            return "gemini"
        elif await self.providers["ollama"].is_available():
            logger.warning("Gemini unavailable, falling back to Ollama")
            return "ollama"
        else:
            raise NoProviderAvailableError("Gemini unavailable, Ollama unavailable")
    
    elif generator == "ollama":
        if await self.providers["ollama"].is_available():
            return "ollama"
        elif await self.providers["gemini"].is_available():
            logger.warning("Ollama unavailable, falling back to Gemini")
            return "gemini"
        else:
            raise NoProviderAvailableError("Ollama unavailable, Gemini unavailable")
    
    else:  # "auto"
        session = await self.session_mgr.get(session_id)
        # Jika completeness tinggi → Ollama (local, gratis)
        # Jika completeness rendah → Gemini (butuh escalation)
        if session.completeness_score >= 0.8:
            if await self.providers["ollama"].is_available():
                return "ollama"
            elif await self.providers["gemini"].is_available():
                return "gemini"
        else:
            if await self.providers["gemini"].is_available():
                return "gemini"
            elif await self.providers["ollama"].is_available():
                return "ollama"
        
        raise NoProviderAvailableError("No generator provider available")
```

### 5. Error Handling

Tambah error baru di `app/utils/errors.py`:

```python
class NoProviderAvailableError(AppError):
    """E012 — Tidak ada generator provider yang tersedia."""
    def __init__(self, details: str = ""):
        super().__init__(
            message="Tidak ada generator TOR yang tersedia.",
            code="E012",
            details=details,
        )
```

## Catatan
- `_call_gemini_with_retry()` tetap ada untuk Gemini (dengan retry + backoff)
- `_call_ollama()` cukup sekali panggil (Ollama lokal lebih stabil, retry tidak terlalu diperlukan)
- Cache hanya untuk Gemini (Ollama gratis, tidak perlu cache)
