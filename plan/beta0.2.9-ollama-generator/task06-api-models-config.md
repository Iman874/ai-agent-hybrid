# Task 06: API Models & Config Updates

## Status
[ ] Belum dimulai

## Deskripsi
Update semua model dan config yang diperlukan untuk mendukung multi-provider generator.

## File yang Diubah
- **MODIFY**: `app/config.py`
- **MODIFY**: `app/models/api.py`
- **MODIFY**: `app/models/routing.py`
- **MODIFY**: `app/models/generate.py`
- **MODIFY**: `app/main.py`

## Spesifikasi

### 1. Config (`app/config.py`)

```python
# === Ollama TOR Generator ===
ollama_tor_model: str = ""                    # Jika kosong, pakai ollama_chat_model
ollama_tor_temperature: float = 0.3
ollama_tor_timeout: int = 120                 # TOR generate butuh waktu lebih lama

# === Generator Settings ===
generator_auto_threshold: float = 0.8         # Threshold completeness untuk auto mode
```

### 2. HybridOptions (`app/models/routing.py`)

```python
class HybridOptions(BaseModel):
    force_generate: bool = False
    language: str = "id"
    chat_mode: str = "local"
    think: bool = True
    generator: str = "auto"        # "auto" | "gemini" | "ollama"
```

### 3. TORMetadata (`app/models/generate.py`)

```python
class TORMetadata(BaseModel):
    generated_by: str              # Nama model: "gemini-2.0-flash" | "qwen2.5:7b"
    generator: str = "gemini"      # NEW: "gemini" | "ollama"
    mode: str                      # "standard" | "escalation"
    word_count: int
    generation_time_ms: int
    has_assumptions: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0
```

### 4. GenerateRequest (`app/models/generate.py`)

```python
class GenerateRequest(BaseModel):
    session_id: str
    mode: Literal["standard", "escalation"] = "standard"
    generator: Literal["auto", "gemini", "ollama"] = "auto"  # NEW
    force_regenerate: bool = False
```

### 5. Main App (`app/main.py`)

Di dalam `lifespan`, init `OllamaGeneratorProvider` dan `OllamaPromptBuilder`, lalu register ke `GenerateService`:

```python
from app.ai.ollama_generator_provider import OllamaGeneratorProvider
from app.core.ollama_prompt_builder import OllamaPromptBuilder

# Init Ollama Generator
ollama_generator = OllamaGeneratorProvider(settings)
app.state.ollama_generator = ollama_generator
logger.info("Ollama Generator Provider initialized")

# Init Ollama Prompt Builder
ollama_prompt_builder = OllamaPromptBuilder()

# Update GenerateService init
app.state.generate_service = GenerateService(
    gemini_provider=gemini_provider,
    ollama_provider=ollama_generator,       # NEW
    session_mgr=session_mgr,
    rag_pipeline=rag_pipeline,
    gemini_prompt_builder=GeminiPromptBuilder(),
    ollama_prompt_builder=ollama_prompt_builder,  # NEW
    post_processor=PostProcessor(),
    cache=tor_cache,
    cost_ctrl=cost_controller,
    style_manager=style_manager,
)
```

## Catatan
- `ollama_tor_model` bisa kosong — fallback ke `ollama_chat_model`
- `generator_auto_threshold` bisa diubah user nanti via Settings
- Pastikan `GenerateService` constructor sudah di-update sesuai task04
