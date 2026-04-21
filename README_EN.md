# 🤖 AI Agent Hybrid — TOR Generator

> **[🇬🇧 English](./README_EN.md)** | **[🇮🇩 Bahasa Indonesia](./README_ID.md)**

**AI-powered assistant** for automatically generating **Term of Reference (TOR)** documents through interactive LLM interviews.

This system combines **Local LLM** (Ollama) and **Gemini API** in a hybrid architecture — the backend serves as the *source of truth*, with an adaptive React-based frontend.

---

## ✨ Feature Highlights

| Feature | Description | Version |
|---|---|---|
| 💬 **Chat Engine** | Interactive multi-turn interview to collect TOR data | `v0.1.0` |
| 📚 **RAG System** | Retrieval-Augmented Generation with ChromaDB for reference document context | `v0.1.1` |
| 🚀 **Gemini Generator** | Generate complete TOR via Gemini API from interview data | `v0.1.2` |
| 🧠 **Decision Engine** | Automatic routing between chat ↔ generate, escalation to Gemini when local LLM is stuck | `v0.1.3` |
| 🔌 **REST API Layer** | FastAPI endpoints: `/hybrid`, `/chat`, `/generate`, `/models`, `/health` | `v0.1.4` |
| 📄 **Document-to-TOR** | Upload PDF/DOCX/TXT → auto-generate TOR without interview | `v0.1.6` |
| 🎨 **TOR Format & Style** | Writing style system (formal/semi-formal) with custom templates | `v0.1.9` |
| 📥 **PDF/Markdown Export** | Download TOR output as PDF or Markdown | `v0.1.10` |
| 🗂️ **Session History** | Chat session history stored in SQLite, can be resumed anytime | `v0.1.11` |
| ⚛️ **React Frontend** | Migration from Streamlit to React + Vite + TailwindCSS + Zustand | `v0.2.1` |
| 📜 **Generate History** | History of previously generated TOR documents, viewable anytime | `v0.2.4` |
| 🌊 **Real-time Streaming** | SSE streaming for generate and chat (real tokens, not fake split) | `v0.2.5` — `v0.2.6` |
| 🖼️ **Multimodal & Vision** | Image upload in chat, model capability detection, [VISION] badge in UI | `v0.2.7` |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, FastAPI, Pydantic v2, asyncio |
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS v4, Zustand |
| **AI Providers** | Ollama (local), Google Gemini API (cloud) |
| **Database** | SQLite (aiosqlite), ChromaDB (vector store) |
| **Transport** | SSE (primary), WebSocket (fallback), HTTP (fallback) |

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

Open **[http://localhost:5173](http://localhost:5173)** in your browser.

> 📖 Full setup guide available at [`how_to_run.md`](./how_to_run.md)

---

## 📁 Project Structure

```
ai-agent-hybrid/
├── app/                    # Backend (FastAPI)
│   ├── ai/                 # Ollama & Gemini providers
│   ├── api/routes/         # REST endpoints
│   ├── core/               # Decision engine, capability resolver
│   ├── services/           # Chat, stream, generate services
│   └── rag/                # RAG pipeline (ChromaDB)
├── app_frontend/           # Frontend (React + Vite)
│   └── src/
│       ├── components/     # UI components
│       ├── stores/         # Zustand state management
│       └── types/          # TypeScript interfaces
├── data/                   # SQLite DB, ChromaDB, documents
└── plan/                   # Design docs & task breakdowns
```

---

## 📋 Release History

### v0.2.x — React Era
| Version | Name | Highlight |
|---|---|---|
| `v0.2.7` | Model Capability | Per-model vision/text detection, adaptive UI, backend validation |
| `v0.2.6` | Streaming Chat | Real SSE token streaming for chat (replacing fake streaming) |
| `v0.2.5` | Streaming Generate | Real SSE streaming for TOR generation process |
| `v0.2.4` | Generate History | History of previously generated TOR documents |
| `v0.2.3` | Session & Model Fix | Session management and model switching fixes |
| `v0.2.2` | React Polish | UI polish, dark mode, responsive layout |
| `v0.2.1` | React Migration | Full migration from Streamlit to React + Vite + Zustand |

### v0.1.x — Streamlit Era
| Version | Name | Highlight |
|---|---|---|
| `v0.1.15` | Performance | Streamlit performance optimization |
| `v0.1.14` | Sidebar Overhaul | Sidebar and navigation redesign |
| `v0.1.13` | UI Notification | Notification and toast system |
| `v0.1.12` | Doc Upload & Style | Document upload + TOR writing style system |
| `v0.1.11` | Session History | Chat session history with SQLite |
| `v0.1.10` | Document Export | Export TOR to PDF/Markdown |
| `v0.1.9` | TOR Format System | TOR templates and writing styles |
| `v0.1.8` | UI Redesign | Chat UI visual redesign |
| `v0.1.7` | Chat UI Overhaul | Major interview UI improvements |
| `v0.1.6` | Doc-to-TOR | Generate TOR from document files |
| `v0.1.5` | Streamlit UI | First Streamlit-based frontend |
| `v0.1.4` | API Layer | REST API endpoints with FastAPI |
| `v0.1.3` | Decision Engine | Automatic chat ↔ generate routing |
| `v0.1.2` | Gemini Generator | Gemini API integration for TOR generation |
| `v0.1.1` | RAG System | Retrieval-Augmented Generation pipeline |
| `v0.1.0` | Chat Engine | Multi-turn interview engine with Ollama |

---

## 📄 License

Private project — not for public distribution.
