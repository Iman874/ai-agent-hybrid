# Task 07: Relocate Model Selector — Sidebar → Tab Chat

> **Status**: [x] Selesai
> **Estimasi**: High (2–3 jam)
> **Dependency**: Task 01, Task 06

## 1. Deskripsi

Memindahkan model selector (Local LLM / Gemini API) dari sidebar ke dalam **tab Chat**, karena pilihan model hanya relevan untuk wawancara chat. Tab lain (Gemini Direct, Dari Dokumen, Format TOR) selalu menggunakan Gemini API secara default.

## 2. Tujuan Teknis

- `_render_model_selector()` **dihapus** dari `sidebar.py`
- Model selector widget baru dibuat di `chat.py` (compact, di atas area chat)
- Semua logic model switch (reset session, thinking mode) dipindahkan ke `chat.py`
- Sidebar lebih bersih tanpa section MODEL

## 3. Scope

**Yang dikerjakan:**
- `streamlit_app/components/sidebar.py` — hapus `_render_model_selector()` + pemanggilan
- `streamlit_app/components/chat.py` — tambah model selector widget

**Yang tidak dikerjakan:**
- Perubahan backend (mode tetap dikirim via `chat_mode` di `send_message`)
- Default `chat_mode` di `state.py` tetap sama

## 4. Langkah Implementasi

### 4.1 Hapus Model Selector dari `sidebar.py`

- [x] Hapus pemanggilan `_render_model_selector()` dari `render_sidebar()` (line 20):

```python
# SEBELUM:
def render_sidebar():
    with st.sidebar:
        _render_brand()
        _render_new_chat()
        st.divider()
        _render_session_history()
        st.divider()
        _render_model_selector()   # ← HAPUS
        st.divider()               # ← HAPUS (divider sebelum progress)
        _render_progress()
        ...

# SESUDAH:
def render_sidebar():
    with st.sidebar:
        _render_brand()
        _render_new_chat()
        st.divider()
        _render_session_history()
        st.divider()
        _render_progress()
        ...
```

- [x] **Hapus** seluruh fungsi `_render_model_selector()` (line 149-228).

- [x] **Hapus** import `fetch_models` dari `api.client` di `sidebar.py` (jika tidak dipakai di mana pun lagi di file ini):

```python
# Cek apakah fetch_models masih dipakai di sidebar:
# Jika tidak → hapus dari import
```

### 4.2 Tambah Model Selector di `chat.py`

- [x] Tambah import di `chat.py`:

```python
from api.client import fetch_models
from state import reset_session
from utils.notify import notify
```

- [x] Buat fungsi `_render_chat_model_selector()`:

```python
def _render_chat_model_selector():
    """Compact model selector — hanya tampil di tab Chat."""
    models = fetch_models()
    local_models = [m for m in models if m["type"] == "local" and m["status"] == "available"]
    gemini_models = [m for m in models if m["type"] == "gemini" and m["status"] == "available"]

    mode_opts, mode_map = [], {}
    if local_models:
        mode_opts.append("Local LLM")
        mode_map["Local LLM"] = "local"
    if gemini_models:
        mode_opts.append("Gemini API")
        mode_map["Gemini API"] = "gemini"

    if not mode_opts:
        notify("Tidak ada model tersedia.", "error", method="inline")
        return

    current_label = next(
        (lbl for lbl, m in mode_map.items() if m == st.session_state.chat_mode),
        mode_opts[0],
    )

    col_radio, col_model = st.columns([1, 1])

    with col_radio:
        selected = st.radio(
            "Provider",
            mode_opts,
            index=mode_opts.index(current_label),
            horizontal=True,
            label_visibility="collapsed",
            key="chat_provider_radio",
        )

    new_mode = mode_map.get(selected, "local")

    with col_model:
        if new_mode == "local" and local_models:
            chat_models = [
                m["id"] for m in local_models
                if "embed" not in m["id"].lower() and "nomic" not in m["id"].lower()
            ]
            if chat_models:
                st.selectbox(
                    "Model",
                    chat_models,
                    label_visibility="collapsed",
                    key="chat_model_select",
                )
        elif new_mode == "gemini" and gemini_models:
            st.caption(f"_{gemini_models[0]['id']}_")

    # Handle mode switch
    if new_mode != st.session_state.chat_mode:
        if st.session_state.session_id and st.session_state.messages:
            notify("Ganti model akan mereset session.", "warning", method="inline")
            if st.button("Konfirmasi Reset", use_container_width=True, key="model_reset_confirm"):
                st.session_state.chat_mode = new_mode
                reset_session()
                st.rerun()
        else:
            st.session_state.chat_mode = new_mode

    # Thinking Mode toggle
    if new_mode == "local":
        chat_models_list = [
            m["id"] for m in local_models
            if "embed" not in m["id"].lower() and "nomic" not in m["id"].lower()
        ]
        active_model = chat_models_list[0] if chat_models_list else ""
        if active_model.endswith("-cloud"):
            think_on = st.toggle(
                "Deep Reasoning",
                value=st.session_state.thinking_mode,
                help="Matikan untuk response lebih cepat.",
                key="thinking_toggle",
            )
            if think_on != st.session_state.thinking_mode:
                st.session_state.thinking_mode = think_on

    # Ollama offline notice
    offline = [m for m in models if m["type"] == "local" and m["status"] == "offline"]
    if offline and not local_models:
        from utils.icons import mi_inline
        st.markdown(
            mi_inline("cloud_off", "Ollama offline", 16, color="var(--color-text-muted)"),
            unsafe_allow_html=True,
        )
```

### 4.3 Integrasikan Model Selector ke Layout Chat

- [x] Di `render_chat_tab()`, tambahkan pemanggilan `_render_chat_model_selector()` **di bagian atas**, sebelum riwayat chat dan input area:

```python
def render_chat_tab():
    """Render tab Chat: history view ATAU live chat."""

    if st.session_state.is_viewing_history:
        _render_history_view()
        return

    # --- Model Selector (hanya di tab Chat) ---
    _render_chat_model_selector()
    st.divider()

    # ... rest of existing chat rendering ...
```

### 4.4 Pastikan `chat_mode` Masih Bekerja

- [x] Verifikasi bahwa `st.session_state.chat_mode` masih dikirim di `send_message()` (`client.py` line 28):

```python
opts["chat_mode"] = st.session_state.get("chat_mode", "local")
```

Ini **tidak perlu diubah** — state key tetap sama, hanya tempat render widget yang pindah.

## 5. Output yang Diharapkan

### Sidebar SESUDAH:

```
🤖 TOR Generator
[Obrolan baru]
───────────────
RIWAYAT
[dropdown session ▾]
[Lihat Semua]
───────────────
PROGRESS
[■■■■■■□□□□] 60%
Turn: 5    Status: CHATTING
Fields (3/7)
[Force Generate TOR]
───────────────
SYSTEM
✓ API Connected
Session: abc123...
```

### Tab Chat SESUDAH:

```
┌─────────────────────────────────────┐
│ ○ Local LLM  ● Gemini API         │  ← Radio horizontal
│ gemini-2.5-pro                     │  ← Caption (model info)
├─────────────────────────────────────┤
│ Chat messages...                    │
│ ...                                 │
│ [Send message _______________]      │
└─────────────────────────────────────┘
```

## 6. Acceptance Criteria

- [x] `_render_model_selector()` **dihapus** dari `sidebar.py`.
- [x] Model selector **muncul** di tab Chat (di atas messages).
- [x] Switching provider (Local/Gemini) bekerja — session reset saat ada data.
- [x] Thinking Mode toggle tetap muncul saat model cloud terdeteksi.
- [x] Ollama offline notice tetap muncul.
- [x] `chat_mode` masih dikirim dengan benar di `send_message()`.
- [x] Sidebar lebih bersih (tanpa section MODEL).
- [x] **Belum ada model selector** di tab lain (Gemini Direct, Dari Dokumen, Format TOR).
- [x] Server start tanpa error.
