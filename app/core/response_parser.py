import json
import re
import logging

from pydantic import ValidationError

from app.models.tor import LLMParsedResponse
from app.utils.errors import LLMParseError

logger = logging.getLogger("ai-agent-hybrid.parser")


class ResponseParser:
    """Extract dan validasi JSON dari raw LLM output."""

    @staticmethod
    def extract_json(raw: str) -> dict:
        """
        Extract JSON object dari raw string.

        Strategi:
        1. Direct JSON parse (ideal: LLM output pure JSON)
        2. Regex: cari JSON object di dalam mixed text
        3. Raise LLMParseError jika gagal

        Args:
            raw: Raw string output dari LLM

        Returns:
            dict — parsed JSON object

        Raises:
            LLMParseError: Jika tidak bisa extract JSON
        """
        raw = raw.strip()

        # === Strategi 1: Direct parse ===
        try:
            result = json.loads(raw)
            if isinstance(result, dict) and "status" in result:
                logger.debug("JSON parsed via direct parse")
                return result
        except json.JSONDecodeError:
            pass

        # === Strategi 2b: Cari antara ``` code blocks ===
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        code_matches = re.findall(code_block_pattern, raw, re.DOTALL)
        for match in code_matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict) and "status" in parsed:
                    logger.debug("JSON parsed from code block")
                    return parsed
            except json.JSONDecodeError:
                continue

        # === Strategi 2: Regex — cari JSON object di dalam teks ===
        # Cari pattern { ... } yang mengandung nested objects
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, raw, re.DOTALL)

        # Coba dari match terpanjang/terakhir (karena LLM kadang output teks dulu, JSON di akhir)
        for match in sorted(matches, key=len, reverse=True):
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict) and "status" in parsed:
                    logger.debug("JSON parsed via regex extraction")
                    return parsed
            except json.JSONDecodeError:
                continue

        # === Strategi 3: Gagal ===
        preview = raw[:200].replace("\n", " ")
        logger.warning(f"Failed to extract JSON. Raw preview: {preview}")
        raise LLMParseError(
            details=f"Tidak dapat mengekstrak JSON dari respons LLM. "
                    f"Raw response (first 200 chars): {preview}"
        )

    @staticmethod
    def validate_parsed(data: dict) -> LLMParsedResponse:
        """
        Validasi dict terhadap Pydantic schema LLMParsedResponse.

        Args:
            data: dict hasil extract_json()

        Returns:
            LLMParsedResponse — validated Pydantic model

        Raises:
            LLMParseError: Jika schema tidak sesuai
        """
        try:
            return LLMParsedResponse(**data)
        except ValidationError as e:
            logger.warning(f"Schema validation failed: {e}")
            raise LLMParseError(
                details=f"JSON valid tapi schema tidak sesuai: {e.errors()}"
            )
