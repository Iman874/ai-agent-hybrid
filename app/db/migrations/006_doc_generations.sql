-- Migration 006: Document generation history
-- Menyimpan riwayat setiap generate TOR dari dokumen yang diupload

CREATE TABLE IF NOT EXISTS document_generations (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    context TEXT DEFAULT '',
    style_id TEXT,
    style_name TEXT,
    status TEXT DEFAULT 'processing'
        CHECK(status IN ('processing','completed','failed')),
    tor_content TEXT,
    metadata_json TEXT DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_docgen_created ON document_generations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_docgen_status ON document_generations(status);
