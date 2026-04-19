# Task 07: Component — Sidebar (`components/sidebar.py`)

## Status: 🔲 Pending

---

## 1. Judul Task

Extract dan redesign sidebar dengan Material Icons dan layout baru.

## 2. Deskripsi

Pindahkan seluruh sidebar UI dari monolit ke `components/sidebar.py`. Ganti
semua emoji dengan Material Icons. Sidebar berisi: brand, new chat button,
model selector, progress bar, fields checklist, force generate, dan system status.

## 3. Tujuan Teknis

- `render_sidebar()` — single entry function yang render seluruh sidebar
- Gunakan Material Icons untuk semua visual indicators
- Sidebar labels menggunakan CSS class `.sidebar-label`
- Model selector (radio + selectbox) tetap fungsional

## 4. Scope

**Yang dikerjakan:**
- `components/sidebar.py` — semua sidebar sections
- Material Icons: `smart_toy`, `add_comment`, `tune`, `computer`, `auto_awesome`,
  `analytics`, `checklist`, `check_circle`, `radio_button_unchecked`, `bolt`,
  `monitoring`, `error`, `warning`, `cloud_off`

**Yang TIDAK dikerjakan:**
- Header / tema toggle (Task 08)
- Chat area (Task 09)
- Forms (Task 10-11)

## 5. Langkah Implementasi

### Step 1: Buat `components/sidebar.py`

Extract dari `streamlit_app.py` lines 303-419:

```python
# streamlit_app/components/sidebar.py
"""Sidebar UI — brand, model selector, progress, fields, system status."""

import streamlit as st
from utils.icons import mi, mi_inline
from state import reset_session
from api.client import fetch_models, check_health, force_generate, handle_response
from config import REQUIRED_FIELDS, OPTIONAL_FIELDS, FIELD_LABELS


def render_sidebar():
    """Render seluruh konten sidebar."""
    with st.sidebar:
        _render_brand()
        _render_new_chat()
        st.divider()
        _render_model_selector()
        st.divider()
        _render_progress()
        _render_fields_checklist()
        _render_force_generate()
        st.divider()
        _render_system_status()


def _render_brand():
    """Logo dan nama aplikasi."""
    st.markdown(
        f'<h2 style="margin:0;">'
        f'{mi("smart_toy", 28, "var(--color-primary)")} TOR Generator'
        f'</h2>',
        unsafe_allow_html=True,
    )


def _render_new_chat():
    """Tombol obrolan baru."""
    if st.button("Obrolan baru", use_container_width=True, type="primary"):
        reset_session()
        st.rerun()


def _render_model_selector():
    """Radio buttons untuk memilih provider (Local / Gemini) + model selectbox."""
    st.markdown(
        '<p class="sidebar-label">MODEL</p>',
        unsafe_allow_html=True,
    )

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
        st.error("Tidak ada model tersedia!")
        return

    current_label = next(
        (lbl for lbl, m in mode_map.items() if m == st.session_state.chat_mode),
        mode_opts[0],
    )
    selected = st.radio(
        "Provider",
        mode_opts,
        index=mode_opts.index(current_label),
        label_visibility="collapsed",
    )
    new_mode = mode_map.get(selected, "local")

    if new_mode == "local" and local_models:
        chat_models = [
            m["id"] for m in local_models
            if "embed" not in m["id"].lower() and "nomic" not in m["id"].lower()
        ]
        if chat_models:
            st.selectbox("Model", chat_models, label_visibility="collapsed")

    if new_mode == "gemini" and gemini_models:
        st.caption(f"_{gemini_models[0]['id']}_")

    # Handle mode switch
    if new_mode != st.session_state.chat_mode:
        if st.session_state.session_id and st.session_state.messages:
            st.warning("Ganti model = reset session")
            if st.button("Konfirmasi Reset", use_container_width=True):
                st.session_state.chat_mode = new_mode
                reset_session()
                st.rerun()
        else:
            st.session_state.chat_mode = new_mode

    # Ollama offline notice
    offline = [m for m in models if m["type"] == "local" and m["status"] == "offline"]
    if offline and not local_models:
        st.markdown(
            mi_inline("cloud_off", "Ollama offline", 16, color="var(--color-text-muted)"),
            unsafe_allow_html=True,
        )


def _render_progress():
    """Progress bar + turn count + status."""
    st.markdown('<p class="sidebar-label">PROGRESS</p>', unsafe_allow_html=True)

    state = st.session_state.current_state
    score = state.get("completeness_score", 0.0)
    st.progress(score, text=f"{score:.0%}")

    c1, c2 = st.columns(2)
    c1.metric("Turn", state.get("turn_count", 0))
    c2.metric("Status", state.get("status", "NEW")[:10])


def _render_fields_checklist():
    """Checklist field TOR yang sudah/belum terisi."""
    state = st.session_state.current_state
    filled = state.get("filled_fields", [])
    filled_count = sum(1 for f in REQUIRED_FIELDS if f in filled)

    with st.expander(f"Fields ({filled_count}/{len(REQUIRED_FIELDS)})"):
        for f in REQUIRED_FIELDS:
            if f in filled:
                icon = mi("check_circle", 16, "var(--color-success)", filled=True)
            else:
                icon = mi("radio_button_unchecked", 16, "var(--color-text-subtle)")
            label = FIELD_LABELS.get(f, f.replace("_", " ").title())
            st.markdown(f"{icon} {label}", unsafe_allow_html=True)

        st.caption("_Opsional_")
        for f in OPTIONAL_FIELDS:
            if f in filled:
                icon = mi("check_circle", 16, "var(--color-success)", filled=True)
            else:
                icon = mi("check_box_outline_blank", 16, "var(--color-text-subtle)")
            label = FIELD_LABELS.get(f, f.replace("_", " ").title())
            st.markdown(f"{icon} {label}", unsafe_allow_html=True)


def _render_force_generate():
    """Tombol force generate (hanya muncul jika relevant)."""
    if st.session_state.session_id and not st.session_state.tor_document:
        st.divider()
        if st.button("Force Generate TOR", use_container_width=True):
            with st.spinner("Generating..."):
                data = force_generate(st.session_state.session_id)
            if handle_response(data):
                st.rerun()
    elif st.session_state.tor_document:
        st.divider()
        st.markdown(
            mi_inline("task_alt", "TOR ready", 16, color="var(--color-success)"),
            unsafe_allow_html=True,
        )


def _render_system_status():
    """System status: API health + session ID."""
    st.markdown('<p class="sidebar-label">SYSTEM</p>', unsafe_allow_html=True)

    health = check_health()
    h = health.get("status", "unreachable")

    if h == "healthy":
        st.markdown(
            mi_inline("check_circle", "API Connected", 16, color="var(--color-success)"),
            unsafe_allow_html=True,
        )
    elif h == "unreachable":
        st.markdown(
            mi_inline("error", "API Offline", 16, color="var(--color-error)"),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            mi_inline("warning", h, 16, color="var(--color-warning)"),
            unsafe_allow_html=True,
        )

    if st.session_state.session_id:
        sid = st.session_state.session_id[:8]
        st.caption(f"Session: `{sid}...`")
```

### Step 2: Update `app.py`

```python
from components.sidebar import render_sidebar
render_sidebar()
```

### Step 3: Verifikasi visual

- Material Icons render di semua lokasi sidebar
- Model selector berfungsi
- Progress bar dan fields checklist akurat
- System status menunjukkan warna yang benar

## 6. Output yang Diharapkan

```
streamlit_app/components/
├── __init__.py
├── sidebar.py       (~180 lines)
```

## 7. Dependencies

- **Task 01** — config, state
- **Task 03** — `mi()`, `mi_inline()`
- **Task 04** — `fetch_models`, `check_health`, `force_generate`, `handle_response`

## 8. Acceptance Criteria

- [ ] `render_sidebar()` menampilkan brand dengan icon `smart_toy`
- [ ] Tombol "Obrolan baru" berfungsi (reset session)
- [ ] Model selector (radio + selectbox) berfungsi
- [ ] Progress bar menampilkan score yang benar
- [ ] Fields checklist menampilkan `check_circle` (filled) dan `radio_button_unchecked` (empty)
- [ ] System status menampilkan ikon warna yang benar (green/red/yellow)
- [ ] Session ID ditampilkan jika ada
- [ ] Tidak ada emoji tersisa — semua Material Icons

## 9. Estimasi

**Medium** — Sidebar paling kompleks karena banyak sub-sections.
