# Cara Menjalankan AI Agent Hybrid (v0.2.7)

Project ini terdiri dari **tiga komponen** yang harus berjalan bersamaan:

1. **Ollama** — Local LLM runtime (port 11434)
2. **Backend** — FastAPI server (port 8000)
3. **Frontend** — React + Vite dev server (port 5173)

---

## ⚡ Quick Start

Buka **3 terminal** dan jalankan masing-masing:

**Terminal 1 — Ollama:**
```powershell
ollama serve
```

**Terminal 2 — Backend** (pastikan `(venv)` aktif):
```powershell
.\\venv\\Scripts\\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 3 — Frontend:**
```powershell
cd app_frontend
npm run dev
```

Buka browser: **[http://localhost:5173](http://localhost:5173)**

---

## Prasyarat

Pastikan hal berikut sudah terinstall di sistem:

| Komponen | Versi Minimum | Keterangan |
|---|---|---|
| **Python** | 3.11+ | Backend runtime |
| **Node.js** | 18+ | Frontend build tool |
| **npm** | 9+ | Package manager untuk frontend |
| **Ollama** | 0.4+ | Opsional jika hanya pakai Gemini |
| **Git** | - | Version control |

### Environment Variables

Salin file `.env.example` menjadi `.env` dan isi konfigurasi yang diperlukan:

```powershell
copy .env.example .env
```

Variabel penting yang **wajib diisi**:

| Variable | Keterangan |
|---|---|
| `GEMINI_API_KEY` | API key dari Google AI Studio (wajib untuk mode Gemini) |
| `OLLAMA_CHAT_MODEL` | Model Ollama untuk chat (default: `qwen2.5:7b-instruct`) |
| `OLLAMA_EMBED_MODEL` | Model embedding untuk RAG (default: `qwen3-embedding:0.6b`) |

---

## Setup Pertama Kali

### 1. Clone Repository

```powershell
git clone https://github.com/Iman874/ai-agent-hybrid.git
cd ai-agent-hybrid
```

### 2. Setup Backend (Python)

```powershell
# Buat virtual environment
python -m venv venv

# Aktifkan venv
.\\venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Frontend (React)

```powershell
cd app_frontend
npm install
cd ..
```

### 4. Setup Ollama Models

Download model LLM dan embedding yang diperlukan:

```bash
ollama pull qwen2.5:7b-instruct
ollama pull qwen3-embedding:0.6b
```

### 5. Konfigurasi Environment

```powershell
copy .env.example .env
# Edit .env dan isi GEMINI_API_KEY
```

---

## Menjalankan Aplikasi

### Terminal 1 — Ollama Runtime

```powershell
ollama serve
```

> Biarkan terminal ini terbuka. Jika hanya menggunakan Gemini API, langkah ini bisa dilewati.

### Terminal 2 — Backend (FastAPI)

```powershell
.\\venv\\Scripts\\activate
uvicorn app.main:app --reload --port 8000
```

Verifikasi backend berjalan:
- **API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Model List**: [http://localhost:8000/api/v1/models](http://localhost:8000/api/v1/models)

### Terminal 3 — Frontend (React + Vite)

```powershell
cd app_frontend
npm run dev
```

Frontend tersedia di: **[http://localhost:5173](http://localhost:5173)**

---

## Fitur Aplikasi (v0.2.7)

### 💬 Chat — Wawancara AI Interaktif
- **Multi-provider**: Pilih antara Local LLM (Ollama) atau Gemini API
- **SSE Streaming**: Real-time token streaming dengan fallback WebSocket → HTTP
- **Thinking Mode**: Lihat proses reasoning model (toggle on/off)
- **Multimodal**: Upload gambar di chat (muncul otomatis jika model support vision)
- **RAG Context**: Jawaban diperkaya dengan dokumen referensi TOR

### 📄 Generate — Buat TOR Otomatis
- **Dari Chat**: Setelah wawancara cukup lengkap, TOR digenerate otomatis
- **Dari Dokumen**: Upload PDF/DOCX/TXT → TOR langsung dihasilkan
- **Style System**: Pilih gaya penulisan formal/semi-formal
- **Export**: Download hasil TOR sebagai PDF atau Markdown

### 🧠 Model Capability System
- Backend secara otomatis mendeteksi kemampuan tiap model (text, vision, streaming)
- Frontend menyesuaikan UI berdasarkan capability model yang dipilih
- Badge **[VISION]** muncul di dropdown model yang support input gambar
- Validasi backend menolak gambar jika model tidak support vision

### Sidebar
- **Model Selector**: Dropdown model dengan badge capability
- **Session Manager**: Buat, hapus, dan navigasi antar sesi chat
- **Dark/Light Theme**: Toggle tema via menu di header

---

## Arsitektur Project

```
ai-agent-hybrid/
├── app/                        # Backend (FastAPI)
│   ├── ai/                     # AI providers (Ollama, Gemini)
│   ├── api/routes/             # API endpoints
│   ├── core/                   # Decision engine, capability resolver
│   ├── models/                 # Pydantic models
│   ├── services/               # Business logic (chat, stream, generate)
│   ├── rag/                    # RAG pipeline
│   └── main.py                 # FastAPI app entry point
├── app_frontend/               # Frontend (React + Vite + TailwindCSS)
│   ├── src/
│   │   ├── api/                # API client functions
│   │   ├── components/         # React components (chat, layout, shared)
│   │   ├── stores/             # Zustand state management
│   │   ├── types/              # TypeScript interfaces
│   │   └── App.tsx             # Root component
│   └── package.json
├── data/                       # SQLite DB, ChromaDB, documents
├── plan/                       # Design docs & task breakdowns
├── .env                        # Environment config (tidak di-commit)
├── .env.example                # Template environment
├── requirements.txt            # Python dependencies
└── how_to_run.md               # File ini
```

---

## Troubleshooting

| Error | Solusi |
|---|---|
| `ModuleNotFoundError` | Pastikan `(venv)` aktif: `.\\venv\\Scripts\\activate` |
| `Connection refused port 8000` | Jalankan backend terlebih dahulu (Terminal 2) |
| `Ollama unreachable` | Jalankan `ollama serve` atau pilih mode Gemini di sidebar |
| `npm: command not found` | Install Node.js dari [nodejs.org](https://nodejs.org) |
| `CORS error di browser` | Pastikan backend berjalan di port 8000 |
| Upload gambar tidak muncul | Pilih model yang support vision (Gemini atau llava) |
| `GEMINI_API_KEY not set` | Isi `GEMINI_API_KEY` di file `.env` |

---

## Perintah Berguna

```powershell
# Install ulang Python dependencies
.\\venv\\Scripts\\pip install -r requirements.txt

# Install ulang frontend dependencies
cd app_frontend && npm install && cd ..

# Build frontend untuk production
cd app_frontend && npm run build && cd ..

# Jalankan test suite
.\\venv\\Scripts\\pytest tests/ -v

# Type check frontend
cd app_frontend && npx tsc --noEmit && cd ..

# Cek model yang tersedia
curl http://localhost:8000/api/v1/models
```
