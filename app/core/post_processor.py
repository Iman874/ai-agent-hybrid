import re
import logging
from app.models.generate import ProcessedTOR

logger = logging.getLogger("ai-agent-hybrid.gemini.postprocessor")


class PostProcessor:
    """Validasi dan clean output TOR dari Gemini."""

    EXPECTED_SECTIONS = [
        "Latar Belakang",
        "Tujuan",
        "Ruang Lingkup",
        "Output",
        "Timeline",
    ]
    MIN_WORD_COUNT = 300

    @staticmethod
    def process(raw_tor: str) -> ProcessedTOR:
        """Validate dan clean TOR output."""
        content = PostProcessor._clean_formatting(raw_tor)
        word_count = len(content.split())
        has_assumptions = "[ASUMSI]" in content
        missing_sections = PostProcessor._check_structure(content)

        if word_count < PostProcessor.MIN_WORD_COUNT:
            logger.warning(f"TOR pendek: {word_count} kata (min: {PostProcessor.MIN_WORD_COUNT})")

        if missing_sections:
            logger.warning(f"TOR missing sections: {missing_sections}")

        return ProcessedTOR(
            content=content,
            word_count=word_count,
            has_assumptions=has_assumptions,
            missing_sections=missing_sections,
        )

    @staticmethod
    def _clean_formatting(text: str) -> str:
        """Remove wrapping code blocks, normalize whitespace."""
        # Remove ```markdown ... ``` wrapper
        text = re.sub(r'^```(?:markdown)?\s*\n', '', text)
        text = re.sub(r'\n```\s*$', '', text)
        # Normalize multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def _check_structure(content: str) -> list[str]:
        """Check apakah semua expected sections ada."""
        missing = []
        for section in PostProcessor.EXPECTED_SECTIONS:
            if section.lower() not in content.lower():
                missing.append(section)
        return missing
