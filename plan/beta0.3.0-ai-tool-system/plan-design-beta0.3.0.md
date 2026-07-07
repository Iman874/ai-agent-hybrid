# Beta 0.3.0 — AI Tool System (Internet Search Skill)

## 1. Ringkasan

Saat ini AI (Ollama & Gemini) hanya bisa merespon berdasarkan **pengetahuan internal** (training data) dan **konteks RAG** (dokumen lokal). AI **tidak bisa** mencari informasi terbaru dari internet — sehingga:

- Data yang usang/tidak ada di training data → AI mengarang (halusinasi)
- Informasi real-time (berita, harga, regulasi terbaru) → tidak bisa diakses
- TOR yang membutuhkan data eksternal → kualitasnya rendah

**Beta 0.3.0** menambahkan **Tool System** — sebuah framework yang memungkinkan AI memanggil "skill" (tools) eksternal. **Skill pertama** yang akan diimplementasikan adalah **Internet Search** — AI bisa mencari informasi dari web jika diberikan akses.

> **Konsep**: Sama seperti *Function Calling* di OpenAI, *Tool Use* di Anthropic, atau *Tools* di Ollama — LLM memutuskan KAPAN perlu memanggil tool, lalu hasil tool dikembalikan ke LLM untuk diproses lebih lanjut.

---

## 2. Analisis Masalah

### 2.1 Kondisi Saat Ini

```
User: "Buatkan TOR tentang AI untuk sektor kesehatan di Indonesia tahun 2025"

AI (Ollama/Gemini):
  ┌─────────────────────────────────────────────┐
  │ Hanya punya training data sampai 2024       │
  │ Tidak tahu regulasi terbaru                 │
  │ Tidak tahu statistik kesehatan 2025         │
  │ → Halusinasi angka, kebijakan, data         │
  └─────────────────────────────────────────────┘
```

### 2.2 Dampak

| # | Problem | Dampak |
|---|---------|--------|
| 1 | **Data usang** | TOR menggunakan informasi kadaluarsa |
| 2 | **Halusinasi fakta** | AI mengarang statistik, kebijakan, nama |
| 3 | **Tidak bisa verifikasi** | User harus cek manual semua klaim |
| 4 | **TOR tidak kontekstual** | Tidak bisa menyesuaikan dengan situasi terkini |
| 5 | **Keterbatasan domain** | Hanya bisa domain yang ada di training data |

### 2.3 Root Cause

- LLM adalah **static knowledge model** — pengetahuannya terpotong pada tanggal training
- Tidak ada mekanisme untuk LLM **memanggil sumber eksternal** saat membutuhkan informasi
- Arsitektur saat ini: `User → LLM → Response` (linear, tanpa tool invocation)

---

## 3. Konsep: Tool Calling / Function Calling

### 3.1 Apa itu Tool Calling?

Tool Calling adalah kemampuan LLM untuk **memanggil fungsi eksternal** selama generasi response. Alurnya:

```
User: "Cari berita terbaru tentang AI"

1. LLM menerima prompt + daftar tool yang tersedia
2. LLM memutuskan: "Saya perlu mencari informasi → panggil tool web_search"
3. LLM mengembalikan tool_call: {"name": "web_search", "arguments": {"query": "AI terbaru 2025"}}
4. Sistem EKSEKUSI tool tersebut (search internet)
5. HASIL tool dikirim kembali ke LLM
6. LLM merespon user dengan informasi dari tool
```

### 3.2 Tool vs RAG — Beda Peran

| Aspek | RAG (Existing) | Tool System (New) |
|-------|----------------|-------------------|
| **Sumber data** | Dokumen lokal (TOR lama) | Internet real-time |
| **Kapan dipanggil** | Setiap chat (otomatis) | Saat LLM memutuskan perlu |
| **Inisiatif** | Sistem (pasif) | LLM (aktif) |
| **Konteks** | Spesifik domain TOR | General information |
| **Update data** | Manual (ingest) | Real-time |
| **Biaya** | Embedding murah | API search (bisa gratis) |

> **Keduanya komplementer**: RAG untuk pengetahuan domain internal, Tool untuk informasi eksternal real-time.

---

## 4. Keputusan Arsitektur (FINAL — TIDAK BOLEH DIUBAH)

### 4.1 Tool Abstraction: `BaseTool`

Semua tool WAJIB mengimplementasi abstract class berikut:

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel


class ToolSpec(BaseModel):
    """Spesifikasi tool yang dikirim ke LLM."""
    name: str                              # Nama tool (snake_case)
    description: str                       # Deskripsi untuk LLM
    parameters: dict                       # JSON Schema parameter


class ToolResult(BaseModel):
    """Hasil eksekusi tool."""
    tool_name: str
    success: bool
    data: str                              # String result untuk LLM
    error: str | None = None
    metadata: dict = {}                    # Durasi, sumber, dll


class BaseTool(ABC):
    """Abstract base class untuk semua tool/skill."""

    @property
    @abstractmethod
    def spec(self) -> ToolSpec:
        """Spesifikasi tool — dikirim ke LLM agar tahu cara pakai."""
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Eksekusi tool dengan arguments dari LLM."""
        ...
```

**Rules:**
- Setiap tool punya `spec` yang mendeskripsikan diri ke LLM (name, description, parameters JSON Schema)
- `execute()` menerima arguments sesuai spec.parameters
- `ToolResult.data` adalah string — siap untuk di-inject ke konteks LLM
- Tool TIDAK BOLEH memiliki side effect ke session/state — murni ambil data

### 4.2 Tool Registry

Semua tool didaftarkan di satu tempat:

```python
class ToolRegistry:
    """Registry semua tool yang tersedia untuk LLM."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Daftarkan tool."""
        self._tools[tool.spec.name] = tool

    def get_specs(self) -> list[ToolSpec]:
        """Kembalikan specs semua tool — untuk dikirim ke LLM."""
        return [t.spec for t in self._tools.values()]

    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Eksekusi tool by name."""
        if name not in self._tools:
            return ToolResult(
                tool_name=name,
                success=False,
                data="",
                error=f"Tool '{name}' tidak ditemukan",
            )
        return await self._tools[name].execute(**kwargs)
```

**Rules:**
- `ToolRegistry` adalah **singleton** di aplikasi — diinisialisasi di `main.py`
- Tool bisa ditambah/dihapus tanpa mengubah kode provider
- Frontend bisa query `GET /tools` untuk tahu tool apa yang aktif

### 4.3 WebSearchTool — Implementasi Pertama

```python
class WebSearchTool(BaseTool):
    """Mencari informasi dari internet."""

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="web_search",
            description="Cari informasi terbaru dari internet. "
                        "Gunakan ketika kamu membutuhkan data real-time, "
                        "berita terbaru, statistik terkini, regulasi, "
                        "atau informasi yang mungkin tidak ada di training data-mu.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Kata kunci pencarian",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Jumlah hasil maksimal (1-10)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        )

    async def execute(self, query: str, max_results: int = 5) -> ToolResult:
        """Eksekusi pencarian internet."""
        try:
            results = await self._search_web(query, max_results)
            return ToolResult(
                tool_name="web_search",
                success=True,
                data=self._format_results(results),
                metadata={
                    "query": query,
                    "result_count": len(results),
                    "source": "web",
                },
            )
        except Exception as e:
            return ToolResult(
                tool_name="web_search",
                success=False,
                data="",
                error=str(e),
            )
```

#### 4.3.1 Backend Search Engine — DuckDuckGo (Default, Gratis)

```
PILIHAN SEARCH ENGINE:
  PRIMARY:   DuckDuckGo (gratis, tanpa API key) — via duckduckgo_search library
  FALLBACK:  Bing Search API (butuh API key) — opsional
  FALLBACK:  SerpAPI (butuh API key) — opsional
  FALLBACK:  Custom search engine — untuk enterprise
```

**Kenapa DuckDuckGo?**
- **Gratis** — tidak perlu API key
- **Tanpa rate limit ketat** — cocok untuk development
- **Privasi** — tidak track user
- **Library Python mature**: `duckduckgo_search`

**Implementasi:**
```python
from duckduckgo_search import DDGS

async def _search_web(self, query: str, max_results: int = 5) -> list[dict]:
    """Search via DuckDuckGo (async wrapper)."""
    def _sync_search():
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))

    results = await asyncio.to_thread(_sync_search)
    return [
        {
            "title": r["title"],
            "snippet": r["body"],
            "url": r["href"],
        }
        for r in results
    ]
```

#### 4.3.2 Format Output ke LLM

Hasil search harus diformat agar LLM bisa memprosesnya dengan mudah:

```
=== HASIL PENCARIAN INTERNET ===
Query: "regulasi AI kesehatan Indonesia 2025"

Sumber 1: [Kemenkes RI - Kebijakan AI Kesehatan 2025]
URL: https://kemenkes.go.id/...
Konten: Menteri Kesehatan meluncurkan kebijakan AI untuk layanan kesehatan...
──────────────────────────────────────
Sumber 2: [DetikHealth - AI di RS Indonesia]
URL: https://health.detik.com/...
Konten: 5 rumah sakit di Indonesia sudah mengadopsi AI untuk diagnosis...
──────────────────────────────────────
...
=== AKHIR HASIL PENCARIAN ===
```

**Rules:**
- Setiap sumber punya: title, URL, konten (snippet)
- Dipisah dengan garis pembatas yang jelas
- Ada marker `=== HASIL PENCARIAN INTERNET ===` dan `=== AKHIR HASIL PENCARIAN ===`
- LLM bisa dengan mudah memparsing dan mengutip sumber

### 4.4 Provider Integration — Tool Calling

#### 4.4.1 Strategi: Prompt Injection (Universal)

Karena **Ollama** dan **Gemini** memiliki dukungan tool calling yang berbeda:

| Provider | Tool Calling Native | Strategy |
|----------|-------------------|----------|
| **Ollama** | ✅ Support `tools` parameter di chat API | Bisa native |
| **Gemini** | ✅ Support `tools` / `function_declarations` | Bisa native |
| **Fallback** | — | Prompt injection |

**Keputusan: HYBRID STRATEGY**

```
PRIMARY:   Native tool calling (Ollama tools param / Gemini function_declarations)
            → LLM return tool_call → sistem eksekusi → hasil dikirim balik

FALLBACK:  Prompt injection
            → Deskripsi tool di-inject ke system prompt
            → LLM return teks: [[TOOL_CALL: web_search(query="...")]]
            → Sistem parse teks → eksekusi → hasil di-inject ke konteks
```

**Kenapa hybrid?**
- Ollama dan Gemini modern support native tool calling
- Tapi tidak semua model (terutama local kecil) support format tool calling
- Prompt injection sebagai fallback universal

#### 4.4.2 Native Tool Calling — Ollama

```python
# Di OllamaProvider.chat()
tools_specs = tool_registry.get_specs()
tools_payload = [
    {
        "type": "function",
        "function": {
            "name": t.name,
            "description": t.description,
            "parameters": t.parameters,
        }
    }
    for t in tools_specs
]

# Kirim ke Ollama dengan tools parameter
response = await self.client.chat(
    model=self.model,
    messages=messages,
    tools=tools_payload,  # <-- Tool definitions
    options={...},
)
```

**Ollama Response dengan Tool Call:**
```json
{
  "message": {
    "role": "assistant",
    "content": "",
    "tool_calls": [
      {
        "function": {
          "name": "web_search",
          "arguments": {"query": "regulasi AI kesehatan Indonesia 2025"}
        }
      }
    ]
  }
}
```

#### 4.4.3 Native Tool Calling — Gemini

```python
# Di GeminiChatProvider
tools_payload = [
    {
        "function_declarations": [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in tool_registry.get_specs()
        ]
    }
]

# Kirim ke Gemini dengan tools
self.model = genai.GenerativeModel(
    model_name=settings.gemini_model,
    tools=tools_payload,
)
```

#### 4.4.4 Tool Call Execution Loop

Setelah LLM memanggil tool, sistem harus:

```
1. Parse tool_call dari response LLM
2. Eksekusi tool via ToolRegistry
3. Inject hasil tool ke messages:
   [
     ...messages sebelumnya...,
     {"role": "assistant", "content": "", "tool_calls": [...]},
     {"role": "tool", "content": "<hasil search>", "name": "web_search"},
   ]
4. Kirim BALIK ke LLM untuk response final
5. LLM merespon user dengan informasi dari tool
```

**MAX TOOL CALLS PER TURN:**
```
Maximum tool calls per turn: 3
  → Mencegah infinite loop tool calling
  → Jika > 3, force stop dan return error ke user
```

### 4.5 Prompt Injection Fallback (Universal)

Untuk model yang tidak support native tool calling:

```python
# Di system prompt, tambahkan:
TOOL_DESCRIPTION = """
Anda memiliki akses ke tool berikut:

## web_search
Deskripsi: Cari informasi terbaru dari internet.
Parameter:
  - query (string, required): Kata kunci pencarian
  - max_results (integer, optional): Jumlah hasil (1-10), default 5

CARA MENGGUNAKAN TOOL:
Jika Anda membutuhkan informasi yang tidak Anda ketahui,
KELUARKAN teks persis dengan format berikut:
[[TOOL_CALL: web_search(query="kata kunci", max_results=5)]]

Setelah tool dieksekusi, hasilnya akan diberikan ke Anda.
Gunakan hasil tersebut untuk merespon user.
"""
```

**Parser untuk Prompt Injection:**
```python
import re

TOOL_CALL_PATTERN = re.compile(
    r'\[\[TOOL_CALL:\s*(\w+)\(([^)]*)\)\]\]'
)

def parse_tool_calls(text: str) -> list[dict]:
    """Parse tool calls dari response LLM (prompt injection mode)."""
    matches = TOOL_CALL_PATTERN.findall(text)
    results = []
    for name, args_str in matches:
        # Parse keyword arguments
        args = {}
        if args_str.strip():
            for pair in args_str.split(","):
                key, _, value = pair.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                args[key] = value
        results.append({"name": name, "arguments": args})
    return results
```

### 4.6 Tool-Aware Chat Service

`ChatService.process_message()` perlu di-update untuk mendukung tool calling:

```
1. Build messages (seperti biasa)
2. Inject tool specs ke messages (native atau prompt injection)
3. Call LLM
4. IF response contains tool_call:
     a. Eksekusi tool
     b. Inject hasil ke messages
     c. Call LLM lagi (dengan hasil tool)
     d. Ulangi sampai max 3x atau tidak ada tool_call lagi
5. Parse final response
6. Return ChatResult (seperti biasa)
```

**Flow Diagram:**
```
User Message
    │
    ▼
Build Messages + Tool Specs
    │
    ▼
Call LLM ─────────────────────┐
    │                          │
    ▼                          │
Ada Tool Call? ──YES──► Execute Tool
    │                          │
    NO                         │
    │                          │
    ▼                          │
Parse Response ◄──────────────┘
    │
    ▼
Return ChatResult
```

### 4.7 Tool Execution Context di Frontend

User perlu tahu bahwa AI sedang menggunakan tool:

```
[Chat Interface]

User: "Cari data terbaru tentang AI di Indonesia"

AI: [Mencari informasi di internet...]  ← Tool indicator
    🔍 web_search("AI Indonesia 2025")
    ✅ Mendapatkan 5 hasil dari internet
    
    Berdasarkan hasil pencarian, berikut data terbaru...
```

**SSE Events untuk Tool:**
```
data: {"type": "tool_start", "tool": "web_search", "args": {"query": "..."}}
data: {"type": "tool_result", "tool": "web_search", "status": "success", "result_count": 5}
data: {"type": "token", "t": "Berdasarkan hasil pencarian..."}
```

**Frontend Component:**
```typescript
// ToolCallIndicator.tsx
interface ToolCallEvent {
  tool: string;
  args: Record<string, unknown>;
  status: "running" | "success" | "error";
  resultCount?: number;
}
```

### 4.8 Konfigurasi & Environment

```python
# Di Settings (config.py)
class Settings(BaseSettings):
    # ... existing settings ...
    
    # === Tool System ===
    tool_web_search_enabled: bool = True
    tool_web_search_provider: str = "duckduckgo"  # duckduckgo | bing | serpapi
    tool_web_search_max_results: int = 5
    tool_max_calls_per_turn: int = 3
    
    # Bing Search API (opsional)
    bing_search_api_key: str = ""
    
    # SerpAPI (opsional)
    serpapi_api_key: str = ""
```

### 4.9 Keamanan & Rate Limiting

| Aspek | Implementasi |
|-------|-------------|
| **Rate limit search** | Max 30 search/menit per session |
| **URL filtering** | Blokir domain berbahaya (optional) |
| **Content safety** | Filter hasil search (optional) |
| **User consent** | Tool hanya aktif jika user setujui |
| **Tool toggle** | User bisa nonaktifkan tool dari frontend |

---

## 5. Arsitektur File & Folder

### 5.1 Backend — File Baru

```
app/
├── tools/                          # [NEW] Folder semua tool
│   ├── __init__.py
│   ├── base.py                     # BaseTool, ToolSpec, ToolResult
│   ├── registry.py                 # ToolRegistry
│   ├── web_search.py               # WebSearchTool (DuckDuckGo)
│   └── errors.py                   # Tool-specific errors
│
├── ai/
│   ├── tool_handler.py             # [NEW] Tool call execution & loop
│   └── ... (existing)
│
├── core/
│   └── capability_resolver.py      # [MODIFY] Tambah tool support capability
│
├── services/
│   └── chat_service.py             # [MODIFY] Integrasi tool calling
│
├── api/
│   └── routes/
│       ├── hybrid.py               # [MODIFY] SSE events untuk tool
│       └── tools.py                # [NEW] GET /tools endpoint
│
├── config.py                       # [MODIFY] Tambah settings tool
└── main.py                         # [MODIFY] Init ToolRegistry
```

### 5.2 Frontend — File Baru/Modifikasi

```
app_frontend/src/
├── api/
│   └── tools.ts                    # [NEW] API client untuk tools
│
├── types/
│   └── api.ts                      # [MODIFY] Tambah ToolSpec, ToolCall types
│
├── stores/
│   └── tool-store.ts               # [NEW] Zustand store untuk tool state
│
├── components/
│   └── chat/
│       ├── ToolCallIndicator.tsx    # [NEW] Indikator tool sedang running
│       └── ChatContainer.tsx        # [MODIFY] Integrasi tool indicator
│
└── i18n/
    └── locales/
        ├── id.ts                   # [MODIFY] Tool-related translations
        └── en.ts                   # [MODIFY]
```

---

## 6. API Specification

### 6.1 New Endpoint: `GET /tools`

```json
// Request
GET /api/v1/tools

// Response
{
  "tools": [
    {
      "name": "web_search",
      "description": "Cari informasi terbaru dari internet...",
      "enabled": true,
      "parameters": {
        "type": "object",
        "properties": {
          "query": { "type": "string", "description": "Kata kunci pencarian" },
          "max_results": { "type": "integer", "description": "Jumlah hasil (1-10)", "default": 5 }
        },
        "required": ["query"]
      }
    }
  ]
}
```

### 6.2 Modified: `POST /hybrid/stream` — New SSE Events

```json
// Tool execution started
data: {"type": "tool_start", "tool": "web_search", "args": {"query": "..."}}

// Tool execution result
data: {"type": "tool_result", "tool": "web_search", "status": "success", "result_count": 5}

// Tool execution error
data: {"type": "tool_error", "tool": "web_search", "error": "Search API timeout"}
```

### 6.3 Modified: `HybridRequest` — Tool Toggle

```typescript
interface HybridRequest {
  session_id: string | null;
  message: string;
  images?: string[];
  options?: {
    // ... existing options ...
    tools_enabled?: boolean;        // [NEW] User bisa nonaktifkan tool
  };
}
```

---

## 7. Data Flow — Skenario Lengkap

### 7.1 Skenario: User Minta TOR dengan Data Internet

```
User: "Buatkan TOR tentang implementasi AI di RS Indonesia tahun 2025"

STEP 1: Chat Service menerima pesan
  ├── Build messages + tool specs
  ├── Call Ollama (local LLM)
  │
STEP 2: Ollama memutuskan perlu search
  ├── Response: tool_call web_search(query="implementasi AI rumah sakit Indonesia 2025")
  │
STEP 3: Sistem eksekusi tool
  ├── ToolRegistry.execute("web_search", query="...")
  ├── DuckDuckGo search → 5 results
  ├── Format hasil → string
  │
STEP 4: Kirim hasil tool ke LLM
  ├── Inject ke messages sebagai "role": "tool"
  ├── Call Ollama lagi (second pass)
  │
STEP 5: Ollama generate response dengan data internet
  ├── Response: teks lengkap dengan informasi dari hasil search
  ├── Parse → ChatResult(status="NEED_MORE_INFO" atau "READY_TO_GENERATE")
  │
STEP 6: Decision Engine routing
  ├── Jika READY → GenerateService → TOR final
  ├── Jika NEED_MORE_INFO → lanjut chat
```

### 7.2 Skenario: Tool Gagal (Timeout/Error)

```
STEP 1: LLM panggil web_search
STEP 2: Tool gagal (timeout / API error)
STEP 3: ToolResult(success=False, error="Search API timeout")
STEP 4: Inject error ke LLM:
  "Pencarian internet gagal: Search API timeout. 
   Gunakan pengetahuan yang Anda miliki."
STEP 5: LLM fallback ke pengetahuan internal
STEP 6: Response tetap diberikan (dengan disclaimer)
```

### 7.3 Skenario: User Nonaktifkan Tool

```
User mengirim tools_enabled=false di options

STEP 1: Tool specs TIDAK dikirim ke LLM
STEP 2: LLM hanya pakai pengetahuan internal + RAG
STEP 3: Sama seperti sistem saat ini (tanpa tool)
```

---

## 8. Daftar Task

| Kode | Task | Layer | Deskripsi | Estimasi |
|------|------|-------|-----------|----------|
| **T01** | `task01-tool-abstraction.md` | Backend | BaseTool, ToolSpec, ToolResult — abstract class & Pydantic models | 1 jam |
| **T02** | `task02-tool-registry.md` | Backend | ToolRegistry — register, get_specs, execute | 1 jam |
| **T03** | `task03-web-search-tool.md` | Backend | WebSearchTool — DuckDuckGo implementation | 2 jam |
| **T04** | `task04-tool-handler.md` | Backend | Tool call execution loop — parse, execute, inject, re-call LLM | 3 jam |
| **T05** | `task05-ollama-tool-integration.md` | Backend | Integrasi native tool calling ke OllamaProvider | 2 jam |
| **T06** | `task06-gemini-tool-integration.md` | Backend | Integrasi function_declarations ke GeminiChatProvider | 2 jam |
| **T07** | `task07-prompt-injection-fallback.md` | Backend | Prompt injection fallback untuk model tanpa native tool calling | 1.5 jam |
| **T08** | `task08-chat-service-update.md` | Backend | Update ChatService.process_message untuk tool loop | 2 jam |
| **T09** | `task09-sse-tool-events.md` | Backend | Tool_start, tool_result, tool_error SSE events di hybrid.py | 1 jam |
| **T10** | `task10-tools-api-endpoint.md` | Backend | GET /tools endpoint + ToolRegistry integration | 30 menit |
| **T11** | `task11-config-settings.md` | Backend | Settings untuk tool (enable, provider, max_calls, dll) | 30 menit |
| **T12** | `task12-frontend-tool-types.md` | Frontend | ToolSpec, ToolCall types + tool-store Zustand | 1 jam |
| **T13** | `task13-frontend-tool-api.md` | Frontend | API client tools.ts + tool store actions | 1 jam |
| **T14** | `task14-tool-call-indicator.md` | Frontend | ToolCallIndicator component — UI tool status | 1.5 jam |
| **T15** | `task15-chat-store-tool-events.md` | Frontend | Update chat-store untuk handle tool_start/tool_result SSE | 1 jam |
| **T16** | `task16-tool-toggle-ui.md` | Frontend | Settings toggle untuk enable/disable tool | 1 jam |
| **T17** | `task17-i18n-tool-keys.md` | Frontend | ID/EN translations untuk tool features | 30 menit |
| **T18** | `task18-testing.md` | Testing | Unit test + integration test untuk tool system | 2 jam |

**Total Estimasi: ~23 jam (~3 hari kerja)**

---

## 9. Dependencies & Prasyarat

### 9.1 Library Baru

```bash
# Backend
duckduckgo_search>=6.0.0    # Web search via DuckDuckGo

# Optional (untuk search engine alternatif)
# bing-search-url-python     # Bing Search API
# google-search-results       # SerpAPI
```

### 9.2 Prasyarat

| # | Prasyarat | Status |
|---|-----------|--------|
| 1 | Beta 0.2.9 (Ollama Generator) — selesai | ✅ |
| 2 | Beta 0.2.8 (Chat Streaming Generate) — selesai | ✅ |
| 3 | SSE infrastructure — sudah ada | ✅ |
| 4 | ChatService + DecisionEngine — sudah ada | ✅ |
| 5 | Frontend Zustand stores — sudah ada | ✅ |

### 9.3 Model Support

| Model | Tool Calling Native | Notes |
|-------|-------------------|-------|
| **qwen2.5:7b-instruct** (Ollama) | ✅ | Support tools parameter |
| **gemini-2.0-flash** (Gemini) | ✅ | Support function_declarations |
| **llama3.2** (Ollama) | ✅ | Support tools |
| **mistral** (Ollama) | ⚠️ | Bergantung versi |
| **Model kecil (< 3B)** | ❌ | Prompt injection fallback |

---

## 10. Future Expansion — Tool Lain

Setelah WebSearchTool, sistem bisa dikembangkan dengan tool lain:

| Tool | Deskripsi | Priority |
|------|-----------|----------|
| **web_search** | Cari informasi internet | 🔴 P0 (Sekarang) |
| **web_scrape** | Ambil konten lengkap dari URL tertentu | 🟡 P1 |
| **calculator** | Kalkulasi matematika presisi tinggi | 🟡 P1 |
| **current_datetime** | Dapatkan tanggal/waktu saat ini | 🟢 P2 |
| **weather** | Cek cuaca lokasi tertentu | 🟢 P2 |
| **document_search** | Search di dokumen internal (RAG via tool) | 🟢 P2 |
| **code_executor** | Eksekusi Python snippet (sandboxed) | 🔴 P0 (Terpisah) |

---

## 11. Risiko & Mitigasi

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| **LLM terlalu sering panggil tool** | Biaya API, latency | Batasi max 3 calls per turn |
| **Tool hasil data tidak akurat** | TOR kualitas rendah | Tampilkan sumber ke user |
| **DuckDuckGo rate limit** | Search gagal | Implementasi caching + fallback provider |
| **Model local tidak support tool calling** | Tool tidak jalan | Prompt injection fallback |
| **Infinite loop tool calling** | Hang | Hard limit 3 calls + timeout |
| **User khawatir privasi** | Tidak mau pakai | Tool toggle + disclaimer |

---

## 12. Testing Strategy

| Level | Fokus | Tools |
|-------|-------|-------|
| **Unit** | BaseTool, ToolRegistry, WebSearchTool | pytest |
| **Unit** | Tool call parser (prompt injection) | pytest |
| **Integration** | ChatService + Tool loop | pytest + mock search |
| **Integration** | SSE events untuk tool | pytest + TestClient |
| **E2E** | Frontend → Backend tool flow | Playwright |
| **Manual** | Berbagai skenario search | Postman + UI |

---

## 13. Kesimpulan

Beta 0.3.0 menghadirkan **Tool System** yang memungkinkan AI (Ollama & Gemini) untuk mencari informasi dari internet secara real-time. Ini adalah lompatan besar dari sistem yang hanya mengandalkan pengetahuan internal dan RAG statis.

**Key Deliverables:**
1. ✅ Tool abstraction framework (`BaseTool`, `ToolRegistry`)
2. ✅ WebSearchTool (DuckDuckGo — gratis, tanpa API key)
3. ✅ Native tool calling (Ollama tools param + Gemini function_declarations)
4. ✅ Prompt injection fallback (untuk model kecil)
5. ✅ Tool execution loop (max 3 calls per turn)
6. ✅ Frontend tool indicator (real-time status)
7. ✅ User toggle (enable/disable tool)
8. ✅ Comprehensive error handling & fallback

**Dampak:**
- TOR yang dihasilkan punya **data real-time** dan **fakta terverifikasi**
- AI bisa menjawab pertanyaan tentang **kejadian terkini**
- Sistem tetap **gratis** (DuckDuckGo) tanpa API key tambahan
- Arsitektur **extensible** — tool baru bisa ditambah tanpa mengubah kode existing
