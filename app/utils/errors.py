class AppError(Exception):
    """Base exception untuk semua error aplikasi."""
    def __init__(self, message: str, code: str = "E999", details: str | None = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


class OllamaConnectionError(AppError):
    """E001 — Ollama tidak bisa dihubungi."""
    def __init__(self, details: str | None = None):
        super().__init__(
            message="Tidak dapat terhubung ke Ollama. Pastikan Ollama berjalan dengan perintah: ollama serve",
            code="E001",
            details=details or "Connection refused: localhost:11434",
        )


class LLMParseError(AppError):
    """E002 — Gagal parse JSON dari output LLM."""
    def __init__(self, details: str | None = None):
        super().__init__(
            message="Gagal mem-parse respons dari LLM. Format JSON tidak valid.",
            code="E002",
            details=details,
        )


class RateLimitError(AppError):
    """E003 — Batas panggilan API tercapai."""
    def __init__(self, message: str = "Batas panggilan API tercapai.", details: str | None = None):
        super().__init__(message=message, code="E003", details=details)


class GeminiAPIError(AppError):
    """E004 — Error dari Gemini API."""
    def __init__(self, details: str | None = None):
        super().__init__(
            message="Terjadi error saat menghubungi Gemini API.",
            code="E004",
            details=details,
        )


class SessionNotFoundError(AppError):
    """E006 — Session tidak ditemukan di database."""
    def __init__(self, session_id: str):
        super().__init__(
            message="Session tidak ditemukan. Mulai percakapan baru.",
            code="E006",
            details=f"session_id: {session_id}",
        )
        self.session_id = session_id


class OllamaTimeoutError(AppError):
    """E008 — Ollama timeout saat memproses request."""
    def __init__(self, timeout_seconds: int = 60):
        super().__init__(
            message=f"Ollama tidak merespons dalam {timeout_seconds} detik. "
                    "Coba model yang lebih kecil atau tingkatkan hardware.",
            code="E008",
            details=f"timeout: {timeout_seconds}s",
        )
