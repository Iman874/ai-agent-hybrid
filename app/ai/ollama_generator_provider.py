"""OllamaGeneratorProvider — generate TOR via Ollama local LLM."""

import asyncio
import json
import logging

import httpx
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

    async def is_model_available(self, model_id: str) -> bool:
        """Cek apakah model tertentu tersedia di Ollama."""
        try:
            result = await asyncio.wait_for(
                self.client.list(), timeout=5
            )
            model_ids = [m.model for m in result.models]
            return model_id in model_ids
        except Exception as e:
            logger.warning(f"Ollama is_model_available failed: {e}")
            return False

    async def generate(self, prompt: str, model_override: str | None = None) -> str:
        """Generate TOR via Ollama — non-streaming.

        Args:
            prompt: Prompt string untuk generate TOR.

        Returns:
            str: Full text TOR yang dihasilkan.

        Raises:
            OllamaConnectionError: Ollama tidak berjalan.
            OllamaTimeoutError: Request melebihi batas waktu.
        """
        model_to_use = model_override or self.model
        messages = [
            {"role": "system", "content": OLLAMA_TOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await asyncio.wait_for(
                self.client.chat(
                    model=model_to_use,
                    messages=messages,
                    think=False,
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
                f"model={model_to_use}"
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

    async def generate_stream(self, prompt: str, model_override: str | None = None):
        """Generate TOR via Ollama — streaming token per token using httpx.

        Args:
            prompt: Prompt string untuk generate TOR.

        Yields:
            str: Text chunks dari Ollama secara real-time (may be empty).

        Raises:
            OllamaConnectionError: Ollama tidak berjalan.
            OllamaTimeoutError: Request melebihi batas waktu.
        """
        model_to_use = model_override or self.model
        messages = [
            {"role": "system", "content": OLLAMA_TOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        chunk_count = 0
        content_count = 0
        
        try:
            logger.info(f"Initiating stream to model: {model_to_use}")
            
            # Build request URL
            base_url = getattr(self.client, 'host', 'http://localhost:11434') or 'http://localhost:11434'
            url = f"{base_url}/api/chat"
            
            payload = {
                "model": model_to_use,
                "messages": messages,
                "think": False,
                "stream": True,
                "options": {
                    "temperature": self.temperature,
                    "num_ctx": self.num_ctx,
                },
            }
            
            logger.info(f"Using httpx to stream from: {url}")
            
            # Use httpx directly for streaming (Ollama library's streaming is broken)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream('POST', url, json=payload) as resp:
                    logger.info(f"Got response: {resp.status_code}")
                    if resp.status_code != 200:
                        error_text = await resp.aread()
                        logger.error(f"Ollama API error: {resp.status_code} {error_text}")
                        raise OllamaConnectionError(details=f"HTTP {resp.status_code}")
                    
                    logger.info(f"Starting to iterate stream lines...")
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        
                        chunk_count += 1
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            logger.warning(f"Chunk #{chunk_count}: Failed to parse JSON")
                            continue
                        
                        content = data.get("message", {}).get("content", "")
                        logger.debug(f"Chunk #{chunk_count}: content_len={len(content)}")
                        if content:
                            content_count += 1
                            logger.info(f"  Content chunk #{content_count}: {content[:50]}...")
                        yield content
                    
                    logger.info(f"Stream ended, total_chunks={chunk_count}, content_chunks={content_count}")

        except asyncio.TimeoutError as e:
            logger.error(f"Ollama stream timeout: {e}")
            raise OllamaTimeoutError(timeout_seconds=self.timeout)
        except ConnectionError as e:
            logger.error(f"Ollama connection error: {e}")
            raise OllamaConnectionError(details=str(e))
        except Exception as e:
            error_msg = str(e).lower()
            if "connect" in error_msg or "refused" in error_msg:
                raise OllamaConnectionError(details=str(e))
            logger.error(f"Ollama generate stream error: {type(e).__name__}: {e}", exc_info=True)
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
