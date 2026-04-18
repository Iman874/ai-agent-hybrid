-- Migration 002: RAG Document Tracking Table
CREATE TABLE IF NOT EXISTS rag_documents (
    id TEXT PRIMARY KEY,               -- document hash ID (dari DocumentLoader)
    filename TEXT NOT NULL,
    category TEXT NOT NULL             CHECK(category IN ('tor_template', 'tor_example', 'guideline')),
    file_type TEXT NOT NULL,
    char_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(filename, category)         -- prevent duplicate ingest
);

CREATE INDEX IF NOT EXISTS idx_rag_docs_category ON rag_documents(category);
CREATE INDEX IF NOT EXISTS idx_rag_docs_ingested ON rag_documents(ingested_at);
