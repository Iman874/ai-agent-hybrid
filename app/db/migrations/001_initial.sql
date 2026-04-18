-- Migration 001: Initial schema for sessions and chat messages
-- Dijalankan otomatis saat application startup

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    state TEXT DEFAULT 'NEW' CHECK(state IN ('NEW','CHATTING','READY','ESCALATED','GENERATING','COMPLETED')),
    turn_count INTEGER DEFAULT 0,
    completeness_score REAL DEFAULT 0.0,
    extracted_data_json TEXT DEFAULT '{}',
    generated_tor TEXT,
    escalation_reason TEXT,
    gemini_calls_count INTEGER DEFAULT 0,
    total_tokens_local INTEGER DEFAULT 0,
    total_tokens_gemini INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
    content TEXT NOT NULL,
    parsed_status TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_state ON sessions(state);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at);
