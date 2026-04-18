# Task 08 — Prompt Builder

## 1. Judul Task

Implementasi `PromptBuilder` — compose messages array dari system prompt + RAG context + chat history + user message.

## 2. Deskripsi

Membuat class `PromptBuilder` yang menyusun array `messages` yang siap dikirim ke Ollama. Array ini terdiri dari system prompt, opsional RAG context, chat history terakhir (max 10 turn), dan pesan user terbaru.

## 3. Tujuan Teknis

- `PromptBuilder.build_chat_messages()` menghasilkan list messages yang terstruktur dan benar
- System prompt selalu di posisi pertama
- RAG context hanya di-inject jika ada (tidak None)
- Chat history di-limit agar tidak melebihi context window
- User message selalu di posisi terakhir

## 4. Scope

### Yang dikerjakan
- `app/core/prompt_builder.py` — class `PromptBuilder` dengan method `build_chat_messages()`

### Yang tidak dikerjakan
- Prompt Gemini (itu beta0.1.2)
- RAG retrieval (itu beta0.1.1; di sini hanya terima string RAG context)

## 5. Langkah Implementasi

### Step 1: Buat `app/core/prompt_builder.py`

```python
from app.ai.prompts.chat_system import SYSTEM_PROMPT_CHAT
from app.ai.prompts.rag_injection import RAG_CONTEXT_TEMPLATE
from app.models.session import ChatMessage


class PromptBuilder:
    """Compose messages array untuk dikirim ke Ollama."""

    @staticmethod
    def build_chat_messages(
        chat_history: list[ChatMessage],
        user_message: str,
        rag_context: str | None = None,
        max_history_turns: int = 10,
    ) -> list[dict]:
        """
        Compose messages array yang siap dikirim ke Ollama.

        Args:
            chat_history: Daftar pesan sebelumnya (dari DB)
            user_message: Pesan user saat ini
            rag_context: Konteks dari RAG pipeline (jika ada)
            max_history_turns: Maksimal turn yang di-include
                              (1 turn = 1 user + 1 assistant = 2 messages)

        Returns:
            List of {"role": str, "content": str} siap kirim ke Ollama

        Urutan messages:
            1. System prompt (chat interviewer)
            2. RAG context (jika ada, sebagai system message tambahan)
            3. Chat history (max N turn terakhir)
            4. User message terbaru
        """
        messages = []

        # 1. System prompt (SELALU ada di posisi pertama)
        messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT_CHAT,
        })

        # 2. RAG context (opsional)
        if rag_context:
            messages.append({
                "role": "system",
                "content": RAG_CONTEXT_TEMPLATE.format(rag_context=rag_context),
            })

        # 3. Chat history (max N turn terakhir)
        # 1 turn = 2 messages (user + assistant), jadi max_messages = max_turns * 2
        max_messages = max_history_turns * 2
        recent_history = chat_history[-max_messages:]
        for msg in recent_history:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        # 4. User message terbaru (SELALU di posisi terakhir)
        messages.append({
            "role": "user",
            "content": user_message,
        })

        return messages
```

### Step 2: Test manual

```python
from app.core.prompt_builder import PromptBuilder
from app.models.session import ChatMessage
from datetime import datetime

# Test 1: Tanpa history, tanpa RAG
messages = PromptBuilder.build_chat_messages(
    chat_history=[],
    user_message="Saya mau buat TOR workshop",
)
print(f"Count: {len(messages)}")  # 2: system + user
print(f"First role: {messages[0]['role']}")   # system
print(f"Last role: {messages[-1]['role']}")    # user

# Test 2: Dengan history
history = [
    ChatMessage(session_id="x", role="user", content="Halo", timestamp=datetime.utcnow()),
    ChatMessage(session_id="x", role="assistant", content="Hai!", timestamp=datetime.utcnow()),
]
messages = PromptBuilder.build_chat_messages(
    chat_history=history,
    user_message="Tentang AI",
)
print(f"Count: {len(messages)}")  # 4: system + 2 history + user

# Test 3: Dengan RAG context
messages = PromptBuilder.build_chat_messages(
    chat_history=[],
    user_message="Buat TOR",
    rag_context="Contoh TOR: Workshop Python 3 hari...",
)
print(f"Count: {len(messages)}")  # 3: system + RAG + user
print(f"Role[1]: {messages[1]['role']}")   # system (RAG)
assert "Contoh TOR" in messages[1]["content"]
```

## 6. Output yang Diharapkan

```python
# Tanpa RAG, tanpa history:
[
    {"role": "system", "content": "Kamu adalah AI asisten yang bertugas..."},
    {"role": "user", "content": "Saya mau buat TOR workshop"},
]

# Dengan RAG dan history:
[
    {"role": "system", "content": "Kamu adalah AI asisten..."},
    {"role": "system", "content": "## REFERENSI...\nContoh TOR: ..."},
    {"role": "user", "content": "Halo"},
    {"role": "assistant", "content": "Hai!"},
    {"role": "user", "content": "Tentang AI"},
]
```

## 7. Dependencies

- **Task 03** — model `ChatMessage`
- **Task 06** — `SYSTEM_PROMPT_CHAT`, `RAG_CONTEXT_TEMPLATE`

## 8. Acceptance Criteria

- [ ] `build_chat_messages()` selalu menaruh system prompt di index 0
- [ ] `build_chat_messages()` selalu menaruh user message di index terakhir
- [ ] Jika `rag_context=None`, tidak ada RAG system message
- [ ] Jika `rag_context="..."`, RAG di-inject sebagai system message di index 1
- [ ] Chat history di-limit ke `max_history_turns * 2` messages terbaru
- [ ] Jika `chat_history=[]`, output hanya system + user (2 messages)
- [ ] Jika `chat_history` punya 20 messages dan `max_history_turns=5`, hanya 10 messages terakhir yang masuk
- [ ] Urutan messages: system → (RAG) → history → user

## 9. Estimasi

**Low** — ~45 menit
