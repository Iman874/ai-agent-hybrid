# Task 06 — GeminiPromptBuilder

## 1. Judul Task

Implementasikan `GeminiPromptBuilder` — class yang meng-inject data/history ke prompt template untuk mode standard dan escalation.

## 2. Deskripsi

Builder yang mengambil prompt template dari Task 05, lalu mengganti placeholder `{DATA_JSON}`, `{RAG_EXAMPLES}`, dan `{FULL_CHAT_HISTORY}` dengan data aktual. Juga memformat chat history menjadi string readable.

## 3. Tujuan Teknis

- `build_standard(data, rag_examples) → str` — inject data JSON + RAG ke standard prompt
- `build_escalation(chat_history, partial_data, rag_examples) → str` — inject history ke escalation prompt
- `format_chat_history(messages) → str` — helper untuk format list ChatMessage ke string

## 4. Scope

### Yang dikerjakan
- `app/core/gemini_prompt_builder.py` — class `GeminiPromptBuilder`

### Yang tidak dikerjakan
- Prompt template content (sudah di Task 05)
- Calling Gemini API

## 5. Langkah Implementasi

### Step 1: Buat `app/core/gemini_prompt_builder.py`

```python
import logging
from app.ai.prompts.generate_tor import GEMINI_STANDARD_PROMPT
from app.ai.prompts.escalation import GEMINI_ESCALATION_PROMPT
from app.models.tor import TORData
from app.models.session import ChatMessage

logger = logging.getLogger("ai-agent-hybrid.gemini.prompt")


def format_chat_history(messages: list[ChatMessage]) -> str:
    """Format list ChatMessage menjadi string readable."""
    lines = []
    for msg in messages:
        role_label = "USER" if msg.role == "user" else "ASISTEN"
        lines.append(f"[{role_label}]: {msg.content}")
    return "\n\n".join(lines)


class GeminiPromptBuilder:
    """Build prompt untuk Gemini standard dan escalation mode."""

    @staticmethod
    def build_standard(data: TORData, rag_examples: str | None = None) -> str:
        """Build prompt untuk standard TOR generation."""
        data_json = data.model_dump_json(indent=2, exclude_none=True)

        prompt = GEMINI_STANDARD_PROMPT.replace("{DATA_JSON}", data_json)

        if rag_examples:
            prompt = prompt.replace("{RAG_EXAMPLES}", rag_examples)
        else:
            prompt = prompt.replace(
                "## REFERENSI STYLE (dari RAG, jika ada)\n{RAG_EXAMPLES}",
                "## REFERENSI STYLE\nTidak ada referensi tersedia. Gunakan best-practice umum."
            )

        return prompt

    @staticmethod
    def build_escalation(
        chat_history: str,
        partial_data: TORData | None = None,
        rag_examples: str | None = None,
    ) -> str:
        """Build prompt untuk escalation mode."""
        prompt = GEMINI_ESCALATION_PROMPT.replace("{FULL_CHAT_HISTORY}", chat_history)

        if partial_data:
            partial_json = partial_data.model_dump_json(indent=2, exclude_none=True)
            prompt += f"\n\n## DATA PARSIAL YANG TERSEDIA\n{partial_json}"

        if rag_examples:
            prompt += f"\n\n## REFERENSI STYLE\n{rag_examples}"

        return prompt
```

### Step 2: Verifikasi

```python
from app.core.gemini_prompt_builder import GeminiPromptBuilder, format_chat_history
from app.models.tor import TORData
from app.models.session import ChatMessage
from datetime import datetime

# Test standard mode
data = TORData(judul="Workshop AI", tujuan="Belajar AI untuk ASN")
prompt = GeminiPromptBuilder.build_standard(data, rag_examples="Contoh TOR...")
assert "Workshop AI" in prompt
assert "Contoh TOR..." in prompt
print("Test 1: build_standard OK")

# Test standard tanpa RAG
prompt2 = GeminiPromptBuilder.build_standard(data)
assert "Tidak ada referensi tersedia" in prompt2
print("Test 2: build_standard tanpa RAG OK")

# Test escalation
history = [
    ChatMessage(session_id="x", role="user", content="Buat TOR AI"),
    ChatMessage(session_id="x", role="assistant", content="Jelaskan lebih detail?"),
]
formatted = format_chat_history(history)
prompt3 = GeminiPromptBuilder.build_escalation(formatted, partial_data=data)
assert "[USER]: Buat TOR AI" in prompt3
assert "Workshop AI" in prompt3
print("Test 3: build_escalation OK")

print("ALL PROMPT BUILDER TESTS PASSED")
```

## 6. Output yang Diharapkan

Prompt string yang siap dikirim ke Gemini API, lengkap dengan data/history/referensi.

## 7. Dependencies

- **Task 05** — prompt templates
- **beta0.1.0** — `TORData`, `ChatMessage` models

## 8. Acceptance Criteria

- [ ] `build_standard()` mengganti `{DATA_JSON}` dengan JSON TORData
- [ ] `build_standard()` mengganti `{RAG_EXAMPLES}` atau fallback ke "Tidak ada referensi"
- [ ] `build_escalation()` mengganti `{FULL_CHAT_HISTORY}` dengan formatted chat
- [ ] `build_escalation()` append partial data JSON jika tersedia
- [ ] `format_chat_history()` menghasilkan format `[USER]: ...` dan `[ASISTEN]: ...`

## 9. Estimasi

**Low** — ~1 jam
