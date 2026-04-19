# Cara Menjalankan AI Agent Hybrid (v0.1.8)

Project ini terdiri dari dua komponen yang harus berjalan bersamaan:
1. **Backend** — FastAPI server (port 8000)
2. **Frontend** — Streamlit chat UI (port 8501)

---

## ⚡ Quick Start (pastikan `(venv)` aktif dulu)

**Terminal 1 — Backend:**
```powershell
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```powershell
streamlit run streamlit_app/app.py --server.port 8501
```

Buka browser: **[http://localhost:8501](http://localhost:8501)**

---

## Prasyarat

Sebelum menjalankan, pastikan hal berikut sudah terpenuhi:

| Komponen | Keterangan |
|---|---|
| **Python venv** | Library terinstall di virtual environment, bukan sistem |
| **Ollama** | Wajib jika ingin pakai Local LLM (opsional jika pakai Gemini saja) |
| **Gemini API Key** | Wajib jika ingin pakai mode Gemini (atur di `.env`) |

---

## Langkah 1 — Aktifkan Virtual Environment

Buka terminal di root folder project (`d:\Iman874\Documents\Github\ai-agent-hybrid`):

```powershell
.\venv\Scripts\activate
```

Jika berhasil, akan muncul awalan `(venv)` di kiri command line.

---

## Langkah 2 — (Opsional) Jalankan Ollama

Wajib jika ingin menggunakan mode **Local LLM**. Buka terminal terpisah:

```bash
ollama serve
```

> Jangan tutup terminal ini selama aplikasi berjalan.
> Jika hanya pakai Gemini API, langkah ini bisa dilewati.

---

## Langkah 3 — Jalankan FastAPI Backend

Di terminal dengan `(venv)` aktif:

```powershell
uvicorn app.main:app --reload --port 8000
```

Backend tersedia di:
- **API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## Langkah 4 — Jalankan Streamlit Frontend

Buka **terminal baru** (dengan `(venv)` aktif juga), lalu jalankan:

```powershell
streamlit run streamlit_app/app.py --server.port 8501
```

Frontend tersedia di: [http://localhost:8501](http://localhost:8501)

---

## Fitur UI (v0.1.8)

### Chat Mode
Di sidebar, pilih provider untuk chat:
- **🖥️ Local LLM** — gunakan model Ollama lokal (qwen2.5, dll.)
- **✨ Gemini API** — gunakan Gemini langsung sebagai interviewer

### Tabs Utama
| Tab | Fungsi |
|---|---|
| 💬 **Chat** | Wawancara interaktif untuk menyusun TOR |
| 🚀 **Gemini Direct** | Generate TOR langsung dari form tanpa chat |
| 📄 **Dari Dokumen** | Upload PDF/TXT/DOCX → TOR otomatis |

### Toggle Tampilan (⋮)
Klik tombol `⋮` di pojok kanan atas area chat untuk ganti tema:
- 🖥 **Ikuti Sistem** — mengikuti preferensi dark/light OS/browser
- 🌙 **Gelap** — dark mode
- ☀️ **Terang** — light mode

> **Catatan**: Pergantian tema kini difasilitasi penuh via runtime state engine 
> sehingga tidak ada lagi *blank reloads* yang parah pada transisi komponen UI.

---

## Troubleshooting

| Error | Solusi |
|---|---|
| `ModuleNotFoundError` | Pastikan `(venv)` aktif sebelum menjalankan apapun |
| `Connection refused port 8000` | Jalankan backend (Langkah 3) terlebih dahulu |
| `Ollama unreachable` | Jalankan `ollama serve` atau pilih mode Gemini API di sidebar |
| Theme tidak berubah setelah restart | Hapus file `.streamlit/.current_theme` dan restart Streamlit |

---

## Install ulang dependensi (jika diperlukan)

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Jalankan Test Suite

```powershell
.\venv\Scripts\pytest.exe tests/ -v
```
