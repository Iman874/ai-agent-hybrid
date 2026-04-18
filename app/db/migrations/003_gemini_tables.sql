-- Migration 003: Gemini Generator Tables

-- Cache TOR yang sudah di-generate
CREATE TABLE IF NOT EXISTS tor_cache (
    session_id TEXT PRIMARY KEY,
    tor_content TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_used TEXT NOT NULL,
    mode TEXT NOT NULL                CHECK(mode IN ('standard', 'escalation')),
    word_count INTEGER,
    generation_time_ms INTEGER,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Log setiap panggilan ke Gemini API (cost tracking)
CREATE TABLE IF NOT EXISTS gemini_call_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model TEXT NOT NULL,
    mode TEXT NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    duration_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_gemini_calls_time ON gemini_call_log(called_at);
CREATE INDEX IF NOT EXISTS idx_gemini_calls_session ON gemini_call_log(session_id);
