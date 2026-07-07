# Task 08 — ChatService Tool Integration

## Deskripsi

**Task paling kritis** dalam Tool System. Mengintegrasikan seluruh komponen tool (ToolRegistry, ToolHandler, provider tool calling, prompt injection) ke dalam **`ChatService.process_message()`** dan **`process_message_stream()`**.

Ini adalah titik di mana semua komponen yang sudah dibangun di task-task sebelumnya benar-benar bekerja bersama. Setelah task ini, AI bisa memanggil tool selama percakapan dengan user.

---

## Tujuan Teknis

- `process_message()` bisa mendeteksi kapan LLM memanggil tool, mengeksekusinya, dan memberikan hasilnya ke LLM untuk response final
- `process_message_stream()` bisa mengirim tool events (tool_start, tool_result, tool_error) ke frontend via SSE
- User bisa mengaktifkan/menonaktifkan tool via `HybridOptions.tools_enabled`
- Tool calling bekerja untuk mode chat local (Ollama) maupun Gemini
- Sistem otomatis memilih antara native tool calling dan prompt injection berdasarkan kemampuan model
- Backward compatible — tanpa tool registry, behavior tidak berubah

---

## Scope

### Termasuk

- Modifikasi `app/services/chat_service.py`:

  **Update `__init__()`:**
  - Tambah parameter: `tool_handler: ToolHandler | None = None`
  - Tambah parameter: `tool_registry: ToolRegistry | None = None`
  - Simpan sebagai instance variables

  **Update `process_message()`:**
  - Tambah parameter: `tools_enabled: bool = True`
  - Flow baru:
    1. Build messages (seperti biasa)
    2. Jika `tools_enabled=True` dan `tool_handler` tersedia:
       a. Dapatkan tool specs dari `tool_registry.get_specs()`
       b. Tentukan strategi: native atau prompt injection?
          - Cek `has_native_tool_support(model_name, provider)` dari Task 07
          - Jika native: kirim specs ke provider (via parameter `tools`)
          - Jika tidak: inject prompt via `build_tool_injection_prompt()` ke system prompt
       c. Panggil `tool_handler.execute_with_loop(provider_call_fn, messages)`
       d. Dapatkan final messages, final response, dan tool_call_history
    3. Parse final response (seperti biasa)
    4. Return `ChatResult` (seperti biasa)

  **Update `process_message_stream()`:**
  - Tambah parameter: `tools_enabled: bool = True`
  - Flow baru (sama seperti di atas):
    1. Build messages
    2. Jika tools_enabled:
       a. Dapatkan specs, tentukan strategi
       b. Call LLM
       c. Jika ada tool_call:
          - Yield `StreamEvent(type="tool_start", tool=name, args=arguments)`
          - Eksekusi tool
          - Jika sukses: yield `StreamEvent(type="tool_result", ...)`
          - Jika gagal: yield `StreamEvent(type="tool_error", ...)`
          - Inject hasil, re-call LLM
       d. Yield token/thinking/done seperti biasa
    3. Parse dan return

  **Update `_get_provider()`:**
  - Return provider + provider name untuk keperluan deteksi native tool support

- Modifikasi `app/core/decision_engine.py`:
  - Update `route()` — teruskan `tools_enabled` dari `HybridOptions` ke `ChatService`
  - Update `HybridOptions` di `app/models/routing.py` — tambah field `tools_enabled: bool = True`

### Tidak Termasuk

- SSE event types baru (Task 09)
- Frontend tool indicator (Task 14)
- Tool toggle UI (Task 16)
- Implementasi tool handler (Task 04)

---

## Langkah Implementasi

### Langkah 1: Update `ChatService.__init__()`

```python
# Di app/services/chat_service.py
from app.ai.tool_handler import ToolHandler
from app.tools.registry import ToolRegistry
from app.ai.prompts.tool_injection import (
    build_tool_injection_prompt,
    has_native_tool_support,
)


class ChatService:
    """Orchestrator utama Chat Engine — multi-provider dengan tool support."""

    def __init__(
        self,
        ollama: OllamaProvider,
        session_mgr: SessionManager,
        prompt_builder: PromptBuilder,
        parser: ResponseParser,
        rag_pipeline: RAGPipeline | None = None,
        gemini_chat=None,
        tool_handler: ToolHandler | None = None,  # NEW
        tool_registry: ToolRegistry | None = None,  # NEW
    ):
        self.ollama = ollama
        self.gemini_chat = gemini_chat
        self.session_mgr = session_mgr
        self.prompt_builder = prompt_builder
        self.parser = parser
        self.rag_pipeline = rag_pipeline
        self.tool_handler = tool_handler  # NEW
        self.tool_registry = tool_registry  # NEW
        self._logger = logger
```

### Langkah 2: Update `process_message()` — Tool Loop

```python
async def process_message(
    self,
    session_id: str | None,
    message: str,
    rag_context: str | None = None,
    chat_mode: str = "local",
    think: bool = True,
    model_preference: str | None = None,
    images: list[str] | None = None,
    tools_enabled: bool = True,  # NEW
) -> ChatResult:
    """Process satu turn chat — dengan dukungan tool calling."""
    
    # === Step 1-3: Session, History, Build prompt (SAMA) ===
    # ... (kode yang sudah ada) ...

    # === Step 3.5: Inject tool specs ===
    provider = self._get_provider(chat_mode)
    provider_name = "ollama" if provider == self.ollama else "gemini"
    
    use_tools = (
        tools_enabled
        and self.tool_handler is not None
        and self.tool_registry is not None
        and self.tool_registry.count() > 0
    )

    if use_tools:
        tool_specs = self.tool_registry.get_specs()
        model_id = model_preference or (
            self.ollama.model if provider == self.ollama else self.gemini_chat.model_name
        )
        
        # Tentukan strategi: native atau prompt injection
        if has_native_tool_support(model_id, provider_name):
            self._logger.debug(
                f"Using native tool calling for {model_id} ({provider_name})"
            )
            # Native: kirim tool specs via parameter ke provider
            # ToolHandler.execute_with_loop akan handle ini
            provider_call_fn = lambda msgs: provider.chat(
                msgs, think=think, model=model_preference, tools=tool_specs,
            )
        else:
            self._logger.debug(
                f"Using prompt injection for {model_id} ({provider_name})"
            )
            # Prompt injection: inject ke system prompt
            tool_prompt = build_tool_injection_prompt(tool_specs)
            if tool_prompt:
                # Inject ke system prompt terakhir
                for i, msg in enumerate(messages):
                    if msg["role"] == "system":
                        messages[i] = {
                            "role": "system",
                            "content": msg["content"] + "\n\n" + tool_prompt,
                        }
                        break
            provider_call_fn = lambda msgs: provider.chat(
                msgs, think=think, model=model_preference,
            )

        # === Step 4: Execute with tool loop ===
        final_messages, response, tool_call_history = await self.tool_handler.execute_with_loop(
            provider_call_fn=provider_call_fn,
            messages=messages,
            tools_enabled=True,
        )

        # Log tool calls
        if tool_call_history:
            self._logger.info(
                f"Tool calls in this turn: {len(tool_call_history)} — "
                f"{[t['name'] for t in tool_call_history]}"
            )
    else:
        # === Step 4 (original): Call LLM tanpa tool ===
        parsed = await self._call_with_retry(
            messages, session, max_retries=2,
            provider=provider, think=think,
            model_preference=model_preference,
        )

    # === Step 5-8: Parse, Merge, Update session, Return (SAMA) ===
    # ... (kode yang sudah ada) ...
```

### Langkah 3: Update `process_message_stream()` — Tool Events

```python
async def process_message_stream(
    self,
    session_id: str | None,
    message: str,
    rag_context: str | None = None,
    chat_mode: str = "local",
    think: bool = True,
    model_preference: str | None = None,
    images: list[str] | None = None,
    tools_enabled: bool = True,  # NEW
) -> AsyncGenerator[StreamEvent, None]:
    """Streaming version — dengan tool events."""
    
    # === Step 1-3: Session, History, Build prompt (SAMA) ===
    # ... (kode yang sudah ada) ...

    provider = self._get_provider(chat_mode)
    provider_name = "ollama" if provider == self.ollama else "gemini"
    
    use_tools = (
        tools_enabled
        and self.tool_handler is not None
        and self.tool_registry is not None
        and self.tool_registry.count() > 0
    )

    if use_tools:
        tool_specs = self.tool_registry.get_specs()
        model_id = model_preference or (
            self.ollama.model if provider == self.ollama else self.gemini_chat.model_name
        )
        
        if has_native_tool_support(model_id, provider_name):
            provider_call_fn = lambda msgs: provider.chat(
                msgs, think=think, model=model_preference, tools=tool_specs,
            )
        else:
            tool_prompt = build_tool_injection_prompt(tool_specs)
            if tool_prompt:
                for i, msg in enumerate(messages):
                    if msg["role"] == "system":
                        messages[i] = {
                            "role": "system",
                            "content": msg["content"] + "\n\n" + tool_prompt,
                        }
                        break
            provider_call_fn = lambda msgs: provider.chat(
                msgs, think=think, model=model_preference,
            )

        # Execute with tool loop — dengan yield events
        final_messages, response, tool_call_history = await self.tool_handler.execute_with_loop(
            provider_call_fn=provider_call_fn,
            messages=messages,
            tools_enabled=True,
        )

        # Yield tool events ke frontend
        for tc in tool_call_history:
            yield StreamEvent(
                type="tool_start",
                tool=tc["name"],
                args=tc.get("arguments", {}),
            )
            # TODO: Hasil tool sudah di-inject, kita perlu track result-nya
            yield StreamEvent(
                type="tool_result",
                tool=tc["name"],
                status="success",
            )

        # Parse response dan yield token/done seperti biasa
        # ... (streaming token dari response) ...
    else:
        # Original streaming tanpa tool
        # ... (kode yang sudah ada) ...
```

### Langkah 4: Update `DecisionEngine`

```python
# Di app/core/decision_engine.py
# Update route() method — teruskan tools_enabled

async def route(
    self,
    session_id: str | None,
    message: str,
    options: HybridOptions | None = None,
    images: list[str] | None = None,
) -> RoutingResult:
    options = options or HybridOptions()
    tools_enabled = options.tools_enabled  # NEW
    
    # ... (kode yang sudah ada) ...
    
    chat_result = await self.chat.process_message(
        session_id=session_id,
        message=message,
        rag_context=rag_context,
        chat_mode=chat_mode,
        think=options.think,
        model_preference=options.model_preference,
        images=images,
        tools_enabled=tools_enabled,  # NEW
    )
    
    # ... (sisanya sama) ...
```

### Langkah 5: Update `HybridOptions`

```python
# Di app/models/routing.py
class HybridOptions(BaseModel):
    force_generate: bool = False
    language: str = "id"
    chat_mode: str = "local"
    think: bool = True
    model_preference: str | None = None
    tools_enabled: bool = True  # NEW — user bisa nonaktifkan tool
```

---

## Output yang Diharapkan

- `ChatService.process_message()` bisa memproses tool calls dalam alur chat
- Tool loop bekerja untuk chat biasa maupun streaming
- Sistem otomatis memilih native tool calling atau prompt injection
- Tool events dikirim ke frontend via stream
- Backward compatible — tanpa tool, behavior tidak berubah

---

## Dependencies

- **Task 04 (Tool Handler)** — `ToolHandler`
- **Task 05 (Ollama Tool Integration)** — tools parameter
- **Task 06 (Gemini Tool Integration)** — tools parameter
- **Task 07 (Prompt Injection Fallback)** — `build_tool_injection_prompt()`, `has_native_tool_support()`

---

## Acceptance Criteria

### Functional
- [ ] `process_message()` dengan `tools_enabled=True` bisa memanggil tool
- [ ] Tool result di-inject ke messages dan LLM dipanggil ulang
- [ ] `process_message_stream()` mengirim tool_start/tool_result events
- [ ] Sistem otomatis pilih native tool calling jika model support
- [ ] Sistem otomatis fallback ke prompt injection jika model tidak support
- [ ] Dengan `tools_enabled=False`, behavior tidak berubah
- [ ] Tanpa `tool_handler`/`tool_registry`, behavior tidak berubah
- [ ] Tanpa tool terdaftar, behavior tidak berubah

### Integration
- [ ] `DecisionEngine.route()` meneruskan `tools_enabled` ke ChatService
- [ ] `HybridOptions` memiliki field `tools_enabled`
- [ ] Tool call history di-log untuk observability

### Edge Cases
- [ ] Tool dipanggil → hasil di-inject → LLM panggil tool lagi → max 3 kali
- [ ] Tool gagal → LLM fallback ke pengetahuan internal
- [ ] Multiple tool calls dalam satu turn → semua dieksekusi
- [ ] Streaming dengan tool → tool events muncul sebelum token

---

## Estimasi

**High** (~2.5 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Analisis kode existing ChatService | 20 menit |
| Implementasi tool loop di process_message | 60 menit |
| Implementasi tool events di process_message_stream | 45 menit |
| Update DecisionEngine & HybridOptions | 15 menit |
| Validasi & testing | 30 menit |
