# Task 01 — Setup Project Structure & Configuration

## 1. Judul Task

Setup struktur folder project, virtual environment, dependencies, dan Pydantic Settings configuration.

## 2. Deskripsi

Menyiapkan fondasi project dari nol: membuat folder structure, menginstall semua dependencies yang dibutuhkan, dan membuat konfigurasi environment berbasis Pydantic Settings yang membaca dari file `.env`.

## 3. Tujuan Teknis

- Struktur folder `app/` sudah terbentuk lengkap dengan semua `__init__.py`
- Virtual environment aktif dengan semua packages terinstall
- `app/config.py` bisa membaca semua parameter dari `.env`
- `.env.example` tersedia sebagai template
- `requirements.txt` lengkap

## 4. Scope

### Yang dikerjakan
- Buat seluruh directory tree (`app/`, `app/ai/`, `app/core/`, `app/models/`, `app/db/`, `app/api/`, `app/services/`, `app/utils/`)
- Buat semua `__init__.py` (boleh kosong dulu)
- Buat `requirements.txt` dengan semua library
- Buat `.env.example` dengan semua variabel
- Buat `app/config.py` dengan Pydantic Settings

### Yang tidak dikerjakan
- Belum ada logic apapun (hanya skeleton)
- Belum ada FastAPI app
- Belum ada database

## 5. Langkah Implementasi

### Step 1: Buat virtual environment

```bash
cd d:\Iman874\Documents\Github\ai-agent-hybrid
python -m venv venv
.\venv\Scripts\activate
```

### Step 2: Buat `requirements.txt`

```
# Framework
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.0
pydantic-settings>=2.0

# AI Providers
ollama>=0.4.0

# Database
aiosqlite>=0.20.0

# Utilities
python-dotenv>=1.0
python-multipart>=0.0.9
httpx>=0.27.0

# Testing
pytest>=8.0
pytest-asyncio>=0.24.0
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Buat seluruh directory tree

```
app/
├── __init__.py
├── config.py
├── ai/
│   ├── __init__.py
│   └── prompts/
│       └── __init__.py
├── core/
│   └── __init__.py
├── models/
│   └── __init__.py
├── db/
│   ├── __init__.py
│   └── migrations/
├── api/
│   ├── __init__.py
│   └── routes/
│       └── __init__.py
├── services/
│   └── __init__.py
└── utils/
    └── __init__.py
```

Buat semua `__init__.py` sebagai file kosong.

### Step 5: Buat `.env.example`

```env
# === APP ===
APP_NAME=ai-agent-hybrid
APP_PORT=8000
LOG_LEVEL=INFO

# === OLLAMA ===
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen2.5:7b-instruct
OLLAMA_EMBED_MODEL=bge-m3
OLLAMA_TIMEOUT=60
OLLAMA_TEMPERATURE=0.3
OLLAMA_NUM_CTX=4096

# === GEMINI (untuk modul berikutnya) ===
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=4096

# === DATABASE ===
SESSION_DB_PATH=./data/sessions.db

# === COST CONTROL ===
MAX_GEMINI_CALLS_PER_SESSION=3
MAX_GEMINI_CALLS_PER_HOUR=20
MAX_CHAT_TURNS=15
```

### Step 6: Copy `.env.example` menjadi `.env`

```bash
copy .env.example .env
```

### Step 7: Buat `app/config.py`

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "ai-agent-hybrid"
    app_port: int = 8000
    log_level: str = "INFO"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen2.5:7b-instruct"
    ollama_embed_model: str = "bge-m3"
    ollama_timeout: int = 60
    ollama_temperature: float = 0.3
    ollama_num_ctx: int = 4096

    # Gemini (dipakai di modul berikutnya)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 4096

    # Database
    session_db_path: str = "./data/sessions.db"

    # Cost Control
    max_gemini_calls_per_session: int = 3
    max_gemini_calls_per_hour: int = 20
    max_chat_turns: int = 15

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### Step 8: Verifikasi config bisa di-load

Buat script test sederhana:

```python
# test cepat: python -c "from app.config import Settings; s = Settings(); print(s.model_dump())"
```

## 6. Output yang Diharapkan

Setelah task ini selesai:

```
ai-agent-hybrid/
├── .env
├── .env.example
├── requirements.txt
├── venv/
└── app/
    ├── __init__.py
    ├── config.py          ← Pydantic Settings, bisa di-import
    ├── ai/
    │   ├── __init__.py
    │   └── prompts/
    │       └── __init__.py
    ├── core/
    │   └── __init__.py
    ├── models/
    │   └── __init__.py
    ├── db/
    │   ├── __init__.py
    │   └── migrations/
    ├── api/
    │   ├── __init__.py
    │   └── routes/
    │       └── __init__.py
    ├── services/
    │   └── __init__.py
    └── utils/
        └── __init__.py
```

Running `python -c "from app.config import Settings; print(Settings().app_name)"` menghasilkan:
```
ai-agent-hybrid
```

## 7. Dependencies

- Tidak ada task sebelumnya (ini task pertama)
- Python 3.11+ harus sudah terinstall

## 8. Acceptance Criteria

- [ ] Virtual environment berhasil dibuat dan aktif
- [ ] `pip install -r requirements.txt` berjalan tanpa error
- [ ] Semua folder dan `__init__.py` sudah terbuat
- [ ] `.env.example` berisi semua variabel yang dibutuhkan
- [ ] `.env` sudah di-copy dari `.env.example`
- [ ] `from app.config import Settings` berhasil tanpa error
- [ ] `Settings()` berhasil membaca default values
- [ ] `Settings()` berhasil membaca dari `.env` jika ada
- [ ] `.gitignore` sudah mengecualikan `venv/`, `.env`, `data/`, `__pycache__/`

## 9. Estimasi

**Low** — ~1 jam
