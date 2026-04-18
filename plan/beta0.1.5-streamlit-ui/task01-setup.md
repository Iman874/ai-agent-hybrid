# Task 01 — Setup: Install Streamlit & Scaffold App

## 1. Judul Task

Install Streamlit, buat file dasar `streamlit_app.py`, init session state, dan update Makefile.

## 2. Deskripsi

Setup fondasi Streamlit app: install dependency, buat file entry point dengan page config, inisialisasi semua `st.session_state` keys, dan tambah `make ui` shortcut di Makefile.

## 3. Tujuan Teknis

- `streamlit_app.py` bisa dijalankan tanpa error
- Session state ter-inisialisasi dengan semua keys yang dibutuhkan
- `make ui` bisa start Streamlit server di port 8501
- `requirements.txt` include streamlit

## 4. Scope

### Yang dikerjakan
- Install `streamlit`
- Buat `streamlit_app.py` dengan page config dan session state init
- Update `Makefile` — tambah target `ui`
- Update `requirements.txt`

### Yang tidak dikerjakan
- Chat UI logic (task selanjutnya)
- Sidebar (task selanjutnya)
- API integration (task selanjutnya)

## 5. Langkah Implementasi

### Step 1: Install streamlit

```bash
pip install streamlit>=1.38.0
```

### Step 2: Update `requirements.txt`

Tambahkan:
```
streamlit>=1.38.0
```

### Step 3: Buat `streamlit_app.py`

```python
import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="TOR Generator — AI Agent Hybrid",
    page_icon="🤖",
    layout="wide",
)

# --- Constants ---
API_URL = "http://localhost:8000/api/v1"

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

# --- Placeholder UI ---
st.title("💬 AI TOR Generator")
st.caption("Ceritakan kebutuhan Anda, AI akan bantu menyusun dokumen TOR profesional.")
st.info("🚧 UI sedang dalam pengembangan...")
```

### Step 4: Update `Makefile`

Tambah target:
```makefile
# Run Streamlit UI
ui:
	streamlit run streamlit_app.py --server.port 8501
```

### Step 5: Verifikasi

```bash
streamlit run streamlit_app.py --server.port 8501
# Buka http://localhost:8501 — halaman muncul tanpa error
```

## 6. Output yang Diharapkan

Halaman Streamlit kosong dengan title "💬 AI TOR Generator" dan info placeholder.

## 7. Dependencies

- beta0.1.4 selesai (backend berjalan)

## 8. Acceptance Criteria

- [ ] `streamlit` ter-install
- [ ] `streamlit_app.py` bisa dijalankan tanpa error
- [ ] `st.session_state` ter-inisialisasi dengan semua keys
- [ ] `make ui` start Streamlit di port 8501
- [ ] `requirements.txt` updated

## 9. Estimasi

**Low** — ~20 menit
