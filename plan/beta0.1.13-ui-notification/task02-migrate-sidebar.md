# Task 02: Migrasi Notifikasi — `sidebar.py`

> **Status**: [x] Selesai
> **Estimasi**: Low (30 menit – 1 jam)
> **Dependency**: Task 01

## 1. Deskripsi

Mengganti semua panggilan `st.error()`, `st.warning()`, `st.info()`, `st.success()` di `sidebar.py` dengan `notify()`. Juga mengganti emoji Unicode dengan Material Symbols di session history.

## 2. Tujuan Teknis

- Semua notifikasi di sidebar menggunakan `notify()`
- Tidak ada lagi panggilan langsung `st.error/warning/info/success` di file ini
- Emoji status session (`✅`, `⏳`, `⚡`, `📄`) diganti dengan Material Symbols via `mi()`

## 3. Scope

**Yang dikerjakan:**
- `streamlit_app/components/sidebar.py` — migrasi notifikasi + icon

**Yang tidak dikerjakan:**
- Pemindahan model selector (task 07)
- File lain (task 03-05)

## 4. Langkah Implementasi

### 4.1 Tambah Import

- [x] Tambahkan import `notify` di bagian atas:

```python
from utils.notify import notify
```

### 4.2 Migrasi Session History — Icon Status (line 50-56)

- [x] Ubah fungsi `format_label()` dalam `_render_session_history()`:

```python
# SEBELUM (line 50-56):
def format_label(s: dict) -> str:
    icon = "✅" if s["state"] == "COMPLETED" else "⏳" if s["state"] in ("CHATTING", "NEW") else "⚡"
    title = s["title"] or f"Session {s['id'][:8]}"
    if len(title) > 30:
        title = title[:30] + "..."
    return f"{icon} {title}"

# SESUDAH:
def format_label(s: dict) -> str:
    state_icons = {
        "COMPLETED": "✅",
        "CHATTING": "⏳",
        "NEW": "⏳",
        "ESCALATED": "⚡",
    }
    icon = state_icons.get(s["state"], "📄")
    title = s["title"] or f"Session {s['id'][:8]}"
    if len(title) > 30:
        title = title[:30] + "..."
    return f"{icon} {title}"
```

> **Catatan**: `st.selectbox` format_func tidak support HTML, jadi emoji harus tetap di sini.
> Material icon conversion untuk session history dilakukan di dialog modal (step 4.3).

### 4.3 Migrasi Session Dialog — Icon Status (line 99-108)

- [x] Ubah icon status di `show_all_sessions_dialog()`:

```python
# SEBELUM (line 99-108):
if s["state"] == "COMPLETED":
    icon = "✅"
elif s["state"] in ("CHATTING", "NEW"):
    icon = "⏳"
elif s["state"] == "ESCALATED":
    icon = "⚡"
else:
    icon = "📄"

# SESUDAH:
_STATE_MATERIAL_ICONS = {
    "COMPLETED": ("check_circle", "var(--color-success)"),
    "CHATTING": ("hourglass_empty", "var(--color-warning)"),
    "NEW": ("hourglass_empty", "var(--color-text-muted)"),
    "ESCALATED": ("bolt", "var(--color-accent)"),
}
icon_name, icon_color = _STATE_MATERIAL_ICONS.get(
    s["state"], ("description", "var(--color-text-muted)")
)
state_icon = mi(icon_name, 18, icon_color, filled=True)
```

- [x] Pastikan `title` line juga pakai Material icon:

```python
# SEBELUM:
st.markdown(f"**{icon} {title}**")

# SESUDAH:
st.markdown(f"**{state_icon} {title}**", unsafe_allow_html=True)
```

- [x] Ubah `has_tor` badge:

```python
# SEBELUM:
has_tor = "📝 TOR" if s["has_tor"] else ""

# SESUDAH:
has_tor = f'{mi("article", 14, "var(--color-success)", filled=True)} TOR' if s["has_tor"] else ""
```

- [x] Update caption line juga:

```python
st.caption(f"{s['turn_count']} Turn · {s['state']} · {date} {has_tor}")
# ubah menjadi:
st.markdown(
    f"<small>{s['turn_count']} Turn · {s['state']} · {date} {has_tor}</small>",
    unsafe_allow_html=True,
)
```

### 4.4 Migrasi `st.info()` (line 96)

```python
# SEBELUM:
st.info("Belum ada riwayat session.")

# SESUDAH:
notify("Belum ada riwayat session.", "info", method="inline")
```

### 4.5 Migrasi Tombol "Lihat Semua" (line 86)

```python
# SEBELUM:
st.button("📋 Lihat Semua", ...)

# SESUDAH:
st.button("Lihat Semua", ...)
# catatan: icon di button bisa tetap emoji karena button tidak support HTML
# ATAU ganti dengan text biasa tanpa emoji
```

### 4.6 Migrasi Notifikasi Model Selector (line 169, 198)

Ini **belum dihapus** di task ini (model selector dipindahkan di task 07), tapi notifikasinya bisa dimigrasikan:

```python
# Line 169 — SEBELUM:
st.error("Tidak ada model tersedia!")
# SESUDAH:
notify("Tidak ada model tersedia!", "error", method="inline")

# Line 198 — SEBELUM:
st.warning("Ganti model = reset session")
# SESUDAH:
notify("Ganti model akan mereset session.", "warning", method="inline")
```

## 5. Output yang Diharapkan

Setelah migrasi, `sidebar.py`:
- Tidak ada `st.error()`, `st.warning()`, `st.info()`, `st.success()` langsung
- Session dialog modal menampilkan Material Icons untuk status
- Semua notifikasi melalui `notify()`

## 6. Acceptance Criteria

- [x] Tidak ada panggilan `st.error/warning/info/success` langsung di `sidebar.py` (kecuali di `_render_model_selector` yang akan dipindah di task 07).
- [x] Session history dropdown tetap berfungsi (emoji OK di dropdown karena selectbox limitation).
- [x] Dialog modal "Lihat Semua" menampilkan Material Icons untuk status.
- [x] Server start tanpa error.
