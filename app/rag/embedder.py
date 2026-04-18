import logging
import ollama

from app.config import Settings
from app.utils.errors import EmbeddingModelError

logger = logging.getLogger("ai-agent-hybrid.rag.embedder")


class OllamaEmbedder:
    """Generate embeddings via Ollama qwen3-embedding:0.6b model."""

    def __init__(self, settings: Settings):
        self.client = ollama.AsyncClient(host=settings.ollama_base_url)
        self.model = settings.embedding_model
        self.batch_size = settings.embedding_batch_size

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings untuk list teks (batch processing).

        Args:
            texts: List string yang akan di-embed

        Returns:
            List of embedding vectors (list of float)

        Raises:
            EmbeddingModelError: Jika model belum di-pull
        """
        if not texts:
            return []

        all_embeddings = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            logger.debug(
                f"Embedding batch {i // self.batch_size + 1}: {len(batch)} texts"
            )

            try:
                response = await self.client.embed(
                    model=self.model,
                    input=batch,
                )
                all_embeddings.extend(response["embeddings"])
            except ollama.ResponseError as e:
                error_str = str(e).lower()
                if "model" in error_str and ("not found" in error_str or "pull" in error_str):
                    raise EmbeddingModelError(self.model)
                raise

        logger.debug(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings

    async def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding untuk satu query string.

        Args:
            query: Teks query

        Returns:
            Embedding vector (list of float)
        """
        embeddings = await self.embed_texts([query])
        return embeddings[0]
