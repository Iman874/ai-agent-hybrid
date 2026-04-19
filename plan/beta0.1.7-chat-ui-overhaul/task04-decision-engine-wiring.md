# Task 04: Wiring DecisionEngine + main.py — Forward chat_mode

## Deskripsi
Update `DecisionEngine` agar mem-forward `chat_mode` dari `HybridOptions` ke `ChatService.process_message()`. Update `main.py` untuk menginisialisasi `GeminiChatProvider` dan meng-inject ke `ChatService`.

## Tujuan Teknis
1. `DecisionEngine.route()` mengekstrak `options.chat_mode` dan meneruskan ke `ChatService`
2. `main.py` membuat instance `GeminiChatProvider` dan meng-pass ke `ChatService`
3. Semua wiring complete — request `chat_mode: "gemini"` end-to-end berfungsi

## Scope
- **Dikerjakan**:
  - Modifikasi `app/core/decision_engine.py` → forward `chat_mode`
  - Modifikasi `app/main.py` → init `GeminiChatProvider`, pass ke `ChatService`
- **Tidak dikerjakan**:
  - UI (task05-08)

## Langkah Implementasi

### Step 1: Update DecisionEngine

```python
# app/core/decision_engine.py

# Di method route():
async def route(self, session_id, message, options=None) -> RoutingResult:
    options = options or HybridOptions()
    chat_mode = options.chat_mode  # NEW — extract chat_mode

    ...

    # STEP 4: Chat with LLM (pass chat_mode)
    chat_result = await self.chat.process_message(
        session_id=session_id,
        message=message,
        rag_context=rag_context,
        chat_mode=chat_mode,  # NEW
    )
    ...
```

### Step 2: Update main.py

```python
# app/main.py — di dalam lifespan()

from app.ai.gemini_chat_provider import GeminiChatProvider

# Init Gemini Chat Provider
gemini_chat_provider = GeminiChatProvider(settings)
app.state.gemini_chat_provider = gemini_chat_provider
logger.info("Gemini Chat Provider initialized")

# Update ChatService init
app.state.chat_service = ChatService(
    ollama=ollama_provider,
    gemini_chat=gemini_chat_provider,  # NEW
    session_mgr=session_mgr,
    prompt_builder=PromptBuilder(),
    parser=ResponseParser(),
    rag_pipeline=rag_pipeline,
)
```

### Step 3: Verifikasi end-to-end

Test via curl:
```bash
curl -X POST http://localhost:8000/api/v1/hybrid \
  -H "Content-Type: application/json" \
  -d '{"message": "Halo, saya mau buat TOR", "options": {"chat_mode": "gemini"}}'
```

## Output yang Diharapkan
- Request dengan `chat_mode: "gemini"` → chat diproses via Gemini API
- Request dengan `chat_mode: "local"` (atau tanpa options) → chat via Ollama (default)
- Response format **identik** di kedua mode

## Dependencies
- Task 01 (GeminiChatProvider)
- Task 02 (ChatService refactor)
- Task 03 (chat_mode di HybridOptions)

## Acceptance Criteria
- [ ] `DecisionEngine.route()` forward `chat_mode` ke `ChatService.process_message()`
- [ ] `main.py` init `GeminiChatProvider` dan pass ke `ChatService`
- [ ] Request `chat_mode: "gemini"` → Gemini digunakan untuk chat
- [ ] Request `chat_mode: "local"` → Ollama digunakan (backward compatible)
- [ ] Server start tanpa error
- [ ] End-to-end test via curl berhasil

## Estimasi
Low
