import asyncio
import json
import logging
import time

import httpx

from app.ai.base import BaseLLMProvider
from app.config import Settings
from app.utils.errors import ZenAPIError, ZenTimeoutError

logger = logging.getLogger("ai-agent-hybrid.zen-chat")


class ZenChatProvider(BaseLLMProvider):
    """OpenCode Zen API sebagai chat interviewer — output format identik OllamaProvider.

    Menggunakan endpoint chat/completions OpenAI-compatible.
    """

    def __init__(self, settings: Settings):
        self.api_key = settings.zen_api_key
        self.model = settings.zen_model
        self.base_url = settings.zen_base_url.rstrip("/")
        self.temperature = settings.zen_temperature
        self.timeout = settings.zen_timeout

        logger.info(
            f"ZenChatProvider initialized: model={self.model}, "
            f"base_url={self.base_url}"
        )

    async def chat(self, messages: list[dict], think: bool = True, model: str | None = None) -> dict:
        """Chat via Zen API — non-streaming.

        Input:  format Ollama [{"role": "system"|"user"|"assistant", "content": str}, ...]
        Output: {"content": str, "total_duration": int, "eval_count": int}
        """
        _ = think
        model_to_use = model or self.model
        start = time.monotonic()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Hapus field images dari messages (Zen API tidak support)
        clean_messages = []
        for msg in messages:
            clean_msg = {"role": msg["role"], "content": msg["content"]}
            clean_messages.append(clean_msg)

        payload = {
            "model": model_to_use,
            "messages": clean_messages,
            "temperature": self.temperature,
            "stream": False,
        }

        url = f"{self.base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await asyncio.wait_for(
                    client.post(url, headers=headers, json=payload),
                    timeout=self.timeout,
                )

            if response.status_code != 200:
                error_body = response.text[:500]
                logger.error(f"Zen chat error: {response.status_code} {error_body}")
                raise ZenAPIError(details=f"HTTP {response.status_code}: {error_body}")

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            duration_ns = int((time.monotonic() - start) * 1e9)

            usage = data.get("usage", {})
            eval_count = (usage.get("completion_tokens", 0) if usage else 0)

            logger.info(
                f"Zen chat: {duration_ns / 1e9:.1f}s, "
                f"{len(content)} chars, tokens={eval_count}"
            )

            return {
                "content": content,
                "total_duration": duration_ns,
                "eval_count": eval_count,
            }

        except asyncio.TimeoutError:
            logger.error(f"Zen chat timeout after {self.timeout}s")
            raise ZenTimeoutError(timeout_seconds=self.timeout)
        except httpx.ConnectError as e:
            logger.error(f"Zen chat connection error: {e}")
            raise ZenAPIError(details=f"Connection error: {e}")
        except httpx.HTTPStatusError as e:
            raise ZenAPIError(details=str(e)[:300])
        except Exception as e:
            logger.error(f"Zen chat unexpected error: {e}")
            raise ZenAPIError(details=str(e)[:300])

    async def chat_stream(self, messages: list[dict], think: bool = True, model: str | None = None):
        """Streaming chat via Zen API — SSE.

        Yields: dict dengan key "token", "thinking", "done".
        """
        _ = think
        model_to_use = model or self.model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        clean_messages = []
        for msg in messages:
            clean_msg = {"role": msg["role"], "content": msg["content"]}
            clean_messages.append(clean_msg)

        payload = {
            "model": model_to_use,
            "messages": clean_messages,
            "temperature": self.temperature,
            "stream": True,
        }

        url = f"{self.base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if resp.status_code != 200:
                        error_text = await resp.aread()
                        logger.error(f"Zen chat stream error: {resp.status_code} {error_text[:500]}")
                        raise ZenAPIError(details=f"HTTP {resp.status_code}")

                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                yield {"done": True}
                                return
                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            choices = data.get("choices", [])
                            if not choices:
                                continue

                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")

                            if content:
                                yield {"token": content}

        except asyncio.TimeoutError:
            logger.error(f"Zen chat stream timeout after {self.timeout}s")
            raise ZenTimeoutError(timeout_seconds=self.timeout)
        except httpx.ConnectError as e:
            logger.error(f"Zen chat stream connection error: {e}")
            raise ZenAPIError(details=f"Connection error: {e}")
        except Exception as e:
            logger.error(f"Zen chat stream error: {e}")
            raise ZenAPIError(details=str(e)[:300])
