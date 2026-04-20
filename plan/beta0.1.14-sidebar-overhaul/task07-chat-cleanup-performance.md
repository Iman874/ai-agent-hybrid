# Task 07: Chat Cleanup + Performance — Hapus Model Selector, Tambah Cache

## 1. Judul Task

Cleanup `chat.py` (hapus model selector) + tambah `@st.cache_data` untuk API calls

## 2. Deskripsi

Menghapus `_render_chat_model_selector()` dari `chat.py` (karena model selector sudah pindah ke sidebar di task 02) dan menambahkan caching pada API calls yang berat agar sidebar tidak lambat.

## 3. Tujuan Teknis

- Hapus `_render_chat_model_selector()` dari `chat.py`
- Hapus import `fetch_models` dari `chat.py`
- Tambah `@st.cache_data(ttl=N)` pada: `fetch_models()`, `fetch_session_list()`, `check_health()`
- Validasi tidak ada state keys lama yang tidak terpakai

## 4. Scope

**Yang dikerjakan:**
- `streamlit_app/components/chat.py` — hapus model selector
- `streamlit_app/api/client.py` — tambah `@st.cache_data`

**Yang tidak dikerjakan:**
- Logic chat (tidak diubah)
- Backend API (tidak diubah)

## 5. Langkah Implementasi

### 5.1 Cleanup `chat.py`

**Hapus fungsi:**
- `_render_chat_model_selector()` (seluruh fungsi, ~80 baris)

**Hapus dari import:**
```python
# HAPUS:
from api.client import fetch_models
```

**Hapus pemanggilan:**
```python
# Di render_chat_tab(), HAPUS baris:
_render_chat_model_selector()
st.divider()
```

### 5.2 Setelah cleanup, `render_chat_tab()` menjadi:

```python
def render_chat_tab():
    # === HISTORY VIEW MODE ===
    if st.session_state.is_viewing_history:
        _render_history_view()
        return

    # Empty state
    if not st.session_state.messages and not st.session_state.tor_document:
        _render_empty_state()

    # Message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # TOR Preview
    if st.session_state.tor_document:
        render_tor_preview(
            st.session_state.tor_document,
            session_id=st.session_state.session_id,
            escalation_info=st.session_state.escalation_info,
            key_suffix="_hybrid",
        )

    # Chat input
    if prompt := st.chat_input("Tanyakan apa saja..."):
        _handle_user_input(prompt)
```

### 5.3 Tambah `@st.cache_data` di `api/client.py`

Pada fungsi yang dipanggil setiap render di sidebar:

```python
@st.cache_data(ttl=30)  # Cache 30 detik
def fetch_models() -> list[dict]:
    """Fetch daftar model dari API."""
    ...

@st.cache_data(ttl=10)  # Cache 10 detik
def fetch_session_list(limit: int = 10) -> list[dict]:
    """Fetch daftar session terbaru."""
    ...

@st.cache_data(ttl=15)  # Cache 15 detik
def check_health() -> dict:
    """Check API health status."""
    ...
```

> **Catatan**: `@st.cache_data` akan cache berdasarkan argumen. Jika limit berubah, cache baru dibuat. TTL pendek agar data tetap fresh.

### 5.4 Cleanup Import `reset_session` dari `chat.py`

Cek apakah `reset_session` masih dipakai di `chat.py`. Jika hanya dipakai oleh `_render_chat_model_selector()` yang dihapus, hapus importnya juga.

## 6. Output yang Diharapkan

- `chat.py` lebih pendek (~80 baris berkurang)
- Tab Chat langsung menampilkan empty state / messages tanpa model selector
- Sidebar tidak lambat karena API calls di-cache
- Rerun sidebar tidak memicu fetch API setiap kali

## 7. Dependencies

- Task 02 (sidebar sudah punya model selector)
- Task 03 (app.py sudah tidak pakai tabs)

## 8. Acceptance Criteria

- [ ] `_render_chat_model_selector()` dihapus dari `chat.py`
- [ ] `fetch_models` tidak di-import di `chat.py`
- [ ] Tab Chat masih berfungsi normal (empty state, messages, input)
- [ ] `fetch_models()` punya `@st.cache_data(ttl=30)`
- [ ] `fetch_session_list()` punya `@st.cache_data(ttl=10)`
- [ ] `check_health()` punya `@st.cache_data(ttl=15)`
- [ ] Sidebar terasa lebih responsif (tidak fetch API setiap render)
- [ ] Tidak ada import yang tidak terpakai
- [ ] Server start tanpa error
- [ ] Existing tests tetap PASS

## 9. Estimasi

Low (30 menit – 1 jam)
