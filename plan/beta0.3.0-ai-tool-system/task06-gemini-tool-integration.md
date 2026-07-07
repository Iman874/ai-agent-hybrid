# Task 06 — Gemini Native Tool Calling Integration

## Deskripsi

Mengintegrasikan native tool calling ke **`GeminiChatProvider`**. Gemini API mendukung `function_declarations` — kita akan mengirim tool specs sebagai function declarations ke Gemini, dan memproses response `function_call` yang dikembalikan.

Ini adalah **primary strategy** untuk Gemini. Semua model Gemini modern (`gemini-1.5-pro`, `gemini-2.0-flash`, dll) support function calling. Jika karena alasan tertentu tidak support, sistem akan fallback ke prompt injection (Task 07).

---

## Tujuan Teknis

- `GeminiChatProvider` bisa menerima `tools: list[ToolSpec]` dan mengirimnya sebagai `function_declarations`
- `GeminiChatProvider.chat()` bisa mengembalikan `tool_calls` dari response Gemini
- `GeminiChatProvider.chat_stream()` bisa mengindikasikan function call selama streaming
- Format `tool_calls` yang dikembalikan **konsisten** dengan `OllamaProvider` — sehingga `ToolHandler` bisa memproses keduanya tanpa membedakan provider
- Backward compatible — tanpa parameter `tools`, behavior tidak berubah

---

## Scope

### Termasuk

- Modifikasi `app/ai/gemini_chat_provider.py`:

  **Update `__init__()` method:**
  - Tambah parameter: `tools: list[ToolSpec] | None = None`
  - Konversi `ToolSpec` ke format Gemini:
    ```python
    tools_payload = [
        {
            "function_declarations": [
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
                for t in (tools or [])
            ]
        }
    ]
    ```
  - Inisialisasi `genai.GenerativeModel` dengan `tools=tools_payload`
  - Jika `tools` kosong atau None, jangan kirim parameter `tools`

  **Update `chat()` method:**
  - Setelah `send_message()` atau `generate_content()`, cek response untuk `function_call`
  - Gemini `function_call` ada di `response.candidates[0].content.parts[0].function_call`
  - Extract: `name` dan `args`
  - Konversi ke format yang konsisten dengan Ollama:
    ```python
    tool_calls = [
        {
            "function": {
                "name": function_call.name,
                "arguments": dict(function_call.args),  # Proto → dict
            }
        }
    ]
    ```
  - Return `tool_calls` dalam response dict

  **Update `chat_stream()` method:**
  - Jika stream chunk mengandung `function_call`, yield sebagai event
  - Format yield: `{"token": "", "thinking": "", "done": False, "tool_calls": [...]}`

  **Edge cases:**
  - Gemini bisa return `function_call` + `text` bersamaan — handle keduanya
  - `function_call.args` adalah `proto.MutableMapping` — harus dikonversi ke dict biasa
  - Jika Gemini memanggil multiple functions dalam satu response (jarang, tapi mungkin)

### Tidak Termasuk

- Tool execution loop (Task 04 — ToolHandler)
- Ollama integration (Task 05)
- Prompt injection fallback (Task 07)
- Integrasi ke ChatService (Task 08)

---

## Langkah Implementasi

### Langkah 1: Baca file existing

Baca `app/ai/gemini_chat_provider.py` — pahami struktur `__init__()`, `chat()`, `chat_stream()`, dan `_convert_messages()`.

### Langkah 2: Update `__init__()` method

```python
class GeminiChatProvider(BaseLLMProvider):
    """Gemini API sebagai chat interviewer — return format identik OllamaProvider."""

    def __init__(self, settings: Settings, tools: list[ToolSpec] | None = None):
        """Inisialisasi GeminiChatProvider.

        Args:
            settings: Settings aplikasi.
            tools: Tool specs untuk function calling. Jika None, function calling dinonaktifkan.
        """
        genai.configure(api_key=settings.gemini_api_key)

        # Konfigurasi dasar
        generation_config = genai.GenerationConfig(
            temperature=settings.gemini_temperature,
            max_output_tokens=settings.gemini_max_tokens,
            response_mime_type="application/json",
        )

        # Tool specs — konversi ke format Gemini function_declarations
        model_kwargs = {
            "model_name": settings.gemini_model,
            "generation_config": generation_config,
        }

        if tools:
            tools_payload = [
                {
                    "function_declarations": [
                        {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.parameters,
                        }
                        for t in tools
                    ]
                }
            ]
            model_kwargs["tools"] = tools_payload
            # Jika tools aktif, jangan paksa response MIME type JSON
            # karena response bisa berupa function_call
            model_kwargs["generation_config"].response_mime_type = None

        self.model = genai.GenerativeModel(**model_kwargs)
        self.timeout = settings.gemini_timeout
        self.model_name = settings.gemini_model
```

### Langkah 3: Update `chat()` method — Parse function_call

```python
async def chat(self, messages: list[dict], think: bool = True, model: str | None = None) -> dict:
    """Chat via Gemini API — dengan dukungan function calling.

    Args:
        messages: List of messages in Ollama format.
        think: Diabaikan untuk Gemini (kompatibilitas interface).
        model: Diabaikan untuk Gemini (kompatibilitas interface).

    Returns:
        dict: {"content": str, "total_duration": int, "eval_count": int, "tool_calls": list | None}
    """
    start = time.monotonic()
    gemini_messages = self._convert_messages(messages)

    try:
        if len(gemini_messages) > 1:
            chat_session = self.model.start_chat(history=gemini_messages[:-1])
            last_parts = gemini_messages[-1]["parts"]
            response = await asyncio.wait_for(
                asyncio.to_thread(chat_session.send_message, last_parts),
                timeout=self.timeout,
            )
        else:
            prompt = gemini_messages[0]["parts"]
            response = await asyncio.wait_for(
                asyncio.to_thread(self.model.generate_content, prompt),
                timeout=self.timeout,
            )
    except asyncio.TimeoutError:
        raise GeminiTimeoutError(self.timeout)
    except Exception as e:
        raise GeminiAPIError(details=str(e)[:200])

    duration_ns = int((time.monotonic() - start) * 1e9)

    # Parse response — cek function_call
    content = ""
    tool_calls = None

    try:
        candidate = response.candidates[0]
        for part in candidate.content.parts:
            if hasattr(part, "function_call") and part.function_call is not None:
                # Ada function call!
                fc = part.function_call
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append({
                    "function": {
                        "name": fc.name,
                        "arguments": dict(fc.args),  # Proto MutableMapping → dict
                    }
                })
            elif hasattr(part, "text") and part.text:
                content += part.text
    except (IndexError, AttributeError):
        # Fallback: response.text
        content = getattr(response, "text", "")

    usage = getattr(response, "usage_metadata", None)
    eval_count = getattr(usage, "candidates_token_count", 0) if usage else 0

    return {
        "content": content,
        "total_duration": duration_ns,
        "eval_count": eval_count,
        "tool_calls": tool_calls,  # None jika tidak ada function call
    }
```

### Langkah 4: Update `chat_stream()` method

```python
async def chat_stream(self, messages: list[dict], think: bool = True, model: str | None = None):
    """Streaming chat via Gemini API — dengan dukungan function calling.

    Yields:
        dict: {"token": str, "thinking": str, "done": bool, "tool_calls": list | None}
    """
    gemini_messages = self._convert_messages(messages)

    try:
        if len(gemini_messages) > 1:
            chat_session = self.model.start_chat(history=gemini_messages[:-1])
            last_parts = gemini_messages[-1]["parts"]
            response = await asyncio.wait_for(
                asyncio.to_thread(chat_session.send_message, last_parts, stream=True),
                timeout=self.timeout,
            )
        else:
            prompt = gemini_messages[0]["parts"] if gemini_messages else ""
            response = await asyncio.wait_for(
                asyncio.to_thread(self.model.generate_content, prompt, stream=True),
                timeout=self.timeout,
            )

        for chunk in response:
            text = ""
            tool_calls = None

            try:
                candidate = chunk.candidates[0]
                for part in candidate.content.parts:
                    if hasattr(part, "function_call") and part.function_call is not None:
                        fc = part.function_call
                        if tool_calls is None:
                            tool_calls = []
                        tool_calls.append({
                            "function": {
                                "name": fc.name,
                                "arguments": dict(fc.args),
                            }
                        })
                    elif hasattr(part, "text") and part.text:
                        text += part.text
            except (IndexError, AttributeError):
                text = getattr(chunk, "text", "")

            if text or tool_calls:
                yield {
                    "token": text,
                    "thinking": "",
                    "done": False,
                    "tool_calls": tool_calls,
                }

        yield {"token": "", "thinking": "", "done": True, "tool_calls": None}

    except asyncio.TimeoutError:
        raise GeminiTimeoutError(self.timeout)
    except Exception as e:
        raise GeminiAPIError(details=str(e)[:200])
```

### Langkah 5: Validasi

```python
import asyncio
from app.tools.base import ToolSpec
from app.ai.gemini_chat_provider import GeminiChatProvider
from app.config import Settings


async def test():
    settings = Settings()
    
    # Test tanpa tools
    provider = GeminiChatProvider(settings)
    result = await provider.chat(
        messages=[{"role": "user", "content": "Halo"}],
    )
    assert "content" in result
    assert result.get("tool_calls") is None
    print("Without tools: OK")

    # Test dengan tools
    tools = [
        ToolSpec(
            name="web_search",
            description="Search the web",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        )
    ]
    
    provider_with_tools = GeminiChatProvider(settings, tools=tools)
    result = await provider_with_tools.chat(
        messages=[{"role": "user", "content": "Cari berita AI terbaru"}],
    )
    print(f"With tools: content_len={len(result['content'])}, tool_calls={result.get('tool_calls')}")

    print("Validation passed!")


asyncio.run(test())
```

---

## Output yang Diharapkan

- `GeminiChatProvider` bisa menerima tool specs sebagai `function_declarations`
- Response mengandung `tool_calls` jika Gemini memutuskan memanggil function
- Format `tool_calls` konsisten dengan `OllamaProvider`
- `chat_stream()` bisa mengindikasikan function call
- Backward compatible — tanpa tools, behavior tidak berubah

---

## Dependencies

- **Task 01 (Tool Abstraction)** — `ToolSpec`
- **Task 04 (Tool Handler)** — format tool_calls yang diharapkan
- Gemini API key yang valid di `.env`

---

## Acceptance Criteria

### Functional
- [ ] `__init__(tools=[...])` mengirim function_declarations ke Gemini
- [ ] `chat()` mengembalikan `tool_calls` jika Gemini memanggil function
- [ ] Format tool_calls konsisten dengan Ollama: `[{"function": {"name": "...", "arguments": {...}}}]`
- [ ] `chat_stream()` yield tool_calls di stream chunk
- [ ] Tanpa parameter `tools`, behavior tidak berubah
- [ ] `response_mime_type="application/json"` tidak dikirim jika tools aktif

### Edge Cases
- [ ] `function_call.args` (proto MutableMapping) dikonversi ke dict biasa
- [ ] Gemini return text + function_call bersamaan — keduanya di-handle
- [ ] Multiple function calls dalam satu response — semua diproses
- [ ] Function call tanpa arguments — tetap valid

### Logging
- [ ] Function declarations yang dikirim di-log (DEBUG)
- [ ] Function call yang diterima di-log (INFO)

---

## Estimasi

**Medium** (~2 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Analisis kode existing GeminiChatProvider | 15 menit |
| Implementasi tools parameter di __init__ | 30 menit |
| Implementasi function_call parsing di chat() | 45 menit |
| Implementasi function_call di chat_stream() | 30 menit |
| Validasi & testing | 20 menit |
