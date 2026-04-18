from datetime import datetime
from pydantic import BaseModel
from typing import Literal


VALID_CATEGORIES = Literal["tor_template", "tor_example", "guideline"]


class DocumentMetadata(BaseModel):
    source: str                      # filename
    category: str                    # "tor_template" | "tor_example" | "guideline"
    file_type: str                   # "md" | "txt"
    char_count: int
    loaded_at: datetime


class Document(BaseModel):
    id: str                          # hash-based ID
    content: str                     # raw text content
    metadata: DocumentMetadata


class ChunkMetadata(BaseModel):
    source: str
    category: str
    file_type: str
    chunk_index: int                 # 0-based
    total_chunks: int
    char_count: int
    loaded_at: datetime


class Chunk(BaseModel):
    id: str                          # "{doc_id}_chunk_{index}"
    text: str
    metadata: ChunkMetadata


class RetrievedChunk(BaseModel):
    id: str
    text: str
    score: float                     # similarity score (0.0 - 1.0)
    metadata: ChunkMetadata


class IngestFileDetail(BaseModel):
    filename: str
    chunks: int
    char_count: int
    status: str                      # "ingested" | "skipped" | "error"


class IngestResult(BaseModel):
    status: str                      # "success" | "partial"
    ingested_files: int
    total_chunks: int
    collection_size: int
    details: list[IngestFileDetail]


class VectorDBInfo(BaseModel):
    type: str = "chromadb"
    collection: str
    total_documents: int
    total_chunks: int
    embedding_model: str
    embedding_dimensions: int = 1024


class RAGDocumentInfo(BaseModel):
    filename: str
    category: str
    chunks: int
    ingested_at: str


class RAGStatus(BaseModel):
    status: str                      # "healthy" | "degraded"
    vector_db: VectorDBInfo
    documents: list[RAGDocumentInfo]
