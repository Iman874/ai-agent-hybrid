# Task 07 — Ollama Provider (LLM Client)

## 1. Judul Task

Implementasi `OllamaProvider` — async client untuk komunikasi dengan Ollama REST API.

## 2. Deskripsi

Membuat class `OllamaProvider` yang mengirim chat completion request ke Ollama (`localhost:11434`) menggunakan Ollama Python SDK. Termasuk handling timeout, connection error, dan response parsing.

## 3. Tujuan Teknis

- `OllamaProvider.chat(messages)` kirim request ke Ollama dan return content + metadata
- Timeout handling: raise `OllamaTimeoutError` setelah N detik
- Connection error handling: raise `OllamaConnectionError` jika Ollama tidak berjalan
- JSON mode aktif (`format="json"`) agar LLM output JSON

## 4. Scope

### Yang dikerjakan
- `app/ai/base.py` — abstract base class `BaseLLMProvider`
- `app/ai/ollama_provider.py` — `OllamaProvider` implementation

### Yang tidak dikerjakan
- Retry logic (itu di ChatService, task 11)
- Prompt building (itu di task 08)
- Gemini provider (itu di beta0.1.2)

## 5. Langkah Implementasi

### Step 1: Buat `app/ai/base.py`

```python
from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Abstract base class untuk semua LLM provider."""

    @abstractmethod
    async def chat(self, messages: list[dict]) -> dict:
        """
        Kirim chat completion.
        Args:
            messages: list of {"role": str, "content": str}
        Returns:
            {"content": str, "total_duration": int, "eval_count": int}
        """
        ...
```

### Step 2: Buat `app/ai/ollama_provider.py`

```python
import asyncio
import logging

import ollama

from app.ai.base import BaseLLMProvider
from app.config import Settings
from app.utils.errors import OllamaConnectionError, OllamaTimeoutError

logger = logging.getLogger("ai-agent-hybrid.ollama")


class OllamaProvider(BaseLLMProvider):
    """Client async untuk Ollama REST API."""

    def __init__(self, settings: Settings):
        self.client = ollama.AsyncClient(host=settings.ollama_base_url)
        self.model = settings.ollama_chat_model
        self.temperature = settings.ollama_temperature
        self.num_ctx = settings.ollama_num_ctx
        self.timeout = settings.ollama_timeout

    async def chat(self, messages: list[dict]) -> dict:
        """
        Kirim chat completion ke Ollama.

        Args:
            messages: list of {"role": "system"|"user"|"assistant", "content": str}

        Returns:
            {
                "content": str,       # respons dari LLM
                "total_duration": int, # durasi total dalam nanoseconds
                "eval_count": int,     # jumlah token yang di-generate
            }

        Raises:
            OllamaConnectionError: Ollama tidak berjalan
            OllamaTimeoutError: Request melebihi batas waktu
        """
        logger.debug(
            f"Sending chat to Ollama ({self.model}), "
            f"{len(messages)} messages, temp={self.temperature}"
        )

        try:
            response = await asyncio.wait_for(
                self.client.chat(
                    model=self.model,
                    messages=messages,
                    format="json",
                    options={
                        "temperature": self.temperature,
                        "num_ctx": self.num_ctx,
                    },
                ),
                timeout=self.timeout,
            )

            content = response["message"]["content"]
            total_duration = response.get("total_duration", 0)
            eval_count = response.get("eval_count", 0)

            logger.debug(
                f"Ollama response received: {len(content)} chars, "
                f"duration={total_duration / 1e9:.1f}s, "
                f"tokens={eval_count}"
            )

            return {
                "content": content,
                "total_duration": total_duration,
                "eval_count": eval_count,
            }

        except asyncio.TimeoutError:
            logger.error(f"Ollama timeout after {self.timeout}s")
            raise OllamaTimeoutError(timeout_seconds=self.timeout)

        except ConnectionError as e:
            logger.error(f"Ollama connection error: {e}")
            raise OllamaConnectionError(details=str(e))

        except Exception as e:
            # Catch ollama SDK specific errors (e.g., model not found)
            error_msg = str(e).lower()
            if "connect" in error_msg or "refused" in error_msg:
                logger.error(f"Ollama connection error: {e}")
                raise OllamaConnectionError(details=str(e))
            logger.error(f"Ollama unexpected error: {e}")
            raise
```

### Step 3: Update `app/ai/__init__.py`

```python
from app.ai.base import BaseLLMProvider
from app.ai.ollama_provider import OllamaProvider
```

### Step 4: Test manual (pastikan `ollama serve` berjalan)

```python
import asyncio
from app.config import Settings
from app.ai.ollama_provider import OllamaProvider

async def test():
    settings = Settings()
    provider = OllamaProvider(settings)

    messages = [
        {"role": "system", "content": "Jawab dalam format JSON: {\"status\": \"ok\", \"message\": \"...\"}"},
        {"role": "user", "content": "Halo, apa kabar?"},
    ]

    result = await provider.chat(messages)
    print(f"Content: {result['content']}")
    print(f"Duration: {result['total_duration'] / 1e9:.1f}s")
    print(f"Tokens: {result['eval_count']}")

asyncio.run(test())
```

## 6. Output yang Diharapkan

Jika Ollama berjalan:
```
Content: {"status": "ok", "message": "Halo! Saya baik-baik saja."}
Duration: 2.3s
Tokens: 15
```

Jika Ollama tidak berjalan:
```
app.utils.errors.OllamaConnectionError: Tidak dapat terhubung ke Ollama...
```

## 7. Dependencies

- **Task 01** — `ollama` package terinstall, `config.py` sudah ada
- **Task 02** — `OllamaConnectionError`, `OllamaTimeoutError` terdefinisi
- **External**: Ollama harus terinstall dan model `qwen2.5:7b-instruct` sudah di-pull

## 8. Acceptance Criteria

- [ ] `OllamaProvider(settings)` berhasil diinstansiasi
- [ ] `OllamaProvider.chat(messages)` return dict dengan key `content`, `total_duration`, `eval_count`
- [ ] Response `content` berisi string (output dari LLM)
- [ ] Jika Ollama tidak berjalan → raise `OllamaConnectionError`
- [ ] Jika melebihi timeout → raise `OllamaTimeoutError`
- [ ] JSON mode aktif: LLM menghasilkan output JSON (bukan teks bebas)
- [ ] Temperature dan num_ctx dikirim ke Ollama sesuai config
- [ ] Logging: debug log saat kirim dan terima response

## 9. Estimasi

**Medium** — ~1.5 jam
