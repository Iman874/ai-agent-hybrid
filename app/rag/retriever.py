import logging
from app.models.rag import RetrievedChunk, ChunkMetadata
from app.rag.embedder import OllamaEmbedder
from app.rag.vector_store import ChromaVectorStore

logger = logging.getLogger("ai-agent-hybrid.rag.retriever")


class Retriever:
    """Retrieve relevant chunks dari vector store berdasarkan query."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        embedder: OllamaEmbedder,
        default_top_k: int = 3,
        default_threshold: float = 0.7,
    ):
        self.store = vector_store
        self.embedder = embedder
        self.default_top_k = default_top_k
        self.default_threshold = default_threshold

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        category_filter: str | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        """
        Retrieve most relevant chunks untuk query.

        Args:
            query: Teks query (user message / judul TOR)
            top_k: Jumlah chunk yang dikembalikan
            category_filter: Filter berdasarkan category metadata
            score_threshold: Minimum similarity score (0.0 - 1.0)

        Returns:
            List RetrievedChunk, diurutkan descending by score
        """
        top_k = top_k or self.default_top_k
        score_threshold = score_threshold or self.default_threshold

        # Step 1: Embed query
        logger.debug(f"Embedding query: '{query[:50]}...'")
        query_embedding = await self.embedder.embed_query(query)

        # Step 2: Query vector DB (ambil lebih banyak untuk filtering)
        where = {"category": category_filter} if category_filter else None
        raw_results = self.store.query(
            query_embedding=query_embedding,
            n_results=top_k * 2,
            where=where,
        )

        # Step 3: Convert distances → similarity scores & filter
        chunks = []
        if raw_results.get("ids") and raw_results["ids"][0]:
            for i, doc_id in enumerate(raw_results["ids"][0]):
                distance = raw_results["distances"][0][i]
                similarity = 1 - distance  # cosine distance → similarity

                if similarity >= score_threshold:
                    raw_meta = raw_results["metadatas"][0][i]
                    chunks.append(RetrievedChunk(
                        id=doc_id,
                        text=raw_results["documents"][0][i],
                        score=round(similarity, 4),
                        metadata=ChunkMetadata(**raw_meta),
                    ))

        # Sort descending by score, limit to top_k
        chunks.sort(key=lambda c: c.score, reverse=True)
        result = chunks[:top_k]

        logger.info(
            f"Retrieved {len(result)} chunks "
            f"(threshold={score_threshold}, filter={category_filter})"
        )
        return result
