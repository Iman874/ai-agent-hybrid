# Task 10: Testing — Ollama Generator

## Status
[ ] Belum dimulai

## Deskripsi
Buat unit test dan integration test untuk memastikan Ollama generator berfungsi dengan benar, termasuk fallback chain.

## File yang Diubah
- **NEW**: `tests/test_ollama_generator.py`
- **MODIFY**: `tests/conftest.py` (tambah fixture)

## Spesifikasi

### 1. Unit Test: BaseGeneratorProvider

```python
# tests/test_ollama_generator.py

async def test_base_generator_provider_interface():
    """Pastikan semua method abstract terdefinisi."""
    with pytest.raises(TypeError):
        BaseGeneratorProvider()  # Tidak bisa di-instantiate langsung

async def test_gemini_provider_implements_interface(mock_gemini_provider):
    """Pastikan GeminiProvider mengimplementasi BaseGeneratorProvider."""
    assert isinstance(mock_gemini_provider, BaseGeneratorProvider)
    assert mock_gemini_provider.provider_name == "gemini"
    assert await mock_gemini_provider.is_available() is True
```

### 2. Unit Test: OllamaGeneratorProvider

```python
async def test_ollama_generator_provider_init(mock_settings):
    """Test inisialisasi dengan model terpisah."""
    provider = OllamaGeneratorProvider(mock_settings)
    assert provider.provider_name == "ollama"
    assert provider.model == mock_settings.ollama_tor_model

async def test_ollama_generator_fallback_model(mock_settings):
    """Test fallback ke ollama_chat_model jika tor_model kosong."""
    mock_settings.ollama_tor_model = ""
    provider = OllamaGeneratorProvider(mock_settings)
    assert provider.model == mock_settings.ollama_chat_model

async def test_ollama_generator_is_available(mocker):
    """Test is_available() — true jika model terdaftar."""
    mock_client = mocker.AsyncMock()
    mock_client.list.return_value = mocker.MagicMock(
        models=[mocker.MagicMock(model="qwen2.5:7b-instruct")]
    )
    mocker.patch("ollama.AsyncClient", return_value=mock_client)
    
    settings = mocker.MagicMock(ollama_base_url="http://localhost:11434")
    settings.ollama_tor_model = "qwen2.5:7b-instruct"
    
    provider = OllamaGeneratorProvider(settings)
    assert await provider.is_available() is True

async def test_ollama_generator_is_available_false(mocker):
    """Test is_available() — false jika model tidak terdaftar."""
    mock_client = mocker.AsyncMock()
    mock_client.list.return_value = mocker.MagicMock(models=[])
    mocker.patch("ollama.AsyncClient", return_value=mock_client)
    
    settings = mocker.MagicMock(ollama_base_url="http://localhost:11434")
    settings.ollama_tor_model = "nonexistent-model"
    
    provider = OllamaGeneratorProvider(settings)
    assert await provider.is_available() is False

async def test_ollama_generate_stream(mocker):
    """Test streaming generate yield token per token."""
    mock_client = mocker.AsyncMock()
    chunks = [
        {"message": {"content": "## "}, "done": False},
        {"message": {"content": "Judul"}, "done": False},
        {"message": {"content": ""}, "done": True},
    ]
    
    async def mock_chat(**kwargs):
        class AsyncStream:
            def __aiter__(self):
                return iter(chunks).__aiter__()
        return AsyncStream()
    
    mock_client.chat = mock_chat
    mocker.patch("ollama.AsyncClient", return_value=mock_client)
    
    settings = mocker.MagicMock(ollama_base_url="http://localhost:11434")
    settings.ollama_tor_model = "qwen2.5:7b-instruct"
    settings.ollama_tor_temperature = 0.3
    settings.ollama_num_ctx = 4096
    settings.ollama_tor_timeout = 120
    
    provider = OllamaGeneratorProvider(settings)
    tokens = []
    async for token in provider.generate_stream("Buat TOR"):
        tokens.append(token)
    
    assert tokens == ["## ", "Judul"]
```

### 3. Unit Test: GenerateService Provider Resolution

```python
async def test_generate_service_resolve_auto_ollama(mocker):
    """Test auto mode pilih Ollama jika completeness >= 0.8."""
    service = _create_generate_service(mocker)
    session = mocker.MagicMock(completeness_score=0.85)
    service.session_mgr.get.return_value = session
    service.providers["ollama"].is_available.return_value = True
    
    result = await service._resolve_provider("session-1", "auto", "standard")
    assert result == "ollama"

async def test_generate_service_resolve_auto_gemini(mocker):
    """Test auto mode pilih Gemini jika completeness < 0.8."""
    service = _create_generate_service(mocker)
    session = mocker.MagicMock(completeness_score=0.45)
    service.session_mgr.get.return_value = session
    service.providers["gemini"].is_available.return_value = True
    
    result = await service._resolve_provider("session-1", "auto", "standard")
    assert result == "gemini"

async def test_generate_service_fallback_gemini_to_ollama(mocker):
    """Test fallback Gemini → Ollama jika Gemini unavailable."""
    service = _create_generate_service(mocker)
    service.providers["gemini"].is_available.return_value = False
    service.providers["ollama"].is_available.return_value = True
    
    result = await service._resolve_provider("session-1", "gemini", "standard")
    assert result == "ollama"

async def test_generate_service_no_provider_available(mocker):
    """Test error jika semua provider unavailable."""
    service = _create_generate_service(mocker)
    service.providers["gemini"].is_available.return_value = False
    service.providers["ollama"].is_available.return_value = False
    
    with pytest.raises(NoProviderAvailableError):
        await service._resolve_provider("session-1", "auto", "standard")
```

### 4. Integration Test: End-to-End

```python
async def test_ollama_generate_tor_integration(test_client, mocker):
    """Test full flow: chat → READY → generate via Ollama."""
    # Mock chat service return READY_TO_GENERATE
    # Mock Ollama generator return TOR content
    # Verify response contains TOR document with generator="ollama"
    pass

async def test_generate_chat_stream_with_ollama(test_client, mocker):
    """Test SSE streaming generate dari chat via Ollama."""
    # Mock Gemini unavailable
    # Mock Ollama available
    # POST /generate/chat/stream with generator="ollama"
    # Verify SSE events: status → token → done
    pass
```

### 5. Test Fixtures (`tests/conftest.py`)

```python
@pytest.fixture
def mock_ollama_generator_provider(mocker):
    """Mock OllamaGeneratorProvider untuk testing."""
    provider = mocker.AsyncMock(spec=OllamaGeneratorProvider)
    provider.provider_name = "ollama"
    provider.model = "qwen2.5:7b-instruct"
    provider.is_available.return_value = True
    
    async def mock_generate_stream(prompt):
        yield "# TOR Test\nContent"
    
    provider.generate_stream = mock_generate_stream
    provider.generate.return_value = "# TOR Test\nContent"
    return provider
```

## Catatan
- Unit test fokus pada logic routing dan fallback
- Integration test perlu mock Ollama (karena tidak selalu running)
- Pastikan test mencakup semua skenario: auto, gemini, ollama, fallback, no provider
