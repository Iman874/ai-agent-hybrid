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

    async def chat(self, messages: list[dict]) -> dict:
        """
        Kirim chat completion ke Ollama.

        Args:
            messages: list of {"role": "system"|"user"|"assistant", "content": str}

        Returns:
            {
                "content": str,       # respons dari LLM
                "total_duration": int, # durasi total dalam nanoseconds
                "eval_count": int,     # jumlah token yang di-generate
            }

        Raises:
            OllamaConnectionError: Ollama tidak berjalan
            OllamaTimeoutError: Request melebihi batas waktu
        """
        logger.debug(
            f"Sending chat to Ollama ({self.model}), "
            f"{len(messages)} messages, temp={self.temperature}"
        )

        try:
            response = await asyncio.wait_for(
                self.client.chat(
                    model=self.model,
                    messages=messages,
                    format="json",
                    options={
                        "temperature": self.temperature,
                        "num_ctx": self.num_ctx,
                    },
                ),
                timeout=self.timeout,
            )

            content = response["message"]["content"]
            total_duration = response.get("total_duration", 0)
            eval_count = response.get("eval_count", 0)

            logger.debug(
                f"Ollama response received: {len(content)} chars, "
                f"duration={total_duration / 1e9:.1f}s, "
                f"tokens={eval_count}"
            )

            return {
                "content": content,
                "total_duration": total_duration,
                "eval_count": eval_count,
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
