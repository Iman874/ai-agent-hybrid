import logging
from app.config import Settings
from app.models.rag import IngestResult, IngestFileDetail, RetrievedChunk
from app.rag.document_loader import DocumentLoader
from app.rag.text_splitter import TextChunker
from app.rag.embedder import OllamaEmbedder
from app.rag.vector_store import ChromaVectorStore
from app.rag.retriever import Retriever
from app.rag.context_formatter import ContextFormatter

logger = logging.getLogger("ai-agent-hybrid.rag.pipeline")


class RAGPipeline:
    """Orchestrator utama RAG System."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.loader = DocumentLoader()
        self.chunker = TextChunker(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
            min_chunk_size=settings.rag_min_chunk_size,
        )
        self.embedder = OllamaEmbedder(settings)
        self.store = ChromaVectorStore(settings)
        self.retriever = Retriever(
            vector_store=self.store,
            embedder=self.embedder,
            default_top_k=settings.rag_top_k,
            default_threshold=settings.rag_score_threshold,
        )
        self.formatter = ContextFormatter()

    async def ingest_files(
        self, file_paths: list[str], category: str
    ) -> IngestResult:
        """
        Ingest file dari filesystem.

        Args:
            file_paths: List path file yang akan di-ingest
            category: Kategori dokumen

        Returns:
            IngestResult dengan detail setiap file
        """
        logger.info(f"Starting ingest: {len(file_paths)} files, category={category}")

        all_chunks = []
        details = []

        for fpath in file_paths:
            try:
                # Load dokumen
                doc = self.loader._load_file_by_path(fpath, category)

                # Chunking
                chunks = self.chunker.split(doc)

                if not chunks:
                    details.append(IngestFileDetail(
                        filename=doc.metadata.source,
                        chunks=0,
                        char_count=doc.metadata.char_count,
                        status="skipped"
                    ))
                    continue

                all_chunks.extend(chunks)
                details.append(IngestFileDetail(
                    filename=doc.metadata.source,
                    chunks=len(chunks),
                    char_count=doc.metadata.char_count,
                    status="ingested"
                ))
            except Exception as e:
                logger.error(f"Failed to process {fpath}: {e}")
                details.append(IngestFileDetail(
                    filename=str(fpath).split("/")[-1],
                    chunks=0,
                    char_count=0,
                    status=f"error: {str(e)[:50]}"
                ))

        # Embed dan upsert semua chunks
        if all_chunks:
            texts = [c.text for c in all_chunks]
            embeddings = await self.embedder.embed_texts(texts)

            self.store.upsert(
                ids=[c.id for c in all_chunks],
                embeddings=embeddings,
                documents=texts,
                metadatas=[c.metadata.model_dump(mode="json") for c in all_chunks],
            )

        result = IngestResult(
            status="success",
            ingested_files=sum(1 for d in details if d.status == "ingested"),
            total_chunks=len(all_chunks),
            collection_size=self.store.count(),
            details=details,
        )
        logger.info(
            f"Ingest complete: {result.ingested_files} files, "
            f"{result.total_chunks} chunks, total={result.collection_size}"
        )
        return result

    async def ingest_from_uploads(
        self,
        uploads: list[tuple[str, bytes]],  # list of (filename, content)
        category: str,
    ) -> IngestResult:
        """Ingest dari uploaded file bytes (dipakai oleh API endpoint)."""
        all_chunks = []
        details = []

        for filename, content in uploads:
            try:
                doc = self.loader.load_from_upload(filename, content, category)
                chunks = self.chunker.split(doc)

                if not chunks:
                    details.append(IngestFileDetail(
                        filename=filename, chunks=0,
                        char_count=doc.metadata.char_count, status="skipped"
                    ))
                    continue

                all_chunks.extend(chunks)
                details.append(IngestFileDetail(
                    filename=filename, chunks=len(chunks),
                    char_count=doc.metadata.char_count, status="ingested"
                ))
            except Exception as e:
                logger.error(f"Upload ingest failed for {filename}: {e}")
                details.append(IngestFileDetail(
                    filename=filename, chunks=0, char_count=0,
                    status=f"error: {str(e)[:50]}"
                ))

        if all_chunks:
            texts = [c.text for c in all_chunks]
            embeddings = await self.embedder.embed_texts(texts)
            self.store.upsert(
                ids=[c.id for c in all_chunks],
                embeddings=embeddings,
                documents=texts,
                metadatas=[c.metadata.model_dump(mode="json") for c in all_chunks],
            )

        return IngestResult(
            status="success",
            ingested_files=sum(1 for d in details if d.status == "ingested"),
            total_chunks=len(all_chunks),
            collection_size=self.store.count(),
            details=details,
        )

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        category_filter: str | None = None,
        score_threshold: float | None = None,
    ) -> str | None:
        """Retrieve dan return formatted context string. None jika tidak ada yang relevan."""
        chunks = await self.retriever.retrieve(
            query=query,
            top_k=top_k,
            category_filter=category_filter,
            score_threshold=score_threshold,
        )
        return self.formatter.format(chunks)

    async def retrieve_raw(
        self,
        query: str,
        top_k: int | None = None,
        category_filter: str | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve tanpa formatting (untuk debugging/API response)."""
        return await self.retriever.retrieve(
            query=query,
            top_k=top_k,
            category_filter=category_filter,
            score_threshold=score_threshold,
        )

    async def get_status(self) -> dict:
        """Status vector DB."""
        sources = self.store.get_all_sources()
        return {
            "status": "healthy",
            "vector_db": {
                "type": "chromadb",
                "collection": ChromaVectorStore.COLLECTION_NAME,
                "total_chunks": self.store.count(),
                "total_documents": len(sources),
                "embedding_model": self.settings.embedding_model,
                "embedding_dimensions": 1024,
            },
            "documents": sources,
        }
