import asyncio
import logging

import ollama

from app.ai.base import BaseLLMProvider
from app.config import Settings
from app.utils.errors import OllamaConnectionError, OllamaTimeoutError

logger = logging.getLogger("ai-agent-hybrid.ollama")


class OllamaProvider(BaseLLMProvider):
    """Client async untuk Ollama REST API."""

    def __init__(self, settings: Settings):
        self.client = ollama.AsyncClient(host=settings.ollama_base_url)
        self.model = settings.ollama_chat_model
        self.temperature = settings.ollama_temperature
        self.num_ctx = settings.ollama_num_ctx
        self.timeout = settings.ollama_timeout
        self.is_cloud = self.model.endswith("-cloud")

        if self.is_cloud:
            logger.info(f"Cloud model detected: {self.model}")

    async def chat(self, messages: list[dict], think: bool = True) -> dict:
        """
        Kirim chat completion ke Ollama.

        Args:
            messages: list of {"role": "system"|"user"|"assistant", "content": str}
            think: Apakah model boleh menggunakan thinking/reasoning mode.
                   Jika False, response jauh lebih cepat tapi tanpa deep reasoning.

        Returns:
            {
                "content": str,       # respons dari LLM
                "total_duration": int, # durasi total dalam nanoseconds
                "eval_count": int,     # jumlah token yang di-generate
                "thinking": str,      # thinking text (jika ada)
            }

        Raises:
            OllamaConnectionError: Ollama tidak berjalan
            OllamaTimeoutError: Request melebihi batas waktu
        """
        logger.debug(
            f"Sending chat to Ollama ({self.model}), "
            f"{len(messages)} messages, temp={self.temperature}, "
            f"cloud={self.is_cloud}, think={think}"
        )

        # Build request kwargs
        chat_kwargs = {
            "model": self.model,
            "messages": messages,
            "format": "json",
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
            },
        }

        # Kontrol thinking mode via parameter 'think'
        # Menonaktifkan thinking bisa menghemat ~950 token per request
        if not think:
            # SDK Ollama Python mungkin belum mensupport parameter 'think' secara nating
            # Jadi kita tambahkan prefix /nothink atau instruksi eksplisit
            if self.is_cloud and len(messages) > 0:
                messages[-1]["content"] = "/nothink " + messages[-1]["content"]

        try:
            response = await asyncio.wait_for(
                self.client.chat(**chat_kwargs),
                timeout=self.timeout,
            )

            content = response["message"]["content"]
            thinking = response["message"].get("thinking", "")
            total_duration = response.get("total_duration", 0)
            eval_count = response.get("eval_count", 0)

            logger.debug(
                f"Ollama response received: {len(content)} chars, "
                f"thinking={len(thinking)} chars, "
                f"duration={total_duration / 1e9:.1f}s, "
                f"tokens={eval_count}"
            )

            return {
                "content": content,
                "total_duration": total_duration,
                "eval_count": eval_count,
                "thinking": thinking,
            }

        except asyncio.TimeoutError:
            logger.error(f"Ollama timeout after {self.timeout}s")
            raise OllamaTimeoutError(timeout_seconds=self.timeout)

        except ConnectionError as e:
            logger.error(f"Ollama connection error: {e}")
            raise OllamaConnectionError(details=str(e))

        except Exception as e:
            # Catch ollama SDK specific errors (e.g., model not found)
            error_msg = str(e).lower()
            if "connect" in error_msg or "refused" in error_msg:
                logger.error(f"Ollama connection error: {e}")
                raise OllamaConnectionError(details=str(e))
            logger.error(f"Ollama unexpected error: {e}")
            raise

    async def chat_stream(self, messages: list[dict], think: bool = True):
        """
        Streaming chat completion — yield token demi token.
        
        Yields:
            dict: {"token": str, "done": bool, "thinking": str}
        """
        chat_kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
            },
        }

        if not think and self.is_cloud and len(messages) > 0:
            if not messages[-1]["content"].startswith("/nothink "):
                messages[-1]["content"] = "/nothink " + messages[-1]["content"]

        try:
            stream = await asyncio.wait_for(
                self.client.chat(**chat_kwargs),
                timeout=self.timeout,
            )

            async for chunk in stream:
                msg = chunk.get("message", {})
                yield {
                    "token": msg.get("content", ""),
                    "thinking": msg.get("thinking", ""),
                    "done": chunk.get("done", False),
                }

        except asyncio.TimeoutError:
            logger.error(f"Ollama stream timeout after {self.timeout}s")
            raise OllamaTimeoutError(timeout_seconds=self.timeout)

        except Exception as e:
            error_msg = str(e).lower()
            if "connect" in error_msg or "refused" in error_msg:
                raise OllamaConnectionError(details=str(e))
            raise
