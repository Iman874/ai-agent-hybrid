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
