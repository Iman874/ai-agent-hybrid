# Task 05: Migrasi Notifikasi — `client.py` + `chat.py`

> **Status**: [x] Selesai
> **Estimasi**: Low (30 menit – 1 jam)
> **Dependency**: Task 01

## 1. Deskripsi

Mengganti semua panggilan `st.error()` di `client.py` dan `st.warning()/st.info()` di `chat.py` dengan `notify()`.

## 2. Tujuan Teknis

- Semua error handling di API client menggunakan `notify()`
- Chat history view guard clause menggunakan `notify()` dengan Material Icons

## 3. Scope

**Yang dikerjakan:**
- `streamlit_app/api/client.py`
- `streamlit_app/components/chat.py`

**Yang tidak dikerjakan:**
- Pemindahan model selector ke chat (task 07)

## 4. Langkah Implementasi

### 4.1 `client.py` — Migrasi Error Handling

**Tambah import:**
```python
from utils.notify import notify
```

**⚠️ PENTING**: Beberapa `st.error()` di `client.py` berada di dalam fungsi yang juga return value. Pastikan `notify()` **tidak** menggantikan return statement. Pola yang benar:

```python
# BENAR:
notify("Error message", "error")
return None   # tetap return

# SALAH:
notify("Error message", "error")
# lupa return → function continues
```

**Line 161 — `handle_response()`:**
```python
# SEBELUM:
st.error(f"❌ {data['error']}")

# SESUDAH:
notify(data["error"], "error")
```

**Line 283 — `fetch_session_list()`:**
```python
# SEBELUM:
st.error(f"Gagal memuat riwayat session: {e}")

# SESUDAH:
notify(f"Gagal memuat riwayat session: {e}", "error")
```

**Line 305 — `fetch_session_detail()` (404):**
```python
# SEBELUM:
st.error("Session tidak ditemukan.")

# SESUDAH:
notify("Session tidak ditemukan.", "error")
```

**Line 307 — `fetch_session_detail()` (HTTP error):**
```python
# SEBELUM:
st.error(f"Gagal memuat session: HTTP {e.response.status_code}")

# SESUDAH:
notify(f"Gagal memuat session: HTTP {e.response.status_code}", "error")
```

**Line 310 — `fetch_session_detail()` (general error):**
```python
# SEBELUM:
st.error(f"Error: {e}")

# SESUDAH:
notify(f"Error: {e}", "error")
```

**Line 335 — Export (connection error):**
```python
# SEBELUM:
st.error("Backend tidak bisa dihubungi untuk export.")

# SESUDAH:
notify("Backend tidak bisa dihubungi untuk export.", "error", icon="cloud_off")
```

**Line 339 — Export (404):**
```python
# SEBELUM:
st.error("TOR belum di-generate untuk session ini.")

# SESUDAH:
notify("TOR belum di-generate untuk session ini.", "warning", icon="description")
```

**Line 341 — Export (HTTP error):**
```python
# SEBELUM:
st.error(f"Export gagal: HTTP {e.response.status_code}")

# SESUDAH:
notify(f"Export gagal: HTTP {e.response.status_code}", "error")
```

**Line 344 — Export (general error):**
```python
# SEBELUM:
st.error(f"Export error: {e}")

# SESUDAH:
notify(f"Export error: {e}", "error")
```

### 4.2 `chat.py` — Migrasi Guard Clause + Warning

**Tambah import:**
```python
from utils.notify import notify
```

**Line 83 — Warning data session:**
```python
# SEBELUM:
st.warning("Data session tidak tersedia.")

# SESUDAH:
notify("Data session tidak tersedia.", "warning", method="inline")
```

**Line 94 — History view info banner:**
```python
# SEBELUM:
st.info(
    "📋 Anda sedang melihat arsip session lama. "
    "Kembali ke session aktif untuk melanjutkan chat."
)

# SESUDAH:
notify(
    "Anda sedang melihat arsip session lama. "
    "Kembali ke session aktif untuk melanjutkan chat.",
    "info", icon="history", method="inline"
)
```

## 5. Output yang Diharapkan

- `client.py`: Semua 9+ panggilan `st.error()` → `notify()`
- `chat.py`: 2 panggilan `st.warning()` + `st.info()` → `notify()`
- Tidak ada emoji dalam pesan notifikasi
- Return behavior di client functions tetap terjaga

## 6. Acceptance Criteria

- [x] `client.py` — tidak ada `st.error()` langsung.
- [x] `chat.py` — tidak ada `st.warning()/st.info()` langsung.
- [x] Semua error handling di client functions tetap **return properly** setelah notify.
- [x] Guard clause di chat history view menampilkan icon Material `history`.
- [x] Server start tanpa error.
