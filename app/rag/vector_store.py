import logging
import chromadb

from app.config import Settings
from app.utils.errors import VectorDBError

logger = logging.getLogger("ai-agent-hybrid.rag.vector_store")


class ChromaVectorStore:
    """Wrapper ChromaDB untuk manajemen vector embeddings."""

    COLLECTION_NAME = "tor_documents"

    def __init__(self, settings: Settings):
        self.persist_path = settings.chroma_db_path
        self.collection_name = settings.chroma_collection_name

        try:
            self.client = chromadb.PersistentClient(path=self.persist_path)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},  # cosine similarity
            )
            logger.info(
                f"ChromaDB initialized: path={self.persist_path}, "
                f"collection={self.collection_name}, "
                f"total_chunks={self.collection.count()}"
            )
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            raise VectorDBError(
                f"Tidak dapat menginisialisasi ChromaDB di '{self.persist_path}'. Error: {e}"
            )

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        """Upsert chunks ke collection (add jika baru, update jika sudah ada)."""
        if not ids:
            return

        # ChromaDB max 5000 per upsert
        batch_size = 5000
        for i in range(0, len(ids), batch_size):
            end = i + batch_size
            self.collection.upsert(
                ids=ids[i:end],
                embeddings=embeddings[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end],
            )

        logger.debug(f"Upserted {len(ids)} chunks")

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 6,
        where: dict | None = None,
    ) -> dict:
        """
        Query collection untuk chunks yang paling similar.

        Returns: dict dengan keys: ids, documents, metadatas, distances
        """
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": min(n_results, self.collection.count() or 1),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        return self.collection.query(**kwargs)

    def count(self) -> int:
        """Total chunks di collection."""
        return self.collection.count()

    def delete_by_source(self, source: str) -> None:
        """Hapus semua chunks dari satu file (untuk re-ingest)."""
        try:
            self.collection.delete(where={"source": source})
            logger.info(f"Deleted chunks for source: {source}")
        except Exception as e:
            logger.warning(f"Delete by source failed for '{source}': {e}")

    def get_all_sources(self) -> list[dict]:
        """List semua dokumen yang sudah di-ingest beserta jumlah chunk-nya."""
        if self.collection.count() == 0:
            return []

        results = self.collection.get(include=["metadatas"])
        sources: dict[str, dict] = {}

        for meta in results["metadatas"]:
            src = meta["source"]
            if src not in sources:
                sources[src] = {
                    "source": src,
                    "category": meta.get("category", "unknown"),
                    "chunks": 0,
                }
            sources[src]["chunks"] += 1

        return list(sources.values())
