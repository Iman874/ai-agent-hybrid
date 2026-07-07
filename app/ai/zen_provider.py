import asyncio
import json
import logging

import httpx

from app.config import Settings
from app.ai.base_generator import BaseGeneratorProvider
from app.utils.errors import ZenAPIError, ZenTimeoutError

logger = logging.getLogger("ai-agent-hybrid.zen")


ZEN_TOR_SYSTEM_PROMPT = """Kamu adalah penulis dokumen TOR (Term of Reference / Kerangka Acuan Kerja) profesional.

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


class ZenProvider(BaseGeneratorProvider):
    """Generate TOR via OpenCode Zen API (OpenAI-compatible).

    Menggunakan endpoint chat/completions dari Zen.
    Model default: deepseek-v4-flash-free.
    """

    def __init__(self, settings: Settings):
        self.api_key = settings.zen_api_key
        self.model = settings.zen_model
        self.base_url = settings.zen_base_url.rstrip("/")
        self.temperature = settings.zen_temperature
        self.timeout = settings.zen_timeout

        logger.info(
            f"ZenProvider initialized: model={self.model}, "
            f"base_url={self.base_url}, timeout={self.timeout}s"
        )

    @property
    def provider_name(self) -> str:
        return "zen"

    async def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str) -> str:
        """Generate TOR via Zen API — non-streaming."""
        messages = [
            {"role": "system", "content": ZEN_TOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
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
                logger.error(f"Zen API error: {response.status_code} {error_body}")
                raise ZenAPIError(
                    details=f"HTTP {response.status_code}: {error_body}"
                )

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            logger.info(
                f"Zen generate completed: {len(content)} chars, "
                f"model={self.model}"
            )
            return content

        except asyncio.TimeoutError:
            logger.error(f"Zen API timeout after {self.timeout}s")
            raise ZenTimeoutError(timeout_seconds=self.timeout)
        except httpx.ConnectError as e:
            logger.error(f"Zen connection error: {e}")
            raise ZenAPIError(details=f"Connection error: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Zen HTTP error: {e}")
            raise ZenAPIError(details=str(e)[:300])
        except Exception as e:
            logger.error(f"Zen generate unexpected error: {e}")
            raise ZenAPIError(details=str(e)[:300])

    async def generate_stream(self, prompt: str):
        """Generate TOR via Zen API — streaming SSE."""
        messages = [
            {"role": "system", "content": ZEN_TOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": True,
        }

        url = f"{self.base_url}/chat/completions"
        chunk_count = 0
        content_count = 0

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if resp.status_code != 200:
                        error_text = await resp.aread()
                        logger.error(f"Zen stream error: {resp.status_code} {error_text[:500]}")
                        raise ZenAPIError(details=f"HTTP {resp.status_code}")

                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            chunk_count += 1
                            if content:
                                content_count += 1
                            yield content

            logger.info(
                f"Zen stream ended: total_chunks={chunk_count}, "
                f"content_chunks={content_count}"
            )

        except asyncio.TimeoutError:
            logger.error(f"Zen stream timeout after {self.timeout}s")
            raise ZenTimeoutError(timeout_seconds=self.timeout)
        except httpx.ConnectError as e:
            logger.error(f"Zen stream connection error: {e}")
            raise ZenAPIError(details=f"Connection error: {e}")
        except Exception as e:
            logger.error(f"Zen stream error: {e}")
            raise ZenAPIError(details=str(e)[:300])
