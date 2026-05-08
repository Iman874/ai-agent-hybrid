"""OllamaPromptBuilder — build prompt untuk Ollama TOR generation."""

import logging

from app.ai.prompts.ollama_generate_tor import OLLAMA_STANDARD_PROMPT
from app.ai.prompts.ollama_escalation import OLLAMA_ESCALATION_PROMPT
from app.ai.prompts.ollama_document_tor import OLLAMA_DOCUMENT_TO_TOR_PROMPT
from app.ai.prompts.ollama_continue_tor import OLLAMA_CONTINUE_TOR_PROMPT
from app.models.tor import TORData
from app.models.session import ChatMessage

logger = logging.getLogger("ai-agent-hybrid.ollama.prompt")


def format_chat_history(messages: list[ChatMessage]) -> str:
    """Format list ChatMessage menjadi string readable."""
    lines = []
    for msg in messages:
        role_label = "USER" if msg.role == "user" else "ASISTEN"
        lines.append(f"[{role_label}]: {msg.content}")
    return "\n\n".join(lines)


class OllamaPromptBuilder:
    """Build prompt untuk Ollama TOR generation.

    Prompt untuk Ollama harus lebih eksplisit tentang format Markdown
    karena Ollama tidak mendukung response_mime_type="application/json".
    """

    @staticmethod
    def build_standard(
        data: TORData,
        rag_examples: str | None = None,
        format_spec: str | None = None,
    ) -> str:
        """Build prompt string untuk standard TOR generation via Ollama.

        Args:
            data: Data TOR yang terkumpul dari chat.
            rag_examples: Contoh dari RAG (optional).
            format_spec: Spesifikasi format dari style aktif (optional).

        Returns:
            str: Prompt string siap kirim ke Ollama.
        """
        data_json = data.model_dump_json(indent=2, exclude_none=True)

        prompt = OLLAMA_STANDARD_PROMPT.replace("{DATA_JSON}", data_json)

        if rag_examples:
            prompt = prompt.replace("{RAG_EXAMPLES}", rag_examples)
        else:
            prompt = prompt.replace(
                "## REFERENSI KONTEN (dari RAG, jika ada)\n{RAG_EXAMPLES}",
                "",
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
        """Build prompt string untuk escalation mode via Ollama.

        Args:
            chat_history: Riwayat percakapan dalam format string.
            partial_data: Data TOR parsial yang sudah terkumpul (optional).
            rag_examples: Contoh dari RAG (optional).
            format_spec: Spesifikasi format dari style aktif (optional).

        Returns:
            str: Prompt string siap kirim ke Ollama.
        """
        prompt = OLLAMA_ESCALATION_PROMPT.replace(
            "{FULL_CHAT_HISTORY}", chat_history
        )

        if partial_data:
            partial_json = partial_data.model_dump_json(
                indent=2, exclude_none=True
            )
            prompt += (
                f"\n\n## DATA PARSIAL YANG TERSEDIA\n{partial_json}"
            )

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
        """Build prompt untuk document-to-TOR generation via Ollama.

        Args:
            document_text: Teks dari dokumen sumber.
            user_context: Konteks tambahan dari user (optional).
            rag_examples: Contoh dari RAG (optional).
            format_spec: Spesifikasi format dari style aktif (optional).

        Returns:
            str: Prompt string siap kirim ke Ollama.
        """
        prompt = OLLAMA_DOCUMENT_TO_TOR_PROMPT.replace("{DOCUMENT_TEXT}", document_text)
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
        """Build prompt untuk melanjutkan TOR yang terputus via Ollama.

        Args:
            document_text: Teks dari dokumen sumber.
            partial_tor: TOR yang sudah dihasilkan sebagian.
            rag_examples: Contoh dari RAG (optional).
            format_spec: Spesifikasi format dari style aktif (optional).

        Returns:
            str: Prompt string siap kirim ke Ollama.
        """
        prompt = OLLAMA_CONTINUE_TOR_PROMPT.replace("{DOCUMENT_TEXT}", document_text)
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
