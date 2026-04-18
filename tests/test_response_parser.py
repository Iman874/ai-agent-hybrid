import pytest
from app.core.response_parser import ResponseParser
from app.utils.errors import LLMParseError


class TestExtractJSON:
    parser = ResponseParser()

    def test_direct_json(self):
        raw = '{"status": "NEED_MORE_INFO", "message": "Halo!", "confidence": 0.5}'
        result = self.parser.extract_json(raw)
        assert result["status"] == "NEED_MORE_INFO"

    def test_json_with_whitespace(self):
        raw = '  \n {"status": "READY_TO_GENERATE", "message": "OK", "confidence": 0.9} \n '
        result = self.parser.extract_json(raw)
        assert result["status"] == "READY_TO_GENERATE"

    def test_mixed_text_json(self):
        raw = 'Berikut:\n{"status": "NEED_MORE_INFO", "message": "Test", "confidence": 0.3}\nSemoga membantu!'
        result = self.parser.extract_json(raw)
        assert result["status"] == "NEED_MORE_INFO"

    def test_code_block_json(self):
        raw = '```json\n{"status": "READY_TO_GENERATE", "message": "Done", "confidence": 0.9}\n```'
        result = self.parser.extract_json(raw)
        assert result["status"] == "READY_TO_GENERATE"

    def test_no_json_raises_error(self):
        with pytest.raises(LLMParseError):
            self.parser.extract_json("ini bukan JSON sama sekali")

    def test_empty_string_raises_error(self):
        with pytest.raises(LLMParseError):
            self.parser.extract_json("")


class TestValidateParsed:
    parser = ResponseParser()

    def test_valid_need_more_info(self):
        data = {"status": "NEED_MORE_INFO", "message": "Test", "confidence": 0.5}
        result = self.parser.validate_parsed(data)
        assert result.status == "NEED_MORE_INFO"
        assert result.confidence == 0.5

    def test_invalid_status_raises_error(self):
        data = {"status": "INVALID", "message": "Test"}
        with pytest.raises(LLMParseError):
            self.parser.validate_parsed(data)

    def test_confidence_out_of_range(self):
        data = {"status": "NEED_MORE_INFO", "message": "Test", "confidence": 1.5}
        with pytest.raises(LLMParseError):
            self.parser.validate_parsed(data)

    def test_missing_message_raises_error(self):
        data = {"status": "NEED_MORE_INFO"}
        with pytest.raises(LLMParseError):
            self.parser.validate_parsed(data)
