# Task 02: Refactor ChatService untuk Multi-Provider

## Deskripsi
Modifikasi `ChatService` agar bisa menerima parameter `chat_mode` dan memilih antara `OllamaProvider` atau `GeminiChatProvider` secara dinamis.

## Tujuan Teknis
1. Tambahkan parameter `gemini_chat: GeminiChatProvider` di constructor `ChatService`
2. Tambahkan parameter `chat_mode: str` di method `process_message()`
3. Pilih provider berdasarkan `chat_mode`: `"local"` → Ollama, `"gemini"` → GeminiChat

## Scope
- **Dikerjakan**:
  - Modifikasi constructor `ChatService.__init__()` untuk terima `gemini_chat`
  - Modifikasi `process_message()` untuk terima `chat_mode` parameter
  - Modifikasi `_call_with_retry()` untuk menerima provider sebagai argument
  - Update fallback behavior untuk kedua provider
- **Tidak dikerjakan**:
  - Perubahan di `DecisionEngine` (task04)
  - Perubahan di `main.py` (task04)
  - UI changes

## Langkah Implementasi

### Step 1: Update Constructor

```python
class ChatService:
    def __init__(
        self,
        ollama: OllamaProvider,
        gemini_chat: "GeminiChatProvider | None" = None,  # NEW
        session_mgr: SessionManager,
        prompt_builder: PromptBuilder,
        parser: ResponseParser,
        rag_pipeline: RAGPipeline | None = None,
    ):
        self.ollama = ollama
        self.gemini_chat = gemini_chat  # NEW
        ...
```

### Step 2: Update `process_message()`

```python
async def process_message(
    self,
    session_id: str | None,
    message: str,
    rag_context: str | None = None,
    chat_mode: str = "local",  # NEW
) -> ChatResult:
    ...
    # Step 4: Call LLM berdasarkan mode
    provider = self._get_provider(chat_mode)
    parsed = await self._call_with_retry(messages, session, max_retries=2, provider=provider)
    ...
```

### Step 3: Tambah helper `_get_provider()`

```python
def _get_provider(self, chat_mode: str):
    """Return LLM provider berdasarkan chat_mode."""
    if chat_mode == "gemini" and self.gemini_chat:
        return self.gemini_chat
    return self.ollama
```

### Step 4: Update `_call_with_retry()` signature

```python
async def _call_with_retry(
    self,
    messages: list[dict],
    session: Session,
    max_retries: int = 2,
    provider = None,  # NEW — BaseLLMProvider
) -> LLMParsedResponse:
    ...
    provider = provider or self.ollama
    ...
    for attempt in range(max_retries + 1):
        raw_response = await provider.chat(working_messages)
        ...
```

## Output yang Diharapkan
- `ChatService` bisa menerima `chat_mode="local"` atau `chat_mode="gemini"`
- Default behavior (`chat_mode="local"`) TIDAK berubah — backward compatible
- Jika `gemini_chat` tidak di-pass atau `None`, fallback ke Ollama

## Dependencies
- Task 01 (GeminiChatProvider harus sudah ada)

## Acceptance Criteria
- [ ] `ChatService.__init__()` menerima parameter `gemini_chat` (opsional)
- [ ] `process_message()` menerima parameter `chat_mode` (default `"local"`)
- [ ] `_call_with_retry()` menerima `provider` parameter
- [ ] `chat_mode="local"` → pakai `self.ollama`
- [ ] `chat_mode="gemini"` → pakai `self.gemini_chat`
- [ ] Jika `self.gemini_chat` is None dan `chat_mode="gemini"` → fallback ke Ollama dengan warning log
- [ ] Semua existing tests/functionality tidak terpengaruh (backward compatible)

## Estimasi
Medium
