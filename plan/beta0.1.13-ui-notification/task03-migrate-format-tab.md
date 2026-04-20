# Task 03: Migrasi Notifikasi — `format_tab.py` + Hapus `icon()` Lokal

> **Status**: [x] Selesai
> **Estimasi**: Medium (1–2 jam)
> **Dependency**: Task 01

## 1. Deskripsi

Mengganti semua notifikasi di `format_tab.py` dengan `notify()`, dan **menghapus** fungsi `icon()` lokal (line 6-8) yang duplikat dengan `mi()` dari `utils/icons.py`.

## 2. Tujuan Teknis

- Fungsi lokal `icon()` dihapus → semua pakai `mi()` dari `utils/icons.py`
- 10+ panggilan `st.error/warning/success/info` dimigrasikan ke `notify()`
- Konsistensi icon style di seluruh file

## 3. Scope

**Yang dikerjakan:**
- `streamlit_app/components/format_tab.py` — hapus `icon()`, migrasi notifikasi

**Yang tidak dikerjakan:**
- File lain (task 02, 04, 05)

## 4. Langkah Implementasi

### 4.1 Hapus Fungsi `icon()` Lokal + Tambah Import

- [x] **Hapus** line 6-8:

```python
# HAPUS:
def icon(name: str, size: str = "1.1rem") -> str:
    """Render Material Symbol sebagai HTML inline."""
    return f'<span class="material-symbols-outlined" style="vertical-align:middle;font-size:{size}">{name}</span>'
```

- [x] **Tambah** import di bagian atas:

```python
import streamlit as st
import pandas as pd
from api import client
from utils.icons import mi       # ← BARU: ganti icon() lokal
from utils.notify import notify   # ← BARU: notification system
```

### 4.2 Ganti Semua `icon(...)` → `mi(...)`

Cari-dan-ganti semua pemanggilan `icon("name")` → `mi("name")`.

**Catatan**: `icon()` menggunakan `size: str` (CSS unit, e.g. `"1.1rem"`), sedangkan `mi()` menggunakan `size: int` (pixel). Konversi:

| `icon()` call | `mi()` replacement |
|---------------|---------------------|
| `icon("palette", "1.4rem")` | `mi("palette", 22)` |
| `icon("description")` | `mi("description", 18)` |
| `icon("format_list_bulleted")` | `mi("format_list_bulleted", 18)` |
| `icon("tune")` | `mi("tune", 18)` |
| `icon("auto_awesome")` | `mi("auto_awesome", 18)` |
| `icon("edit_note")` | `mi("edit_note", 18)` |

- [x] Ganti semua pemanggilan (cari `icon(` dan ganti):

```python
# Line 13 — SEBELUM:
icon("palette", "1.4rem") + " **Konfigurasi Format TOR**"
# SESUDAH:
mi("palette", 22) + " **Konfigurasi Format TOR**"

# Line 64 — SEBELUM:
icon("description") + f" **{selected_style['name']}**"
# SESUDAH:
mi("description", 18) + f" **{selected_style['name']}**"

# Line 123 — SEBELUM:
icon("auto_awesome") + " **Ekstrak Format dari Dokumen**"
# SESUDAH:
mi("auto_awesome", 18) + " **Ekstrak Format dari Dokumen**"

# dll — cari semua `icon(` dan ganti ke `mi(`
```

### 4.3 Migrasi Notifikasi — Style Management

```python
# Line 20 — SEBELUM:
st.warning("Menunggu koneksi backend untuk memuat format...")
# SESUDAH:
notify("Menunggu koneksi backend untuk memuat format...", "warning", icon="sync", method="inline")

# Line 49 — SEBELUM:
st.success("Format aktif berhasil diubah.")
# SESUDAH:
notify("Format aktif berhasil diubah.", "success")

# Line 52 — SEBELUM:
st.error("Gagal mengubah format aktif.")
# SESUDAH:
notify("Gagal mengubah format aktif.", "error")
```

### 4.4 Migrasi Notifikasi — Action Row (Klon, Hapus)

```python
# Line 93 (klon error) — SEBELUM:
st.error(res["error"])
# SESUDAH:
notify(res["error"], "error", method="inline")

# Line 100 (hapus warning) — SEBELUM:
st.warning("Tindakan ini tidak bisa dibatalkan.")
# SESUDAH:
notify("Tindakan ini tidak bisa dibatalkan.", "warning", method="inline")

# Line 102 (hapus guard) — SEBELUM:
st.error("Ubah aktif style ke format lain sebelum menghapus!")
# SESUDAH:
notify("Ubah aktif style ke format lain sebelum menghapus!", "error", method="inline")

# Line 107 (hapus error) — SEBELUM:
st.error(res["error"])
# SESUDAH:
notify(res["error"], "error", method="inline")
```

### 4.5 Migrasi Notifikasi — Extraction Section

```python
# Line 126-129 (info box) — SEBELUM:
st.info(
    "AI dapat membaca struktur format TOR dari contoh dokumen Word/PDF "
    "dan membuatkannya menjadi profil baru yang bisa langsung Anda pakai."
)
# SESUDAH:
notify(
    "AI dapat membaca struktur format TOR dari contoh dokumen Word/PDF "
    "dan membuatkannya menjadi profil baru yang bisa langsung Anda pakai.",
    "info", icon="auto_awesome", method="inline"
)

# Line 148 — SEBELUM:
st.error(f"Gagal melakukan ekstraksi: {res['error']}")
# SESUDAH:
notify(f"Gagal melakukan ekstraksi: {res['error']}", "error", method="banner")

# Line 155 — SEBELUM:
st.error(f"Gagal menyimpan: {save_res['error']}")
# SESUDAH:
notify(f"Gagal menyimpan: {save_res['error']}", "error", method="banner")

# Line 157 — SEBELUM:
st.success("Ekstraksi berhasil! Format baru telah ditambahkan.")
# SESUDAH:
notify("Ekstraksi berhasil! Format baru telah ditambahkan.", "success")

# Line 163 — SEBELUM:
st.error(f"Error: {e}")
# SESUDAH:
notify(f"Terjadi kesalahan: {e}", "error", method="banner")
```

### 4.6 Migrasi Notifikasi — Edit Form

```python
# Line 352 — SEBELUM:
st.error(f"Gagal menyimpan: {result['error']}")
# SESUDAH:
notify(f"Gagal menyimpan: {result['error']}", "error")

# Line 354 — SEBELUM:
st.success("Style berhasil disimpan!")
# SESUDAH:
notify("Style berhasil disimpan!", "success")
```

## 5. Output yang Diharapkan

- File tidak lagi memiliki fungsi `icon()` lokal
- Semua icon render via `mi()` dari `utils/icons.py`
- Semua notifikasi via `notify()`
- Server start tanpa error

## 6. Acceptance Criteria

- [x] Fungsi `icon()` lokal (line 6-8) **dihapus** dari file.
- [x] Semua `icon(...)` diganti menjadi `mi(...)` dengan size pixel yang tepat.
- [x] Tidak ada panggilan `st.error/warning/info/success` langsung.
- [x] Semua notifikasi melalui `notify()`.
- [x] Tab "Format TOR" tetap berfungsi normal (CRUD styles, extraction).
- [x] Server start tanpa import error.
