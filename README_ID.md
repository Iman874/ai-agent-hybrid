# 🤖 AI Agent Hybrid — TOR Generator

> **[🇬🇧 English](./README_EN.md)** | **[🇮🇩 Bahasa Indonesia](./README_ID.md)**

**Asisten berbasis AI** untuk membuat dokumen **Kerangka Acuan Kerja (TOR/Term of Reference)** secara otomatis melalui wawancara interaktif dengan LLM.

Sistem ini menggabungkan **Local LLM** (Ollama) dan **Gemini API** dalam arsitektur hybrid — backend sebagai *source of truth*, frontend adaptif berbasis React.

---

## ✨ Highlight Fitur

| Fitur | Deskripsi | Versi |
|---|---|---|
| 💬 **Chat Engine** | Wawancara interaktif multi-turn untuk mengumpulkan data TOR | `v0.1.0` |
| 📚 **RAG System** | Retrieval-Augmented Generation dengan ChromaDB untuk konteks dokumen referensi | `v0.1.1` |
| 🚀 **Gemini Generator** | Generate TOR lengkap via Gemini API dari data hasil wawancara | `v0.1.2` |
| 🧠 **Decision Engine** | Routing otomatis antara chat ↔ generate, eskalasi ke Gemini jika LLM lokal mentok | `v0.1.3` |
| 🔌 **REST API Layer** | FastAPI endpoints: `/hybrid`, `/chat`, `/generate`, `/models`, `/health` | `v0.1.4` |
| 📄 **Document-to-TOR** | Upload PDF/DOCX/TXT → TOR otomatis tanpa wawancara | `v0.1.6` |
| 🎨 **TOR Format & Style** | Sistem gaya penulisan (formal/semi-formal) dengan custom template | `v0.1.9` |
| 📥 **PDF/Markdown Export** | Download hasil TOR sebagai PDF atau Markdown | `v0.1.10` |
| 🗂️ **Session History** | Riwayat sesi chat tersimpan di SQLite, bisa dilanjutkan kapan saja | `v0.1.11` |
| ⚛️ **React Frontend** | Migrasi dari Streamlit ke React + Vite + TailwindCSS + Zustand | `v0.2.1` |
| 📜 **Generate History** | Riwayat dokumen TOR yang pernah digenerate, bisa dilihat ulang | `v0.2.4` |
| 🌊 **Real-time Streaming** | SSE streaming untuk generate dan chat (real token, bukan fake split) | `v0.2.5` — `v0.2.6` |
| 🖼️ **Multimodal & Vision** | Upload gambar di chat, deteksi capability model, badge [VISION] di UI | `v0.2.7` |

---

## 🏗️ Tech Stack

| Layer | Teknologi |
|---|---|
| **Backend** | Python, FastAPI, Pydantic v2, asyncio |
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS v4, Zustand |
| **AI Providers** | Ollama (lokal), Google Gemini API (cloud) |
| **Database** | SQLite (aiosqlite), ChromaDB (vector store) |
| **Transport** | SSE (utama), WebSocket (fallback), HTTP (fallback) |

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

Buka **[http://localhost:5173](http://localhost:5173)** di browser.

> 📖 Panduan lengkap ada di [`how_to_run.md`](./how_to_run.md)

---

## 📁 Struktur Project

```
ai-agent-hybrid/
├── app/                    # Backend (FastAPI)
│   ├── ai/                 # Provider Ollama & Gemini
│   ├── api/routes/         # REST endpoints
│   ├── core/               # Decision engine, capability resolver
│   ├── services/           # Layanan chat, stream, generate
│   └── rag/                # RAG pipeline (ChromaDB)
├── app_frontend/           # Frontend (React + Vite)
│   └── src/
│       ├── components/     # Komponen UI
│       ├── stores/         # Zustand state management
│       └── types/          # TypeScript interfaces
├── data/                   # SQLite DB, ChromaDB, dokumen
└── plan/                   # Dokumen desain & task breakdown
```

---

## 📋 Riwayat Rilis

### v0.2.x — Era React
| Versi | Nama | Highlight |
|---|---|---|
| `v0.2.7` | Model Capability | Deteksi vision/text per model, UI adaptif, validasi backend |
| `v0.2.6` | Streaming Chat | Real SSE token streaming untuk chat (mengganti fake streaming) |
| `v0.2.5` | Streaming Generate | Real SSE streaming untuk proses generate TOR |
| `v0.2.4` | Generate History | Riwayat dokumen TOR yang pernah digenerate |
| `v0.2.3` | Session & Model Fix | Perbaikan session management dan model switching |
| `v0.2.2` | React Polish | UI polish, dark mode, responsive layout |
| `v0.2.1` | React Migration | Migrasi penuh dari Streamlit ke React + Vite + Zustand |

### v0.1.x — Era Streamlit
| Versi | Nama | Highlight |
|---|---|---|
| `v0.1.15` | Performance | Optimasi performa Streamlit |
| `v0.1.14` | Sidebar Overhaul | Redesign sidebar dan navigasi |
| `v0.1.13` | UI Notification | Sistem notifikasi dan toast |
| `v0.1.12` | Doc Upload & Style | Upload dokumen + sistem gaya penulisan TOR |
| `v0.1.11` | Session History | Riwayat sesi chat dengan SQLite |
| `v0.1.10` | Document Export | Export TOR ke PDF/Markdown |
| `v0.1.9` | TOR Format System | Template dan gaya penulisan TOR |
| `v0.1.8` | UI Redesign | Redesain visual chat UI |
| `v0.1.7` | Chat UI Overhaul | Perbaikan besar UI wawancara |
| `v0.1.6` | Doc-to-TOR | Generate TOR dari file dokumen |
| `v0.1.5` | Streamlit UI | Frontend pertama berbasis Streamlit |
| `v0.1.4` | API Layer | REST API endpoints dengan FastAPI |
| `v0.1.3` | Decision Engine | Routing otomatis chat ↔ generate |
| `v0.1.2` | Gemini Generator | Integrasi Gemini API untuk generate TOR |
| `v0.1.1` | RAG System | Retrieval-Augmented Generation pipeline |
| `v0.1.0` | Chat Engine | Engine wawancara multi-turn dengan Ollama |

---

## 📄 Lisensi

Project privat — tidak untuk distribusi publik.
