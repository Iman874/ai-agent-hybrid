# Task 12: Entry Point Assembly — `app.py` Orchestrator

## Status: 🔲 Pending

---

## 1. Judul Task

Finalisasi `app.py` sebagai entry point yang meng-compose semua komponen.

## 2. Deskripsi

Replace placeholder `app.py` (dari Task 01) dengan versi final yang
meng-import dan menjalankan semua komponen dalam urutan yang benar.
File ini harus ≤50 baris dan tidak mengandung business logic apapun.

## 3. Tujuan Teknis

- `app.py` sebagai orchestrator: bootstrap → layout → render
- Urutan: set_page_config → init_state → apply_theme → inject_styles → components
- Tabs: Chat / Gemini Direct / Dari Dokumen
- Zero business logic — semua didelegasikan ke komponen

## 4. Scope

**Yang dikerjakan:**
- `app.py` final — ~40 lines, clean orchestration
- Integration test semua komponen bersama

**Yang TIDAK dikerjakan:**
- Komponen individual (sudah di Task 06-11)
- CSS / icons (sudah di Task 02-03)

## 5. Langkah Implementasi

### Step 1: Rewrite `app.py`

```python
# streamlit_app/app.py
"""
TOR Generator — AI Agent Hybrid
Entry point untuk Streamlit UI.

Jalankan: streamlit run streamlit_app/app.py --server.port 8501
"""

import streamlit as st
from config import PAGE_CONFIG
from state import init_session_state
from theme import apply_saved_theme
from styles.loader import inject_styles
from components.sidebar import render_sidebar
from components.header import render_header
from components.chat import render_chat_tab
from components.form_direct import render_direct_tab
from components.form_document import render_document_tab


# ============================================
# BOOTSTRAP
# ============================================
st.set_page_config(**PAGE_CONFIG)
init_session_state()
apply_saved_theme()
inject_styles()


# ============================================
# LAYOUT
# ============================================
render_sidebar()
render_header()

tab_chat, tab_direct, tab_doc = st.tabs([
    "Chat",
    "Gemini Direct",
    "Dari Dokumen",
])

with tab_chat:
    render_chat_tab()

with tab_direct:
    render_direct_tab()

with tab_doc:
    render_document_tab()
```

### Step 2: Test startup

```powershell
streamlit run streamlit_app/app.py --server.port 8501
```

Verifikasi:
- Halaman ter-load tanpa error
- Sidebar tampil lengkap
- Header dengan theme toggle berfungsi
- 3 tabs ada dan bisa di-switch

### Step 3: Test fungsional per tab

#### Tab Chat:
1. Muncul empty state (icon `forum` besar)
2. Ketik pesan → spinner → response tampil
3. TOR preview muncul jika data cukup

#### Tab Gemini Direct:
1. Form 7 field tampil
2. Klik Generate tanpa judul → error banner
3. Isi judul + tujuan → Generate → TOR preview

#### Tab Dari Dokumen:
1. File uploader tampil
2. Upload file → Generate → TOR preview

### Step 4: Test theme switching

1. Klik `⋮` → pilih "Terang" → halaman berubah + semua komponen ikut
2. Restart Streamlit → tema masih light (persisten)
3. Klik `⋮` → pilih "Gelap" → kembali dark

### Step 5: Test model switching

1. Sidebar → pilih "Gemini API" → header berubah "TOR Generator · Gemini"
2. Jika ada session aktif → warning muncul + konfirmasi reset

## 6. Output yang Diharapkan

```
streamlit_app/
├── app.py               (~45 lines — clean, no logic)
├── config.py
├── state.py
├── theme.py
├── api/
│   ├── __init__.py
│   └── client.py
├── components/
│   ├── __init__.py
│   ├── sidebar.py
│   ├── header.py
│   ├── chat.py
│   ├── form_direct.py
│   ├── form_document.py
│   └── tor_preview.py
├── utils/
│   ├── __init__.py
│   ├── formatters.py
│   └── icons.py
└── styles/
    ├── __init__.py
    ├── base.css
    ├── components.css
    └── loader.py
```

Total: 17 files, 0 business logic di `app.py`.

## 7. Dependencies

- **Task 01-11** — SEMUA task sebelumnya harus selesai

## 8. Acceptance Criteria

- [ ] `app.py` ≤50 baris
- [ ] `app.py` tidak mengandung business logic (hanya imports + compose)
- [ ] `streamlit run streamlit_app/app.py` start tanpa error
- [ ] Sidebar render lengkap (brand, model, progress, fields, system)
- [ ] Header render + theme toggle berfungsi
- [ ] Tab Chat berfungsi (empty state, chat, TOR preview)
- [ ] Tab Gemini Direct berfungsi (form, validate, generate)
- [ ] Tab Dari Dokumen berfungsi (upload, generate)
- [ ] Theme switching dark ↔ light tanpa crash
- [ ] Model switching local ↔ gemini berfungsi
- [ ] Semua Material Icons render (tidak ada missing icon)
- [ ] Tidak ada emoji tersisa di seluruh UI

## 9. Estimasi

**Medium** — Integrasi semua komponen + end-to-end testing.
