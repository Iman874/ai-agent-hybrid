# Task 02 — Custom Exceptions & Logger Setup

## 1. Judul Task

Buat semua custom exception classes dan setup structured logging.

## 2. Deskripsi

Membuat fondasi error handling dan logging yang akan dipakai di seluruh modul. Semua error yang bisa terjadi di sistem harus punya exception class sendiri agar mudah di-catch dan di-format di API response.

## 3. Tujuan Teknis

- Semua custom exceptions terdefinisi di `app/utils/errors.py`
- Logger terstruktur siap dipakai di semua modul
- Setiap exception punya error code (E001, E002, dst)

## 4. Scope

### Yang dikerjakan
- Custom exception classes (6 class)
- Structured logger setup
- Error code mapping

### Yang tidak dikerjakan
- Global error handler di FastAPI (itu di task endpoint)
- Try-catch di business logic (itu di task masing-masing)

## 5. Langkah Implementasi

### Step 1: Buat `app/utils/errors.py`

```python
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
```

### Step 2: Buat `app/utils/logger.py`

```python
import logging
import sys


def setup_logger(name: str = "ai-agent-hybrid", level: str = "INFO") -> logging.Logger:
    """Setup structured logger untuk aplikasi."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Hindari duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Format: timestamp - name - level - message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_logger(module_name: str) -> logging.Logger:
    """Get child logger untuk modul tertentu."""
    return logging.getLogger(f"ai-agent-hybrid.{module_name}")
```

### Step 3: Verifikasi

```python
# test cepat
from app.utils.errors import OllamaConnectionError, SessionNotFoundError
from app.utils.logger import setup_logger, get_logger

logger = setup_logger()
logger.info("Test logger OK")

try:
    raise SessionNotFoundError("test-123")
except SessionNotFoundError as e:
    logger.error(f"[{e.code}] {e.message} — {e.details}")
    # Output: [E006] Session tidak ditemukan. Mulai percakapan baru. — session_id: test-123
```

## 6. Output yang Diharapkan

File yang dibuat:
- `app/utils/errors.py` — 6 custom exception classes
- `app/utils/logger.py` — logger setup dengan `setup_logger()` dan `get_logger()`

Behavior:

```
2026-04-18 15:00:00 | ai-agent-hybrid      | INFO    | Server starting...
2026-04-18 15:00:01 | ai-agent-hybrid.chat  | ERROR   | [E001] Tidak dapat terhubung ke Ollama...
```

## 7. Dependencies

- **Task 01** — project structure dan dependencies sudah terinstall

## 8. Acceptance Criteria

- [ ] `from app.utils.errors import OllamaConnectionError` berhasil
- [ ] `from app.utils.errors import LLMParseError` berhasil
- [ ] `from app.utils.errors import SessionNotFoundError` berhasil
- [ ] `from app.utils.errors import OllamaTimeoutError` berhasil
- [ ] `from app.utils.errors import RateLimitError` berhasil
- [ ] `from app.utils.errors import GeminiAPIError` berhasil
- [ ] Semua exception punya atribut `code`, `message`, `details`
- [ ] `SessionNotFoundError` punya atribut tambahan `session_id`
- [ ] `setup_logger()` menghasilkan logger yang print ke stdout
- [ ] `get_logger("chat")` menghasilkan child logger `ai-agent-hybrid.chat`
- [ ] Tidak ada duplicate handler jika `setup_logger()` dipanggil 2x

## 9. Estimasi

**Low** — ~30 menit
