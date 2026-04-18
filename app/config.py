from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "ai-agent-hybrid"
    app_version: str = "0.1.0"
    app_port: int = 8000
    app_env: str = "development"
    log_level: str = "INFO"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen2.5:7b-instruct"
    ollama_embed_model: str = "bge-m3"
    ollama_timeout: int = 60
    ollama_temperature: float = 0.3
    ollama_num_ctx: int = 4096

    # Gemini (dipakai di modul berikutnya)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 4096
    gemini_timeout: int = 120

    # Database
    session_db_path: str = "./data/sessions.db"

    # Cost Control
    max_gemini_calls_per_session: int = 3
    max_gemini_calls_per_hour: int = 20
    max_chat_turns: int = 15

    # === RAG Settings ===
    chroma_db_path: str = "./data/chroma_db"
    chroma_collection_name: str = "tor_documents"
    embedding_model: str = "qwen3-embedding:0.6b"
    embedding_batch_size: int = 32
    rag_documents_path: str = "./data/documents"
    rag_top_k: int = 3
    rag_score_threshold: float = 0.7
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    rag_min_chunk_size: int = 50

    # === Escalation Settings ===
    escalation_max_idle_turns: int = 5
    escalation_absolute_max_turns: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
