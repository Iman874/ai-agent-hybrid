-- Migration 008: Add model_name to chat_messages

ALTER TABLE chat_messages
ADD COLUMN model_name TEXT;
