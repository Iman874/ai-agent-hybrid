# Task 01: Buat GeminiChatProvider

## Deskripsi
Membuat class `GeminiChatProvider` yang membungkus Gemini API agar bisa digunakan sebagai chat interviewer, dengan return format **identik** dengan `OllamaProvider.chat()`.

## Tujuan Teknis
1. Buat file `app/ai/gemini_chat_provider.py`
2. Class mengimplementasikan interface `BaseLLMProvider`
3. Method `chat(messages)` menerima format Ollama messages dan mengkonversi ke Gemini format
4. Return value `{"content": str, "total_duration": int, "eval_count": int}` — sama persis dengan Ollama

## Scope
- **Dikerjakan**:
  - Class `GeminiChatProvider` dengan constructor dan method `chat()`
  - Konversi format messages `[{"role": "system"|"user"|"assistant", "content": str}]` → Gemini chat format
  - Error handling: timeout, API error, rate limit
  - Logging yang konsisten
- **Tidak dikerjakan**:
  - Modifikasi `ChatService` (task02)
  - UI changes

## Langkah Implementasi

### Step 1: Review `BaseLLMProvider` interface
```python
# app/ai/base.py — pastikan ada abstract method chat()
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict]) -> dict:
        pass
```

### Step 2: Buat `GeminiChatProvider`
```python
# app/ai/gemini_chat_provider.py

import logging
import time
import asyncio
import google.generativeai as genai

from app.ai.base import BaseLLMProvider
from app.config import Settings
from app.utils.errors import GeminiTimeoutError, GeminiAPIError

logger = logging.getLogger("ai-agent-hybrid.gemini-chat")


class GeminiChatProvider(BaseLLMProvider):
    """Gemini API sebagai chat interviewer."""

    def __init__(self, settings: Settings):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=genai.GenerationConfig(
                temperature=settings.gemini_temperature,
                max_output_tokens=settings.gemini_max_tokens,
                response_mime_type="application/json",  # Force JSON output
            ),
        )
        self.timeout = settings.gemini_timeout
        self.model_name = settings.gemini_model

    async def chat(self, messages: list[dict]) -> dict:
        """
        Chat via Gemini API.
        Input: format Ollama [{role, content}, ...]
        Output: {"content": str, "total_duration": int, "eval_count": int}
        """
        start = time.monotonic()

        # Convert messages ke format Gemini
        gemini_messages = self._convert_messages(messages)

        try:
            chat_session = self.model.start_chat(history=gemini_messages[:-1])
            last_msg = gemini_messages[-1]["parts"][0]

            response = await asyncio.wait_for(
                asyncio.to_thread(chat_session.send_message, last_msg),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            raise GeminiTimeoutError(self.timeout)
        except Exception as e:
            raise GeminiAPIError(details=str(e)[:200])

        duration_ns = int((time.monotonic() - start) * 1e9)
        content = response.text

        usage = getattr(response, "usage_metadata", None)
        eval_count = getattr(usage, "candidates_token_count", 0) if usage else 0

        logger.info(f"Gemini chat: {duration_ns / 1e9:.1f}s, {len(content)} chars")

        return {
            "content": content,
            "total_duration": duration_ns,
            "eval_count": eval_count,
        }

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """Konversi format Ollama → Gemini chat format."""
        result = []
        system_text = ""

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_text += content + "\n"
            elif role == "user":
                text = (system_text + content) if system_text else content
                system_text = ""
                result.append({"role": "user", "parts": [text]})
            elif role == "assistant":
                result.append({"role": "model", "parts": [content]})

        # Jika hanya ada system message tanpa user message
        if system_text and not result:
            result.append({"role": "user", "parts": [system_text]})

        return result
```

### Step 3: Pastikan `BaseLLMProvider` di `base.py` sudah proper
Buka `app/ai/base.py` dan verifikasi interface-nya compatible.

## Output yang Diharapkan
- File baru: `app/ai/gemini_chat_provider.py`
- Class bisa di-import tanpa error
- Return format identik dengan `OllamaProvider.chat()`

## Dependencies
- Tidak ada (task pertama)

## Acceptance Criteria
- [ ] File `app/ai/gemini_chat_provider.py` ada dan bisa di-import
- [ ] `GeminiChatProvider` extends `BaseLLMProvider`
- [ ] Method `chat()` return `{"content": str, "total_duration": int, "eval_count": int}`
- [ ] System messages dikonversi dengan benar (prepend ke user message pertama)
- [ ] `response_mime_type="application/json"` agar output selalu JSON
- [ ] Error handling: `GeminiTimeoutError`, `GeminiAPIError`
- [ ] Logging setiap panggilan

## Estimasi
Medium
