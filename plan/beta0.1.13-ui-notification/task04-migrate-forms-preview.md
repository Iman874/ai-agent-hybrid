# Task 04: Migrasi Notifikasi — `form_document.py`, `form_direct.py`, `tor_preview.py`

> **Status**: [x] Selesai
> **Estimasi**: Low (30 menit – 1 jam)
> **Dependency**: Task 01

## 1. Deskripsi

Mengganti semua notifikasi dan emoji icon di 3 file form/preview component dengan `notify()` dan Material Symbols.

## 2. Tujuan Teknis

- Semua `st.info()`, `banner_html()` langsung → `notify()`
- Emoji dalam pesan diganti dengan text biasa (icon ditangani oleh `notify()`)

## 3. Scope

**Yang dikerjakan:**
- `streamlit_app/components/form_document.py`
- `streamlit_app/components/form_direct.py`
- `streamlit_app/components/tor_preview.py`

**Yang tidak dikerjakan:**
- `sidebar.py` (task 02), `format_tab.py` (task 03), `client.py` dan `chat.py` (task 05)

## 4. Langkah Implementasi

### 4.1 `form_document.py`

**Tambah import:**
```python
from utils.notify import notify
```

**Line 14 — Guard clause history:**
```python
# SEBELUM:
st.info("📋 Anda sedang melihat arsip session. Kembali ke obrolan aktif untuk menggunakan fitur ini.")

# SESUDAH:
notify(
    "Anda sedang melihat arsip session. Kembali ke obrolan aktif untuk menggunakan fitur ini.",
    "info", icon="history", method="inline"
)
```

**Line 69 — Error generate (jika masih ada `banner_html` call):**
```python
# SEBELUM:
st.markdown(
    banner_html("error", result["error"], "error"),
    unsafe_allow_html=True,
)

# SESUDAH:
notify(result["error"], "error", method="banner")
```

**Hapus import `banner_html` jika tidak lagi digunakan:**
```python
# SEBELUM:
from utils.icons import mi, banner_html

# SESUDAH:
from utils.icons import mi
from utils.notify import notify
```

### 4.2 `form_direct.py`

**Tambah import:**
```python
from utils.notify import notify
```

**Line 15 — Guard clause history:**
```python
# SEBELUM:
st.info("📋 Anda sedang melihat arsip session. Kembali ke obrolan aktif untuk menggunakan fitur ini.")

# SESUDAH:
notify(
    "Anda sedang melihat arsip session. Kembali ke obrolan aktif untuk menggunakan fitur ini.",
    "info", icon="history", method="inline"
)
```

**Line 81 — Validation error:**
```python
# SEBELUM:
st.markdown(
    banner_html("error", "Minimal isi <strong>Judul</strong> dan <strong>Tujuan</strong>!", "error"),
    unsafe_allow_html=True,
)

# SESUDAH:
notify("Minimal isi Judul dan Tujuan!", "error", method="banner")
```

**Line 99 — Generate error:**
```python
# SEBELUM:
st.markdown(
    banner_html("error", result["error"], "error"),
    unsafe_allow_html=True,
)

# SESUDAH:
notify(result["error"], "error", method="banner")
```

**Cleanup import:**
```python
# SEBELUM:
from utils.icons import mi, mi_inline, banner_html

# SESUDAH (jika banner_html tidak dipakai lagi):
from utils.icons import mi, mi_inline
from utils.notify import notify
```

### 4.3 `tor_preview.py`

**Tambah import:**
```python
from utils.notify import notify
```

**Line 27 — Success banner:**
```python
# SEBELUM:
st.markdown(
    banner_html("task_alt", "TOR Berhasil Dibuat!", "success"),
    unsafe_allow_html=True,
)

# SESUDAH:
notify("TOR Berhasil Dibuat!", "success", method="banner")
```

**Line 91 — Escalation banner (jika ada):**
```python
# SEBELUM:
st.markdown(
    banner_html("auto_awesome", "TOR di-generate oleh Gemini (escalation)", "info"),
    unsafe_allow_html=True,
)

# SESUDAH:
notify("TOR di-generate oleh Gemini (escalation).", "info", icon="auto_awesome", method="banner")
```

**Cleanup import:**
```python
# SEBELUM:
from utils.icons import mi, mi_inline, banner_html

# SESUDAH (jika banner_html tidak dipakai lagi):
from utils.icons import mi, mi_inline
from utils.notify import notify
```

## 5. Output yang Diharapkan

Ketiga file:
- Tidak ada `st.info()/st.error()` langsung
- Tidak ada `banner_html()` langsung di komponen (semua via `notify()`)
- Tidak ada emoji dalam pesan notifikasi
- Semua notifikasi melalui `notify()`

## 6. Acceptance Criteria

- [x] `form_document.py` — semua notifikasi via `notify()`.
- [x] `form_direct.py` — semua notifikasi via `notify()`.
- [x] `tor_preview.py` — semua notifikasi via `notify()`.
- [x] Guard clause history view menampilkan icon `history` (Material Design).
- [x] Import `banner_html` dihapus dari file yang tidak lagi memakainya langsung.
- [x] Server start tanpa error.
