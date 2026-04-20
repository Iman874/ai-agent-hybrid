# Task 03: App.py Rewrite — Hapus Tabs, Render by active_tool

## 1. Judul Task

Hapus `st.tabs()` dari area utama dan render konten berdasarkan `active_tool`

## 2. Deskripsi

Mengganti navigasi tab-based (`st.tabs(["Chat", "Gemini Direct", "Dari Dokumen", "Format TOR"])`) dengan render langsung berdasarkan state `active_tool`. Ini menghilangkan tab besar di atas yang membuat app terasa seperti dashboard.

## 3. Tujuan Teknis

- Hapus semua `st.tabs()` dan `with tab_*:` blocks
- Render konten berdasarkan `st.session_state.active_tool`
- Hanya 2 tool yang dirender: `"chat"` → `render_chat_tab()`, `"generate_doc"` → `render_document_tab()`
- `form_direct.py` dan `format_tab.py` tidak lagi dirender langsung di area utama

## 4. Scope

**Yang dikerjakan:**
- `streamlit_app/app.py`

**Yang tidak dikerjakan:**
- Sidebar (task 02)
- Settings dialog (task 05)
- Konten chat/dokumen (tidak diubah)

## 5. Langkah Implementasi

### 5.1 Hapus Import yang Tidak Dipakai

```python
# HAPUS:
from components.form_direct import render_direct_tab   # tidak dirender lagi
from components.format_tab import render_format_tab     # pindah ke settings
```

### 5.2 Rewrite Layout Section

**Sebelum:**
```python
render_sidebar()
render_header()

tab_chat, tab_direct, tab_doc, tab_format = st.tabs([
    "Chat",
    "Gemini Direct",
    "Dari Dokumen",
    "Format TOR",
])

with tab_chat:
    render_chat_tab()

with tab_direct:
    render_direct_tab()

with tab_doc:
    render_document_tab()

with tab_format:
    render_format_tab()
```

**Sesudah:**
```python
render_sidebar()
render_header()

# Render berdasarkan tool aktif (BUKAN tabs)
tool = st.session_state.get("active_tool", "chat")

if tool == "chat":
    render_chat_tab()
elif tool == "generate_doc":
    render_document_tab()
```

### 5.3 File Lengkap

```python
# streamlit_app/app.py
"""
Generator TOR — AI Agent Hybrid
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

# Render berdasarkan tool aktif (BUKAN tabs)
tool = st.session_state.get("active_tool", "chat")

if tool == "chat":
    render_chat_tab()
elif tool == "generate_doc":
    render_document_tab()
```

## 6. Output yang Diharapkan

- **Tidak ada tab besar** di atas area utama
- Halaman langsung menampilkan konten tool yang dipilih di sidebar
- Switching tool: klik radio "Alat" di sidebar → konten area utama berubah

## 7. Dependencies

- Task 01 (state: `active_tool`)
- Task 02 (sidebar: tools radio)

## 8. Acceptance Criteria

- [ ] Tidak ada `st.tabs()` di `app.py`
- [ ] Tidak ada import `render_direct_tab` atau `render_format_tab`
- [ ] Tool `"chat"` → render `render_chat_tab()`
- [ ] Tool `"generate_doc"` → render `render_document_tab()`
- [ ] Switching tool via sidebar radio bekerja tanpa error
- [ ] Server start tanpa error

## 9. Estimasi

Low (15–30 menit)
