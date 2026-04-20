# 📘 Plan Design — Beta 0.1.14
# ChatGPT-Style UI Overhaul — Stabilized

> **Codename**: `chatgpt-style-ui`
> **Versi**: Beta 0.1.14
> **Tanggal**: 2026-04-20
> **Status**: Draft — Menunggu Review
> **Prasyarat**: Beta 0.1.13 (UI Notification) selesai

---

## 1. Ringkasan

Mengubah layout aplikasi dari **tab-based dashboard** menjadi **sidebar-driven chat UI** bergaya ChatGPT. Fokus pada stabilitas, edge case handling, dan UX polish tanpa fitur baru.

### Bug yang Diperbaiki

| Bug | Penyebab | Fix |
|-----|----------|-----|
| Infinite loop saat pilih session | `st.selectbox` retain value + `st.rerun()` setiap render | Hapus selectbox → button list |
| Dropdown tidak reset setelah "Obrolan baru" | `reset_session()` tidak mereset widget key | Tidak ada dropdown lagi |

### Elemen yang DIHAPUS dari UI

| Element | Pengganti |
|---------|-----------|
| `st.tabs(["Chat","Gemini Direct","Dari Dokumen","Format TOR"])` | Sidebar Tools radio |
| `st.selectbox` riwayat session | Button list |
| Progress bar + metrics di sidebar | Dihapus sepenuhnya |
| Fields checklist di sidebar | Dihapus sepenuhnya |
| Force Generate di sidebar | Dihapus sepenuhnya |
| System status 3-baris | 1 baris kecil di bawah sidebar |
| Theme popover di header | Pindah ke Settings dialog |
| Model selector di chat.py | Pindah ke sidebar top |
| Tab "Gemini Direct" | Dihapus dari navigasi |
| Tab "Format TOR" | Pindah ke Settings dialog |

---

## 2. Target Layout

```
┌────────────────────┬──────────────────────────────────────┐
│                    │ [smart_toy] TOR Generator            │
│ gemma4:e2b · Olla▾ │──────────────────────────────────────│
│                    │                                      │
│ [add] Obrolan baru │                                      │
│                    │                                      │
│ RIWAYAT            │           [forum]                    │
│   Pengadaan laptop │   Ceritakan kebutuhan TOR Anda       │
│   Workshop AI      │   Mulai chat untuk menyusun          │
│   Training DevOps  │   Term of Reference.                 │
│                    │                                      │
│ ALAT               │                                      │
│   ● Obrolan        │                                      │
│   ○ Generate Dokumen│                                     │
│                    │                                      │
│ ─────────────────  │                                      │
│ [settings] Pengaturan │                                   │
│ [circle] API · abc123 │ [Tanyakan apa saja...          ]  │
└────────────────────┴──────────────────────────────────────┘
```

> Semua `[nama]` di atas = Material Design icon via `mi()` atau `icon=":material/nama:"`.
> TIDAK ADA emoji.

---

## 3. Spesifikasi Per Element — Stabilized

### Constraint: Icon

Semua icon WAJIB menggunakan `mi()` atau `mi_inline()` dari `utils/icons.py`.

**Daftar icon yang digunakan:**

| Konteks | Icon Name | Metode |
|---------|-----------|--------|
| Header brand | `smart_toy` | `mi("smart_toy", 20, "var(--color-primary)")` (HTML) |
| Obrolan baru button | `add` | `st.button("Obrolan baru", icon=":material/add:")` |
| Empty state riwayat | `forum` | `mi("forum", 32, ...)` (HTML) |
| Empty state chat | `forum` | `mi("forum", 64, ...)` (HTML) |
| Tool: Obrolan | `chat` | Label text: `"Obrolan"` |
| Tool: Generate Dokumen | `description` | Label text: `"Generate Dokumen"` |
| Pengaturan button | `settings` | `st.button("Pengaturan", icon=":material/settings:")` |
| Status dot (online) | `circle` | `mi("circle", 6, "var(--color-success)", filled=True)` (HTML) |
| Status dot (offline) | `circle` | `mi("circle", 6, "var(--color-error)", filled=True)` (HTML) |
| TOR ready | `task_alt` | Existing usage |
| Lihat semua button | `arrow_forward` | `st.button("Lihat semua", icon=":material/arrow_forward:")` |

**Cara pasang icon di Streamlit widget:**
- `st.button(label, icon=":material/icon_name:")` → icon built-in Streamlit
- `mi("icon_name", size)` → HTML span (untuk `st.markdown(..., unsafe_allow_html=True)`)  
- `st.radio` format_func **tidak support HTML** → gunakan plain text label

**TIDAK BOLEH**: Emoji sebagai icon utama UI (`✅`, `⏳`, `⚡`, `📋`, `📄`, `💬`, `⚙`).

---

### 3.1 Sidebar — A. Model AI Selector

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

    # --- Edge case: validasi index ---
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

    # --- Clamp index (defensive) ---
    if selected_idx >= len(options):
        selected_idx = 0

    selected = options[selected_idx]

    # --- Hanya trigger jika BENAR-BENAR berubah ---
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

**Edge cases yang ditangani:**
- List kosong → pesan warning kecil (Material icon, bukan emoji)
- `active_model_id` tidak ada dalam list → fallback ke index 0
- Index out of range → clamp ke 0
- Hanya trigger change jika ID benar-benar berbeda

---

### 3.2 Sidebar — B. Obrolan Baru

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

> `icon=":material/add:"` — Streamlit built-in Material icon parameter. Tidak perlu `mi()`.

---

### 3.3 Sidebar — C. Riwayat (Anti-Flicker)

**Masalah**: `st.button` + `st.rerun()` bisa menyebabkan flicker/double trigger jika state belum stabil saat rerun.

**Solusi**: State guard `_loading_session_id` — hanya proses load jika belum dalam proses loading.

```python
def _render_session_list():
    st.caption("RIWAYAT")

    # --- Anti-flicker: early return jika sedang loading ---
    loading = st.session_state.get("_loading_session_id")
    if loading:
        st.caption("_Memuat sesi..._")
        return

    sessions = fetch_session_list(limit=4)

    if not sessions:
        # Empty state — Material icon via mi(), BUKAN emoji
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

    # Lihat semua
    if len(sessions) >= 4:
        if st.button(
            "Lihat semua",
            icon=":material/arrow_forward:",
            key="all_sessions",
            use_container_width=True,
        ):
            show_all_sessions_dialog()
```

**Anti-flicker flow:**
```
User klik session
     ↓
st.session_state._loading_session_id = "abc"
     ↓
fetch_session_detail() → load_history_session()
     ↓
st.session_state._loading_session_id = None
     ↓
st.rerun()
     ↓
Render ulang: _loading_session_id == None → render normal
```

**Guard di awal fungsi:**
- `if loading: return` → jika `_loading_session_id` masih ada (edge case: rerun cepat), tampilkan "Memuat..." dan skip render buttons
- Ini mencegah double-click dan flicker total

---

### 3.4 Sidebar — D. Alat (Hanya 2)

> **PENTING**: `st.radio` `format_func` **tidak support HTML**.
> Oleh karena itu label tool menggunakan plain text, bukan `mi()`.

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

    # Hanya rerun jika BENAR-BENAR berubah
    if selected != current:
        st.session_state.active_tool = selected
        st.rerun()
```

**Validasi:**
- Hanya `"chat"` dan `"generate_doc"` — tidak ada `"direct"`, tidak ada tab lain
- Label UI: `"Obrolan"` dan `"Generate Dokumen"` (full Bahasa Indonesia)
- `format_func` → plain text (radio tidak mendukung HTML)
- Index fallback ke 0 jika `current` invalid
- Rerun hanya saat berubah

---

### 3.5 Sidebar — E. Bawah

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

    # Status — 1 baris kecil, icon via mi() (HTML)
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

> `icon=":material/settings:"` → Streamlit built-in, bukan `mi()`.  
> Status dot tetap pakai `mi()` karena itu HTML inline, bukan widget.

---

### 3.6 Sidebar — Full Render

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

Urutan top-to-bottom:
1. Model selector
2. Obrolan baru
3. ─── divider ───
4. Riwayat (button list)
5. ─── divider ───
6. Alat (radio)
7. ─── divider ───
8. Pengaturan + status

---

### 3.7 Top Bar (Header)

```python
def render_header():
    """Render top bar — hanya tampil di mode Obrolan.
    Di mode Generate Dokumen, form_document.py sudah punya header sendiri.
    """
    tool = st.session_state.get("active_tool", "chat")

    # Hanya tampilkan header di mode Obrolan
    if tool == "chat":
        icon = mi("smart_toy", 20, "var(--color-primary)")
        st.markdown(
            f'<h3 style="margin:0;display:flex;align-items:center;gap:8px;">'
            f'{icon} Generator TOR</h3>',
            unsafe_allow_html=True,
        )
```

- **Mode Obrolan**: tampilkan "Generator TOR" header
- **Mode Generate Dokumen**: TIDAK tampil (form_document.py punya header "Generate TOR dari Dokumen")
- Tidak ada theme popover (sudah di Settings)
- Tidak ada label provider (sudah di sidebar)

---

### 3.8 Area Utama

```python
# app.py
render_sidebar()
render_header()

tool = st.session_state.get("active_tool", "chat")
if tool == "chat":
    render_chat_tab()
elif tool == "generate_doc":
    render_document_tab()
```

- **TIDAK ADA** `st.tabs()` di area utama
- Render langsung berdasarkan `active_tool`

---

### 3.9 Settings Dialog (ChatGPT-Style)

Desain terinspirasi pengaturan ChatGPT — sidebar navigasi kiri + konten kanan, **bukan** tabs lebar.

```
┌────────────────────────────────────────────────┐
│ Pengaturan                                [✕]  │
│                                                │
│ ┌──────────┬─────────────────────────────────┐ │
│ │ ▌Umum    │  Penampilan                     │ │
│ │  Format  │    ○ Default sistem             │ │
│ │  Lanjutan│    ● Gelap                      │ │
│ │          │    ○ Terang                      │ │
│ │          │                                 │ │
│ │          │  ───────────                    │ │
│ │          │                                 │ │
│ │          │  Bahasa                         │ │
│ │          │    ● Bahasa Indonesia            │ │
│ │          │    ○ English                     │ │
│ │          │    (Fitur mendatang)             │ │
│ └──────────┴─────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

```python
# components/settings_dialog.py

@st.dialog("Pengaturan", width="large")
def show_settings_dialog():
    """Dialog pengaturan — ChatGPT-style sidebar nav."""
    col_nav, col_content = st.columns([1, 3])

    # --- Sidebar navigasi ---
    with col_nav:
        nav_items = {
            "umum": "Umum",
            "format_tor": "Format TOR",
            "lanjutan": "Lanjutan",
        }
        current_section = st.session_state.get("_settings_section", "umum")

        for key, label in nav_items.items():
            btn_type = "primary" if key == current_section else "secondary"
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state._settings_section = key
                st.rerun()

    # --- Konten ---
    with col_content:
        section = st.session_state.get("_settings_section", "umum")

        if section == "umum":
            _render_general_settings()
        elif section == "format_tor":
            _render_format_tor_settings()
        elif section == "lanjutan":
            _render_advanced_settings()


def _render_general_settings():
    """Section Umum — Tema + Bahasa."""
    st.markdown("#### Penampilan")
    current = get_current_theme()
    opts = {"system": "Default sistem", "dark": "Gelap", "light": "Terang"}
    selected = st.radio(
        "Tema",
        list(opts.keys()),
        format_func=lambda k: opts[k],
        index=list(opts.keys()).index(current),
        label_visibility="collapsed",
    )
    if selected != current:
        switch_theme(selected)

    st.divider()

    st.markdown("#### Bahasa")
    st.radio(
        "Bahasa", ["Bahasa Indonesia", "English"],
        label_visibility="collapsed",
    )
    st.caption("Fitur bahasa akan tersedia di versi mendatang.")


def _render_format_tor_settings():
    """Section Format TOR — style management."""
    st.markdown("#### Format TOR")
    try:
        from components.format_tab import render_format_settings
        render_format_settings()
    except ImportError:
        st.caption("_Pengaturan format TOR belum tersedia._")


def _render_advanced_settings():
    """Section Lanjutan — pengaturan teknis."""
    st.markdown("#### Pengaturan Lanjutan")
    st.caption("Pengaturan teknis untuk developer.")

    with st.expander("API Endpoint"):
        st.code("http://localhost:8000/api/v1")

    with st.expander("Cache"):
        if st.button("Hapus Cache", key="clear_cache"):
            st.cache_data.clear()
            notify("Cache berhasil dihapus.", "success")
```

**Desain ChatGPT-style:**
- Layout 2 kolom: navigasi sidebar kiri (1/4) + konten kanan (3/4)
- 3 section: **Umum** (tema + bahasa), **Format TOR** (style management), **Lanjutan** (cache, API)
- Navigasi via button list, bukan tabs lebar
- `_settings_section` state mengontrol section aktif

---

## 4. State Changes

```python
# state.py — defaults baru
defaults = {
    ...
    "active_tool": "chat",            # "chat" | "generate_doc"
    "active_model_id": None,          # e.g. "gemma4:e2b"
    "_loading_session_id": None,      # anti-flicker guard
    ...
}

# reset_session() — perubahan:
def reset_session():
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.current_state = { ... }
    st.session_state.tor_document = None
    st.session_state.escalation_info = None
    st.session_state.direct_tor = None
    st.session_state.doc_tor = None
    st.session_state.is_viewing_history = False
    st.session_state.history_session = None
    st.session_state._loading_session_id = None
    # active_tool → reset ke "chat"
    st.session_state.active_tool = "chat"
    # active_model_id → TIDAK direset (preferensi model tetap)
    # chat_mode → TIDAK direset
    # doc style states...
    st.session_state.doc_style_mode = "active"
    st.session_state.doc_selected_style_id = None
    st.session_state.doc_detected_style = None
    st.session_state.doc_awaiting_confirm = False
```

---

## 5. File Changes

### 5.1 File yang Dimodifikasi

| # | File | Perubahan |
|---|------|-----------|
| 1 | `state.py` | Tambah `active_tool`, `active_model_id`, `_loading_session_id` |
| 2 | `sidebar.py` | Rewrite total: model selector, button list, tools, settings |
| 3 | `app.py` | Hapus `st.tabs()`, render by `active_tool` |
| 4 | `header.py` | Simplify: hapus theme popover, hanya teks + `mi("smart_toy")` |
| 5 | `chat.py` | Hapus `_render_chat_model_selector()` |
| 6 | `components.css` | CSS overhaul: sidebar buttons, tools radio, compact |
| 7 | `format_tab.py` | Expose `render_format_settings()` untuk settings dialog |

### 5.2 File Baru

| # | File | Deskripsi |
|---|------|-----------|
| 1 | `components/settings_dialog.py` | `@st.dialog` — tabs: Tampilan / Format TOR / Bahasa |

### 5.3 File yang Dihapus dari Navigasi

| File | Status |
|------|--------|
| `form_direct.py` | Tidak dirender — kode tetap ada, hanya di-skip di `app.py` |

---

## 6. CSS — Micro UX Polish

```css
/* === SIDEBAR OVERHAUL === */

/* Section captions (RIWAYAT, TOOLS) — subtle */
[data-testid="stSidebar"] .stCaption p {
    font-weight: 600 !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: var(--color-text-subtle) !important;
    margin-bottom: var(--space-1) !important;
}

/* Session list buttons — flat, transparent, text-left */
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    text-align: left !important;
    font-size: var(--text-sm) !important;
    font-weight: 400 !important;
    padding: var(--space-2) var(--space-3) !important;
    border-radius: var(--radius-md) !important;
    color: var(--color-text-muted) !important;
    transition: background var(--transition-fast),
                color var(--transition-fast) !important;
}
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
    background: color-mix(in srgb, var(--color-text) 6%, transparent) !important;
    color: var(--color-text) !important;
}

/* Active session — subtle highlight, slightly bolder */
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: color-mix(in srgb, var(--color-primary) 10%, transparent) !important;
    border: none !important;
    box-shadow: none !important;
    text-align: left !important;
    font-size: var(--text-sm) !important;
    font-weight: 600 !important;
    padding: var(--space-2) var(--space-3) !important;
    border-radius: var(--radius-md) !important;
    color: var(--color-text) !important;
}

/* Tools radio — compact, small */
[data-testid="stSidebar"] .stRadio > div {
    gap: 2px !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: var(--text-sm) !important;
    padding: var(--space-1) var(--space-2) !important;
}
[data-testid="stSidebar"] .stRadio label span {
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
}

/* Model selectbox — compact */
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
    font-size: var(--text-sm) !important;
}
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div {
    padding: var(--space-1) var(--space-2) !important;
    border-radius: var(--radius-md) !important;
    border-color: var(--color-border) !important;
}

/* Dividers in sidebar — very subtle */
[data-testid="stSidebar"] hr {
    border-color: color-mix(in srgb, var(--color-border) 40%, transparent) !important;
    margin: var(--space-3) 0 !important;
}

/* Settings button — muted style */
[data-testid="stSidebar"] button[data-testid*="settings"] {
    font-size: var(--text-sm) !important;
    color: var(--color-text-subtle) !important;
}
```

**UX Polish details:**
- Hover: `color-mix(... 6%, transparent)` — sangat halus, bukan kontras keras
- Active: `color-mix(... 10%, transparent)` — subtle, bukan solid color
- Dividers: 40% opacity — tipis
- Font hierarchy: caption 0.65rem → buttons 0.8125rem → brand 1rem
- Spacing: `var(--space-2)` padding konsisten di semua sidebar buttons

---

## 7. Performance Checklist

| Check | Implementasi |
|-------|-------------|
| ❌ Rerun tanpa perubahan state | Tools radio: `if selected != current` guard |
| ❌ Double-click session load | `_loading_session_id` anti-flicker guard |
| ❌ Fetch models setiap render | `@st.cache_data(ttl=30)` pada `fetch_models()` |
| ❌ Fetch sessions setiap render | `@st.cache_data(ttl=10)` pada `fetch_session_list()` |
| ❌ Health check setiap render | `@st.cache_data(ttl=15)` pada `check_health()` |
| ❌ State keys tidak terpakai | Hapus state keys lama yang tidak relevan |

---

## 8. Task Breakdown

| # | Task | Scope | Estimasi |
|---|------|-------|----------|
| 1 | **State update** — Tambah `active_tool`, `active_model_id`, `_loading_session_id`; update `reset_session()` | State | Low |
| 2 | **Sidebar rewrite** — Model selector (edge-case safe), session list (anti-flicker + delete), tools, bottom | Sidebar | High |
| 3 | **App.py rewrite** — Hapus `st.tabs`, render by `active_tool` | Layout | Medium |
| 4 | **Header simplify** — Hapus theme popover, conditional render (hanya mode Obrolan) | Header | Low |
| 5 | **Settings dialog** — ChatGPT-style sidebar nav: Umum / Format TOR / Lanjutan | New file | Medium |
| 6 | **CSS overhaul** — Session buttons, tools radio, subtle dividers, hover polish, delete button | Styling | Medium |
| 7 | **Chat cleanup + performance** — Hapus model selector dari chat.py, tambah `@st.cache_data` | Cleanup | Low |
| 8 | **Hapus sesi** — API endpoint `DELETE /sessions/{id}`, client function, UI button | Backend + UI | Medium |
| 9 | **Fix double header** — Header conditional: hanya mode Obrolan, skip di Generate Dokumen | Header | Low |
| 10 | **Settings redesign** — Ganti tabs → sidebar nav (Umum/Format TOR/Lanjutan), CSS polish | Settings | Medium |

---

## 9. Batasan Scope

| Termasuk | Tidak Termasuk |
|----------|----------------|
| Hapus `st.tabs()` dari area utama | User management / login |
| Session list button-based (anti-flicker) | Search/filter session |
| Delete session via icon button | Session rename |
| Model selector `nama · provider` (edge-case safe) | Session bulk delete |
| Alat: Obrolan + Generate Dokumen (hanya 2) | Tool tambahan |
| Settings dialog (tabs: theme/format/bahasa) | Fitur bahasa aktif |
| CSS ChatGPT-style (micro polish) | Mobile responsive |
| Gemini Direct dihapus dari nav | Hapus kode `form_direct.py` |
| Semua icon Material Design via `mi()` | Library icon baru |
| Anti-flicker session loading | Pagination session |
| `@st.cache_data` untuk API calls | Backend caching |

---

## 10. Verification

### Backend (Developer)
- `active_tool` switches correctly (hanya `"chat"` / `"generate_doc"`)
- `reset_session()` resets `active_tool` ke `"chat"`
- Model selector fallback ke index 0 jika invalid
- Anti-flicker guard prevents double load
- Tidak ada `st.selectbox` untuk session history
- Tidak ada emoji sebagai icon utama UI

### Manual UI (User)
- Klik session → load sekali, tanpa flicker/loop
- "Obrolan baru" → reset clean, riwayat deselect
- Alat switching Obrolan ↔ Generate Dokumen
- Settings dialog opens, tabs work
- Model selector shows `nama · provider`
- Sidebar terasa minimal — bukan dashboard
- Dark mode clean, hover halus
- Tidak ada tab di area utama
