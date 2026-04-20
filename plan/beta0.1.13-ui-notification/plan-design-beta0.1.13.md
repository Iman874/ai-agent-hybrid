# 📘 Plan Design — Beta 0.1.13
# UI Notification System + Icon Consistency + Model Selector Relocation

> **Codename**: `ui-notification-polish`
> **Versi**: Beta 0.1.13
> **Tanggal**: 2026-04-20
> **Status**: Draft — Menunggu Review
> **Prasyarat**: Beta 0.1.12 (Doc Upload Style) selesai

---

## 1. Masalah yang Ditemukan

### 1.1 Tidak Ada Sistem Notifikasi Terstruktur

Saat ini, semua feedback ke user menggunakan **panggilan Streamlit bawaan yang tersebar** tanpa pola konsisten:

| Metode | Jumlah Panggilan | Masalah |
|--------|------------------|---------|
| `st.error("...")` | 15+ lokasi | Text only, tidak ada icon Material, tidak ada auto-dismiss |
| `st.warning("...")` | 5+ lokasi | Tidak konsisten — kadang ada emoji, kadang tidak |
| `st.success("...")` | 5+ lokasi | Muncul sebentar lalu hilang saat rerun |
| `st.info("...")` | 5+ lokasi | Campur aduk antara guard clause dan notifikasi |
| `banner_html(...)` | 5 lokasi | Sudah lebih baik (pakai Material Icon), tapi hanya di beberapa file |
| `st.toast(...)` | **0 lokasi** | Sama sekali belum dipakai |

**Konsekuensi:**
- User tidak tahu apa yang terjadi saat server mati (`st.error` tersembunyi di sidebar)
- TOR berhasil di-generate tapi tidak ada notifikasi prominent
- Error saat extraction hanya muncul sekilas dan hilang saat rerun
- Style confirmation tidak ada feedback yang jelas

### 1.2 Icon Tidak Konsisten

Dua sistem icon berjalan bersamaan:

| Sistem | Contoh | Lokasi |
|--------|--------|--------|
| **Material Symbols** (via `mi()`) | `mi("check_circle")`, `mi("smart_toy")` | `header.py`, `sidebar.py` (field checklist), `tor_preview.py` |
| **Emoji Unicode** | `✅`, `⏳`, `⚡`, `📋`, `📝`, `📤`, `🎨`, `🔍` | `sidebar.py` (session history), `form_document.py`, `format_tab.py` |
| **Campur** | `"📋 Anda sedang melihat..."` (emoji + text) | `form_document.py`, `form_direct.py`, `chat.py` |

**Contoh spesifik yang harus diperbaiki:**

```python
# sidebar.py line 51 — pakai emoji, bukan Material
icon = "✅" if s["state"] == "COMPLETED" else "⏳" if ...

# sidebar.py line 86 — emoji di button
st.button("📋 Lihat Semua", ...)

# format_tab.py line 6-8 — fungsi icon() sendiri, BUKAN dari utils/icons.py
def icon(name: str, size: str = "1.1rem") -> str:
    return f'<span class="material-symbols-outlined" ...>{name}</span>'

# form_document.py line 14 — emoji di st.info
st.info("📋 Anda sedang melihat arsip session...")
```

### 1.3 Model Selector Salah Tempat

Model selector (Local LLM vs Gemini API) saat ini ada di **sidebar global** (`_render_model_selector()`, line 149-228), padahal:

- Model selection **hanya relevan untuk tab Chat** (wawancara)
- Tab "Gemini Direct", "Dari Dokumen", dan "Format TOR" → **selalu pakai Gemini API** secara default
- User bisa berpikir bahwa mengubah model ke "Local" akan mempengaruhi semua tab — padahal **tidak**
- Header saat ini menampilkan `TOR Generator · Local` vs `TOR Generator · Gemini` yang misleading

---

## 2. Solusi yang Diusulkan

### 2.1 Notification Center — `notify()` Function

Buat sebuah fungsi utility tunggal `notify()` yang menjadi **satu-satunya cara** menampilkan notifikasi ke user:

```python
# streamlit_app/utils/notify.py

def notify(
    message: str,
    type: str = "info",          # "success" | "error" | "warning" | "info"
    icon: str | None = None,      # Material Symbol name, auto-detect jika None
    duration: int = 5,            # Detik sebelum auto-dismiss (0 = persistent)
    method: str = "toast",        # "toast" | "banner" | "inline"
):
    """Satu-satunya fungsi untuk menampilkan notifikasi ke user.

    Methods:
    - toast: st.toast() — muncul di pojok, hilang otomatis (untuk konfirmasi ringan)
    - banner: banner_html() — muncul di body, persistent (untuk hasil penting)
    - inline: st.info/error/warning/success — in-place (untuk guard clause)
    """
```

**Auto-detect icon berdasarkan type:**

| Type | Default Icon | Warna |
|------|-------------|-------|
| `success` | `task_alt` | `var(--color-success)` |
| `error` | `error` | `var(--color-error)` |
| `warning` | `warning` | `var(--color-warning)` |
| `info` | `info` | `var(--color-info)` |

### 2.2 Penggunaan `notify()` di Seluruh Aplikasi

**Aturan:**

| Kategori Event | Method | Contoh |
|----------------|--------|--------|
| **Aksi berhasil** (TOR generated, style disimpan, session reset) | `toast` | `notify("TOR berhasil dibuat!", "success")` |
| **Error** (API down, generation gagal, parse error) | `toast` + `banner` | `notify("Backend tidak tersedia", "error", method="banner")` |
| **Guard clause** (mode history, disabled feature) | `inline` | `notify("Anda sedang melihat arsip", "info", method="inline")` |
| **Konfirmasi** (ganti model, hapus style) | `inline` | `notify("Ganti model = reset session", "warning", method="inline")` |
| **Progress update** (generating, extracting) | Tetap `st.spinner()` | Tidak berubah |

### 2.3 Contoh Migrasi

```python
# SEBELUM (inconsistent):
st.error("Backend tidak bisa dihubungi.")                    # text only
st.success("Format aktif berhasil diubah.")                  # text only
st.info("📋 Anda sedang melihat arsip session.")             # emoji
banner_html("error", result["error"], "error")               # custom HTML
st.warning("Menunggu koneksi backend untuk memuat format...")  # text only

# SESUDAH (consistent via notify()):
notify("Backend tidak bisa dihubungi.", "error", icon="cloud_off")
notify("Format aktif berhasil diubah.", "success")
notify("Anda sedang melihat arsip session.", "info", icon="history", method="inline")
notify(result["error"], "error", method="banner")
notify("Menunggu koneksi backend...", "warning", icon="sync", method="inline")
```

### 2.4 Icon Standardisasi — Semua Pakai Material Design

**Mapping Emoji → Material Symbol:**

| Lokasi | Sebelum (Emoji) | Sesudah (Material) |
|--------|-----------------|---------------------|
| Session history status | `✅` `⏳` `⚡` `📄` | `check_circle` `hourglass_empty` `bolt` `description` |
| Session history TOR | `📝 TOR` | `mi("article", ...)` |
| Lihat Semua button | `📋 Lihat Semua` | `mi_inline("list", "Lihat Semua")` |
| Guard clause | `📋 Anda sedang...` | `mi("history", ...) + text` |
| Style selector | `🎨`, `📋`, `🔍` | `mi("palette")`, `mi("list")`, `mi("search")` |
| Format tab extraction | `✨` | `mi("auto_awesome")` (sudah benar) |
| Popover menu | `⋮` (text) | Tetap `⋮` (ini acceptable sebagai three-dot menu) |

**File `format_tab.py` — Hapus fungsi `icon()` lokal:**

```python
# SEBELUM (line 6-8 format_tab.py):
def icon(name: str, size: str = "1.1rem") -> str:
    return f'<span class="material-symbols-outlined" ...>{name}</span>'

# SESUDAH:
from utils.icons import mi  # Pakai fungsi yang sudah ada
```

### 2.5 Model Selector Relokasi

**Pindahkan dari sidebar → tab Chat**

**Sebelum:**
```
SIDEBAR:
├── Brand
├── Obrolan Baru
├── Riwayat
├── ❌ MODEL SELECTOR ← salah tempat (global padahal hanya untuk chat)
├── Progress
├── Fields Checklist
├── Force Generate
└── System Status
```

**Sesudah:**
```
SIDEBAR:
├── Brand
├── Obrolan Baru
├── Riwayat
├── Progress
├── Fields Checklist
├── Force Generate
└── System Status

TAB CHAT (di atas area input):
┌──────────────────────────┐
│ 🤖 Local LLM  ○ Gemini  │  ← Compact radio
│ Model: qwen2.5:3b ▾     │  ← Selectbox (hanya di local)
└──────────────────────────┘
│ Chat messages...         │
│ [input box]              │
```

**Header juga disederhanakan:**

```python
# SEBELUM:
# "TOR Generator · Local" / "TOR Generator · Gemini" 
# ↑ Ini misleading karena seolah-olah seluruh app pakai satu provider

# SESUDAH:
# "TOR Generator" (tanpa mention provider)
# Provider hanya di tab Chat
```

---

## 3. Arsitektur Perubahan

### 3.1 File Baru

| # | File | Deskripsi |
|---|------|-----------|
| 1 | `streamlit_app/utils/notify.py` | Fungsi `notify()` — notification center |

### 3.2 File yang Dimodifikasi

| # | File | Perubahan |
|---|------|-----------|
| 1 | `streamlit_app/components/sidebar.py` | Hapus `_render_model_selector()`, ganti semua emoji → mi() |
| 2 | `streamlit_app/components/header.py` | Hapus provider label dari title |
| 3 | `streamlit_app/components/chat.py` | Tambah model selector di atas area chat |
| 4 | `streamlit_app/components/format_tab.py` | Hapus fungsi `icon()` lokal → pakai `mi()` dari utils, ganti st.error/success → notify() |
| 5 | `streamlit_app/components/form_document.py` | Ganti st.info/error → notify() |
| 6 | `streamlit_app/components/form_direct.py` | Ganti banner_html direct call → notify() |
| 7 | `streamlit_app/components/tor_preview.py` | Ganti banner_html → notify() |
| 8 | `streamlit_app/api/client.py` | Ganti st.error → notify() |

---

## 4. Detail Teknis

### 4.1 `notify()` Implementation

```python
# streamlit_app/utils/notify.py
import streamlit as st
from utils.icons import mi, banner_html

# Default icon per type
_DEFAULT_ICONS = {
    "success": "task_alt",
    "error": "error",
    "warning": "warning",
    "info": "info",
}

def notify(
    message: str,
    type: str = "info",
    icon: str | None = None,
    method: str = "toast",
) -> None:
    """Unified notification function.

    Args:
        message: Pesan untuk user
        type: "success" | "error" | "warning" | "info"
        icon: Material Symbol name (auto-detect jika None)
        method: "toast" | "banner" | "inline"
    """
    resolved_icon = icon or _DEFAULT_ICONS.get(type, "info")

    if method == "toast":
        # st.toast dengan emoji fallback (toast tidak support HTML)
        emoji_map = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
        st.toast(f"{emoji_map.get(type, 'ℹ️')} {message}")

    elif method == "banner":
        st.markdown(
            banner_html(resolved_icon, message, type),
            unsafe_allow_html=True,
        )

    elif method == "inline":
        func_map = {
            "success": st.success,
            "error": st.error,
            "warning": st.warning,
            "info": st.info,
        }
        icon_html = mi(resolved_icon, 18)
        func = func_map.get(type, st.info)
        func(f"{message}", icon=f":{resolved_icon}:")
```

### 4.2 Model Selector di Tab Chat

```python
# Di chat.py — sebelum chat input area, setelah header
def _render_chat_model_selector():
    """Compact model selector — hanya di tab Chat."""
    col1, col2, col3 = st.columns([2, 2, 1])

    models = fetch_models()
    local_models = [m for m in models if m["type"] == "local" and m["status"] == "available"]
    gemini_models = [m for m in models if m["type"] == "gemini" and m["status"] == "available"]

    with col1:
        mode_opts = []
        if local_models:
            mode_opts.append("Local LLM")
        if gemini_models:
            mode_opts.append("Gemini API")

        if not mode_opts:
            st.caption("⚠️ Tidak ada model")
            return

        selected = st.radio(
            "Chat model",
            mode_opts,
            horizontal=True,
            label_visibility="collapsed",
            key="chat_model_radio",
        )

    with col2:
        new_mode = "local" if selected == "Local LLM" else "gemini"
        if new_mode == "local" and local_models:
            chat_models = [m["id"] for m in local_models
                          if "embed" not in m["id"].lower()]
            if chat_models:
                st.selectbox("Model", chat_models,
                            label_visibility="collapsed",
                            key="chat_model_select")
        elif new_mode == "gemini" and gemini_models:
            st.caption(f"_{gemini_models[0]['id']}_")

    with col3:
        # Thinking mode toggle
        if new_mode == "local":
            ...

    # Handle mode change
    if new_mode != st.session_state.chat_mode:
        ...
```

### 4.3 Sidebar Setelah Cleanup

```python
def render_sidebar():
    with st.sidebar:
        _render_brand()
        _render_new_chat()
        st.divider()
        _render_session_history()  # semua emoji → mi()
        st.divider()
        # ❌ _render_model_selector() — DIHAPUS dari sini
        _render_progress()
        _render_fields_checklist()
        _render_force_generate()
        st.divider()
        _render_system_status()
```

### 4.4 Header Setelah Simplifikasi

```python
def render_header():
    col_title, col_menu = st.columns([9, 1])
    with col_title:
        icon = mi("smart_toy", 22, "var(--color-primary)")
        st.markdown(
            f'<h3 style="margin:0;display:flex;align-items:center;gap:8px;">'
            f'{icon} TOR Generator'
            f'</h3>',
            unsafe_allow_html=True,
        )
    with col_menu:
        _render_theme_popover()
```

---

## 5. Daftar Semua Notifikasi yang Perlu Dimigrasikan

### 5.1 Per File

| File | Line | Sebelum | Sesudah |
|------|------|---------|---------|
| `sidebar.py` | 96 | `st.info("Belum ada riwayat session.")` | `notify("Belum ada riwayat session.", "info", method="inline")` |
| `sidebar.py` | 169 | `st.error("Tidak ada model tersedia!")` | Pindah ke `chat.py` |
| `sidebar.py` | 198 | `st.warning("Ganti model = reset session")` | Pindah ke `chat.py`, `notify(... "warning", method="inline")` |
| `format_tab.py` | 20 | `st.warning("Menunggu koneksi...")` | `notify("Menunggu koneksi backend...", "warning", icon="sync", method="inline")` |
| `format_tab.py` | 49 | `st.success("Format aktif berhasil diubah.")` | `notify("Format aktif berhasil diubah.", "success")` |
| `format_tab.py` | 52 | `st.error("Gagal mengubah format aktif.")` | `notify("Gagal mengubah format aktif.", "error")` |
| `format_tab.py` | 93,107,148,163,352 | `st.error(...)` | `notify(msg, "error", method="banner")` |
| `format_tab.py` | 157,354 | `st.success(...)` | `notify(msg, "success")` |
| `form_document.py` | 14 | `st.info("📋 Anda sedang melihat arsip...")` | `notify("Anda sedang melihat arsip.", "info", icon="history", method="inline")` |
| `form_direct.py` | 15 | `st.info("📋 Anda sedang melihat arsip...")` | `notify("Anda sedang melihat arsip.", "info", icon="history", method="inline")` |
| `client.py` | 161,283,305,307,310 | `st.error(...)` | `notify(..., "error")` |
| `client.py` | 335,339,341,344 | `st.error(...)` | `notify(..., "error")` |
| `tor_preview.py` | 27 | `banner_html("task_alt", "TOR Berhasil!", "success")` | `notify("TOR Berhasil Dibuat!", "success", method="banner")` |
| `chat.py` | 83 | `st.warning("Data session tidak tersedia.")` | `notify("Data session tidak tersedia.", "warning", method="inline")` |
| `chat.py` | 94 | `st.info(...)` | `notify(..., "info", icon="history", method="inline")` |

---

## 6. Task Breakdown Estimasi

| # | Task | Scope | Estimasi |
|---|------|-------|----------|
| 1 | **Buat `notify()` utility** — `utils/notify.py` dengan 3 method (toast/banner/inline) | Utility | Low |
| 2 | **Migrasi notifikasi sidebar.py** — Ganti semua st.error/warning/info/success → notify() | Sidebar | Low |
| 3 | **Migrasi notifikasi format_tab.py** — + hapus fungsi `icon()` lokal → pakai `mi()` dari utils | Format Tab | Medium |
| 4 | **Migrasi notifikasi form_document + form_direct + tor_preview** — Termasuk hapus emoji | Forms & Preview | Low |
| 5 | **Migrasi notifikasi client.py + chat.py** — Error handling di API client | Client & Chat | Low |
| 6 | **Icon consistency — sidebar session history** — Ganti semua emoji status → Material Symbols | Sidebar | Medium |
| 7 | **Relocate model selector** — Hapus dari sidebar, tambah di tab Chat, simplify header | Sidebar + Chat + Header | High |
| 8 | **Unit test notify()** — Test 3 method, test auto-detect icon | Backend test only | Low |

> **Catatan**: Testing UI dilakukan manual oleh user. Task 8 hanya mencakup unit test `notify()`.

---

## 7. Risiko & Mitigasi

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| `st.toast()` tidak support HTML/icon | Icon tidak muncul di toast | Fallback ke emoji Unicode di toast only |
| Model selector di tab Chat mempengaruhi layout | Chat area menyempit | Gunakan `st.columns` compact, collapse jika mobile |
| Terlalu banyak file diubah → regresi | Bug visual | Migrasi per-file, test manual setiap file |
| `notify()` call di `client.py` memicu side-effect | Unexpected toast di background | Pastikan `client.py` hanya return error dict, notify di UI layer |

---

## 8. Batasan Scope Beta 0.1.13

| Termasuk | Tidak Termasuk |
|----------|----------------|
| ✅ `notify()` utility function | ❌ Push notification (browser native) |
| ✅ Migrasi semua st.error/warning/success → notify() | ❌ Notification history/log panel |
| ✅ Semua icon konsisten Material Symbols | ❌ Custom icon set / SVG icons |
| ✅ Model selector pindah ke tab Chat | ❌ Per-tab model selection (Direct juga bisa pilih) |
| ✅ Header disederhanakan | ❌ Redesign layout sidebar |

---

## 9. Verification Plan

### 9.1 Unit Tests (Dikerjakan oleh Developer)

```bash
pytest tests/test_notify.py -v
```

**Test cases:**
- `notify()` dengan method "toast" → `st.toast()` dipanggil
- `notify()` dengan method "banner" → `banner_html()` di-render
- `notify()` dengan method "inline" → `st.info/error/warning/success` dipanggil
- Auto-detect icon berdasarkan type

### 9.2 Manual UI Testing (Dikerjakan oleh User)

User akan melakukan testing UI secara mandiri. Developer **tidak** melakukan UI testing.
