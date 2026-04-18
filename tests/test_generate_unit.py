"""Unit tests Gemini Generator — tidak membutuhkan API key."""
import pytest
from app.core.post_processor import PostProcessor
from app.core.gemini_prompt_builder import GeminiPromptBuilder, format_chat_history
from app.models.tor import TORData
from app.models.session import ChatMessage


class TestPostProcessor:
    def test_clean_code_block_wrapper(self):
        raw = "```markdown\n# TOR\nIni konten.\n```"
        result = PostProcessor.process(raw)
        assert not result.content.startswith("```")

    def test_word_count(self):
        result = PostProcessor.process("satu dua tiga empat lima enam")
        assert result.word_count == 6

    def test_has_assumptions_true(self):
        result = PostProcessor.process("Ini [ASUMSI] konten asumsi.")
        assert result.has_assumptions is True

    def test_has_assumptions_false(self):
        result = PostProcessor.process("Ini konten tanpa asumsi.")
        assert result.has_assumptions is False

    def test_missing_sections_detected(self):
        result = PostProcessor.process("## 1. Latar Belakang\nIni saja.")
        assert "Tujuan" in result.missing_sections

    def test_all_sections_present(self):
        tor = "Latar Belakang\nTujuan\nRuang Lingkup\nOutput\nTimeline"
        result = PostProcessor.process(tor)
        assert result.missing_sections == []


class TestGeminiPromptBuilder:
    def test_standard_with_rag(self):
        data = TORData(judul="Workshop AI")
        prompt = GeminiPromptBuilder.build_standard(data, rag_examples="Contoh TOR")
        assert "Workshop AI" in prompt
        assert "Contoh TOR" in prompt

    def test_standard_without_rag(self):
        data = TORData(judul="Workshop AI")
        prompt = GeminiPromptBuilder.build_standard(data)
        assert "Tidak ada referensi tersedia" in prompt

    def test_escalation_with_history(self):
        history = [
            ChatMessage(session_id="x", role="user", content="Buat TOR"),
        ]
        formatted = format_chat_history(history)
        prompt = GeminiPromptBuilder.build_escalation(formatted)
        assert "[USER]: Buat TOR" in prompt

    def test_escalation_with_partial_data(self):
        data = TORData(judul="Test TOR")
        prompt = GeminiPromptBuilder.build_escalation("chat...", partial_data=data)
        assert "Test TOR" in prompt
        assert "DATA PARSIAL" in prompt
