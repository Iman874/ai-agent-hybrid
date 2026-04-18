# Task 13 — Integration Test & End-to-End Verification

## 1. Judul Task

Buat test suite dan lakukan verifikasi end-to-end seluruh Chat Engine.

## 2. Deskripsi

Membuat file test menggunakan `pytest` + `pytest-asyncio` untuk memverifikasi bahwa seluruh Chat Engine berfungsi dari ujung ke ujung. Test mencakup: unit test komponen individual, integration test flow chat multi-turn, dan edge case handling.

## 3. Tujuan Teknis

- Test suite bisa dijalankan dengan `pytest tests/ -v`
- Test ResponseParser: semua strategi parsing
- Test CompletenessCalculator: semua skenario score
- Test SessionManager: CRUD + data integrity
- Test ChatService: full flow dengan mock (tanpa Ollama aktif)
- Test Endpoint: HTTP request/response via TestClient

## 4. Scope

### Yang dikerjakan
- `tests/conftest.py` — shared fixtures
- `tests/test_response_parser.py` — unit test parser
- `tests/test_completeness.py` — unit test completeness
- `tests/test_session_manager.py` — integration test SessionManager
- `tests/test_chat_endpoint.py` — endpoint test via TestClient

### Yang tidak dikerjakan
- Test dengan Ollama real (itu manual test)
- Performance/load testing
- Test modul lain (RAG, Gemini, dll)

## 5. Langkah Implementasi

### Step 1: Buat `tests/__init__.py` (kosong)

### Step 2: Buat `tests/conftest.py`

```python
import pytest
import asyncio
import os
from pathlib import Path

from app.db.database import init_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db_path(tmp_path):
    """Path ke temporary test database."""
    return str(tmp_path / "test_sessions.db")


@pytest.fixture
async def initialized_db(test_db_path):
    """Database yang sudah di-init dengan schema."""
    await init_db(test_db_path)
    return test_db_path
```

### Step 3: Buat `tests/test_response_parser.py`

```python
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
```

### Step 4: Buat `tests/test_completeness.py`

```python
from app.core.completeness import calculate_completeness, merge_extracted_data
from app.models.tor import TORData


class TestCalculateCompleteness:
    def test_empty_data(self):
        assert calculate_completeness(TORData()) == 0.0

    def test_one_field(self):
        assert calculate_completeness(TORData(judul="Workshop")) == 0.17

    def test_three_fields(self):
        data = TORData(judul="X", tujuan="Y", timeline="Z")
        assert calculate_completeness(data) == 0.50

    def test_all_required(self):
        data = TORData(
            judul="X", latar_belakang="X", tujuan="X",
            ruang_lingkup="X", output="X", timeline="X",
        )
        assert calculate_completeness(data) == 1.0

    def test_empty_string_not_counted(self):
        assert calculate_completeness(TORData(judul="")) == 0.0

    def test_whitespace_not_counted(self):
        assert calculate_completeness(TORData(judul="   ")) == 0.0

    def test_optional_bonus_capped(self):
        data = TORData(
            judul="X", latar_belakang="X", tujuan="X",
            ruang_lingkup="X", output="X", timeline="X",
            estimasi_biaya="50jt",
        )
        assert calculate_completeness(data) == 1.0  # capped


class TestMergeData:
    def test_new_updates_existing(self):
        existing = TORData(judul="Old")
        new = TORData(judul="New", tujuan="Added")
        merged = merge_extracted_data(existing, new)
        assert merged.judul == "New"
        assert merged.tujuan == "Added"

    def test_null_does_not_overwrite(self):
        existing = TORData(judul="Keep", tujuan="Keep")
        new = TORData(judul=None, tujuan="Updated")
        merged = merge_extracted_data(existing, new)
        assert merged.judul == "Keep"
        assert merged.tujuan == "Updated"

    def test_empty_does_not_overwrite(self):
        existing = TORData(judul="Keep")
        new = TORData(judul="")
        merged = merge_extracted_data(existing, new)
        assert merged.judul == "Keep"
```

### Step 5: Buat `tests/test_session_manager.py`

```python
import pytest
from app.core.session_manager import SessionManager
from app.models.tor import TORData
from app.utils.errors import SessionNotFoundError


@pytest.mark.asyncio
class TestSessionManager:
    async def test_create_session(self, initialized_db):
        mgr = SessionManager(initialized_db)
        session = await mgr.create()
        assert session.id is not None
        assert session.state == "NEW"
        assert session.turn_count == 0

    async def test_get_session(self, initialized_db):
        mgr = SessionManager(initialized_db)
        created = await mgr.create()
        fetched = await mgr.get(created.id)
        assert fetched.id == created.id

    async def test_get_not_found(self, initialized_db):
        mgr = SessionManager(initialized_db)
        with pytest.raises(SessionNotFoundError):
            await mgr.get("non-existent-uuid")

    async def test_update_session(self, initialized_db):
        mgr = SessionManager(initialized_db)
        session = await mgr.create()
        await mgr.update(session.id, state="CHATTING", turn_count=1)
        updated = await mgr.get(session.id)
        assert updated.state == "CHATTING"
        assert updated.turn_count == 1

    async def test_update_extracted_data(self, initialized_db):
        mgr = SessionManager(initialized_db)
        session = await mgr.create()
        data = TORData(judul="Workshop AI", tujuan="Belajar")
        await mgr.update(session.id, extracted_data=data)
        updated = await mgr.get(session.id)
        assert updated.extracted_data.judul == "Workshop AI"
        assert updated.extracted_data.tujuan == "Belajar"

    async def test_append_and_get_messages(self, initialized_db):
        mgr = SessionManager(initialized_db)
        session = await mgr.create()
        await mgr.append_message(session.id, "user", "Halo")
        await mgr.append_message(session.id, "assistant", "Hai!", "NEED_MORE_INFO")
        history = await mgr.get_chat_history(session.id)
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].role == "assistant"
        assert history[1].parsed_status == "NEED_MORE_INFO"
```

### Step 6: Jalankan test

```bash
pytest tests/ -v --tb=short
```

## 6. Output yang Diharapkan

```
tests/test_response_parser.py::TestExtractJSON::test_direct_json PASSED
tests/test_response_parser.py::TestExtractJSON::test_json_with_whitespace PASSED
tests/test_response_parser.py::TestExtractJSON::test_mixed_text_json PASSED
tests/test_response_parser.py::TestExtractJSON::test_code_block_json PASSED
tests/test_response_parser.py::TestExtractJSON::test_no_json_raises_error PASSED
tests/test_response_parser.py::TestExtractJSON::test_empty_string_raises_error PASSED
tests/test_response_parser.py::TestValidateParsed::test_valid_need_more_info PASSED
tests/test_response_parser.py::TestValidateParsed::test_invalid_status_raises_error PASSED
tests/test_response_parser.py::TestValidateParsed::test_confidence_out_of_range PASSED
tests/test_response_parser.py::TestValidateParsed::test_missing_message_raises_error PASSED
tests/test_completeness.py::TestCalculateCompleteness::test_empty_data PASSED
...
tests/test_session_manager.py::TestSessionManager::test_create_session PASSED
...

========================= 20 passed =========================
```

## 7. Dependencies

- **Semua task sebelumnya (01–12)** harus sudah selesai
- `pytest`, `pytest-asyncio` harus terinstall

## 8. Acceptance Criteria

- [ ] `pytest tests/ -v` berhasil dijalankan
- [ ] Semua test ResponseParser PASSED (6 test)
- [ ] Semua test Completeness PASSED (9 test)
- [ ] Semua test SessionManager PASSED (6 test)
- [ ] 0 test FAILED
- [ ] Test menggunakan temporary database (bukan database production)
- [ ] Tidak ada dependency ke Ollama (test parser & completeness pure unit test)
- [ ] End-to-end test bisa dijalankan manual: `curl POST /chat` → response valid

## 9. Estimasi

**Medium** — ~2 jam
