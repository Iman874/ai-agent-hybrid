"""Abstract base class untuk TOR generation provider."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseGeneratorProvider(ABC):
    """Abstract base class untuk TOR generation provider.

    Semua provider TOR (Gemini, Ollama, dll) WAJIB mengimplementasi
    interface ini agar bisa digunakan oleh GenerateService.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nama unik provider: 'gemini' | 'ollama'."""
        ...

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate TOR full text (non-streaming).

        Args:
            prompt: Prompt string untuk generate TOR.

        Returns:
            str: Full text TOR yang dihasilkan.
        """
        ...

    @abstractmethod
    async def generate_stream(
        self, prompt: str
    ) -> AsyncGenerator[str, None]:
        """Generate TOR streaming — yield text chunks per token.

        Args:
            prompt: Prompt string untuk generate TOR.

        Yields:
            str: Text chunks dari LLM secara real-time.
        """
        ...
        # pylint: disable=unreachable
        yield  # pragma: no cover

    @abstractmethod
    async def is_available(self) -> bool:
        """Cek apakah provider siap digunakan.

        Returns:
            bool: True jika provider bisa dipakai, False jika tidak.
        """
        ...
