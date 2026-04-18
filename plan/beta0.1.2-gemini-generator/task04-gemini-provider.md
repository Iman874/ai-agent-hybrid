# Task 04 — GeminiProvider: Async Client ke Google Gemini API

## 1. Judul Task

Implementasikan `GeminiProvider` — client async yang memanggil Google Gemini API (`gemini-2.0-flash`) dengan retry, timeout, dan usage tracking.

## 2. Deskripsi

Class wrapper async untuk Google Generative AI SDK. Menangani konfigurasi safety settings, generation config, timeout via `asyncio.wait_for`, dan mengekstrak usage metadata (token counts).

## 3. Tujuan Teknis

- `GeminiProvider(settings)` yang meng-configure API key dan model
- `generate(prompt) → GeminiResponse` async method
- Safety settings: block none untuk semua kecuali sexually explicit
- Timeout handling via `asyncio.wait_for` + `asyncio.to_thread`
- Token usage extraction dari response metadata

## 4. Scope

### Yang dikerjakan
- `app/ai/gemini_provider.py` — class `GeminiProvider`
- Install `google-generativeai>=0.8.0`
- Update `requirements.txt`

### Yang tidak dikerjakan
- Retry logic (itu di GenerateService)
- Prompt building

## 5. Langkah Implementasi

### Step 1: Install dependency

```bash
.\venv\Scripts\pip.exe install "google-generativeai>=0.8.0"
```

Tambahkan ke `requirements.txt`:
```
google-generativeai>=0.8.0
```

### Step 2: Buat `app/ai/gemini_provider.py`

```python
import logging
import time
import asyncio
import google.generativeai as genai

from app.config import Settings
from app.models.generate import GeminiResponse
from app.utils.errors import GeminiTimeoutError, GeminiAPIError

logger = logging.getLogger("ai-agent-hybrid.gemini")


class GeminiProvider:
    """Async client untuk Google Gemini API."""

    def __init__(self, settings: Settings):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ],
            generation_config=genai.GenerationConfig(
                temperature=settings.gemini_temperature,
                max_output_tokens=settings.gemini_max_tokens,
                top_p=0.95,
                top_k=40,
            ),
        )
        self.timeout = settings.gemini_timeout
        self.model_name = settings.gemini_model

    async def generate(self, prompt: str) -> GeminiResponse:
        """Generate content via Gemini API."""
        start = time.monotonic()

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content, prompt
                ),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            raise GeminiTimeoutError(self.timeout)
        except Exception as e:
            error_str = str(e)
            if "API_KEY" in error_str.upper() or "INVALID" in error_str.upper():
                raise GeminiAPIError(details=f"API key mungkin tidak valid: {error_str[:200]}")
            raise GeminiAPIError(details=error_str[:200])

        duration_ms = int((time.monotonic() - start) * 1000)

        # Extract usage metadata
        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

        logger.info(
            f"Gemini call: {duration_ms}ms, "
            f"tokens: {prompt_tokens}+{completion_tokens}={prompt_tokens + completion_tokens}"
        )

        return GeminiResponse(
            text=response.text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            duration_ms=duration_ms,
        )
```

### Step 3: Verifikasi (butuh GEMINI_API_KEY valid di .env)

```python
import asyncio
from app.config import Settings
from app.ai.gemini_provider import GeminiProvider

async def test():
    settings = Settings()
    if not settings.gemini_api_key or settings.gemini_api_key == "your-api-key-here":
        print("SKIP: GEMINI_API_KEY belum di-set. Set di .env untuk test.")
        return

    provider = GeminiProvider(settings)
    response = await provider.generate("Berikan satu kalimat motivasi singkat.")
    print(f"Response: {response.text[:100]}...")
    print(f"Tokens: prompt={response.prompt_tokens}, completion={response.completion_tokens}")
    print(f"Duration: {response.duration_ms}ms")
    print("GEMINI PROVIDER TEST PASSED")

asyncio.run(test())
```

## 6. Output yang Diharapkan

```
Response: Hidup adalah perjalanan, bukan tujuan...
Tokens: prompt=12, completion=25
Duration: 1200ms
GEMINI PROVIDER TEST PASSED
```

## 7. Dependencies

- **Task 01** — `GeminiResponse` model
- **Task 02** — `GeminiTimeoutError`, `GeminiAPIError`, `settings.gemini_timeout`
- **External** — `google-generativeai` package + valid API key

## 8. Acceptance Criteria

- [ ] `google-generativeai>=0.8.0` terinstall dan ada di `requirements.txt`
- [ ] `GeminiProvider(settings)` berhasil instantiate
- [ ] `generate(prompt)` return `GeminiResponse` dengan text, tokens, dan duration
- [ ] Timeout handling: raise `GeminiTimeoutError` jika melebihi `gemini_timeout`
- [ ] API error handling: raise `GeminiAPIError` untuk key/quota issues

## 9. Estimasi

**Medium** — ~1.5 jam
