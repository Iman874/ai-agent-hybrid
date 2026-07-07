# Task 04 — Tool Handler (Execution Loop & Parsing)

## Deskripsi

Membangun **`ToolHandler`** — komponen paling kritis dalam Tool System. ToolHandler bertanggung jawab atas **seluruh siklus hidup pemanggilan tool**:

1. **Menerima** tool_call dari LLM (baik native format maupun prompt injection)
2. **Memparsing** tool_call untuk mengekstrak nama tool dan arguments
3. **Mengeksekusi** tool via `ToolRegistry`
4. **Menginject** hasil tool ke conversation messages
5. **Mengirim ulang** ke LLM untuk response final
6. **Mengulangi** sampai tidak ada tool_call lagi atau max calls tercapai

ToolHandler adalah "otak" yang menghubungkan LLM dengan tool-tool yang tersedia. Tanpa komponen ini, LLM tidak bisa benar-benar menggunakan tool.

---

## Tujuan Teknis

- Memproses tool_call dari LLM dalam **dua format**: native (Ollama tools param / Gemini function_declarations) dan prompt injection (`[[TOOL_CALL: ...]]`)
- Parse arguments dari prompt injection format (key=value dengan quoted strings)
- Eksekusi tool via `ToolRegistry` dengan error handling
- Inject hasil tool ke messages dengan format `{"role": "tool", "content": ..., "name": ...}`
- Re-call LLM dengan konteks yang sudah diperkaya hasil tool
- **Mencegah infinite loop** dengan max 3 calls per turn
- **Mencegah duplicate tool calls** (tool yang sama dipanggil dua kali berturut-turut)
- Logging setiap step untuk debugging dan observability

---

## Scope

### Termasuk

- Membuat `app/ai/tool_handler.py`
- Implementasi class `ToolHandler`:

  **`__init__(self, tool_registry: ToolRegistry, max_calls: int = 3)`**
  - Simpan reference ke `ToolRegistry`
  - Set `max_calls` (default 3)
  - Inisialisasi logger

  **`parse_native_tool_calls(self, response: dict) -> list[dict]`**
  - Handle format Ollama: `response["message"]["tool_calls"]`
    ```json
    {
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "function": {
              "name": "web_search",
              "arguments": {"query": "AI Indonesia"}
            }
          }
        ]
      }
    }
    ```
  - Handle format Gemini: `response["function_call"]`
    ```json
    {
      "function_call": {
        "name": "web_search",
        "args": {"query": "AI Indonesia"}
      }
    }
    ```
  - Normalisasi ke format internal: `[{"name": "web_search", "arguments": {"query": "..."}}]`
  - Return empty list jika tidak ada tool_calls

  **`parse_prompt_injection(self, text: str) -> list[dict]`**
  - Regex pattern: `r'\[\[TOOL_CALL:\s*(\w+)\(([^)]*)\)\]\]'`
  - Parse arguments: key=value, value bisa quoted (single/double quotes)
  - Handle multiple arguments: `[[TOOL_CALL: web_search(query="AI", max_results=3)]]`
  - Handle arguments tanpa value (boolean flag): `[[TOOL_CALL: tool_name(flag)]]`
  - Return list of `{"name": ..., "arguments": {...}}`
  - Return empty list jika tidak ada pattern yang cocok

  **`async handle_tool_calls(self, tool_calls: list[dict]) -> list[dict]`**
  - Iterate setiap tool_call
  - Panggil `self.tool_registry.execute(name, **arguments)`
  - Format hasil ke message: `{"role": "tool", "content": result.data, "name": name}`
  - Jika tool gagal: inject pesan error instructif
  - Return list of tool result messages

  **`async execute_with_loop(self, provider_call_fn, messages: list[dict], tools_enabled: bool = True) -> tuple[list[dict], dict, list[dict]]`**
  - Parameter `provider_call_fn`: async callable yang menerima messages dan return response dict
  - Flow:
    1. Call LLM via `provider_call_fn(messages)`
    2. Cek response untuk tool_calls (native dulu, lalu prompt injection)
    3. Jika ada tool_calls:
       a. Increment counter
       b. Jika counter > max_calls: break dengan pesan error
       c. Cek duplicate: jika tool yang sama dipanggil lagi → skip dengan warning
       d. Eksekusi tool via `handle_tool_calls()`
       e. Inject hasil ke messages
       f. Call LLM lagi (kembali ke step 2)
    4. Jika tidak ada tool_calls: return final response
  - Return: `(final_messages, final_response, tool_call_history)`
  - `tool_call_history`: list of dict untuk logging dan frontend events

  **`_check_duplicate(self, tool_calls: list[dict], history: list[dict]) -> list[dict]`**
  - Filter out tool calls yang sudah pernah dipanggil sebelumnya
  - Log warning jika duplicate terdeteksi

### Tidak Termasuk

- Integrasi ke ChatService (task terpisah — Task 08)
- Integrasi ke provider (task terpisah — Task 05, 06)
- SSE events untuk frontend (task terpisah — Task 09)
- Prompt injection template (task terpisah — Task 07)

---

## Langkah Implementasi

### Langkah 1: Buat `app/ai/tool_handler.py`

```python
"""Tool Handler — mengelola siklus hidup pemanggilan tool.

ToolHandler bertanggung jawab untuk:
1. Menerima tool_call dari LLM (native atau prompt injection)
2. Mengeksekusi tool via ToolRegistry
3. Menginject hasil ke messages
4. Re-call LLM untuk response final
5. Mencegah infinite loop (max 3 calls per turn)

Usage:
    handler = ToolHandler(tool_registry)
    final_messages, final_response, history = await handler.execute_with_loop(
        provider_call_fn=ollama_provider.chat,
        messages=conversation_messages,
    )
"""

import logging
import re
from typing import Any, Callable, Coroutine

from app.tools.registry import ToolRegistry
from app.tools.base import ToolResult

logger = logging.getLogger("ai-agent-hybrid.tools.handler")

# Regex untuk prompt injection format: [[TOOL_CALL: name(arg1="val", arg2=val)]]
TOOL_CALL_PATTERN = re.compile(
    r'\[\[TOOL_CALL:\s*(\w+)\s*\(([^)]*)\)\s*\]\]'
)

# Regex untuk parse arguments: key="value" atau key=value
ARG_PATTERN = re.compile(
    r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\S+))'
)


class ToolHandler:
    """Mengelola tool calling lifecycle.

    Attributes:
        tool_registry: Registry untuk mengeksekusi tool.
        max_calls: Maksimum tool calls per turn (default 3).
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        max_calls: int = 3,
    ) -> None:
        """Inisialisasi ToolHandler.

        Args:
            tool_registry: ToolRegistry instance.
            max_calls: Maksimum tool calls per turn. Default 3.

        Raises:
            ValueError: Jika max_calls < 1.
        """
        if max_calls < 1:
            raise ValueError("max_calls must be >= 1")

        self.tool_registry = tool_registry
        self.max_calls = max_calls
        self._logger = logger

    def parse_native_tool_calls(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse tool_calls dari response LLM native format.

        Mendukung format:
        - Ollama: response["message"]["tool_calls"]
        - Gemini: response["function_call"]

        Args:
            response: Response dict dari LLM provider.

        Returns:
            list[dict]: List of {"name": str, "arguments": dict}.
                       Empty list jika tidak ada tool_calls.
        """
        tool_calls: list[dict[str, Any]] = []

        # Format Ollama: message.tool_calls
        message = response.get("message", {})
        raw_calls = message.get("tool_calls", [])

        if raw_calls:
            for call in raw_calls:
                func = call.get("function", {})
                name = func.get("name", "")
                raw_args = func.get("arguments", {})

                # Ollama bisa return arguments sebagai string JSON atau dict
                if isinstance(raw_args, str):
                    import json
                    try:
                        raw_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        self._logger.warning(
                            f"Failed to parse tool call arguments as JSON: {raw_args[:100]}"
                        )
                        raw_args = {}

                if name:
                    tool_calls.append({
                        "name": name,
                        "arguments": raw_args if isinstance(raw_args, dict) else {},
                    })

        # Format Gemini: function_call
        function_call = response.get("function_call")
        if function_call:
            name = function_call.get("name", "")
            args = function_call.get("args", {})
            if name:
                tool_calls.append({
                    "name": name,
                    "arguments": args if isinstance(args, dict) else {},
                })

        if tool_calls:
            self._logger.debug(
                f"Parsed {len(tool_calls)} native tool call(s): "
                f"{[t['name'] for t in tool_calls]}"
            )

        return tool_calls

    def parse_prompt_injection(self, text: str) -> list[dict[str, Any]]:
        """Parse tool calls dari prompt injection format.

        Format: [[TOOL_CALL: name(arg1="val1", arg2=val2)]]

        Args:
            text: Response text dari LLM yang mungkin mengandung tool calls.

        Returns:
            list[dict]: List of {"name": str, "arguments": dict}.
                       Empty list jika tidak ada pattern yang cocok.
        """
        matches = TOOL_CALL_PATTERN.findall(text)
        if not matches:
            return []

        tool_calls: list[dict[str, Any]] = []
        for name, args_str in matches:
            args: dict[str, Any] = {}

            if args_str.strip():
                # Parse key=value pairs
                for match in ARG_PATTERN.finditer(args_str):
                    key = match.group(1)
                    # Value bisa dari group 2 (double quote), 3 (single quote), atau 4 (unquoted)
                    value = match.group(2) or match.group(3) or match.group(4)
                    # Convert numeric strings
                    if value is not None:
                        if value.isdigit():
                            value = int(value)
                        elif value.replace(".", "", 1).isdigit():
                            value = float(value)
                        elif value.lower() in ("true", "false"):
                            value = value.lower() == "true"
                    args[key] = value

            tool_calls.append({"name": name, "arguments": args})

        self._logger.debug(
            f"Parsed {len(tool_calls)} prompt injection tool call(s): "
            f"{[t['name'] for t in tool_calls]}"
        )

        return tool_calls

    async def handle_tool_calls(
        self,
        tool_calls: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Eksekusi tool calls dan return tool result messages.

        Args:
            tool_calls: List of {"name": str, "arguments": dict}.

        Returns:
            list[dict]: List of {"role": "tool", "content": str, "name": str}.
        """
        tool_messages: list[dict[str, Any]] = []

        for call in tool_calls:
            name = call["name"]
            arguments = call.get("arguments", {})

            self._logger.info(f"Executing tool: {name}({arguments})")

            result = await self.tool_registry.execute(name, **arguments)

            if result.success:
                self._logger.debug(
                    f"Tool '{name}' succeeded: data_len={len(result.data)}"
                )
                tool_messages.append({
                    "role": "tool",
                    "content": result.data,
                    "name": name,
                })
            else:
                self._logger.warning(
                    f"Tool '{name}' failed: {result.error}"
                )
                # Inject error message instructif — LLM harus fallback ke pengetahuannya
                error_content = (
                    f"Pencarian menggunakan tool '{name}' gagal: {result.error}. "
                    f"Gunakan pengetahuan yang Anda miliki untuk merespon user. "
                    f"Jangan memanggil tool '{name}' lagi untuk pertanyaan ini."
                )
                tool_messages.append({
                    "role": "tool",
                    "content": error_content,
                    "name": name,
                })

        return tool_messages

    def _check_duplicate(
        self,
        tool_calls: list[dict[str, Any]],
        history: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter duplicate tool calls.

        Tool call dianggap duplicate jika nama tool DAN arguments sama persis
        dengan tool call sebelumnya dalam history.

        Args:
            tool_calls: Tool calls yang akan difilter.
            history: Riwayat tool calls sebelumnya.

        Returns:
            list[dict]: Tool calls yang unik (duplicate dihapus).
        """
        if not history:
            return tool_calls

        # Normalize arguments to hashable form
        def _make_key(tc: dict[str, Any]) -> tuple:
            args = tc.get("arguments", {})
            return (tc["name"], tuple(sorted(args.items())))

        history_keys = {_make_key(h) for h in history}
        filtered = []
        for tc in tool_calls:
            key = _make_key(tc)
            if key in history_keys:
                self._logger.warning(
                    f"Duplicate tool call detected: {tc['name']}({tc.get('arguments', {})}). Skipping."
                )
            else:
                filtered.append(tc)

        return filtered

    async def execute_with_loop(
        self,
        provider_call_fn: Callable[..., Coroutine[Any, Any, dict[str, Any]]],
        messages: list[dict[str, Any]],
        tools_enabled: bool = True,
    ) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
        """Full tool execution loop.

        Flow:
        1. Call LLM
        2. Cek response untuk tool_calls
        3. Jika ada: execute, inject, re-call (max max_calls kali)
        4. Jika tidak ada: return final response

        Args:
            provider_call_fn: Async function untuk call LLM.
                             Signature: async fn(messages) -> dict
            messages: Conversation messages.
            tools_enabled: Jika False, skip tool calling.

        Returns:
            tuple:
                - final_messages: Messages setelah tool results di-inject.
                - final_response: Response final dari LLM.
                - tool_call_history: Riwayat tool calls untuk frontend events.
        """
        if not tools_enabled:
            self._logger.debug("Tools disabled, skipping tool execution loop")
            response = await provider_call_fn(messages)
            return messages, response, []

        current_messages = list(messages)
        tool_call_history: list[dict[str, Any]] = []
        call_count = 0

        while call_count < self.max_calls:
            # Call LLM
            self._logger.debug(
                f"Tool loop iteration {call_count + 1}/{self.max_calls}"
            )
            response = await provider_call_fn(current_messages)

            # Parse tool calls — coba native dulu, lalu prompt injection
            tool_calls = self.parse_native_tool_calls(response)

            # Jika tidak ada native, coba prompt injection dari content
            if not tool_calls:
                content = response.get("message", {}).get("content", "")
                if isinstance(response, dict) and "content" in response:
                    content = response.get("content", "")
                tool_calls = self.parse_prompt_injection(content)

            if not tool_calls:
                # Tidak ada tool call — selesai
                self._logger.debug(
                    f"No tool calls detected after {call_count} iteration(s)"
                )
                return current_messages, response, tool_call_history

            # Filter duplicate
            tool_calls = self._check_duplicate(tool_calls, tool_call_history)
            if not tool_calls:
                # Semua duplicate — selesai
                self._logger.debug("All tool calls were duplicates, stopping loop")
                return current_messages, response, tool_call_history

            # Record history
            tool_call_history.extend(tool_calls)
            call_count += 1

            # Execute tool calls
            self._logger.info(
                f"Executing {len(tool_calls)} tool call(s): "
                f"{[t['name'] for t in tool_calls]}"
            )
            tool_messages = await self.handle_tool_calls(tool_calls)

            # Inject tool results ke messages
            # Format: [..., assistant_msg_with_tool_call, tool_result_1, tool_result_2, ...]
            current_messages.append({
                "role": "assistant",
                "content": response.get("message", {}).get("content", ""),
                "tool_calls": [
                    {"function": {"name": t["name"], "arguments": t["arguments"]}}
                    for t in tool_calls
                ],
            })
            current_messages.extend(tool_messages)

            self._logger.debug(
                f"Tool results injected. Messages now: {len(current_messages)}"
            )

        # Max calls reached
        self._logger.warning(f"Max tool calls ({self.max_calls}) reached")
        # Satu call terakhir tanpa tool
        final_response = await provider_call_fn(current_messages)

        return current_messages, final_response, tool_call_history
```

### Langkah 2: Validasi

```python
import asyncio
from app.tools.registry import ToolRegistry
from app.tools.base import BaseTool, ToolSpec, ToolResult
from app.ai.tool_handler import ToolHandler


# Mock tool
class MockSearchTool(BaseTool):
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
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

    async def execute(self, query: str = "") -> ToolResult:
        return ToolResult(
            tool_name="web_search",
            success=True,
            data=f"=== HASIL PENCARIAN ===\nQuery: {query}\nHasil: ...\n=== AKHIR ===",
            metadata={"query": query, "result_count": 1},
        )


# Mock provider
async def mock_provider(messages):
    # Return tool call on first invocation, normal response on second
    if len(messages) < 4:  # Belum ada tool result
        return {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "web_search",
                            "arguments": {"query": "AI Indonesia"},
                        }
                    }
                ],
            }
        }
    else:
        return {
            "message": {
                "role": "assistant",
                "content": "Berdasarkan hasil pencarian, AI di Indonesia...",
            }
        }


async def test():
    # Setup
    registry = ToolRegistry()
    registry.register(MockSearchTool())
    handler = ToolHandler(registry, max_calls=3)

    # Test parse_native_tool_calls
    response_with_tools = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "web_search",
                        "arguments": {"query": "test"},
                    }
                }
            ],
        }
    }
    calls = handler.parse_native_tool_calls(response_with_tools)
    assert len(calls) == 1
    assert calls[0]["name"] == "web_search"
    assert calls[0]["arguments"]["query"] == "test"

    # Test parse_native_tool_calls — no tools
    calls = handler.parse_native_tool_calls({"message": {"content": "hello"}})
    assert len(calls) == 0

    # Test parse_prompt_injection
    text = 'Halo, saya akan mencari [[TOOL_CALL: web_search(query="AI Indonesia", max_results=5)]]'
    calls = handler.parse_prompt_injection(text)
    assert len(calls) == 1
    assert calls[0]["name"] == "web_search"
    assert calls[0]["arguments"]["query"] == "AI Indonesia"
    assert calls[0]["arguments"]["max_results"] == 5

    # Test parse_prompt_injection — no match
    calls = handler.parse_prompt_injection("Halo, apa kabar?")
    assert len(calls) == 0

    # Test execute_with_loop
    messages = [{"role": "user", "content": "Cari AI Indonesia"}]
    final_messages, final_response, history = await handler.execute_with_loop(
        mock_provider, messages
    )
    assert len(history) == 1  # Satu tool call
    assert history[0]["name"] == "web_search"
    assert "Berdasarkan hasil pencarian" in final_response["message"]["content"]

    print("All validations passed!")


asyncio.run(test())
```

---

## Output yang Diharapkan

```
app/
├── ai/
│   ├── tool_handler.py     # Baru — class ToolHandler
│   └── ... (existing)
├── tools/
│   ├── base.py
│   └── registry.py
```

- `ToolHandler` bisa memproses tool calls dari native format dan prompt injection
- Execution loop aman dengan max calls protection dan duplicate detection
- Tool results di-inject ke messages dengan format yang benar

---

## Dependencies

- **Task 01 (Tool Abstraction)** — `BaseTool`, `ToolSpec`, `ToolResult`
- **Task 02 (Tool Registry)** — `ToolRegistry`
- Standard library: `re`, `json`, `logging`, `typing`

---

## Acceptance Criteria

### Parsing — Native Format
- [ ] `parse_native_tool_calls()` memproses format Ollama (`message.tool_calls`)
- [ ] `parse_native_tool_calls()` memproses format Gemini (`function_call`)
- [ ] `parse_native_tool_calls()` mengembalikan empty list jika tidak ada tool_calls
- [ ] Arguments dalam format string JSON tetap bisa diparse

### Parsing — Prompt Injection
- [ ] `parse_prompt_injection()` memproses `[[TOOL_CALL: name(args)]]`
- [ ] `parse_prompt_injection()` handle double-quoted values: `key="value"`
- [ ] `parse_prompt_injection()` handle single-quoted values: `key='value'`
- [ ] `parse_prompt_injection()` handle unquoted values: `key=value`
- [ ] `parse_prompt_injection()` handle integer values (auto-convert)
- [ ] `parse_prompt_injection()` handle boolean values (true/false)
- [ ] `parse_prompt_injection()` handle multiple arguments
- [ ] `parse_prompt_injection()` mengembalikan empty list jika tidak ada pattern

### Execution Loop
- [ ] `execute_with_loop()` memanggil provider function
- [ ] `execute_with_loop()` mendeteksi tool calls dan mengeksekusinya
- [ ] `execute_with_loop()` menginject tool results ke messages
- [ ] `execute_with_loop()` re-call LLM setelah tool results
- [ ] `execute_with_loop()` berhenti jika tidak ada tool calls
- [ ] `execute_with_loop()` berhenti jika max_calls tercapai
- [ ] `execute_with_loop()` dengan `tools_enabled=False` skip tool calling

### Duplicate Detection
- [ ] Tool call dengan nama dan arguments yang sama di-skip
- [ ] Duplicate di-log dengan level WARNING

### Error Handling
- [ ] Tool gagal → inject error message instructif
- [ ] Max calls tercapai → satu call terakhir tanpa tool
- [ ] `max_calls < 1` → raise `ValueError`

### Logging
- [ ] Setiap iterasi loop di-log (DEBUG)
- [ ] Setiap tool call di-log dengan nama dan arguments (INFO)
- [ ] Tool success di-log (DEBUG)
- [ ] Tool failure di-log (WARNING)
- [ ] Duplicate tool call di-log (WARNING)
- [ ] Max calls reached di-log (WARNING)

---

## Estimasi

**High** (~3 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Implementasi parse_native_tool_calls | 30 menit |
| Implementasi parse_prompt_injection + regex | 45 menit |
| Implementasi handle_tool_calls | 20 menit |
| Implementasi execute_with_loop | 45 menit |
| Implementasi duplicate detection | 15 menit |
| Error handling & edge cases | 20 menit |
| Validasi & testing | 20 menit |
