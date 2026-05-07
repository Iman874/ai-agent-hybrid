# Task 01: Base Generator Provider + Refactor GeminiProvider

## Status
[ ] Belum dimulai

## Deskripsi
Buat abstract class `BaseGeneratorProvider` sebagai kontrak untuk semua TOR generator provider. Refactor `GeminiProvider` yang sudah ada agar mengimplementasi interface ini.

## File yang Diubah
- **NEW**: `app/ai/base_generator.py`
- **MODIFY**: `app/ai/gemini_provider.py`

## Spesifikasi

### 1. BaseGeneratorProvider (`app/ai/base_generator.py`)

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseGeneratorProvider(ABC):
    """Abstract base class untuk TOR generation provider."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nama provider: 'gemini' | 'ollama'."""
        ...

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate TOR full text (non-streaming)."""
        ...

    @abstractmethod
    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Generate TOR streaming — yield text chunks."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Cek apakah provider siap digunakan."""
        ...
```

### 2. GeminiProvider — Implementasi Interface

`GeminiProvider` yang sudah ada harus:
- Inherit `BaseGeneratorProvider`
- Implement `provider_name` → return `"gemini"`
- Method `generate()` sudah ada — sesuaikan signature
- Method `generate_stream()` sudah ada — sesuaikan signature
- Tambah `is_available()` → cek API key tidak kosong

### 3. Method Signatures yang Wajib

```python
class GeminiProvider(BaseGeneratorProvider):
    @property
    def provider_name(self) -> str:
        return "gemini"

    async def generate(self, prompt: str) -> str:
        # Existing logic — return response.text
        ...

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        # Existing logic — yield chunk.text
        ...

    async def is_available(self) -> bool:
        # Cek apakah API key terkonfigurasi
        return bool(self.api_key)
```

## Catatan
- Jangan ubah logic internal `generate()` dan `generate_stream()` — hanya tambahkan interface
- Pastikan import tidak circular
- `BaseGeneratorProvider` terpisah dari `BaseLLMProvider` (yang untuk chat)
