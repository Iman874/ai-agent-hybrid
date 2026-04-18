import logging
from app.models.rag import RetrievedChunk

logger = logging.getLogger("ai-agent-hybrid.rag.formatter")


class ContextFormatter:
    """Format retrieved chunks menjadi context string untuk prompt injection."""

    TEMPLATE_HEADER = (
        "## REFERENSI (Gunakan sebagai inspirasi jika relevan, abaikan jika tidak)\n\n"
        "Berikut adalah contoh/template TOR yang mungkin relevan dengan kebutuhan user:\n"
    )
    TEMPLATE_FOOTER = (
        "\nCatatan: Referensi di atas hanya sebagai panduan style dan detail. "
        "Sesuaikan dengan kebutuhan spesifik user."
    )

    @staticmethod
    def format(chunks: list[RetrievedChunk]) -> str | None:
        """
        Format list chunks menjadi context string.

        Returns:
            Formatted string atau None jika chunks kosong
        """
        if not chunks:
            logger.debug("No chunks to format, returning None")
            return None

        parts = [ContextFormatter.TEMPLATE_HEADER]

        for i, chunk in enumerate(chunks, 1):
            parts.append(
                f"\n---\n"
                f"[Referensi {i}: {chunk.metadata.source} "
                f"(similarity: {chunk.score:.2f})]\n"
                f"{chunk.text}\n"
            )

        parts.append(f"---\n{ContextFormatter.TEMPLATE_FOOTER}")
        context = "\n".join(parts)
        logger.debug(f"Formatted {len(chunks)} chunks → {len(context)} chars")
        return context
