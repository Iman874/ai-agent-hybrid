import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models.rag import Document, Chunk, ChunkMetadata

logger = logging.getLogger("ai-agent-hybrid.rag.splitter")


class TextChunker:
    """Split dokumen menjadi chunks yang siap di-embed."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 50,
    ):
        self.min_chunk_size = min_chunk_size
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
            keep_separator=True,
        )

    def split(self, document: Document) -> list[Chunk]:
        """Split satu Document menjadi list Chunk."""
        raw_chunks = self.splitter.split_text(document.content)

        # Filter chunks yang terlalu pendek
        valid_texts = [c for c in raw_chunks if len(c.strip()) >= self.min_chunk_size]

        if not valid_texts:
            logger.warning(
                f"Document '{document.metadata.source}' menghasilkan 0 valid chunks "
                f"(min_chunk_size={self.min_chunk_size})"
            )
            return []

        chunks = []
        for i, text in enumerate(valid_texts):
            chunk = Chunk(
                id=f"{document.id}_chunk_{i}",
                text=text.strip(),
                metadata=ChunkMetadata(
                    source=document.metadata.source,
                    category=document.metadata.category,
                    file_type=document.metadata.file_type,
                    chunk_index=i,
                    total_chunks=len(valid_texts),
                    char_count=len(text.strip()),
                    loaded_at=document.metadata.loaded_at,
                ),
            )
            chunks.append(chunk)

        logger.debug(
            f"Split '{document.metadata.source}' → {len(chunks)} chunks "
            f"(dari {len(raw_chunks)} raw, {len(raw_chunks)-len(valid_texts)} dibuang)"
        )
        return chunks

    def split_many(self, documents: list[Document]) -> list[Chunk]:
        """Split banyak dokumen sekaligus."""
        all_chunks = []
        for doc in documents:
            all_chunks.extend(self.split(doc))
        return all_chunks
