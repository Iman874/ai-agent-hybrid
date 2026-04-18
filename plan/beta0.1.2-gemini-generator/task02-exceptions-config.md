# Task 02 — Custom Exceptions & Config Update untuk Gemini

## 1. Judul Task

Tambahkan custom exceptions khusus Gemini (`GeminiTimeoutError`, `InsufficientDataError`) dan tambahkan `gemini_timeout` field di Settings.

## 2. Deskripsi

Menambahkan error class spesifik untuk Gemini flow dan memastikan konfigurasi `Settings` memiliki field `gemini_timeout` yang diperlukan oleh `GeminiProvider`. Juga menambahkan `InsufficientDataError` untuk kasus data belum cukup saat generate.

## 3. Tujuan Teknis

- `GeminiTimeoutError` (E008 variant) — timeout saat call Gemini
- `InsufficientDataError` (E011) — session data belum cukup untuk generate
- Field `gemini_timeout: int = 120` di `Settings`
- Update `.env` dan `.env.example` untuk `GEMINI_TIMEOUT`

## 4. Scope

### Yang dikerjakan
- Update `app/utils/errors.py` — tambah 2 exception class baru
- Update `app/config.py` — tambah `gemini_timeout` field
- Update `.env` dan `.env.example`

### Yang tidak dikerjakan
- Logic yang menggunakan exceptions ini

## 5. Langkah Implementasi

### Step 1: Update `app/utils/errors.py`

Tambahkan di akhir file:

```python
class GeminiTimeoutError(AppError):
    """Gemini API timeout."""
    def __init__(self, timeout_seconds: int = 120):
        super().__init__(
            message=f"Gemini API tidak merespons dalam {timeout_seconds} detik.",
            code="E008",
            details=f"timeout: {timeout_seconds}s",
        )


class InsufficientDataError(AppError):
    """Data belum cukup untuk generate TOR."""
    def __init__(self, completeness: float, missing_fields: list[str]):
        super().__init__(
            message=f"Data belum cukup untuk generate TOR. "
                    f"Completeness: {completeness:.0%}. "
                    "Lanjutkan chat dulu atau gunakan mode escalation.",
            code="E011",
            details=f"missing_fields: {', '.join(missing_fields)}",
        )
        self.completeness = completeness
        self.missing_fields = missing_fields
```

### Step 2: Update `app/config.py`

Tambahkan `gemini_timeout` di blok Gemini:

```python
    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 4096
    gemini_timeout: int = 120                # BARU
```

### Step 3: Update `.env` dan `.env.example`

Di blok `# === GEMINI ===`, tambahkan:
```
GEMINI_TIMEOUT=120
```

### Step 4: Verifikasi

```python
from app.utils.errors import GeminiTimeoutError, InsufficientDataError
from app.config import Settings

# Test exceptions
try:
    raise GeminiTimeoutError(120)
except GeminiTimeoutError as e:
    assert e.code == "E008"
    print(f"GeminiTimeoutError OK: {e.message}")

try:
    raise InsufficientDataError(0.3, ["latar_belakang", "tujuan"])
except InsufficientDataError as e:
    assert e.code == "E011"
    print(f"InsufficientDataError OK: {e.message}")

# Test settings
settings = Settings()
assert hasattr(settings, "gemini_timeout")
print(f"gemini_timeout = {settings.gemini_timeout}")

print("ALL TESTS PASSED")
```

## 6. Output yang Diharapkan

```
GeminiTimeoutError OK: Gemini API tidak merespons dalam 120 detik.
InsufficientDataError OK: Data belum cukup untuk generate TOR. Completeness: 30%. ...
gemini_timeout = 120
ALL TESTS PASSED
```

## 7. Dependencies

- Tidak ada (perubahan pada modul utility yang sudah ada)

## 8. Acceptance Criteria

- [ ] `GeminiTimeoutError` bisa di-raise dan memiliki code `E008`
- [ ] `InsufficientDataError` bisa di-raise dengan `completeness` dan `missing_fields`
- [ ] `Settings.gemini_timeout` ada dan default 120
- [ ] `.env` dan `.env.example` memiliki `GEMINI_TIMEOUT`

## 9. Estimasi

**Low** — ~30 menit
