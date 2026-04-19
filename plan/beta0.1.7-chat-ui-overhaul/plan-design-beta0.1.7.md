# 🎨 Plan Design — Beta 0.1.7: Chat UI Overhaul & Model Selector

> **Modul**: Chat UI Overhaul + Hybrid/Gemini-Only Chat Mode
> **Versi**: beta0.1.7
> **Status**: Plan Ready
> **Prasyarat**: beta0.1.6 selesai (Document-to-TOR + PDF Export)

---

## 1. Ringkasan Modul

Beta 0.1.7 memiliki **dua fokus utama**:

### A. Model Selector — Pilih LLM untuk Chat
User bisa memilih model mana yang digunakan untuk **chat interviewer**:
- **Local LLM (Ollama)** — model lokal seperti `qwen2.5:3b`, berjalan offline
- **Gemini API** — gunakan Gemini langsung sebagai interviewer chat (bukan cuma generator)
- Minimal **satu model harus aktif** untuk chat

Ini berarti Gemini bukan cuma untuk generate TOR (seperti sekarang), tapi juga bisa **menjadi chatbot interviewer** langsung — tanpa butuh Ollama sama sekali.

### B. UI Overhaul — Desain ala ChatGPT
Redesign total UI Streamlit:
- **Sidebar kiri** berisi semua kontrol (model selector, session list, settings)
- **Area chat utama** bersih, sederhana, modern
- Tab-tab Gemini Direct & From Document tetap ada tapi lebih terintegrasi
- Dark theme, minimalis, professional

---

## 2. Perubahan Arsitektur

### 2.1 Current Flow (sekarang)

```
User Chat → Hybrid Endpoint → DecisionEngine
                                    │
                                    ├── ChatService (SELALU pakai Ollama lokal)
                                    │         └── OllamaProvider.chat()
                                    │
                                    └── GenerateService (SELALU pakai Gemini)
                                              └── GeminiProvider.generate()
```

**Masalah**: Chat SELALU menggunakan Ollama. Gemini hanya untuk generate TOR.

### 2.2 New Flow (target)

```
User Chat → Hybrid Endpoint → DecisionEngine
                                    │
                                    ├── ChatService (PILIHAN user)
                                    │         ├── OllamaProvider.chat()  ← jika local
                                    │         └── GeminiChatProvider.chat()  ← jika gemini
                                    │
                                    └── GenerateService (SELALU Gemini)
                                              └── GeminiProvider.generate()
```

**Solusi**: ChatService menerima `chat_provider` yang bisa di-swap antara Ollama atau Gemini Chat.

---

## 3. Komponen Baru & Modifikasi

### 3.1 Backend

| File | Tipe | Deskripsi |
|---|---|---|
| `app/ai/base.py` | **MODIFY** | Pastikan interface `BaseLLMProvider` mendukung kedua mode |
| `app/ai/gemini_chat_provider.py` | **NEW** | Wrapper Gemini API untuk mode chat (bukan generate TOR) |
| `app/services/chat_service.py` | **MODIFY** | Accept `chat_provider` parameter, bukan hardcode Ollama |
| `app/core/decision_engine.py` | **MODIFY** | Pass `chat_mode` dari request options |
| `app/models/routing.py` | **MODIFY** | Tambah `chat_mode` di `HybridOptions` |
| `app/models/api.py` | **MODIFY** | Tambah `chat_mode` di `HybridRequest` |
| `app/api/routes/hybrid.py` | **MODIFY** | Forward `chat_mode` ke DecisionEngine |
| `app/api/routes/models.py` | **NEW** | Endpoint `GET /api/v1/models` untuk list available models |
| `app/main.py` | **MODIFY** | Register GeminiChatProvider, expose di app.state |

### 3.2 Frontend

| File | Tipe | Deskripsi |
|---|---|---|
| `streamlit_app.py` | **REWRITE** | Redesign penuh UI ala ChatGPT |

---

## 4. Detail Teknis

### 4.1 GeminiChatProvider (NEW)

```python
# app/ai/gemini_chat_provider.py

class GeminiChatProvider(BaseLLMProvider):
    """Wrapper Gemini API untuk mode chat interviewer."""

    def __init__(self, settings: Settings):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model, ...)
        self.model_name = settings.gemini_model

    async def chat(self, messages: list[dict]) -> dict:
        """
        Konversi messages format Ollama → Gemini chat format.
        Return format sama persis dengan OllamaProvider.chat()
        agar ChatService tidak perlu berubah.
        """
        # Convert messages → Gemini format
        # Call Gemini
        # Return {"content": str, "total_duration": int, "eval_count": int}
```

**Key Design**: Return format SAMA dengan `OllamaProvider.chat()` sehingga `ChatService` tidak perlu perubahan besar — hanya swap provider.

### 4.2 ChatService Modification

```python
# app/services/chat_service.py — perubahan minimal

class ChatService:
    def __init__(
        self,
        ollama: OllamaProvider,
        gemini_chat: GeminiChatProvider,  # NEW
        session_mgr, prompt_builder, parser,
        rag_pipeline=None,
    ):
        self.ollama = ollama
        self.gemini_chat = gemini_chat  # NEW
        ...

    async def process_message(
        self, session_id, message, rag_context=None,
        chat_mode: str = "local",  # NEW: "local" | "gemini"
    ) -> ChatResult:
        ...
        # Step 4: Call LLM berdasarkan mode
        provider = self.gemini_chat if chat_mode == "gemini" else self.ollama
        raw_response = await provider.chat(working_messages)
        ...
```

### 4.3 HybridOptions Extension

```python
# app/models/routing.py

class HybridOptions(BaseModel):
    force_generate: bool = False
    language: str = "id"
    chat_mode: str = "local"  # NEW: "local" | "gemini"
```

### 4.4 Models Endpoint (NEW)

```python
# app/api/routes/models.py

@router.get("/models")
async def list_models(request: Request):
    """Return daftar model yang tersedia."""
    models = []

    # Check Ollama
    try:
        ollama_models = await request.app.state.ollama.list()
        for m in ollama_models:
            models.append({"id": m.name, "type": "local", "status": "available"})
    except:
        models.append({"id": settings.ollama_chat_model, "type": "local", "status": "offline"})

    # Gemini always available if API key exists
    if settings.gemini_api_key:
        models.append({
            "id": settings.gemini_model,
            "type": "gemini",
            "status": "available",
        })

    return {"models": models}
```

### 4.5 UI Redesign — Layout Blueprint

```
┌──────────────────────────────────────────────────────────────────┐
│                    TOR Generator — AI Agent Hybrid                │
├─────────────────────┬────────────────────────────────────────────┤
│                     │                                            │
│  🤖 TOR Generator   │                                            │
│  v0.1.7             │                                            │
│                     │     Welcome!                                │
│  [🔄 New Chat]      │     Pilih mode di sidebar, lalu mulai      │
│                     │     chat untuk membuat TOR.                │
│  ─────────────────  │                                            │
│                     │                                            │
│  ⚙️ Model           │   ┌────────────────────────────────────┐   │
│  ┌───────────────┐  │   │ 🧑 User                            │   │
│  │ ○ Local LLM   │  │   │ Buatkan TOR workshop AI...         │   │
│  │   qwen2.5:3b  │  │   └────────────────────────────────────┘   │
│  │ ● Gemini API  │  │                                            │
│  │   gemini-2.5  │  │   ┌────────────────────────────────────┐   │
│  └───────────────┘  │   │ 🤖 Assistant                       │   │
│                     │   │ Tentu! Beberapa pertanyaan:...      │   │
│  ─────────────────  │   └────────────────────────────────────┘   │
│                     │                                            │
│  📊 Progress        │                                            │
│  ████████░░ 75%     │                                            │
│  Turn: 3 | CHATTING │                                            │
│                     │                                            │
│  ─────────────────  │                                            │
│                     │                                            │
│  📋 Fields          │                                            │
│  ✅ judul           │                                            │
│  ✅ latar_belakang  │                                            │
│  ✅ tujuan          │                                            │
│  ❌ ruang_lingkup   │                                            │
│  ❌ output          │                                            │
│  ❌ timeline        │                                            │
│  ⬜ estimasi_biaya  │                                            │
│                     │                                            │
│  ─────────────────  │   ┌────────────────────────────────────┐   │
│                     │   │ Ketik pesan Anda...            📎 │   │
│  🛠️ Tools           │   └────────────────────────────────────┘   │
│  [🚀 Generate TOR]  │                                            │
│  [📄 From Document] │                                            │
│  [🚀 Gemini Direct] │                                            │
│                     │                                            │
│  ─────────────────  │                                            │
│  🔧 System          │                                            │
│  API: 🟢 Connected  │                                            │
│  Session: a1b2c3... │                                            │
│                     │                                            │
└─────────────────────┴────────────────────────────────────────────┘
```

**Prinsip desain** (revisi Task 10):
1. **Sidebar kiri** = model selector, progress, fields, force generate, system status
2. **Area utama** = tabs [💬 Chat] [🚀 Direct] [📄 Dokumen] — form butuh ruang lebar
3. **Tools berat** (forms, file upload) = di main area tabs, BUKAN sidebar (terlalu sempit)
4. **Theme** = via `.streamlit/config.toml` (native dark), CSS minimal hanya untuk custom elements
5. **Minimalis** = jangan override komponen native Streamlit, biarkan framework handle

### 4.6 Mode Switching di Sidebar

```
⚙️ Chat Model
┌────────────────────┐
│  ○ Local LLM       │  ← radio button
│    Model: [▼ qwen2.5:3b ]  ← selectbox (list dari Ollama)
│                    │
│  ● Gemini API      │  ← radio button
│    Model: gemini-2.5-flash  ← fixed, dari .env
└────────────────────┘

⚠️ Switching model mid-session = start new session
```

---

## 5. Theming Strategy (revisi Task 10)

### 5.1 Native Streamlit Config (PRIMARY)

```toml
# .streamlit/config.toml
[theme]
base = "dark"
primaryColor = "#58a6ff"
backgroundColor = "#0d1117"
secondaryBackgroundColor = "#161b22"
textColor = "#e6edf3"
font = "sans serif"
```

Ini mengatur 90% theming tanpa CSS injection dan **tidak merusak** komponen native.

### 5.2 CSS Injection (MINIMAL — hanya custom elements)

**BOLEH** di-override:
- Chat bubble border radius
- Custom badge/label styling
- Welcome container
- Scrollbar
- Hide Streamlit branding (header/footer/menu)

**JANGAN** override:
- `*` selector (font-family) — merusak icon rendering
- Expander internal styles — merusak arrow icons
- Radio button internal — merusak checked states
- Form native styles — merusak layout
- Input/textarea native — sudah handled oleh config.toml

---

## 6. Flow Lengkap (dengan Model Selector)

```
User:
  1. Buka app → sidebar menampilkan model selector
  2. Pilih "Gemini API" sebagai chat model
  3. Ketik: "Buatkan TOR workshop AI"
  4. Chat berjalan via Gemini (bukan Ollama)
  5. Saat data cukup → Generate TOR (tetap via Gemini generator)

Backend:
  1. Request masuk: {message, options: {chat_mode: "gemini"}}
  2. DecisionEngine → ChatService.process_message(chat_mode="gemini")
  3. ChatService pakai GeminiChatProvider.chat() (bukan OllamaProvider)
  4. Response sama persis formatnya → UI tidak berubah
  5. Saat generate → tetap pakai GeminiProvider.generate()
```

---

## 7. Batasan & Catatan

| Item | Detail |
|---|---|
| **Switch mid-session** | Ganti model = session baru (data reset). Ini untuk menghindari inconsistency. |
| **Gemini Chat cost** | Gemini Chat mode menambah API calls. Cost control tetap berlaku. |
| **Ollama offline** | Jika Ollama offline, radio button Local LLM di-disable otomatis. |
| **Format JSON** | GeminiChatProvider harus bisa output JSON terstruktur sama seperti Ollama. Ini challenge — Gemini mungkin butuh prompt adjustment. |
| **Prompt compatibility** | System prompt dan chat format harus compatible untuk kedua provider. |

---

## 8. Task Breakdown

| # | Task | Status | Deskripsi | Estimasi |
|---|---|---|---|---|
| 1 | `task01-gemini-chat-provider.md` | ✅ Done | Buat `GeminiChatProvider` — wrapper Gemini untuk mode chat | Medium |
| 2 | `task02-chat-service-refactor.md` | ✅ Done | Refactor `ChatService` untuk terima `chat_mode` parameter | Medium |
| 3 | `task03-api-model-selector.md` | ✅ Done | Tambah `chat_mode` di `HybridOptions`, endpoint `GET /models` | Low |
| 4 | `task04-decision-engine-update.md` | ✅ Done | Update `DecisionEngine.route()` forward `chat_mode` | Low |
| 5 | `task05-ui-redesign-layout.md` | ✅ Done | Redesign layout Streamlit: sidebar controls + clean chat area | High |
| 6 | `task06-ui-model-selector.md` | ✅ Done | Implementasi model selector (radio + selectbox) di sidebar | Medium |
| 7 | `task07-ui-theme-css.md` | ⚠️ Broken | Custom CSS: override terlalu agresif, merusak native components | Medium |
| 8 | `task08-ui-tools-integration.md` | ⚠️ Broken | Gemini Direct & From Document di sidebar terlalu sempit | Medium |
| 9 | `task09-testing.md` | 🔲 Pending | Testing end-to-end | Medium |
| 10 | `task10-fix-ui-theme.md` | 🔲 Pending | **FIX**: Native theming + minimal CSS + kembalikan tabs di main area | Medium |

### Dependency Graph
```
Backend (DONE):
  Task 01 ─► Task 02 ─► Task 04 ◄── Task 03

Frontend:
  Task 05 ─► Task 06 ─► Task 07 ─► Task 08 ─► Task 10 (FIX) ─► Task 09
                                                  │
                              Masalah: CSS terlalu agresif + forms di sidebar terlalu sempit
```

---

## 9. Hubungan dengan Modul Sebelumnya

```
Beta 0.1.0: Chat Engine (Ollama)          ← ENHANCED: sekarang multi-provider
Beta 0.1.2: Gemini Generator              ← UNCHANGED: tetap generate via Gemini
Beta 0.1.3: RAG Pipeline                  ← UNCHANGED: tetap sebagai context provider
Beta 0.1.4: Decision Engine               ← MODIFIED: forward chat_mode
Beta 0.1.5: Streamlit UI                  ← REWRITTEN: new layout
Beta 0.1.6: Document-to-TOR              ← PRESERVED: diintegrasikan ke sidebar tools
Beta 0.1.7: THIS — Chat UI + Model Select
```

---

> **Modul ini mengubah flow chat dari single-provider (Ollama only) menjadi multi-provider (Ollama ATAU Gemini), plus redesign UI total menjadi modern ChatGPT-like interface.**
