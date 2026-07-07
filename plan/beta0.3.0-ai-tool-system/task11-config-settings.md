# Task 11 — Tool System Configuration & Initialization

## Deskripsi

Menambahkan konfigurasi untuk Tool System ke `Settings` di `app/config.py` dan menginisialisasi semua komponen tool di `app/main.py`. Task ini menghubungkan semua komponen backend yang sudah dibuat — ToolRegistry, WebSearchTool, ToolHandler — ke dalam aplikasi yang berjalan.

---

## Tujuan Teknis

- Semua pengaturan tool bisa dikonfigurasi via environment variables / `.env`
- `ToolRegistry` diinisialisasi saat aplikasi startup
- `WebSearchTool` didaftarkan ke registry jika diaktifkan
- `ToolHandler` diinisialisasi dengan registry
- Semua komponen tersedia di `app.state` untuk diakses oleh routes dan services
- `ChatService` menerima `tool_handler` dan `tool_registry` saat inisialisasi

---

## Scope

### Termasuk

- Modifikasi `app/config.py` — tambah settings:
  ```python
  # === Tool System ===
  tool_web_search_enabled: bool = True      # Aktifkan web search tool
  tool_web_search_provider: str = "duckduckgo"  # duckduckgo | bing | serpapi
  tool_web_search_max_results: int = 5      # Default max results
  tool_max_calls_per_turn: int = 3          # Max tool calls per chat turn
  bing_search_api_key: str = ""             # Bing API key (opsional)
  serpapi_api_key: str = ""                 # SerpAPI key (opsional)
  ```

- Modifikasi `app/main.py` — di dalam `lifespan()` startup:
  1. Import komponen tool:
     ```python
     from app.tools.registry import ToolRegistry
     from app.tools.web_search import WebSearchTool
     from app.ai.tool_handler import ToolHandler
     ```
  2. Inisialisasi `ToolRegistry`:
     ```python
     tool_registry = ToolRegistry()
     ```
  3. Daftarkan `WebSearchTool` jika enabled:
     ```python
     if settings.tool_web_search_enabled:
         web_search_tool = WebSearchTool()
         tool_registry.register(web_search_tool)
         logger.info(f"WebSearchTool registered (provider={settings.tool_web_search_provider})")
     ```
  4. Inisialisasi `ToolHandler`:
     ```python
     tool_handler = ToolHandler(
         tool_registry=tool_registry,
         max_calls=settings.tool_max_calls_per_turn,
     )
     ```
  5. Simpan ke `app.state`:
     ```python
     app.state.tool_registry = tool_registry
     app.state.tool_handler = tool_handler
     ```
  6. Inject ke `ChatService` saat inisialisasi:
     ```python
     chat_service = ChatService(
         ollama=ollama_provider,
         session_mgr=session_mgr,
         prompt_builder=prompt_builder,
         parser=response_parser,
         rag_pipeline=rag_pipeline,
         gemini_chat=gemini_chat_provider,
         tool_handler=tool_handler,      # NEW
         tool_registry=tool_registry,    # NEW
     )
     ```

- Pastikan settings bisa di-override via `.env`:
  ```
  TOOL_WEB_SEARCH_ENABLED=true
  TOOL_WEB_SEARCH_PROVIDER=duckduckgo
  TOOL_MAX_CALLS_PER_TURN=3
  ```

### Tidak Termasuk

- Implementasi tool (Task 03)
- API endpoint (Task 10)
- Frontend settings UI (Task 16)

---

## Langkah Implementasi

### Langkah 1: Update `app/config.py`

```python
# Di app/config.py — tambah di class Settings

class Settings(BaseSettings):
    # ... existing settings ...
    
    # === Tool System ===
    tool_web_search_enabled: bool = True
    tool_web_search_provider: str = "duckduckgo"
    tool_web_search_max_results: int = 5
    tool_max_calls_per_turn: int = 3
    bing_search_api_key: str = ""
    serpapi_api_key: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### Langkah 2: Update `app/main.py`

```python
# Di app/main.py — di dalam lifespan() startup

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown."""
    settings = Settings()
    app.state.settings = settings
    app.state.start_time = time.time()

    logger.info(f"Starting {settings.app_name}...")

    # Init database
    await init_db(settings.session_db_path)
    logger.info("Database initialized")

    # Init services
    ollama_provider = OllamaProvider(settings)
    session_mgr = SessionManager(settings.session_db_path)
    app.state.session_mgr = session_mgr

    # Init RAG Pipeline
    from app.rag.pipeline import RAGPipeline
    rag_pipeline = RAGPipeline(settings)
    app.state.rag_pipeline = rag_pipeline

    # Init Gemini & Generator components
    from app.ai.gemini_provider import GeminiProvider
    from app.ai.gemini_chat_provider import GeminiChatProvider
    from app.ai.ollama_generator_provider import OllamaGeneratorProvider
    from app.core.gemini_prompt_builder import GeminiPromptBuilder
    from app.core.ollama_prompt_builder import OllamaPromptBuilder
    from app.core.post_processor import PostProcessor
    from app.core.cost_controller import CostController
    from app.core.style_extractor import StyleExtractor
    from app.core.style_manager import StyleManager
    from app.db.repositories.cache_repo import TORCache
    from app.db.repositories.doc_generation_repo import DocGenerationRepo
    from app.services.generate_service import GenerateService

    # === TOOL SYSTEM INITIALIZATION ===
    from app.tools.registry import ToolRegistry
    from app.tools.web_search import WebSearchTool
    from app.ai.tool_handler import ToolHandler

    tool_registry = ToolRegistry()

    if settings.tool_web_search_enabled:
        web_search_tool = WebSearchTool()
        tool_registry.register(web_search_tool)
        logger.info(
            f"WebSearchTool registered: "
            f"provider={settings.tool_web_search_provider}, "
            f"max_results={settings.tool_web_search_max_results}"
        )
    else:
        logger.info("WebSearchTool is disabled via configuration")

    tool_handler = ToolHandler(
        tool_registry=tool_registry,
        max_calls=settings.tool_max_calls_per_turn,
    )
    logger.info(f"ToolHandler initialized: max_calls={settings.tool_max_calls_per_turn}")

    # Save to app state
    app.state.tool_registry = tool_registry
    app.state.tool_handler = tool_handler
    # === END TOOL SYSTEM INIT ===

    # Init Prompt Builder & Response Parser
    prompt_builder = PromptBuilder()
    response_parser = ResponseParser()

    # Init ChatService — dengan tool support
    from app.services.chat_service import ChatService
    chat_service = ChatService(
        ollama=ollama_provider,
        session_mgr=session_mgr,
        prompt_builder=prompt_builder,
        parser=response_parser,
        rag_pipeline=rag_pipeline,
        gemini_chat=gemini_chat_provider,
        tool_handler=tool_handler,       # NEW
        tool_registry=tool_registry,     # NEW
    )
    app.state.chat_service = chat_service
    logger.info("ChatService initialized with tool support")

    # ... (sisanya sama) ...
```

### Langkah 3: Validasi

```bash
# Test startup — harus bisa jalan tanpa error
uvicorn app.main:app --reload

# Cek log — harus ada:
# "WebSearchTool registered: provider=duckduckgo, max_results=5"
# "ToolHandler initialized: max_calls=3"
# "ChatService initialized with tool support"

# Test endpoint
curl http://localhost:8000/api/v1/tools
# Harus return daftar tool

# Test dengan .env override
echo "TOOL_WEB_SEARCH_ENABLED=false" >> .env
# Restart — WebSearchTool tidak terdaftar
# GET /tools → {"tools": []}
```

---

## Output yang Diharapkan

- Settings tool bisa dikonfigurasi via `.env`
- `ToolRegistry` terinisialisasi saat startup
- `WebSearchTool` terdaftar jika `tool_web_search_enabled=True`
- `ToolHandler` terinisialisasi dengan registry
- Semua komponen tersedia di `app.state`
- `ChatService` menerima tool_handler dan tool_registry

---

## Dependencies

- **Task 02 (Tool Registry)** — `ToolRegistry`
- **Task 03 (WebSearchTool)** — `WebSearchTool`
- **Task 04 (Tool Handler)** — `ToolHandler`

---

## Acceptance Criteria

### Configuration
- [ ] Settings tool ada di `config.py` dengan default values
- [ ] Settings bisa di-override via environment variables
- [ ] `.env` file bisa mengontrol tool system

### Initialization
- [ ] `ToolRegistry` diinisialisasi di `main.py` saat startup
- [ ] `WebSearchTool` terdaftar jika `tool_web_search_enabled=True`
- [ ] `WebSearchTool` TIDAK terdaftar jika `tool_web_search_enabled=False`
- [ ] `ToolHandler` diinisialisasi dengan `max_calls` dari settings
- [ ] Semua komponen tersimpan di `app.state`
- [ ] `ChatService` menerima `tool_handler` dan `tool_registry`

### Logging
- [ ] Registrasi WebSearchTool di-log dengan INFO
- [ ] WebSearchTool disabled di-log dengan INFO
- [ ] ToolHandler initialization di-log dengan INFO
- [ ] ChatService tool support di-log dengan INFO

---

## Estimasi

**Low** (~45 menit)

| Aktivitas | Durasi |
|-----------|--------|
| Update config.py | 10 menit |
| Update main.py — tool init | 20 menit |
| Update ChatService init | 10 menit |
| Validasi & testing | 15 menit |
