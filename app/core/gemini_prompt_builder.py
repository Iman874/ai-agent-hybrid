import logging
from app.ai.prompts.generate_tor import GEMINI_STANDARD_PROMPT
from app.ai.prompts.escalation import GEMINI_ESCALATION_PROMPT
from app.ai.prompts.document_tor import DOCUMENT_TO_TOR_PROMPT
from app.ai.prompts.continue_tor import CONTINUE_TOR_PROMPT
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
    """Build prompt untuk Gemini standard, escalation, dan document mode."""

    @staticmethod
    def build_standard(
        data: TORData, 
        rag_examples: str | None = None,
        format_spec: str | None = None,
    ) -> str:
        """Build prompt untuk standard TOR generation."""
        data_json = data.model_dump_json(indent=2, exclude_none=True)

        prompt = GEMINI_STANDARD_PROMPT.replace("{DATA_JSON}", data_json)

        if rag_examples:
            prompt = prompt.replace("{RAG_EXAMPLES}", rag_examples)
        else:
            prompt = prompt.replace(
                "## REFERENSI KONTEN (dari RAG, jika ada)\n{RAG_EXAMPLES}",
                "## REFERENSI KONTEN\nTidak ada referensi tersedia."
            )
            
        fallback_format = "Tulis dalam format Markdown standar."
        prompt = prompt.replace("{FORMAT_SPEC}", format_spec or fallback_format)

        return prompt

    @staticmethod
    def build_escalation(
        chat_history: str,
        partial_data: TORData | None = None,
        rag_examples: str | None = None,
        format_spec: str | None = None,
    ) -> str:
        """Build prompt untuk escalation mode."""
        prompt = GEMINI_ESCALATION_PROMPT.replace("{FULL_CHAT_HISTORY}", chat_history)

        if partial_data:
            partial_json = partial_data.model_dump_json(indent=2, exclude_none=True)
            prompt += f"\n\n## DATA PARSIAL YANG TERSEDIA\n{partial_json}"

        if rag_examples:
            prompt += f"\n\n## REFERENSI KONTEN\n{rag_examples}"

        fallback_format = "Tulis dalam format Markdown standar."
        prompt = prompt.replace("{FORMAT_SPEC}", format_spec or fallback_format)

        return prompt

    @staticmethod
    def build_from_document(
        document_text: str,
        user_context: str = "",
        rag_examples: str | None = None,
        format_spec: str | None = None,
    ) -> str:
        """Build prompt untuk document-to-TOR generation."""
        prompt = DOCUMENT_TO_TOR_PROMPT.replace("{DOCUMENT_TEXT}", document_text)
        prompt = prompt.replace(
            "{USER_CONTEXT}",
            user_context or "Tidak ada konteks tambahan.",
        )

        if rag_examples:
            prompt = prompt.replace(
                "{RAG_EXAMPLES}",
                f"## REFERENSI KONTEN\n{rag_examples}",
            )
        else:
            prompt = prompt.replace("{RAG_EXAMPLES}", "")
            
        fallback_format = "Tulis dalam format Markdown standar."
        prompt = prompt.replace("{FORMAT_SPEC}", format_spec or fallback_format)

        return prompt

    @staticmethod
    def build_continue(
        document_text: str,
        partial_tor: str,
        rag_examples: str | None = None,
        format_spec: str | None = None,
    ) -> str:
        """Build prompt untuk melanjutkan TOR yang terputus."""
        prompt = CONTINUE_TOR_PROMPT.replace("{DOCUMENT_TEXT}", document_text)
        prompt = prompt.replace("{PARTIAL_TOR}", partial_tor)

        if rag_examples:
            prompt = prompt.replace(
                "{RAG_EXAMPLES}",
                f"## REFERENSI KONTEN\n{rag_examples}",
            )
        else:
            prompt = prompt.replace("{RAG_EXAMPLES}", "")
            
        fallback_format = "Tulis kelanjutannya saja dalam format Markdown standar."
        prompt = prompt.replace("{FORMAT_SPEC}", format_spec or fallback_format)

        return prompt
