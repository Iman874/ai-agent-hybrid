-- Migration 004: Escalation Log Table

CREATE TABLE IF NOT EXISTS escalation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rule_name TEXT NOT NULL,
    reason TEXT NOT NULL,
    turn_count INTEGER,
    completeness_score REAL,
    message_that_triggered TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_escalation_session ON escalation_log(session_id);
