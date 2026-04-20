# Task 01: Buat `notify()` Utility Function

> **Status**: [x] Selesai
> **Estimasi**: Low (30 menit – 1 jam)
> **Dependency**: Tidak ada (task pertama, fondasi)

## 1. Deskripsi

Buat file utility `streamlit_app/utils/notify.py` yang berisi satu fungsi `notify()` sebagai **satu-satunya cara** menampilkan notifikasi ke user. Fungsi ini mendukung 3 method: `toast`, `banner`, dan `inline`.

## 2. Tujuan Teknis

- File baru `utils/notify.py` dibuat
- Fungsi `notify()` mendukung parameter: `message`, `type`, `icon`, `method`
- Auto-detect icon Material Symbol berdasarkan `type`
- 3 method rendering: `st.toast()`, `banner_html()`, `st.info/error/warning/success`

## 3. Scope

**Yang dikerjakan:**
- Buat `streamlit_app/utils/notify.py`
- Implementasi `notify()` dengan 3 method

**Yang tidak dikerjakan:**
- Migrasi panggilan di file lain (task 2-5)
- Push notification browser native

## 4. Langkah Implementasi

### 4.1 Buat File Baru

- [x] Buat file `streamlit_app/utils/notify.py`:

```python
# streamlit_app/utils/notify.py
"""Unified notification system for Streamlit UI.

Semua notifikasi ke user harus melalui fungsi `notify()`.
Jangan gunakan st.error/st.warning/st.success/st.info secara langsung lagi.
"""

import streamlit as st
from utils.icons import mi, banner_html

# Default Material Symbol icon per notification type
_DEFAULT_ICONS = {
    "success": "task_alt",
    "error": "error",
    "warning": "warning",
    "info": "info",
}

# Emoji fallback untuk st.toast (tidak support HTML)
_TOAST_EMOJI = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
}

# Streamlit built-in icon mapping (untuk parameter icon= di st.info, dll)
_ST_ICON_MAP = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
}


def notify(
    message: str,
    type: str = "info",
    icon: str | None = None,
    method: str = "toast",
) -> None:
    """Tampilkan notifikasi ke user.

    Args:
        message: Pesan untuk ditampilkan
        type: Jenis notifikasi — "success" | "error" | "warning" | "info"
        icon: Nama Material Symbol (auto-detect jika None)
        method: Cara tampil — "toast" | "banner" | "inline"

    Methods:
        - toast: muncul di pojok kanan atas, hilang otomatis (untuk konfirmasi ringan)
        - banner: HTML banner di body halaman, persistent (untuk hasil penting)
        - inline: st.info/error/warning/success bawaan (untuk guard clause / in-place)

    Example:
        >>> notify("TOR berhasil dibuat!", "success")
        >>> notify("Backend offline", "error", icon="cloud_off", method="banner")
        >>> notify("Anda sedang melihat arsip.", "info", method="inline")
    """
    resolved_icon = icon or _DEFAULT_ICONS.get(type, "info")

    if method == "toast":
        _render_toast(message, type)
    elif method == "banner":
        _render_banner(message, type, resolved_icon)
    elif method == "inline":
        _render_inline(message, type)
    else:
        # Fallback ke toast
        _render_toast(message, type)


def _render_toast(message: str, type: str) -> None:
    """Render notifikasi sebagai toast (pojok kanan atas, auto-dismiss)."""
    emoji = _TOAST_EMOJI.get(type, "ℹ️")
    st.toast(f"{emoji} {message}")


def _render_banner(message: str, type: str, icon_name: str) -> None:
    """Render notifikasi sebagai banner HTML (persistent di body)."""
    st.markdown(
        banner_html(icon_name, message, type),
        unsafe_allow_html=True,
    )


def _render_inline(message: str, type: str) -> None:
    """Render notifikasi inline menggunakan st.info/error/warning/success."""
    func_map = {
        "success": st.success,
        "error": st.error,
        "warning": st.warning,
        "info": st.info,
    }
    func = func_map.get(type, st.info)
    st_icon = _ST_ICON_MAP.get(type)
    if st_icon:
        func(message, icon=st_icon)
    else:
        func(message)
```

### 4.2 Pastikan Import Berjalan

- [x] Verifikasi bahwa `from utils.icons import mi, banner_html` berfungsi dari konteks `utils/notify.py` (keduanya ada di file yang sama level).

## 5. Output yang Diharapkan

```python
# Dari komponen manapun:
from utils.notify import notify

# Toast (ringan, pojok kanan atas):
notify("TOR berhasil dibuat!", "success")

# Banner (prominent, di body halaman):
notify("Backend tidak tersedia.", "error", icon="cloud_off", method="banner")

# Inline (di tempat, seperti guard clause):
notify("Anda sedang melihat arsip session.", "info", method="inline")
```

## 6. Acceptance Criteria

- [x] File `streamlit_app/utils/notify.py` dibuat.
- [x] `notify()` bisa dipanggil dengan `method="toast"` → `st.toast()` terpanggil.
- [x] `notify()` bisa dipanggil dengan `method="banner"` → `banner_html()` di-render.
- [x] `notify()` bisa dipanggil dengan `method="inline"` → `st.info/error/warning/success` terpanggil.
- [x] Auto-detect icon bekerja saat `icon=None`.
- [x] Custom icon override bekerja: `notify("...", icon="cloud_off")`.
- [x] Import dari komponen lain berjalan: `from utils.notify import notify`.
