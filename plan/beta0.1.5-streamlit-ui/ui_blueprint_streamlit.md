# 🎨 UI Blueprint — Streamlit Frontend
# AI Agent Hybrid — TOR Generator

> **Modul**: Streamlit Chat UI
> **Versi**: beta0.1.5
> **Status**: Ready to Implement
> **Estimasi**: 1 hari kerja
> **Prasyarat**: beta0.1.0 s/d beta0.1.4 SEMUA sudah selesai

---

## 1. Rekomendasi Scope

Berdasarkan blueprint utama (Phase 6), saya **merekomendasikan Medium scope + single page** karena:

| Pertimbangan | Keputusan | Alasan |
|---|---|---|
| Kompleksitas | **Single page** | Cukup untuk demo & daily use, tidak overkill |
| Fitur | **Medium** | Chat + sidebar progress + field tracker + download |
| Multi-page? | **Tidak** | RAG admin & health dashboard bisa via API/Swagger dulu |
| Styling | **Streamlit native** | Tidak perlu custom CSS, Streamlit sudah cukup rapi |

### Fitur yang Diimplementasikan

| # | Fitur | Prioritas |
|---|---|---|
| 1 | **Dual-tab mode**: Hybrid Chat + Gemini Direct | ⭐ Must |
| 2 | Chat interface (full conversation) — Tab Hybrid | ⭐ Must |
| 3 | Form input 7 field TOR — Tab Gemini Direct | ⭐ Must |
| 4 | New session button | ⭐ Must |
| 5 | Sidebar: progress & completeness bar | ⭐ Must |
| 6 | Sidebar: filled/missing field tracker | ⭐ Must |
| 7 | TOR preview panel (rendered markdown) — kedua tab | ⭐ Must |
| 8 | Download TOR button (.md) — kedua tab | ⭐ Must |
| 9 | Force generate button | 🔶 Should |
| 10 | Session info display | 🔶 Should |
| 11 | Error handling visual | 🔶 Should |
| 12 | Health status indicator | 💡 Nice to have |

### Fitur yang TIDAK Diimplementasikan

| Fitur | Alasan |
|---|---|
| RAG document manager UI | Pakai `/api/v1/rag/ingest` via script saja |
| PDF export | Ditunda ke roadmap v1.0 |
| Session history / session picker | Ditunda, cukup 1 session per tab |
| Authentication | Ditunda ke roadmap v0.4 |

---

## 2. Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    streamlit_app.py                         │
│                     (port 8501)                             │
│                                                             │
│  ┌──────────────┐  ┌────────────────────────────────────┐  │
│  │   SIDEBAR     │  │          MAIN AREA                  │  │
│  │               │  │                                     │  │
│  │ 🔄 New Sess   │  │  ┌──────────┐  ┌───────────────┐   │  │
│  │ 📊 Progress   │  │  │ 💬 Hybrid │  │ 🚀 Gemini     │   │  │
│  │ 📋 Fields     │  │  │   Chat    │  │   Direct      │   │  │
│  │ 🚀 Force Gen  │  │  ├──────────┤  ├───────────────┤   │  │
│  │ 🔧 System     │  │  │ Chat UI   │  │ Form Input    │   │  │
│  │               │  │  │ Messages  │  │  7 TOR fields │   │  │
│  │               │  │  │ TOR View  │  │ Generate btn  │   │  │
│  │               │  │  │ Download  │  │ TOR Preview   │   │  │
│  │               │  │  └──────────┘  └───────────────┘   │  │
│  └──────────────┘  └────────────────────────────────────┘  │
│                                                             │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP requests
                        ▼
┌────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (port 8000)                │
│                                                             │
│   POST /api/v1/hybrid     ← Tab Hybrid Chat                │
│   POST /api/v1/generate   ← Tab Gemini Direct              │
│   GET  /api/v1/health     ← Sidebar status                 │
└────────────────────────────────────────────────────────────┘
```

### Komunikasi

- **Streamlit → FastAPI**: HTTP via `requests` (sync, karena Streamlit re-run based)
- **Tab Hybrid**: `POST /api/v1/hybrid` (chat + auto-generate)
- **Tab Gemini Direct**: `POST /api/v1/generate` (form → langsung Gemini)
- **Health check**: `GET /api/v1/health` (sidebar status indicator)

---

## 3. Layout Detail

### 3.1 Sidebar

```
┌─────────────────────────────┐
│  🤖 TOR Generator           │
│  ─────────────────────────  │
│                              │
│  [🔄 Percakapan Baru]       │  ← st.button, clears session
│                              │
│  ─── Progress ───            │
│                              │
│  Completeness: 33%           │
│  ████████░░░░░░░░░░░░░░░░░  │  ← st.progress(0.33)
│                              │
│  Turn: 2                     │
│  Status: NEED_MORE_INFO      │
│                              │
│  ─── Fields ───              │
│                              │
│  ✅ judul                    │
│  ✅ latar_belakang           │
│  ❌ tujuan                   │
│  ❌ ruang_lingkup            │
│  ❌ output                   │
│  ❌ timeline                 │
│  ⬜ estimasi_biaya (opsional)│
│                              │
│  ─── Actions ───             │
│                              │
│  [🚀 Force Generate TOR]    │  ← st.button, disabled jika belum mulai
│                              │
│  ─── System ───              │
│  Session: a1b2c3...          │
│  API: 🟢 Connected           │  ← health check result
│  Ollama: 🟢 Up               │
│  Gemini: 🟢 Up               │
│                              │
└─────────────────────────────┘
```

### 3.2 Main Area — Tab Structure

```
┌──────────────────────────────────────────┐
│  ┌──────────────┐  ┌─────────────────┐  │
│  │ 💬 Hybrid     │  │ 🚀 Gemini       │  │  ← st.tabs()
│  │    Chat       │  │    Direct       │  │
│  ├──────────────┘  └─────────────────┤  │
│  │                                    │  │
│  │  (konten aktif sesuai tab)         │  │
│  │                                    │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### 3.3 Tab: 💬 Hybrid Chat

```
┌──────────────────────────────────────┐
│  Chat messages (user ↔ assistant)    │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │ 🧑 User                         │ │
│  │ Buat TOR workshop AI...          │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │ 🤖 Assistant                     │ │
│  │ Berapa lama workshopnya?         │ │
│  └─────────────────────────────────┘ │
│                                       │
│  --- TOR Preview (if generated) ---  │
│  ✅ TOR Berhasil Dibuat!              │
│  📋 Metadata (expander)              │
│  # TERM OF REFERENCE...              │
│  [⬇️ Download TOR (.md)]             │
│  ⚠️ Escalation warning (if any)      │
│                                       │
│  ┌──────────────────────────────┐    │
│  │ Ketik pesan Anda...      [→] │    │
│  └──────────────────────────────┘    │
└──────────────────────────────────────┘
```

### 3.4 Tab: 🚀 Gemini Direct

```
┌──────────────────────────────────────┐
│  🚀 Generate TOR Langsung             │
│  Isi field, Gemini langsung generate  │
│                                       │
│  ┌─────────── FORM ────────────────┐ │
│  │                                  │ │
│  │ Judul Kegiatan *:                │ │  ← st.text_input
│  │ [________________________________]│ │
│  │                                  │ │
│  │ Latar Belakang *:                │ │  ← st.text_area
│  │ [________________________________]│ │
│  │                                  │ │
│  │ Tujuan *:                        │ │  ← st.text_area
│  │ [________________________________]│ │
│  │                                  │ │
│  │ Ruang Lingkup *:                 │ │  ← st.text_area
│  │ [________________________________]│ │
│  │                                  │ │
│  │ Output / Deliverable *:          │ │  ← st.text_area
│  │ [________________________________]│ │
│  │                                  │ │
│  │ Timeline *:                      │ │  ← st.text_input
│  │ [________________________________]│ │
│  │                                  │ │
│  │ Estimasi Biaya (opsional):       │ │  ← st.text_input
│  │ [________________________________]│ │
│  │                                  │ │
│  │ [🚀 Generate TOR]                │ │  ← st.form_submit_button
│  └──────────────────────────────────┘ │
│                                       │
│  --- TOR Preview (if generated) ---  │
│  ✅ TOR Berhasil Dibuat!              │
│  📋 Metadata (expander)              │
│  # TERM OF REFERENCE...              │
│  [⬇️ Download TOR (.md)]             │
│                                       │
└──────────────────────────────────────┘
```

---

## 4. State Management

Streamlit menggunakan `st.session_state` untuk menyimpan data antar rerun:

```python
# State yang di-track:
st.session_state = {
    # === Tab Hybrid ===
    "session_id": str | None,          # session_id dari API
    "messages": [                       # chat history untuk render
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
    ],
    "current_state": {                  # dari API response.state
        "status": "NEED_MORE_INFO",
        "turn_count": 2,
        "completeness_score": 0.33,
        "filled_fields": ["judul", "latar_belakang"],
        "missing_fields": ["tujuan", "ruang_lingkup", "output", "timeline"],
    },
    "tor_document": None,              # TORDocument dari API (Hybrid)
    "escalation_info": None,           # EscalationInfo dari API

    # === Tab Gemini Direct ===
    "direct_tor": None,                # TOR result dari Gemini Direct
}
```

### State Flow

```
User Opens App
    │
    ├─► session_id = None
    ├─► messages = []
    ├─► current_state = default empty
    │
    User Types Message
    │
    ├─► POST /api/v1/hybrid { message, session_id }
    │
    ├─► response.type == "chat"
    │       ├─► session_id = response.session_id
    │       ├─► messages.append(user + assistant)
    │       ├─► current_state = response.state
    │       └─► rerun → sidebar updates progress
    │
    ├─► response.type == "generate"
    │       ├─► messages.append(user + assistant)
    │       ├─► tor_document = response.tor_document
    │       ├─► escalation_info = response.escalation_info
    │       ├─► current_state.status = "COMPLETED"
    │       └─► rerun → TOR preview appears
    │
    User Clicks "Percakapan Baru"
    │
    └─► Reset semua state → fresh start
```

---

## 5. API Integration

### 5.1 Helper Functions

```python
import requests

API_URL = "http://localhost:8000/api/v1"

def send_message(session_id: str | None, message: str, options: dict = None) -> dict:
    """Kirim pesan ke hybrid endpoint."""
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    if options:
        payload["options"] = options

    try:
        resp = requests.post(f"{API_URL}/hybrid", json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "Backend tidak bisa dihubungi. Pastikan server berjalan."}
    except requests.Timeout:
        return {"error": "Request timeout. LLM mungkin sedang sibuk."}
    except requests.HTTPError as e:
        error_data = e.response.json() if e.response else {}
        return {"error": error_data.get("error", {}).get("message", str(e))}


def check_health() -> dict:
    """Cek status backend."""
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        return resp.json()
    except Exception:
        return {"status": "unreachable"}


def force_generate(session_id: str) -> dict:
    """Force generate TOR tanpa validasi completeness."""
    return send_message(session_id, "", options={"force_generate": True})
```

### 5.2 Response Handling

```python
def handle_response(data: dict):
    """Process API response dan update session state."""
    if "error" in data:
        st.error(f"❌ {data['error']}")
        return

    # Update session state
    st.session_state.session_id = data["session_id"]
    st.session_state.current_state = data["state"]

    # Chat message
    st.session_state.messages.append({
        "role": "assistant",
        "content": data["message"],
    })

    # TOR generated?
    if data.get("tor_document"):
        st.session_state.tor_document = data["tor_document"]

    # Escalation?
    if data.get("escalation_info"):
        st.session_state.escalation_info = data["escalation_info"]
```

---

## 6. Pseudocode Lengkap

```python
import streamlit as st
import requests

API_URL = "http://localhost:8000/api/v1"

# --- Page Config ---
st.set_page_config(
    page_title="TOR Generator — AI Agent Hybrid",
    page_icon="🤖",
    layout="wide",
)

# --- Init Session State ---
if "session_id" not in st.session_state:
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.current_state = {
        "status": "NEW",
        "turn_count": 0,
        "completeness_score": 0.0,
        "filled_fields": [],
        "missing_fields": [],
    }
    st.session_state.tor_document = None
    st.session_state.escalation_info = None


# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.title("🤖 TOR Generator")
    st.caption("AI Agent Hybrid v0.1.0")

    # New Session Button
    if st.button("🔄 Percakapan Baru", use_container_width=True):
        for key in ["session_id", "messages", "current_state", "tor_document", "escalation_info"]:
            del st.session_state[key]
        st.rerun()

    st.divider()

    # Progress Section
    state = st.session_state.current_state
    st.subheader("📊 Progress")
    score = state["completeness_score"]
    st.progress(score, text=f"Completeness: {score:.0%}")
    col1, col2 = st.columns(2)
    col1.metric("Turn", state["turn_count"])
    col2.metric("Status", state["status"][:12])

    st.divider()

    # Field Tracker
    st.subheader("📋 Field Tracker")
    REQUIRED_FIELDS = ["judul", "latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"]
    OPTIONAL_FIELDS = ["estimasi_biaya"]

    for field in REQUIRED_FIELDS:
        if field in state.get("filled_fields", []):
            st.markdown(f"✅ **{field}**")
        else:
            st.markdown(f"❌ {field}")

    for field in OPTIONAL_FIELDS:
        if field in state.get("filled_fields", []):
            st.markdown(f"✅ **{field}** _(opsional)_")
        else:
            st.markdown(f"⬜ {field} _(opsional)_")

    st.divider()

    # Force Generate
    if st.session_state.session_id:
        if st.button("🚀 Force Generate TOR", use_container_width=True):
            # ... handle force generate ...
            pass

    st.divider()

    # System Status
    st.subheader("🔧 System")
    if st.session_state.session_id:
        st.text(f"Session: {st.session_state.session_id[:8]}...")
    health = check_health()
    if health.get("status") == "healthy":
        st.success("API: 🟢 Connected")
    elif health.get("status") == "unreachable":
        st.error("API: 🔴 Offline")
    else:
        st.warning(f"API: 🟡 {health.get('status')}")


# ============================================
# MAIN AREA
# ============================================
st.title("💬 AI TOR Generator")
st.caption("Ceritakan kebutuhan Anda, AI akan bantu menyusun dokumen TOR profesional.")

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# TOR Preview (if generated)
if st.session_state.tor_document:
    st.divider()
    st.success("✅ TOR Berhasil Dibuat!")

    tor = st.session_state.tor_document
    with st.expander("📋 Metadata", expanded=False):
        meta = tor["metadata"]
        cols = st.columns(4)
        cols[0].metric("Model", meta["generated_by"])
        cols[1].metric("Mode", meta["mode"])
        cols[2].metric("Words", meta["word_count"])
        cols[3].metric("Time", f"{meta['generation_time_ms']}ms")

    st.markdown(tor["content"])

    st.download_button(
        label="⬇️ Download TOR (.md)",
        data=tor["content"],
        file_name="tor_document.md",
        mime="text/markdown",
    )

    # Escalation warning
    if st.session_state.escalation_info:
        esc = st.session_state.escalation_info
        st.warning(
            f"⚠️ TOR ini dibuat via eskalasi.\n\n"
            f"**Rule**: {esc['triggered_by']}\n\n"
            f"**Alasan**: {esc['reason']}\n\n"
            "Beberapa bagian mungkin menggunakan asumsi."
        )

# Chat Input
if prompt := st.chat_input("Ketik pesan Anda..."):
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call API
    with st.spinner("🤔 AI sedang berpikir..."):
        data = send_message(st.session_state.session_id, prompt)

    # Handle response
    handle_response(data)
    st.rerun()
```

---

## 7. UX Flow & Interaction

### 7.1 Happy Path (Hybrid Tab)

```
1. User buka app → Tab "💬 Hybrid Chat" aktif, sidebar kosong
2. User ketik: "Buat TOR workshop AI" → spinner muncul
3. API response (type: chat) → assistant bubble muncul
   - Sidebar: progress 14%, turn 1, judul ✅
4. User ketik: "3 hari, 30 orang, Juli 2026, budget 50jt"
5. API response (type: generate) → TOR preview muncul
   - Sidebar: progress 100%, status COMPLETED
   - Main: TOR markdown rendered + download button
```

### 7.2 Escalation Path (Hybrid Tab)

```
1. User: "buat TOR AI" → turn 1
2. Assistant: "Berapa lama workshopnya?"
3. User: "terserah" → lazy strike 1
4. User: "gak tau" → lazy strike 2, ESCALATION!
5. API auto-generates TOR → preview with ⚠️ warning
```

### 7.3 Force Generate (Hybrid Tab)

```
1. User sedang chatting, progress 50%
2. User klik "🚀 Force Generate" di sidebar
3. API generates TOR with partial data → preview muncul
```

### 7.4 Gemini Direct (Direct Tab)

```
1. User klik tab "🚀 Gemini Direct"
2. User isi form: judul, latar belakang, tujuan, dll
3. Klik "🚀 Generate TOR" → spinner "Gemini sedang membuat TOR..."
4. TOR preview muncul di bawah form + download button
5. User bisa edit form dan generate ulang
```

---

## 8. Error Handling UX

| Error | Visual |
|---|---|
| Backend offline | `st.error("Backend tidak bisa dihubungi...")` + sidebar red |
| Ollama down | Error from API → `st.error` with hint to run `ollama serve` |
| Timeout | `st.warning("Request timeout...")` + retry suggestion |
| Rate limit | `st.warning("Batas panggilan tercapai...")` |
| Invalid session | Auto-create new session, show info |

---

## 9. File Structure

```
project_root/
├── streamlit_app.py              # Main Streamlit app (single file)
├── app/                          # FastAPI backend (existing)
│   ├── main.py
│   └── ...
└── Makefile                      # Add: make ui
```

### Makefile Addition

```makefile
# Run Streamlit UI
ui:
	streamlit run streamlit_app.py --server.port 8501
```

---

## 10. Dependencies

```bash
# Tambah ke requirements.txt
streamlit>=1.38.0
```

---

## 11. Running

```bash
# Terminal 1: Backend
make run
# atau: uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
make ui
# atau: streamlit run streamlit_app.py
```

Buka browser: `http://localhost:8501`

---

## 12. Task Breakdown

| # | Task | Deskripsi | Estimasi |
|---|---|---|---|
| 1 | `task01-setup.md` | Install streamlit, buat file dasar, config, session state init | Low |
| 2 | `task02-api-helpers.md` | Helper functions: send_message, check_health, force_generate | Low |
| 3 | `task03-chat-ui.md` | Chat interface: message bubbles, input, API call, response handling | Medium |
| 4 | `task04-sidebar.md` | Sidebar: progress bar, field tracker, session info, health status | Medium |
| 5 | `task05-tor-preview.md` | TOR preview, metadata, download button, escalation warning | Medium |
| 6 | `task06-testing.md` | Manual testing: happy path, escalation, force gen, error states | Medium |
| 7 | `task07-mode-tabs.md` | Tambah tab mode: Hybrid Chat + Gemini Direct (form input) | Medium |

---

## 13. Design Decisions

| Keputusan | Alasan |
|---|---|
| **Dual-tab mode** | User butuh fleksibilitas: chat interaktif ATAU form langsung |
| **`st.tabs()` bukan radio** | UX berbeda per mode, tab memisahkan layout |
| **Single file** | Streamlit simple enough, tidak perlu modular |
| **`requests` bukan `httpx`** | Streamlit re-run based (sync), tidak perlu async |
| **No custom CSS** | Streamlit native UI sudah cukup professional |
| **`wide` layout** | Sidebar + main area butuh ruang horizontal |
| **Health check di sidebar** | Non-intrusive, user langsung tahu kalau API down |
| **Download as .md** | Markdown native, PDF ditunda ke v1.0 |

---

> **Dokumen ini menjadi acuan implementasi Streamlit UI.** Setiap task file akan merujuk ke blueprint ini.
