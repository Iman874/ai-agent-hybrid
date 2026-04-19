-- Migration 005: Add title column for session history display
-- SQLite does not support IF NOT EXISTS for ALTER TABLE ADD COLUMN
-- Error akan di-ignore oleh handler di database.py jika kolom sudah ada
ALTER TABLE sessions ADD COLUMN title TEXT DEFAULT NULL;
