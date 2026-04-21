# Task 1: Backend — ModelCapabilityResolver

## Deskripsi

Membuat modul `ModelCapabilityResolver` yang menentukan kemampuan (capabilities) setiap model berdasarkan nama dan provider. Ini adalah fondasi untuk seluruh fitur capability system.

## Tujuan Teknis

- Dataclass `ModelCapabilities` dengan field `supports_text`, `supports_image_input`, `supports_streaming`
- Class `ModelCapabilityResolver` dengan method `resolve(model_id, provider) -> ModelCapabilities`
- Daftar known vision models untuk pattern matching

## Scope

**Dikerjakan:**
- `app/core/capability_resolver.py` (file baru)
- Daftar `KNOWN_VISION_MODELS` 
- Logic resolve per provider (Gemini, Ollama)

**Tidak dikerjakan:**
- Integrasi ke endpoint `/models` (Task 2)
- Frontend (Task 5+)

## Langkah Implementasi

### Step 1: Buat file `app/core/capability_resolver.py`

```python
import logging
from dataclasses import dataclass

logger = logging.getLogger("ai-agent-hybrid.capability")


@dataclass
class ModelCapabilities:
    """Kemampuan sebuah model LLM."""
    supports_text: bool = True
    supports_image_input: bool = False
    supports_streaming: bool = True


class ModelCapabilityResolver:
    """Menentukan kemampuan model berdasarkan nama dan provider."""

    # Daftar model Ollama yang diketahui support vision/image input.
    # Pattern matching: jika model_id mengandung salah satu keyword ini → vision.
    KNOWN_VISION_MODELS: list[str] = [
        "llava",
        "bakllava",
        "moondream",
        "cogvlm",
        "llama3.2-vision",
        "minicpm-v",
        "internvl",
        "llava-phi3",
        "llava-llama3",
    ]

    def resolve(self, model_id: str, provider: str) -> ModelCapabilities:
        """
        Resolve capabilities berdasarkan model_id dan provider.

        Rules:
        - Gemini → supports_image_input = True (hampir semua model Gemini support vision)
        - Ollama → pattern match ke KNOWN_VISION_MODELS
        - Unknown → fail-safe: supports_image_input = False
        """
        if provider == "google":
            return self._resolve_gemini(model_id)
        elif provider == "ollama":
            return self._resolve_ollama(model_id)
        else:
            logger.warning(f"Unknown provider '{provider}' for model '{model_id}'. Using fail-safe.")
            return ModelCapabilities()  # default: text-only

    def _resolve_gemini(self, model_id: str) -> ModelCapabilities:
        """Gemini: hampir semua model support vision."""
        return ModelCapabilities(
            supports_text=True,
            supports_image_input=True,
            supports_streaming=True,
        )

    def _resolve_ollama(self, model_id: str) -> ModelCapabilities:
        """Ollama: pattern match nama model ke known vision models."""
        model_lower = model_id.lower()
        is_vision = any(vm in model_lower for vm in self.KNOWN_VISION_MODELS)

        if is_vision:
            logger.debug(f"Model '{model_id}' matched as vision model.")

        return ModelCapabilities(
            supports_text=True,
            supports_image_input=is_vision,
            supports_streaming=True,
        )
```

### Step 2: Verifikasi resolusi

Test mental dengan beberapa model:

| model_id | provider | `supports_image_input` |
|----------|----------|------------------------|
| `qwen2.5:7b-instruct` | ollama | `False` |
| `llava:13b` | ollama | `True` |
| `bakllava:7b` | ollama | `True` |
| `mistral:7b` | ollama | `False` |
| `gemini-2.0-flash` | google | `True` |
| `unknown-model` | unknown | `False` |

## Output yang Diharapkan

```python
resolver = ModelCapabilityResolver()

caps = resolver.resolve("qwen2.5:7b-instruct", "ollama")
# ModelCapabilities(supports_text=True, supports_image_input=False, supports_streaming=True)

caps = resolver.resolve("llava:13b", "ollama")
# ModelCapabilities(supports_text=True, supports_image_input=True, supports_streaming=True)

caps = resolver.resolve("gemini-2.0-flash", "google")
# ModelCapabilities(supports_text=True, supports_image_input=True, supports_streaming=True)
```

## Dependencies

Tidak ada — ini task pertama.

## Acceptance Criteria

- [ ] File `app/core/capability_resolver.py` dibuat
- [ ] `ModelCapabilities` dataclass dengan 3 field boolean
- [ ] `ModelCapabilityResolver.resolve()` berfungsi
- [ ] Gemini → `supports_image_input = True`
- [ ] Ollama vision model (llava, bakllava, dll) → `supports_image_input = True`
- [ ] Ollama text model (qwen, llama, mistral) → `supports_image_input = False`
- [ ] Unknown provider → fail-safe `supports_image_input = False`
- [ ] Logging untuk unknown provider dan vision match

## Estimasi

Low (30 menit)
