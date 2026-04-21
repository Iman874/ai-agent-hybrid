import logging
import time
import base64
import asyncio
import google.generativeai as genai

from app.ai.base import BaseLLMProvider
from app.config import Settings
from app.utils.errors import GeminiTimeoutError, GeminiAPIError

logger = logging.getLogger("ai-agent-hybrid.gemini-chat")


class GeminiChatProvider(BaseLLMProvider):
    """Gemini API sebagai chat interviewer — return format identik OllamaProvider."""

    def __init__(self, settings: Settings):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=genai.GenerationConfig(
                temperature=settings.gemini_temperature,
                max_output_tokens=settings.gemini_max_tokens,
                response_mime_type="application/json",
            ),
        )
        self.timeout = settings.gemini_timeout
        self.model_name = settings.gemini_model

    async def chat(self, messages: list[dict], think: bool = True) -> dict:
        """
        Chat via Gemini API.
        Input:  format Ollama [{"role": "system"|"user"|"assistant", "content": str}, ...]
        Output: {"content": str, "total_duration": int, "eval_count": int}
        """
        start = time.monotonic()

        gemini_messages = self._convert_messages(messages)

        try:
            if len(gemini_messages) > 1:
                chat_session = self.model.start_chat(history=gemini_messages[:-1])
                last_parts = gemini_messages[-1]["parts"]
                response = await asyncio.wait_for(
                    asyncio.to_thread(chat_session.send_message, last_parts),
                    timeout=self.timeout,
                )
            else:
                prompt = gemini_messages[0]["parts"]
                response = await asyncio.wait_for(
                    asyncio.to_thread(self.model.generate_content, prompt),
                    timeout=self.timeout,
                )
        except asyncio.TimeoutError:
            raise GeminiTimeoutError(self.timeout)
        except Exception as e:
            raise GeminiAPIError(details=str(e)[:200])

        duration_ns = int((time.monotonic() - start) * 1e9)
        content = response.text

        usage = getattr(response, "usage_metadata", None)
        eval_count = getattr(usage, "candidates_token_count", 0) if usage else 0

        logger.info(
            f"Gemini chat: {duration_ns / 1e9:.1f}s, "
            f"{len(content)} chars, tokens={eval_count}"
        )

        return {
            "content": content,
            "total_duration": duration_ns,
            "eval_count": eval_count,
        }

    async def chat_stream(self, messages: list[dict], think: bool = True):
        """
        Streaming chat via Gemini API.

        Yields format identik OllamaProvider:
        {"token": str, "thinking": str, "done": bool}

        Catatan:
        - Gemini tidak punya output thinking token terpisah.
        - Parameter think dipertahankan untuk kompatibilitas interface.
        """
        _ = think  # Unused for Gemini, kept for provider interface compatibility.
        gemini_messages = self._convert_messages(messages)

        try:
            if len(gemini_messages) > 1:
                chat_session = self.model.start_chat(history=gemini_messages[:-1])
                last_parts = gemini_messages[-1]["parts"]
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        chat_session.send_message,
                        last_parts,
                        stream=True,
                    ),
                    timeout=self.timeout,
                )
            else:
                prompt = gemini_messages[0]["parts"] if gemini_messages else ""
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.model.generate_content,
                        prompt,
                        stream=True,
                    ),
                    timeout=self.timeout,
                )

            for chunk in response:
                text = chunk.text if hasattr(chunk, "text") else ""
                if text:
                    yield {
                        "token": text,
                        "thinking": "",
                        "done": False,
                    }

            yield {"token": "", "thinking": "", "done": True}

        except asyncio.TimeoutError:
            raise GeminiTimeoutError(self.timeout)
        except Exception as e:
            raise GeminiAPIError(details=str(e)[:200])

    @staticmethod
    def _detect_mime_type(b64_data: str) -> str:
        """Detect MIME type dari base64 header bytes."""
        if b64_data.startswith("/9j/"):
            return "image/jpeg"
        elif b64_data.startswith("iVBOR"):
            return "image/png"
        elif b64_data.startswith("R0lGOD"):
            return "image/gif"
        elif b64_data.startswith("UklGR"):
            return "image/webp"
        return "image/jpeg"  # default fallback

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """Konversi format Ollama → Gemini chat history format, termasuk images."""
        result = []
        system_text = ""

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            images = msg.get("images", [])

            if role == "system":
                system_text += content + "\n"
            elif role == "user":
                text = (system_text + "\n" + content) if system_text else content
                system_text = ""

                # Build parts: teks + images
                parts: list = [text]
                for img_b64 in images:
                    mime_type = self._detect_mime_type(img_b64)
                    img_bytes = base64.b64decode(img_b64)
                    parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": img_bytes,
                        }
                    })

                result.append({"role": "user", "parts": parts})
            elif role == "assistant":
                result.append({"role": "model", "parts": [content]})

        # Edge case: hanya system message tanpa user message
        if system_text and not result:
            result.append({"role": "user", "parts": [system_text.strip()]})

        return result

