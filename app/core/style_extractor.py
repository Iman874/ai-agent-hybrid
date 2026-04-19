import json
import logging
from app.ai.prompts.extract_style import STYLE_EXTRACTION_PROMPT
from app.ai.gemini_provider import GeminiProvider
from app.models.tor_style import TORStyle

logger = logging.getLogger("ai-agent-hybrid.style_extractor")

class StyleExtractorError(Exception):
    pass

class StyleExtractor:
    """Service untuk mengekstrak definisi TORStyle dari plain-text sebuah file PDF/DOCX menggunakan LLM."""
    
    def __init__(self, gemini: GeminiProvider):
        self.gemini = gemini

    async def extract_from_text(self, document_text: str) -> TORStyle:
        """Kirim teks panjang ke Gemini untuk diekstrak menjadi TORStyle JSON."""
        # Clean potential injections or extremely long texts briefly, though prompt helps
        prompt = STYLE_EXTRACTION_PROMPT.replace("{DOCUMENT_TEXT}", document_text)
        
        # Retry mechanism built-in (1x retry if parsing fails)
        last_error = None
        for attempt in range(2):
            try:
                response = await self.gemini.generate(prompt)
                raw_json = self._clean_json(response.text)
                
                data = json.loads(raw_json)
                
                import uuid
                style_id = f"extracted_{uuid.uuid4().hex[:8]}"
                
                style_data = {
                    "id": style_id,
                    "name": data.get("extracted_name", "Format Ekstrak AI"),
                    "description": data.get("extracted_description", "") + f" (Catatan Analisis AI: {data.get('analysis_notes', '')})",
                    "is_default": False,
                    "is_active": False,
                    "created_at": "",
                    "updated_at": "",
                    "source": "extracted",
                    "sections": data.get("sections", []),
                    "config": data.get("config", {})
                }
                
                # Parse through Pydantic to ensure it's fully valid according to task 01
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc).isoformat()
                style_data["created_at"] = now
                style_data["updated_at"] = now
                
                valid_style = TORStyle(**style_data)
                return valid_style
                
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning(f"Failed to parse LLM extraction JSON on attempt {attempt+1}: {e}\nRaw JSON: {raw_json[:200]}...")
                last_error = e
            except Exception as e:
                raise StyleExtractorError(f"Terjadi kesalahan saat memproses via Gemini: {e}")

        raise StyleExtractorError(f"Gagal melakukan parsing hasil AI menjadi JSON valid: {last_error}")

    def _clean_json(self, text: str) -> str:
        """Membersihkan markdown blocks jika Gemini masih membandel memberikannya (biasanya triple-backticks json)."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
            
        if text.endswith("```"):
            text = text[:-3]
            
        return text.strip()
