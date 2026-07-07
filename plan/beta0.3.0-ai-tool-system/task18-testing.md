# Task 18 — Testing

## Deskripsi

Membuat unit test dan integration test untuk seluruh Tool System. Mencakup pengujian komponen individu (BaseTool, ToolRegistry, WebSearchTool, ToolHandler) hingga integrasi dengan ChatService, SSE events, dan API endpoint.

Semua test harus bisa jalan **tanpa koneksi internet** (menggunakan mock) dan **tanpa dependency eksternal** (Ollama/Gemini).

---

## Tujuan Teknis

- Unit test coverage untuk setiap komponen tool system (> 90%)
- Integration test untuk tool calling flow (ChatService + ToolHandler)
- Integration test untuk SSE tool events
- Integration test untuk GET /tools endpoint
- Mock untuk DuckDuckGo search, Ollama, dan Gemini
- Semua test bisa jalan dengan `pytest tests/`

---

## Scope

### Termasuk — 8 file test

#### 1. `tests/test_tool_base.py` — Test BaseTool, ToolSpec, ToolResult

```python
"""Test untuk tool abstraction layer."""

import pytest
from app.tools.base import BaseTool, ToolSpec, ToolResult


class TestToolSpec:
    def test_valid_spec(self):
        spec = ToolSpec(
            name="web_search",
            description="Search the web",
            parameters={"type": "object", "properties": {}, "required": []},
        )
        assert spec.name == "web_search"
        assert spec.description == "Search the web"

    def test_invalid_name_pattern(self):
        with pytest.raises(Exception):  # Pydantic validation error
            ToolSpec(
                name="Web Search!",  # uppercase + space + special char
                description="test",
                parameters={},
            )

    def test_frozen(self):
        spec = ToolSpec(name="test", description="test", parameters={})
        with pytest.raises(Exception):  # frozen=True
            spec.name = "new_name"


class TestToolResult:
    def test_success_result(self):
        result = ToolResult(
            tool_name="web_search",
            success=True,
            data="search results",
            metadata={"query": "test", "result_count": 5},
        )
        assert result.success is True
        assert result.data == "search results"
        assert result.error is None

    def test_error_result(self):
        result = ToolResult(
            tool_name="web_search",
            success=False,
            data="",
            error="Timeout",
        )
        assert result.success is False
        assert result.data == ""
        assert result.error == "Timeout"

    def test_default_values(self):
        result = ToolResult(tool_name="test", success=True)
        assert result.data == ""
        assert result.error is None
        assert result.metadata == {}


class TestBaseTool:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseTool()

    def test_must_implement_spec_and_execute(self):
        # Class tanpa implementasi spec → error saat instantiasi
        class IncompleteTool(BaseTool):
            pass

        with pytest.raises(TypeError):
            IncompleteTool()
```

#### 2. `tests/test_tool_registry.py` — Test ToolRegistry

```python
"""Test untuk ToolRegistry."""

import pytest
from app.tools.registry import ToolRegistry
from app.tools.base import BaseTool, ToolSpec, ToolResult


class MockTool(BaseTool):
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="mock_tool",
            description="Mock for testing",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(
            tool_name="mock_tool",
            success=True,
            data=f"executed with {kwargs}",
        )


class FailingTool(BaseTool):
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="failing_tool",
            description="Always fails",
            parameters={},
        )

    async def execute(self, **kwargs) -> ToolResult:
        raise RuntimeError("Something went wrong")


class TestToolRegistry:
    @pytest.fixture
    def registry(self):
        return ToolRegistry()

    @pytest.fixture
    def mock_tool(self):
        return MockTool()

    def test_register(self, registry, mock_tool):
        registry.register(mock_tool)
        assert registry.count() == 1
        assert registry.list_tools() == ["mock_tool"]

    def test_register_invalid_type(self, registry):
        with pytest.raises(TypeError):
            registry.register("not_a_tool")  # type: ignore

    def test_register_overwrite(self, registry, mock_tool):
        registry.register(mock_tool)
        registry.register(mock_tool)  # overwrite with warning
        assert registry.count() == 1  # masih 1, bukan 2

    def test_get_specs(self, registry, mock_tool):
        registry.register(mock_tool)
        specs = registry.get_specs()
        assert len(specs) == 1
        assert specs[0].name == "mock_tool"

    def test_get_specs_empty(self, registry):
        assert registry.get_specs() == []

    @pytest.mark.asyncio
    async def test_execute(self, registry, mock_tool):
        registry.register(mock_tool)
        result = await registry.execute("mock_tool", input="hello")
        assert result.success is True
        assert "hello" in result.data

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, registry):
        result = await registry.execute("unknown")
        assert result.success is False
        assert "tidak ditemukan" in result.error

    @pytest.mark.asyncio
    async def test_execute_failing_tool(self, registry):
        registry.register(FailingTool())
        result = await registry.execute("failing_tool")
        assert result.success is False
        assert "gagal" in result.error

    def test_get_tool(self, registry, mock_tool):
        registry.register(mock_tool)
        assert registry.get_tool("mock_tool") is mock_tool
        assert registry.get_tool("unknown") is None

    def test_list_tools(self, registry, mock_tool):
        assert registry.list_tools() == []
        registry.register(mock_tool)
        assert registry.list_tools() == ["mock_tool"]

    def test_count(self, registry, mock_tool):
        assert registry.count() == 0
        registry.register(mock_tool)
        assert registry.count() == 1
```

#### 3. `tests/test_web_search.py` — Test WebSearchTool (Mocked)

```python
"""Test untuk WebSearchTool — menggunakan mock DuckDuckGo."""

from unittest.mock import patch, MagicMock
import pytest
from app.tools.web_search import WebSearchTool


class TestWebSearchTool:
    @pytest.fixture
    def tool(self):
        return WebSearchTool()

    def test_spec(self, tool):
        spec = tool.spec
        assert spec.name == "web_search"
        assert "query" in spec.parameters["required"]
        assert spec.parameters["properties"]["max_results"]["default"] == 5

    @pytest.mark.asyncio
    async def test_execute_empty_query(self, tool):
        result = await tool.execute(query="")
        assert result.success is False
        assert "minimal" in result.error

    @pytest.mark.asyncio
    async def test_execute_short_query(self, tool):
        result = await tool.execute(query="ab")  # < 3 chars
        assert result.success is False

    @pytest.mark.asyncio
    async def test_execute_clamps_max_results(self, tool):
        result = await tool.execute(query="test", max_results=100)
        # Should be clamped to 10, but with mock it might return 0
        # Yang penting tidak error

    @pytest.mark.asyncio
    @patch("app.tools.web_search.DDGS")
    async def test_execute_success(self, mock_ddgs, tool):
        # Mock DuckDuckGo response
        mock_instance = MagicMock()
        mock_instance.text.return_value = [
            {"title": "Result 1", "body": "Content 1", "href": "https://example.com/1"},
            {"title": "Result 2", "body": "Content 2", "href": "https://example.com/2"},
        ]
        mock_ddgs.return_value.__enter__.return_value = mock_instance

        result = await tool.execute(query="AI Indonesia", max_results=2)
        assert result.success is True
        assert "HASIL PENCARIAN INTERNET" in result.data
        assert "Result 1" in result.data
        assert "Result 2" in result.data
        assert result.metadata["result_count"] == 2
        assert result.metadata["source"] == "duckduckgo"

    @pytest.mark.asyncio
    @patch("app.tools.web_search.DDGS")
    async def test_execute_empty_results(self, mock_ddgs, tool):
        mock_instance = MagicMock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value.__enter__.return_value = mock_instance

        result = await tool.execute(query="nonexistent")
        assert result.success is True  # Tetap success
        assert "tidak menemukan hasil" in result.data
        assert result.metadata["result_count"] == 0

    @pytest.mark.asyncio
    @patch("app.tools.web_search.DDGS")
    async def test_execute_timeout(self, mock_ddgs, tool):
        import asyncio
        mock_instance = MagicMock()
        mock_instance.text.side_effect = asyncio.TimeoutError()
        mock_ddgs.return_value.__enter__.return_value = mock_instance

        result = await tool.execute(query="test")
        assert result.success is False
        assert "timeout" in result.error.lower()
```

#### 4. `tests/test_tool_handler.py` — Test ToolHandler

```python
"""Test untuk ToolHandler — parsing dan execution loop."""

import pytest
from app.tools.registry import ToolRegistry
from app.tools.base import BaseTool, ToolSpec, ToolResult
from app.ai.tool_handler import ToolHandler


class MockSearchTool(BaseTool):
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="web_search",
            description="Search",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        )

    async def execute(self, query: str = "", **kwargs) -> ToolResult:
        return ToolResult(
            tool_name="web_search",
            success=True,
            data=f"=== HASIL ===\nQuery: {query}\n=== AKHIR ===",
            metadata={"query": query, "result_count": 1},
        )


class TestToolHandler:
    @pytest.fixture
    def handler(self):
        registry = ToolRegistry()
        registry.register(MockSearchTool())
        return ToolHandler(registry, max_calls=3)

    def test_parse_native_tool_calls_ollama(self, handler):
        response = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "web_search",
                            "arguments": {"query": "test"},
                        }
                    }
                ],
            }
        }
        calls = handler.parse_native_tool_calls(response)
        assert len(calls) == 1
        assert calls[0]["name"] == "web_search"
        assert calls[0]["arguments"]["query"] == "test"

    def test_parse_native_tool_calls_none(self, handler):
        calls = handler.parse_native_tool_calls({"message": {"content": "hello"}})
        assert len(calls) == 0

    def test_parse_prompt_injection(self, handler):
        text = '[[TOOL_CALL: web_search(query="AI Indonesia", max_results=5)]]'
        calls = handler.parse_prompt_injection(text)
        assert len(calls) == 1
        assert calls[0]["name"] == "web_search"
        assert calls[0]["arguments"]["query"] == "AI Indonesia"
        assert calls[0]["arguments"]["max_results"] == 5

    def test_parse_prompt_injection_no_match(self, handler):
        calls = handler.parse_prompt_injection("Halo apa kabar?")
        assert len(calls) == 0

    def test_parse_prompt_injection_multiple(self, handler):
        text = (
            '[[TOOL_CALL: web_search(query="first")]] dan '
            '[[TOOL_CALL: web_search(query="second")]]'
        )
        calls = handler.parse_prompt_injection(text)
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_handle_tool_calls(self, handler):
        tool_calls = [
            {"name": "web_search", "arguments": {"query": "test"}}
        ]
        messages = await handler.handle_tool_calls(tool_calls)
        assert len(messages) == 1
        assert messages[0]["role"] == "tool"
        assert messages[0]["name"] == "web_search"
        assert "HASIL" in messages[0]["content"]

    @pytest.mark.asyncio
    async def test_execute_with_loop(self, handler):
        call_count = 0

        async def mock_provider(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "web_search",
                                    "arguments": {"query": "test"},
                                }
                            }
                        ],
                    }
                }
            return {"message": {"role": "assistant", "content": "Final response"}}

        messages = [{"role": "user", "content": "test"}]
        final_messages, response, history = await handler.execute_with_loop(
            mock_provider, messages
        )
        assert len(history) == 1
        assert history[0]["name"] == "web_search"
        assert response["message"]["content"] == "Final response"

    @pytest.mark.asyncio
    async def test_execute_with_loop_max_calls(self, handler):
        call_count = 0

        async def always_call_tool(messages):
            nonlocal call_count
            call_count += 1
            return {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "web_search",
                                "arguments": {"query": f"call_{call_count}"},
                            }
                        }
                    ],
                }
            }

        messages = [{"role": "user", "content": "test"}]
        final_messages, response, history = await handler.execute_with_loop(
            always_call_tool, messages
        )
        assert len(history) == 3  # Max 3 calls
        assert call_count == 4  # 3 tool calls + 1 final

    @pytest.mark.asyncio
    async def test_execute_with_loop_tools_disabled(self, handler):
        async def mock_provider(messages):
            return {"message": {"role": "assistant", "content": "No tools"}}

        messages = [{"role": "user", "content": "test"}]
        final_messages, response, history = await handler.execute_with_loop(
            mock_provider, messages, tools_enabled=False
        )
        assert len(history) == 0  # Tidak ada tool call
```

#### 5. `tests/test_prompt_injection.py` — Test Prompt Injection Builder

```python
"""Test untuk prompt injection builder."""

from app.tools.base import ToolSpec
from app.ai.prompts.tool_injection import (
    build_tool_injection_prompt,
    has_native_tool_support,
)


class TestBuildToolInjectionPrompt:
    def test_empty_specs(self):
        assert build_tool_injection_prompt([]) == ""

    def test_single_tool(self):
        specs = [
            ToolSpec(
                name="web_search",
                description="Search the web",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                    },
                    "required": ["query"],
                },
            )
        ]
        prompt = build_tool_injection_prompt(specs)
        assert "web_search" in prompt
        assert "Search the web" in prompt
        assert "query" in prompt
        assert "[[TOOL_CALL:" in prompt
        assert "JANGAN" in prompt

    def test_multiple_tools(self):
        specs = [
            ToolSpec(name="tool_a", description="Tool A", parameters={}),
            ToolSpec(name="tool_b", description="Tool B", parameters={}),
        ]
        prompt = build_tool_injection_prompt(specs)
        assert "tool_a" in prompt
        assert "tool_b" in prompt


class TestHasNativeToolSupport:
    def test_gemini_always_true(self):
        assert has_native_tool_support("gemini-2.0-flash", "google") is True
        assert has_native_tool_support("gemini-1.5-pro", "google") is True

    def test_ollama_supported_models(self):
        assert has_native_tool_support("qwen2.5:7b-instruct", "ollama") is True
        assert has_native_tool_support("llama3.2:3b", "ollama") is True
        assert has_native_tool_support("mistral:7b", "ollama") is True

    def test_ollama_unsupported_models(self):
        assert has_native_tool_support("llama3.2:1b", "ollama") is False
        assert has_native_tool_support("tinyllama:1.1b", "ollama") is False

    def test_unknown_provider(self):
        assert has_native_tool_support("any", "unknown") is False
```

#### 6. `tests/test_tool_integration.py` — Test ChatService + Tool

```python
"""Integration test untuk ChatService dengan tool support."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_chat_service_with_tools():
    """Test ChatService.process_message dengan tools_enabled=True."""
    # Mock semua dependencies
    mock_ollama = AsyncMock()
    mock_ollama.chat.return_value = {
        "content": '{"status": "NEED_MORE_INFO", "message": "test"}',
        "tool_calls": None,
    }
    mock_session_mgr = AsyncMock()
    mock_prompt_builder = MagicMock()
    mock_prompt_builder.build_chat_messages.return_value = [
        {"role": "system", "content": "test"},
        {"role": "user", "content": "test"},
    ]
    mock_parser = MagicMock()
    mock_parser.parse.return_value = MagicMock(
        status="NEED_MORE_INFO",
        message="test",
        data=MagicMock(),
        confidence=0.5,
    )

    from app.services.chat_service import ChatService
    from app.tools.registry import ToolRegistry
    from app.tools.base import BaseTool, ToolSpec, ToolResult
    from app.ai.tool_handler import ToolHandler

    # Setup tool
    class MockTool(BaseTool):
        @property
        def spec(self):
            return ToolSpec(name="web_search", description="test", parameters={})

        async def execute(self, **kwargs):
            return ToolResult(tool_name="web_search", success=True, data="results")

    registry = ToolRegistry()
    registry.register(MockTool())
    handler = ToolHandler(registry)

    service = ChatService(
        ollama=mock_ollama,
        session_mgr=mock_session_mgr,
        prompt_builder=mock_prompt_builder,
        parser=mock_parser,
        tool_handler=handler,
        tool_registry=registry,
    )

    result = await service.process_message(
        session_id=None,
        message="test",
        tools_enabled=True,
    )
    assert result is not None
    assert result.status == "NEED_MORE_INFO"


@pytest.mark.asyncio
async def test_chat_service_without_tools():
    """Test ChatService.process_message tanpa tool support — backward compatible."""
    from app.services.chat_service import ChatService

    mock_ollama = AsyncMock()
    mock_ollama.chat.return_value = {
        "content": '{"status": "NEED_MORE_INFO", "message": "test"}',
    }
    mock_session_mgr = AsyncMock()
    mock_prompt_builder = MagicMock()
    mock_prompt_builder.build_chat_messages.return_value = [
        {"role": "user", "content": "test"},
    ]
    mock_parser = MagicMock()
    mock_parser.parse.return_value = MagicMock(
        status="NEED_MORE_INFO", message="test",
        data=MagicMock(), confidence=0.5,
    )

    service = ChatService(
        ollama=mock_ollama,
        session_mgr=mock_session_mgr,
        prompt_builder=mock_prompt_builder,
        parser=mock_parser,
        # Tanpa tool_handler dan tool_registry
    )

    result = await service.process_message(
        session_id=None,
        message="test",
        tools_enabled=False,
    )
    assert result is not None
```

#### 7. `tests/test_sse_tool_events.py` — Test SSE Events

```python
"""Test untuk SSE tool events di hybrid endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_hybrid_stream_tool_events():
    """Test /hybrid/stream mengirim tool_start dan tool_result events."""
    # Ini membutuhkan app FastAPI yang sudah di-setup dengan mock
    # Gunakan TestClient atau AsyncClient dengan ASGITransport
    pass  # Implementasi detail tergantung struktur test yang sudah ada
```

#### 8. `tests/test_tools_api.py` — Test GET /tools

```python
"""Test untuk GET /tools endpoint."""

import pytest
from fastapi.testclient import TestClient


def test_list_tools(client: TestClient):
    """Test GET /tools mengembalikan daftar tool."""
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert isinstance(data["tools"], list)


def test_list_tools_structure(client: TestClient):
    """Test struktur response tool."""
    response = client.get("/api/v1/tools")
    data = response.json()
    if data["tools"]:
        tool = data["tools"][0]
        assert "name" in tool
        assert "description" in tool
        assert "enabled" in tool
        assert "parameters" in tool
```

### Tidak Termasuk

- E2E test dengan browser (Playwright) — bisa ditambahkan nanti
- Load test untuk multiple concurrent tool calls
- Test untuk search engine alternatif (Bing, SerpAPI)

---

## Langkah Implementasi

1. Buat `tests/test_tool_base.py` — test BaseTool, ToolSpec, ToolResult
2. Buat `tests/test_tool_registry.py` — test ToolRegistry
3. Buat `tests/test_web_search.py` — test WebSearchTool (mock DDGS)
4. Buat `tests/test_tool_handler.py` — test ToolHandler
5. Buat `tests/test_prompt_injection.py` — test prompt injection builder
6. Buat `tests/test_tool_integration.py` — test ChatService + tool
7. Buat `tests/test_sse_tool_events.py` — test SSE events
8. Buat `tests/test_tools_api.py` — test GET /tools endpoint
9. Jalankan semua test: `pytest tests/ -v`

---

## Output yang Diharapkan

- 8 file test baru di folder `tests/`
- Coverage untuk semua komponen tool system
- Semua test bisa jalan tanpa koneksi internet

---

## Dependencies

- **Semua task sebelumnya (T01-T17)** — komponen sudah diimplementasi
- **Library**: `pytest`, `pytest-asyncio`, `httpx`, `unittest.mock`

---

## Acceptance Criteria

### Unit Tests
- [ ] Test ToolSpec: valid, invalid name, frozen
- [ ] Test ToolResult: success, error, default values
- [ ] Test BaseTool: cannot instantiate, must implement spec & execute
- [ ] Test ToolRegistry: register, get_specs, execute, error handling
- [ ] Test WebSearchTool: spec, empty query, success (mocked), timeout (mocked)
- [ ] Test ToolHandler: parse native, parse prompt injection, execute loop, max calls
- [ ] Test prompt injection: empty, single tool, multiple tools, native support detection

### Integration Tests
- [ ] Test ChatService + tool: process_message with tools, without tools
- [ ] Test SSE tool events: /hybrid/stream mengirim tool_start/tool_result
- [ ] Test GET /tools: response structure, empty registry

### Quality
- [ ] Semua test menggunakan mock (tidak perlu internet)
- [ ] `pytest tests/ -v` berjalan tanpa error
- [ ] Test coverage > 80% untuk folder `app/tools/` dan `app/ai/tool_handler.py`

---

## Estimasi

**Medium** (~2.5 jam)

| Aktivitas | Durasi |
|-----------|--------|
| test_tool_base.py | 15 menit |
| test_tool_registry.py | 20 menit |
| test_web_search.py | 25 menit |
| test_tool_handler.py | 30 menit |
| test_prompt_injection.py | 15 menit |
| test_tool_integration.py | 25 menit |
| test_sse_tool_events.py | 15 menit |
| test_tools_api.py | 10 menit |
| Run & fix all tests | 15 menit |
