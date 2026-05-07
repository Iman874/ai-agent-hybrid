"""OllamaGeneratorProvider — generate TOR via Ollama local LLM."""

import asyncio
import logging

import ollama

from app.config import Settings
from app.ai.base_generator import BaseGeneratorProvider
from app.utils.errors import OllamaConnectionError, OllamaTimeoutError

logger = logging.getLogger("ai-agent-hybrid.ollama.generator")


class OllamaGeneratorProvider(BaseGeneratorProvider):
    """Generate TOR via Ollama local LLM.

    Menggunakan model terpisah (ollama_tor_model) atau fallback
    ke ollama_chat_model jika tidak dikonfigurasi.
    """

    def __init__(self, settings: Settings):
        self.client = ollama.AsyncClient(host=settings.ollama_base_url)
        # Jika ollama_tor_model tidak diset, pakai ollama_chat_model
        self.model = settings.ollama_tor_model or settings.ollama_chat_model
        self.temperature = settings.ollama_tor_temperature
        self.num_ctx = settings.ollama_num_ctx
        self.timeout = settings.ollama_tor_timeout

        logger.info(
            f"OllamaGeneratorProvider initialized: model={self.model}, "
            f"timeout={self.timeout}s, temp={self.temperature}"
        )

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def is_available(self) -> bool:
        """Cek apakah Ollama berjalan dan model tersedia."""
        try:
            result = await asyncio.wait_for(
                self.client.list(), timeout=5
            )
            model_ids = [m.model for m in result.models]
            available = any(self.model in m for m in model_ids)
            if not available:
                logger.warning(
                    f"Model '{self.model}' not found in Ollama. "
                    f"Available: {model_ids[:5]}..."
                )
            return available
        except asyncio.TimeoutError:
            logger.warning("Ollama is_available check timed out after 5s")
            return False
        except ConnectionError as e:
            logger.warning(f"Ollama connection error in is_available: {e}")
            return False
        except Exception as e:
            logger.warning(f"Ollama is_available check failed: {e}")
            return False

    async def generate(self, prompt: str) -> str:
        """Generate TOR via Ollama — non-streaming.

        Args:
            prompt: Prompt string untuk generate TOR.

        Returns:
            str: Full text TOR yang dihasilkan.

        Raises:
            OllamaConnectionError: Ollama tidak berjalan.
            OllamaTimeoutError: Request melebihi batas waktu.
        """
        messages = [
            {"role": "system", "content": OLLAMA_TOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await asyncio.wait_for(
                self.client.chat(
                    model=self.model,
                    messages=messages,
                    options={
                        "temperature": self.temperature,
                        "num_ctx": self.num_ctx,
                    },
                ),
                timeout=self.timeout,
            )
            content = response["message"]["content"]
            logger.info(
                f"Ollama generate completed: {len(content)} chars, "
                f"model={self.model}"
            )
            return content

        except asyncio.TimeoutError:
            logger.error(f"Ollama generate timeout after {self.timeout}s")
            raise OllamaTimeoutError(timeout_seconds=self.timeout)
        except ConnectionError as e:
            logger.error(f"Ollama connection error: {e}")
            raise OllamaConnectionError(details=str(e))
        except Exception as e:
            error_msg = str(e).lower()
            if "connect" in error_msg or "refused" in error_msg:
                raise OllamaConnectionError(details=str(e))
            logger.error(f"Ollama generate unexpected error: {e}")
            raise

    async def generate_stream(self, prompt: str):
        """Generate TOR via Ollama — streaming token per token.

        Args:
            prompt: Prompt string untuk generate TOR.

        Yields:
            str: Text chunks dari Ollama secara real-time.

        Raises:
            OllamaConnectionError: Ollama tidak berjalan.
            OllamaTimeoutError: Request melebihi batas waktu.
        """
        messages = [
            {"role": "system", "content": OLLAMA_TOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            stream = await asyncio.wait_for(
                self.client.chat(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    options={
                        "temperature": self.temperature,
                        "num_ctx": self.num_ctx,
                    },
                ),
                timeout=self.timeout,
            )

            # Protect against stalled streams with per-chunk timeout.
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        stream.__anext__(), timeout=self.timeout
                    )
                except StopAsyncIteration:
                    break

                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content

        except asyncio.TimeoutError:
            logger.error(f"Ollama generate stream timeout after {self.timeout}s")
            raise OllamaTimeoutError(timeout_seconds=self.timeout)
        except ConnectionError as e:
            logger.error(f"Ollama connection error: {e}")
            raise OllamaConnectionError(details=str(e))
        except Exception as e:
            error_msg = str(e).lower()
            if "connect" in error_msg or "refused" in error_msg:
                raise OllamaConnectionError(details=str(e))
            logger.error(f"Ollama generate stream unexpected error: {e}")
            raise


# System prompt untuk Ollama TOR generation
OLLAMA_TOR_SYSTEM_PROMPT = """Kamu adalah penulis dokumen TOR (Term of Reference / Kerangka Acuan Kerja) profesional.

TUGAS:
Buat dokumen TOR yang lengkap, profesional, dan siap digunakan.

ATURAN:
1. Output dalam format Markdown
2. Jangan gunakan placeholder seperti [isi di sini]
3. Jika ada data kurang, buat asumsi masuk akal dan tandai dengan [ASUMSI]
4. Jangan tambahkan penjelasan di luar dokumen TOR
5. Gunakan bahasa Indonesia formal
6. Struktur TOR minimal: Judul, Latar Belakang, Tujuan, Ruang Lingkup, Output, Timeline
"""
