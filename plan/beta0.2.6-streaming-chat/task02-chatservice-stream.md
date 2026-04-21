# Task 18: ChatService `process_message_stream()` + Hapus Fake Stream

## Deskripsi

Menambahkan method `process_message_stream()` ke `ChatService` sebagai async generator yang yield token real dari LLM. Sekaligus menghapus fake streaming di `StreamService`.

## Tujuan Teknis

- `ChatService.process_message_stream()` → async generator yang yield `StreamEvent` per token
- `StreamService` → hapus fake `.split(" ")` streaming, delegasikan ke ChatService
- Accumulate token → parse JSON → yield done

## Scope

**Dikerjakan:**
- Tambah `process_message_stream()` di `app/services/chat_service.py`
- Hapus fake streaming di `app/services/stream_service.py`
- Reuse logic session, prompt, parsing dari `process_message()`

**Tidak dikerjakan:**
- SSE endpoint (Task 19)
- Frontend (Task 20-21)

## Langkah Implementasi

### Step 1: Tambah `process_message_stream()` di ChatService

File: `app/services/chat_service.py`

```python
async def process_message_stream(
    self,
    session_id: str | None,
    message: str,
    rag_context: str | None = None,
    chat_mode: str = "local",
    think: bool = True,
) -> AsyncGenerator[StreamEvent, None]:
    """
    Streaming version dari process_message().
    Yield StreamEvent per token dari LLM.
    """
    # === Step 1: Session (sama seperti process_message) ===
    if session_id is None:
        session = await self.session_mgr.create()
        self._logger.info(f"New session created: {session.id}")
    else:
        session = await self.session_mgr.get(session_id)
        self._logger.info(f"Continuing session: {session.id}")

    # Yield status dengan session_id
    yield StreamEvent(type="status", response={"session_id": session.id})

    # === Step 2: RAG retrieval ===
    if rag_context is None and self.rag_pipeline is not None:
        try:
            rag_context = await self.rag_pipeline.retrieve(query=message)
        except Exception as e:
            self._logger.warning(f"RAG retrieval failed: {e}")

    # === Step 3: Build prompt ===
    history = await self.session_mgr.get_chat_history(session.id)
    messages = self.prompt_builder.build_chat_messages(
        chat_history=history,
        user_message=message,
        rag_context=rag_context,
    )

    # === Step 4: Stream dari provider ===
    provider = self._get_provider(chat_mode)
    accumulated_content = ""
    has_thinking = False

    try:
        async for chunk in provider.chat_stream(messages, think=think):
            thinking_text = chunk.get("thinking", "")
            token_text = chunk.get("token", "")
            is_done = chunk.get("done", False)

            # Fase thinking (hanya jika provider support)
            if thinking_text:
                if not has_thinking:
                    yield StreamEvent(type="thinking_start")
                    has_thinking = True
                yield StreamEvent(type="thinking_token", token=thinking_text)
            
            # Transisi thinking → token
            if token_text and has_thinking:
                yield StreamEvent(type="thinking_end")
                has_thinking = False

            # Fase token
            if token_text:
                yield StreamEvent(type="token", token=token_text)
                accumulated_content += token_text

            if is_done:
                break

    except Exception as e:
        self._logger.error(f"Stream error: {e}")
        yield StreamEvent(type="error", error=str(e))
        return

    # === Step 5: Parse accumulated content ===
    try:
        data = self.parser.extract_json(accumulated_content)
        parsed = self.parser.validate_parsed(data)
    except LLMParseError:
        # Fallback: gunakan raw content sebagai message
        parsed = self._build_fallback(session, accumulated_content)

    # === Step 6: Merge data & update session ===
    new_data = parsed.data or parsed.extracted_so_far or parsed.partial_data or TORData()
    extracted = merge_extracted_data(session.extracted_data, new_data)
    completeness = calculate_completeness(extracted)

    await self.session_mgr.append_message(session.id, "user", message)
    await self.session_mgr.append_message(session.id, "assistant", parsed.message, parsed.status)

    if session.turn_count == 0:
        title = message[:40].strip()
        if len(message) > 40:
            title += "..."
        await self.session_mgr.update(session.id, title=title)

    await self.session_mgr.update(
        session.id,
        state=self._map_state(parsed.status),
        turn_count=session.turn_count + 1,
        extracted_data=extracted,
        completeness_score=completeness,
    )

    # === Step 7: Yield done ===
    result = ChatResult(
        session_id=session.id,
        status=parsed.status,
        message=parsed.message,
        extracted_data=extracted,
        missing_fields=extracted.missing_fields(),
        confidence=parsed.confidence,
        completeness_score=completeness,
        raw_llm_response=parsed.model_dump_json(),
        escalation_reason=parsed.reason,
    )
    
    # Convert ke API response format
    from app.models.api import SessionState
    yield StreamEvent(
        type="done",
        response={
            "session_id": session.id,
            "type": "chat",
            "message": result.message,
            "state": {
                "status": result.status,
                "turn_count": result.completeness_score,
                "completeness_score": result.completeness_score,
                "filled_fields": result.extracted_data.filled_fields(),
                "missing_fields": result.missing_fields,
            },
            "extracted_data": result.extracted_data.model_dump() if result.extracted_data else None,
        },
    )
```

Import yang perlu ditambahkan:
```python
from typing import AsyncGenerator
from app.services.stream_service import StreamEvent  # reuse dataclass
```

### Step 2: Hapus fake streaming di `StreamService`

File: `app/services/stream_service.py`

**Hapus** bagian ini (L46-55):
```python
# HAPUS: Simulate token streaming from full response
words = response_text.split(" ")
for i, word in enumerate(words):
    yield StreamEvent(type="token", token=word + (" " if i < len(words) - 1 else ""))
```

**Ganti `stream_message()`** menjadi delegasi ke ChatService:
```python
async def stream_message(
    self, session_id: str | None, message: str
) -> AsyncGenerator[StreamEvent, None]:
    """Delegate ke ChatService.process_message_stream()."""
    async for event in self.chat_service.process_message_stream(
        session_id=session_id,
        message=message,
    ):
        yield event
```

### Step 3: Pastikan `StreamEvent` dataclass cukup

Verifikasi `StreamEvent` di `stream_service.py` sudah support semua type:
- `status`, `thinking_start`, `thinking_token`, `thinking_end`, `token`, `done`, `error`

## Output yang Diharapkan

```python
# Stream output untuk Ollama (dengan thinking):
StreamEvent(type="status", response={"session_id": "abc-123"})
StreamEvent(type="thinking_start")
StreamEvent(type="thinking_token", token="Menganalisis...")
StreamEvent(type="thinking_end")
StreamEvent(type="token", token="Berdasarkan ")
StreamEvent(type="token", token="informasi ")
StreamEvent(type="token", token="yang Anda berikan...")
StreamEvent(type="done", response={"session_id": "abc-123", "message": "...", "state": {...}})

# Stream output untuk Gemini (tanpa thinking):
StreamEvent(type="status", response={"session_id": "abc-123"})
StreamEvent(type="token", token="Berdasarkan ")
StreamEvent(type="token", token="informasi ")
StreamEvent(type="done", response={...})
```

## Dependencies

- Task 17: Provider `chat_stream()` harus sudah ready

## Acceptance Criteria

- [ ] `process_message_stream()` ditambahkan ke ChatService
- [ ] Tidak memanggil `process_message()` (blocking) di dalam stream
- [ ] Token real dari provider di-yield langsung
- [ ] Thinking token hanya di-yield jika provider mengirimnya
- [ ] Accumulated content di-parse sebagai JSON setelah stream selesai
- [ ] Session di-update setelah stream selesai (sama seperti `process_message`)
- [ ] `StreamService` fake streaming dihapus
- [ ] `StreamService.stream_message()` mendelegasikan ke ChatService

## Estimasi

High (2-3 jam)
