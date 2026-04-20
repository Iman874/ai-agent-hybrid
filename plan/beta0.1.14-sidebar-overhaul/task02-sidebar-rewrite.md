# Task 02: Sidebar Rewrite — ChatGPT-Style Layout

## 1. Judul Task

Rewrite total `sidebar.py` — model selector, session list, tools, bottom section

## 2. Deskripsi

Menulis ulang sidebar dari layout dashboard (dropdown session + progress bar + fields checklist) menjadi layout ChatGPT-style minimalis (model selector + button list + tools radio + status compact).

## 3. Tujuan Teknis

- Hapus: `st.selectbox` riwayat (penyebab bug loop), progress section, fields checklist, force generate, system status 3-baris
- Tambah: model selector `nama · provider`, button list session, tools radio, status 1-baris
- Semua icon pakai `mi()` atau `icon=":material/...:"` — TIDAK ADA emoji

## 4. Scope

**Yang dikerjakan:**
- `streamlit_app/components/sidebar.py` — rewrite total

**Yang tidak dikerjakan:**
- `app.py` layout (task 03)
- Settings dialog (task 05)
- CSS styling (task 06)

## 5. Langkah Implementasi

### 5.1 Update Imports

```python
# sidebar.py
import streamlit as st
from utils.icons import mi, mi_inline
from utils.notify import notify
from state import reset_session, load_history_session, back_to_active
from api.client import check_health, fetch_models, fetch_session_list, fetch_session_detail, delete_session
```

Hapus imports yang tidak dipakai lagi: `force_generate`, `handle_response`, `REQUIRED_FIELDS`, `OPTIONAL_FIELDS`, `FIELD_LABELS`.

### 5.2 Rewrite `render_sidebar()`

```python
def render_sidebar():
    with st.sidebar:
        _render_model_selector()
        _render_new_chat()
        st.markdown("---")
        _render_session_list()
        st.markdown("---")
        _render_tools()
        _render_bottom()
```

### 5.3 Implementasi `_render_model_selector()`

```python
def _render_model_selector():
    models = fetch_models()
    options = []
    for m in models:
        if m["status"] != "available":
            continue
        if "embed" in m["id"].lower() or "nomic" in m["id"].lower():
            continue
        provider = "Ollama" if m["type"] == "local" else "Gemini"
        options.append({
            "id": m["id"],
            "type": m["type"],
            "label": f"{m['id']} · {provider}",
        })

    if not options:
        st.markdown(
            f"<small style='color:var(--color-text-subtle)'>"
            f"{mi('warning', 14, 'var(--color-warning)')} Model tidak tersedia</small>",
            unsafe_allow_html=True,
        )
        return

    labels = [o["label"] for o in options]

    # Edge case: validasi index
    current_id = st.session_state.get("active_model_id")
    current_idx = 0
    if current_id:
        match = next((i for i, o in enumerate(options) if o["id"] == current_id), None)
        current_idx = match if match is not None else 0

    selected_idx = st.selectbox(
        "Model AI",
        range(len(labels)),
        format_func=lambda i: labels[i],
        index=current_idx,
        label_visibility="collapsed",
        key="model_selector",
    )

    # Clamp index (defensive)
    if selected_idx >= len(options):
        selected_idx = 0

    selected = options[selected_idx]

    # Hanya trigger jika BENAR-BENAR berubah
    if selected["id"] != st.session_state.get("active_model_id"):
        new_mode = "local" if selected["type"] == "local" else "gemini"
        if st.session_state.session_id and st.session_state.messages:
            notify("Ganti model akan mereset sesi.", "warning", method="inline")
            if st.button("Konfirmasi Reset", key="model_reset", use_container_width=True):
                st.session_state.active_model_id = selected["id"]
                st.session_state.chat_mode = new_mode
                reset_session()
                st.rerun()
        else:
            st.session_state.active_model_id = selected["id"]
            st.session_state.chat_mode = new_mode
```

### 5.4 Implementasi `_render_new_chat()`

```python
def _render_new_chat():
    if st.button(
        "Obrolan baru",
        icon=":material/add:",
        use_container_width=True,
        type="primary",
        key="new_chat",
    ):
        reset_session()
        st.rerun()
```

### 5.5 Implementasi `_render_session_list()` (Anti-Flicker)

```python
def _render_session_list():
    st.caption("RIWAYAT")

    # Anti-flicker: early return jika sedang loading
    loading = st.session_state.get("_loading_session_id")
    if loading:
        st.caption("_Memuat sesi..._")
        return

    sessions = fetch_session_list(limit=4)

    if not sessions:
        st.markdown(
            f"<div style='text-align:center;padding:16px 0;color:var(--color-text-subtle)'>"
            f"{mi('forum', 32, 'var(--color-text-subtle)')}<br>"
            f"<small>Belum ada percakapan<br>Mulai obrolan baru</small>"
            f"</div>",
            unsafe_allow_html=True,
        )
        return

    for s in sessions:
        title = s["title"] or f"Sesi {s['id'][:8]}"
        if len(title) > 32:
            title = title[:32] + "…"

        is_active = (
            s["id"] == st.session_state.session_id
            and not st.session_state.is_viewing_history
        )
        is_viewing = (
            st.session_state.is_viewing_history
            and st.session_state.history_session
            and st.session_state.history_session.get("id") == s["id"]
        )

        # Layout 2 kolom: [title] [hapus]
        col_title, col_del = st.columns([5, 1])

        with col_title:
            if st.button(
                title,
                key=f"s_{s['id']}",
                use_container_width=True,
                type="primary" if (is_active or is_viewing) else "secondary",
                disabled=is_active,
            ):
                st.session_state._loading_session_id = s["id"]

                if is_viewing:
                    back_to_active()
                else:
                    detail = fetch_session_detail(s["id"])
                    if detail:
                        load_history_session(detail)

                st.session_state._loading_session_id = None
                st.rerun()

        with col_del:
            if not is_active:  # Tidak bisa hapus sesi aktif
                if st.button(
                    "",
                    icon=":material/close:",
                    key=f"del_{s['id']}",
                ):
                    delete_session(s["id"])
                    st.rerun()

    if len(sessions) >= 4:
        if st.button(
            "Lihat semua",
            icon=":material/arrow_forward:",
            key="all_sessions",
            use_container_width=True,
        ):
            show_all_sessions_dialog()
```

### 5.6 Implementasi `_render_tools()`

```python
def _render_tools():
    st.caption("ALAT")

    tool_labels = {
        "chat": "Obrolan",
        "generate_doc": "Generate Dokumen",
    }
    current = st.session_state.get("active_tool", "chat")
    keys = list(tool_labels.keys())

    selected = st.radio(
        "Alat",
        keys,
        format_func=lambda k: tool_labels[k],
        index=keys.index(current) if current in keys else 0,
        label_visibility="collapsed",
        key="tool_radio",
    )

    if selected != current:
        st.session_state.active_tool = selected
        st.rerun()
```

### 5.7 Implementasi `_render_bottom()`

```python
def _render_bottom():
    st.markdown("---")
    if st.button(
        "Pengaturan",
        icon=":material/settings:",
        use_container_width=True,
        key="btn_settings",
    ):
        show_settings_dialog()

    health = check_health()
    ok = health.get("status") == "healthy"
    dot = mi("circle", 6, "var(--color-success)" if ok else "var(--color-error)", filled=True)
    label = "API Terhubung" if ok else "API Terputus"
    sid = f" · {st.session_state.session_id[:8]}" if st.session_state.session_id else ""
    st.markdown(
        f"<small style='color:var(--color-text-subtle)'>{dot} {label}{sid}</small>",
        unsafe_allow_html=True,
    )
```

> **Catatan**: `show_settings_dialog` akan diimpor dari `settings_dialog.py` (task 05). Untuk sementara, buat placeholder:

```python
def show_settings_dialog():
    """Placeholder — akan diimplementasi di task 05."""
    pass
```

### 5.8 Pertahankan `show_all_sessions_dialog()`

Fungsi `@st.dialog` untuk lihat semua session — **pindahkan dari kode lama**. Sudah ada dan berfungsi (dari beta 0.1.11). Pastikan emoji di dalamnya diganti `mi()`.

## 6. Output yang Diharapkan

Sidebar baru:

```
┌──────────────────────────┐
│ gemma4:e2b · Ollama  ▾   │
│                          │
│ [add] Obrolan baru       │
│ ──────────────────       │
│ RIWAYAT                  │
│   Pengadaan la..    [×]  │
│   Workshop AI..     [×]  │
│   Training De..     [×]  │
│ ▌Sesi aktif              │
│   Lihat semua →          │
│ ──────────────────       │
│ ALAT                     │
│   ● Obrolan              │
│   ○ Generate Dokumen     │
│ ──────────────────       │
│ [settings] Pengaturan    │
│ [●] API Terhubung · abc  │
└──────────────────────────┘
```

> Maks 4 sesi, `[×]` = tombol hapus (`icon=":material/close:"`), sesi aktif tanpa tombol hapus.

## 7. Dependencies

- Task 01 (state update)

## 8. Acceptance Criteria

- [ ] Tidak ada `st.selectbox` untuk riwayat session (bug loop fixed)
- [ ] Tidak ada progress bar, fields checklist, force generate di sidebar
- [ ] Model selector menampilkan `nama · provider` format
- [ ] Model selector fallback ke index 0 jika invalid
- [ ] Session list button-based — klik 1x = load 1x (anti-flicker)
- [ ] Session aktif → disabled (tidak bisa diklik)
- [ ] Maks 4 sesi ditampilkan (bukan 8)
- [ ] Tombol hapus `[×]` per sesi (kecuali sesi aktif)
- [ ] Empty state riwayat pakai `mi("forum")` bukan emoji
- [ ] Tools radio hanya 2: Obrolan + Generate Dokumen
- [ ] Status 1 baris: `API Terhubung · abc123`
- [ ] Semua icon pakai `mi()` atau `icon=":material/..."` — TIDAK ADA emoji
- [ ] Tombol: Obrolan baru (`icon=":material/add:"`), Pengaturan (`icon=":material/settings:"`), Lihat semua (`icon=":material/arrow_forward:"`), Hapus (`icon=":material/close:"`)
- [ ] Server start tanpa error

## 9. Estimasi

High (2–3 jam)
