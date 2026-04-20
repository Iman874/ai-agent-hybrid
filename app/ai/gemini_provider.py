import logging
import time
import asyncio
import google.generativeai as genai
from typing import AsyncGenerator

from app.config import Settings
from app.models.generate import GeminiResponse
from app.utils.errors import GeminiTimeoutError, GeminiAPIError

logger = logging.getLogger("ai-agent-hybrid.gemini")


class GeminiProvider:
    """Async client untuk Google Gemini API."""

    def __init__(self, settings: Settings):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ],
            generation_config=genai.GenerationConfig(
                temperature=settings.gemini_temperature,
                max_output_tokens=settings.gemini_max_tokens,
                top_p=0.95,
                top_k=40,
            ),
        )
        self.timeout = settings.gemini_timeout
        self.model_name = settings.gemini_model

    async def generate(self, prompt: str) -> GeminiResponse:
        """Generate content via Gemini API."""
        start = time.monotonic()

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content, prompt
                ),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            raise GeminiTimeoutError(self.timeout)
        except Exception as e:
            error_str = str(e)
            if "API_KEY" in error_str.upper() or "INVALID" in error_str.upper():
                raise GeminiAPIError(details=f"API key mungkin tidak valid: {error_str[:200]}")
            raise GeminiAPIError(details=error_str[:200])

        duration_ms = int((time.monotonic() - start) * 1000)

        # Extract usage metadata
        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

        logger.info(
            f"Gemini call: {duration_ms}ms, "
            f"tokens: {prompt_tokens}+{completion_tokens}={prompt_tokens + completion_tokens}"
        )

        return GeminiResponse(
            text=response.text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            duration_ms=duration_ms,
        )

    async def generate_stream(
        self, prompt: str, timeout: float | None = None
    ) -> AsyncGenerator[str, None]:
        """Stream generate content — yield text chunks.

        Args:
            prompt: Prompt text to send to Gemini.
            timeout: Max seconds for entire stream. Defaults to self.timeout.

        Yields:
            str: Text chunks from Gemini response.

        Raises:
            GeminiTimeoutError: If stream exceeds timeout.
            GeminiAPIError: If API call fails.
        """
        effective_timeout = timeout or self.timeout
        start = time.monotonic()

        try:
            # generate_content with stream=True → returns sync iterable of chunks
            response = await asyncio.to_thread(
                self.model.generate_content, prompt, stream=True
            )
        except Exception as e:
            error_str = str(e)
            if "API_KEY" in error_str.upper() or "INVALID" in error_str.upper():
                raise GeminiAPIError(
                    details=f"API key mungkin tidak valid: {error_str[:200]}"
                )
            raise GeminiAPIError(details=error_str[:200])

        # Iterate chunks — sync iterable from Gemini SDK
        for chunk in response:
            # Timeout check setiap chunk
            elapsed = time.monotonic() - start
            if elapsed > effective_timeout:
                logger.warning(
                    f"Gemini stream timeout: {elapsed:.1f}s > {effective_timeout}s"
                )
                raise GeminiTimeoutError(effective_timeout)

            if chunk.text:
                yield chunk.text

        duration_ms = int((time.monotonic() - start) * 1000)
        logger.info(f"Gemini stream completed: {duration_ms}ms")
