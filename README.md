# 🤖 AI Agent Hybrid — TOR Generator

> **[🇬🇧 English](./README_EN.md)** | **[🇮🇩 Bahasa Indonesia](./README_ID.md)**

---

**AI-powered assistant** for automatically generating **Term of Reference (TOR)** documents through interactive LLM interviews.

This system combines **Local LLM** (Ollama) and **Gemini API** in a hybrid architecture — backend as the *source of truth*, adaptive React-based frontend.

---

**Asisten berbasis AI** untuk membuat dokumen **Kerangka Acuan Kerja (TOR)** secara otomatis melalui wawancara interaktif dengan LLM.

Sistem ini menggabungkan **Local LLM** (Ollama) dan **Gemini API** dalam arsitektur hybrid — backend sebagai *source of truth*, frontend adaptif berbasis React.

---

## 🚀 Quick Start

```powershell
# Terminal 1 — Ollama
ollama serve

# Terminal 2 — Backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 3 — Frontend
cd app_frontend
npm run dev
```

Open **[http://localhost:5173](http://localhost:5173)**

> 📖 Full guide → [`how_to_run.md`](./how_to_run.md)

---

## � Versi Terkini

| Version | Name | Status |
|---|---|---|
| `v0.2.9` | Ollama Generator | ✅ **Implemented** — Local LLM as TOR generator |
| `v0.3.0` | AI Tool System | 🚧 **In Planning** — Tool abstraction, web search skill |

---

## �📄 License

Private project — not for public distribution.
