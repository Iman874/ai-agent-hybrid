# Task 09 — Response Parser (JSON Extraction dari LLM Output)

## 1. Judul Task

Implementasi `ResponseParser` — extract dan validasi JSON dari raw output LLM.

## 2. Deskripsi

Membuat class `ResponseParser` yang mampu mengekstrak JSON terstruktur dari output LLM. Karena LLM kadang mengeluarkan teks campuran (teks + JSON), parser harus punya beberapa strategi: direct parse, regex extraction, dan raise error jika gagal total.

## 3. Tujuan Teknis

- `ResponseParser.extract_json(raw)` bisa parse JSON dari berbagai format output LLM
- 3 strategi parsing: direct → regex → raise error
- `ResponseParser.validate_parsed(data)` konversi dict → `LLMParsedResponse` (Pydantic)
- Informasi error yang jelas jika parsing gagal

## 4. Scope

### Yang dikerjakan
- `app/core/response_parser.py` — class `ResponseParser` dengan 2 method

### Yang tidak dikerjakan
- Retry logic (itu di ChatService, task 11)
- Fallback response builder (itu di ChatService)

## 5. Langkah Implementasi

### Step 1: Buat `app/core/response_parser.py`

```python
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
            if isinstance(result, dict):
                logger.debug("JSON parsed via direct parse")
                return result
        except json.JSONDecodeError:
            pass

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

        # === Strategi 2b: Cari antara ``` code blocks ===
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        code_matches = re.findall(code_block_pattern, raw, re.DOTALL)
        for match in code_matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict):
                    logger.debug("JSON parsed from code block")
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
```

### Step 2: Test semua strategi

```python
from app.core.response_parser import ResponseParser

parser = ResponseParser()

# === Test 1: Direct JSON (ideal) ===
raw1 = '{"status": "NEED_MORE_INFO", "message": "Halo!", "confidence": 0.5}'
result1 = parser.extract_json(raw1)
assert result1["status"] == "NEED_MORE_INFO"

# === Test 2: Mixed text + JSON ===
raw2 = """Berikut analisis saya:
{"status": "NEED_MORE_INFO", "message": "Bisa ceritakan lebih detail?", "confidence": 0.3}
Semoga membantu!"""
result2 = parser.extract_json(raw2)
assert result2["status"] == "NEED_MORE_INFO"

# === Test 3: JSON di dalam code block ===
raw3 = """```json
{"status": "READY_TO_GENERATE", "message": "Siap!", "confidence": 0.9}
```"""
result3 = parser.extract_json(raw3)
assert result3["status"] == "READY_TO_GENERATE"

# === Test 4: Gagal total ===
raw4 = "Ini bukan JSON sama sekali, hanya teks biasa."
try:
    parser.extract_json(raw4)
    assert False, "Seharusnya raise LLMParseError"
except Exception as e:
    print(f"Expected error: {e}")

# === Test 5: Validate schema ===
data5 = {"status": "NEED_MORE_INFO", "message": "Test", "confidence": 0.5}
validated = parser.validate_parsed(data5)
assert validated.status == "NEED_MORE_INFO"

# === Test 6: Invalid schema ===
data6 = {"status": "INVALID_STATUS", "message": "Test"}
try:
    parser.validate_parsed(data6)
    assert False, "Seharusnya raise LLMParseError"
except Exception as e:
    print(f"Expected error: {e}")

print("All parser tests passed!")
```

## 6. Output yang Diharapkan

```
Expected error: Gagal mem-parse respons dari LLM...
Expected error: Gagal mem-parse respons dari LLM...
All parser tests passed!
```

## 7. Dependencies

- **Task 02** — `LLMParseError` exception
- **Task 03** — `LLMParsedResponse` Pydantic model

## 8. Acceptance Criteria

- [ ] `extract_json('{"status": "NEED_MORE_INFO", ...}')` berhasil (direct parse)
- [ ] `extract_json('teks {"status": ...} teks')` berhasil (regex extract)
- [ ] `extract_json('```json\n{...}\n```')` berhasil (code block extract)
- [ ] `extract_json('teks biasa tanpa JSON')` raise `LLMParseError`
- [ ] `extract_json` return `dict`, bukan string
- [ ] `validate_parsed(valid_dict)` return `LLMParsedResponse`
- [ ] `validate_parsed({"status": "INVALID"})` raise `LLMParseError`
- [ ] `validate_parsed({"status": "NEED_MORE_INFO", "confidence": 1.5})` raise error (confidence > 1.0)
- [ ] Logging: debug log saat strategi berhasil, warning log saat gagal

## 9. Estimasi

**Medium** — ~1.5 jam
