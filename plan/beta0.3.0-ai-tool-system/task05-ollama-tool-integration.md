# Task 05 — Ollama Native Tool Calling Integration

## Deskripsi

Mengintegrasikan native tool calling ke **`OllamaProvider`**. Ollama SDK (v0.4+) mendukung parameter `tools` di chat API — kita akan mengirim tool specs sebagai definisi fungsi ke Ollama, dan memproses response `tool_calls` yang dikembalikan oleh model.

Ini adalah **primary strategy** untuk Ollama. Model-model modern seperti `qwen2.5`, `llama3.2`, dan `mistral` v0.4+ support native tool calling. Jika model tidak support, sistem akan fallback ke prompt injection (Task 07).

---

## Tujuan Teknis

- `OllamaProvider.chat()` bisa menerima `tools: list[ToolSpec]` dan mengirimnya ke Ollama API
- `OllamaProvider.chat()` bisa mengembalikan `tool_calls` dari response Ollama
- `OllamaProvider.chat_stream()` bisa mengindikasikan tool call selama streaming
- Format tool_calls yang dikembalikan konsisten dengan yang diharapkan `ToolHandler`
- Backward compatible — tanpa parameter `tools`, behavior tidak berubah sama sekali
- Handle edge case: Ollama return tool_calls dengan content kosong, arguments sebagai string JSON

---

## Scope

### Termasuk

- Modifikasi `app/ai/ollama_provider.py`:

  **Update `chat()` method:**
  - Tambah parameter: `tools: list[ToolSpec] | None = None`
  - Konversi `ToolSpec` ke format Ollama:
    ```python
    tools_payload = [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
        }
        for t in (tools or [])
    ]
    ```
  - Kirim `tools=tools_payload` ke `self.client.chat()`
  - **PENTING**: Jika `tools` tidak None, jangan kirim `format="json"` — karena bertentangan dengan tools
  - Parse response: extract `message.tool_calls` jika ada
  - Return `tool_calls` dalam response dict dengan format:
    ```python
    {
        "content": "...",
        "total_duration": ...,
        "eval_count": ...,
        "thinking": "...",
        "tool_calls": [
            {"function": {"name": "web_search", "arguments": {"query": "..."}}}
        ],  # None jika tidak ada tool call
    }
    ```

  **Update `chat_stream()` method:**
  - Tambah parameter: `tools: list[ToolSpec] | None = None`
  - Kirim `tools=tools_payload` ke streaming API
  - Jika stream chunk mengandung tool_calls, yield sebagai event:
    ```python
    yield {
        "token": "",
        "thinking": "",
        "done": False,
        "tool_calls": [
            {"function": {"name": "web_search", "arguments": {"query": "..."}}}
        ],
    }
    ```
  - Setelah tool calls selesai, yield `{"done": True}`

  **Edge cases:**
  - Ollama bisa return `arguments` sebagai **string JSON** — harus di-parse
  - Ollama bisa return `content` + `tool_calls` bersamaan — keduanya harus di-handle
  - Jika model tidak support tools, Ollama akan ignore parameter `tools` — tetap aman

### Tidak Termasuk

- Tool execution loop (Task 04 — ToolHandler)
- Gemini integration (Task 06)
- Prompt injection fallback (Task 07)
- Integrasi ke ChatService (Task 08)

---

## Langkah Implementasi

### Langkah 1: Baca file existing

Baca `app/ai/ollama_provider.py` — pahami struktur `chat()` dan `chat_stream()` yang sudah ada.

### Langkah 2: Update `chat()` method

```python
async def chat(
    self,
    messages: list[dict],
    think: bool = True,
    model: str | None = None,
    tools: list[ToolSpec] | None = None,  # NEW
) -> dict:
    """Kirim chat completion ke Ollama.

    Args:
        messages: List of messages.
        think: Apakah model boleh menggunakan thinking mode.
        model: Nama model override.
        tools: Tool specs untuk native tool calling. Jika None, tool calling dinonaktifkan.

    Returns:
        dict dengan field: content, total_duration, eval_count, thinking, tool_calls.
    """
    # Build request kwargs
    has_images = any(m.get("images") for m in messages)
    chat_kwargs = {
        "model": model or self.model,
        "messages": messages,
        "options": {
            "temperature": self.temperature,
            "num_ctx": self.num_ctx,
            "think": think,
        },
    }

    # Tool specs — konversi ke format Ollama
    if tools:
        tools_payload = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]
        chat_kwargs["tools"] = tools_payload
        # Jangan kirim format="json" jika tools aktif — konflik
    elif not has_images:
        chat_kwargs["format"] = "json"

    try:
        response = await asyncio.wait_for(
            self.client.chat(**chat_kwargs),
            timeout=self.timeout,
        )

        # Parse response (sama seperti sebelumnya)
        if hasattr(response, "model_dump"):
            resp = response.model_dump()
        elif dataclasses.is_dataclass(response):
            resp = dataclasses.asdict(response)
        else:
            resp = response

        message = resp.get("message", {}) if isinstance(resp, dict) else {}
        content = message.get("content", "")
        thinking = (
            message.get("thinking")
            or message.get("reasoning")
            or message.get("thoughts")
            or ""
        )

        # Parse tool_calls
        tool_calls = None
        raw_tool_calls = message.get("tool_calls", []) if isinstance(message, dict) else []
        if raw_tool_calls:
            tool_calls = []
            for tc in raw_tool_calls:
                func = tc.get("function", {})
                name = func.get("name", "")
                raw_args = func.get("arguments", {})

                # Handle arguments sebagai string JSON
                if isinstance(raw_args, str):
                    try:
                        raw_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        raw_args = {}

                if name:
                    tool_calls.append({
                        "function": {
                            "name": name,
                            "arguments": raw_args if isinstance(raw_args, dict) else {},
                        }
                    })

        total_duration = resp.get("total_duration", 0) if isinstance(resp, dict) else 0
        eval_count = resp.get("eval_count", 0) if isinstance(resp, dict) else 0

        return {
            "content": content,
            "total_duration": total_duration,
            "eval_count": eval_count,
            "thinking": thinking,
            "tool_calls": tool_calls,  # None jika tidak ada tool call
        }

    except (asyncio.TimeoutError, ConnectionError, Exception) as e:
        # Error handling yang sudah ada
        ...
```

### Langkah 3: Update `chat_stream()` method

```python
async def chat_stream(
    self,
    messages: list[dict],
    think: bool = True,
    model: str | None = None,
    tools: list[ToolSpec] | None = None,  # NEW
):
    """Streaming chat completion — yield token demi token.

    Args:
        messages: List of messages.
        think: Apakah model boleh menggunakan thinking mode.
        model: Nama model override.
        tools: Tool specs untuk native tool calling.

    Yields:
        dict: {"token": str, "thinking": str, "done": bool, "tool_calls": list | None}
    """
    chat_kwargs = {
        "model": model or self.model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": self.temperature,
            "num_ctx": self.num_ctx,
            "think": think,
        },
    }

    if tools:
        tools_payload = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]
        chat_kwargs["tools"] = tools_payload

    try:
        stream = await asyncio.wait_for(
            self.client.chat(**chat_kwargs),
            timeout=self.timeout,
        )

        async for chunk in stream:
            if hasattr(chunk, "model_dump"):
                payload = chunk.model_dump()
            elif dataclasses.is_dataclass(chunk):
                payload = dataclasses.asdict(chunk)
            else:
                payload = chunk

            msg = payload.get("message", {}) if isinstance(payload, dict) else {}
            content = msg.get("content", "")
            thinking = (
                msg.get("thinking")
                or msg.get("reasoning")
                or msg.get("thoughts")
                or ""
            )

            # Parse tool_calls dari stream chunk
            tool_calls = None
            raw_tool_calls = msg.get("tool_calls", []) if isinstance(msg, dict) else []
            if raw_tool_calls:
                tool_calls = []
                for tc in raw_tool_calls:
                    func = tc.get("function", {})
                    name = func.get("name", "")
                    raw_args = func.get("arguments", {})
                    if isinstance(raw_args, str):
                        try:
                            raw_args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            raw_args = {}
                    if name:
                        tool_calls.append({
                            "function": {"name": name, "arguments": raw_args},
                        })

            yield {
                "token": content,
                "thinking": thinking,
                "done": payload.get("done", False) if isinstance(payload, dict) else False,
                "tool_calls": tool_calls,
            }

    except (asyncio.TimeoutError, Exception) as e:
        # Error handling yang sudah ada
        ...
```

### Langkah 4: Validasi

```python
import asyncio
from app.tools.base import ToolSpec
from app.ai.ollama_provider import OllamaProvider
from app.config import Settings


async def test():
    settings = Settings()
    provider = OllamaProvider(settings)

    # Test tanpa tools — harus sama seperti sebelumnya
    result = await provider.chat(
        messages=[{"role": "user", "content": "Halo"}],
        think=False,
    )
    assert "content" in result
    assert result.get("tool_calls") is None  # Tidak ada tool call
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

    result = await provider.chat(
        messages=[{"role": "user", "content": "Cari berita AI terbaru"}],
        think=False,
        tools=tools,
    )
    print(f"With tools: content_len={len(result['content'])}, tool_calls={result.get('tool_calls')}")
    # Mungkin atau mungkin tidak memanggil tool — tergantung model
    # Yang penting tidak error

    print("Validation passed!")


asyncio.run(test())
```

---

## Output yang Diharapkan

- `OllamaProvider.chat()` bisa menerima dan memproses tool specs
- Response mengandung `tool_calls` jika LLM memutuskan memanggil tool
- `chat_stream()` bisa mengindikasikan tool call selama streaming
- Backward compatible — tanpa tools, behavior sama seperti sebelumnya
- `format="json"` tidak dikirim bersamaan dengan tools

---

## Dependencies

- **Task 01 (Tool Abstraction)** — `ToolSpec`
- **Task 04 (Tool Handler)** — format tool_calls yang diharapkan
- Ollama server dengan model yang support tools (qwen2.5, llama3.2, dll)

---

## Acceptance Criteria

### Functional
- [ ] `chat(tools=[...])` mengirim tool specs ke Ollama API
- [ ] Response mengandung `tool_calls` jika LLM memanggil tool
- [ ] Format tool_calls: `[{"function": {"name": "...", "arguments": {...}}}]`
- [ ] `chat(tools=None)` — behavior tidak berubah (backward compatible)
- [ ] `chat_stream(tools=[...])` — yield tool_calls di stream chunk
- [ ] `format="json"` tidak dikirim bersamaan dengan tools

### Edge Cases
- [ ] Ollama return arguments sebagai string JSON → tetap diparse dengan benar
- [ ] Ollama return content + tool_calls bersamaan → keduanya di-handle
- [ ] Model tidak support tools → tools parameter diabaikan, tidak error
- [ ] Tool_calls dengan content kosong → tetap direturn

### Logging
- [ ] Tool specs yang dikirim di-log (DEBUG)
- [ ] Tool_calls yang diterima di-log (INFO)
- [ ] Jumlah tool_calls di-log

---

## Estimasi

**Medium** (~2 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Analisis kode existing OllamaProvider | 15 menit |
| Implementasi tools parameter di chat() | 45 menit |
| Implementasi tools parameter di chat_stream() | 30 menit |
| Parse tool_calls dari response (termasuk string JSON) | 20 menit |
| Validasi & testing | 20 menit |
