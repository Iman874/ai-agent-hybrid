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
