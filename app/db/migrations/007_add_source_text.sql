-- Migration 007: Add source_text column to document_generations
-- Menyimpan teks sumber yang di-parse agar bisa retry/continue tanpa upload ulang

ALTER TABLE document_generations ADD COLUMN source_text TEXT;
