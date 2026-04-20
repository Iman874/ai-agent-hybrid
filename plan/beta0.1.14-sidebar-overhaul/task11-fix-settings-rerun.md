# Task 11: Fix Settings Dialog Close Bug — st.rerun(scope="fragment")

## 1. Judul Task

Fix bug dialog pengaturan menutup saat navigasi antar section

## 2. Deskripsi

Bug: Saat tombol navigasi (Umum / Format TOR / Lanjutan) ditekan di dalam dialog pengaturan, dialog langsung tertutup dan app kembali ke halaman chat.

## 3. Analisis Root Cause

### Penyebab
`@st.dialog` di Streamlit adalah **fragment** (komponen terisolasi). Ketika di dalam dialog memanggil `st.rerun()`, Streamlit me-rerun **seluruh app** — bukan hanya fragment dialog. Ini menyebabkan:

1. Seluruh `app.py` dirender ulang
2. Dialog tidak lagi dalam konteks aktif (karena tombol "Pengaturan" tidak di-klik lagi)
3. Dialog menutup otomatis

### Kode bermasalah (`settings_dialog.py` line 33-34):
```python
if st.button(label, key=f"nav_{key}", ...):
    st.session_state._settings_section = key
    st.rerun()  # ← BUG: rerun seluruh app, bukan fragment saja
```

### Fix
Ganti `st.rerun()` dengan `st.rerun(scope="fragment")`:
```python
st.rerun(scope="fragment")  # ← Hanya rerun dialog fragment
```

`scope="fragment"` memberi tahu Streamlit untuk hanya me-rerun fragment (dialog) yang sedang aktif, tanpa me-rerun seluruh app.

## 4. Tujuan Teknis

- Ganti semua `st.rerun()` di dalam `settings_dialog.py` dengan `st.rerun(scope="fragment")`
- Dialog tetap terbuka saat navigasi antar section
- Periksa juga `switch_theme()` — jika di dalamnya ada `st.rerun()`, perlu penanganan khusus

## 5. Scope

**Yang dikerjakan:**
- `streamlit_app/components/settings_dialog.py`
- Kemungkinan `streamlit_app/theme.py` (jika `switch_theme` memanggil `st.rerun()`)

**Yang tidak dikerjakan:**
- Logic settings (tidak berubah)
- Layout dialog (tidak berubah)

## 6. Langkah Implementasi

### 6.1 Fix Navigasi Button

```python
# settings_dialog.py — line 33-34

# SEBELUM:
if st.button(label, key=f"nav_{key}", ...):
    st.session_state._settings_section = key
    st.rerun()

# SESUDAH:
if st.button(label, key=f"nav_{key}", ...):
    st.session_state._settings_section = key
    st.rerun(scope="fragment")
```

### 6.2 Periksa switch_theme()

Buka `theme.py` dan cek apakah `switch_theme()` memanggil `st.rerun()` di dalamnya:

```python
# theme.py
def switch_theme(theme_name: str):
    st.session_state.theme = theme_name
    # Jika ada st.rerun() di sini → HAPUS
    # Biarkan dialog yang handle rerun-nya sendiri
```

Jika `switch_theme()` memanggil `st.rerun()`:
- **Option A**: Hapus `st.rerun()` dari `switch_theme()` (tema akan ter-apply saat app rerun berikutnya)
- **Option B**: Ganti dengan parameter opsional `rerun=True` yang bisa di-skip dari dialog

### 6.3 Periksa notify() di Clear Cache

```python
# settings_dialog.py — line 93-95
if st.button("Hapus Cache", key="clear_cache"):
    st.cache_data.clear()
    notify("Cache berhasil dihapus.", "success")
    # Jika notify() memanggil st.rerun() → akan close dialog juga!
```

Pastikan `notify()` dengan method yang dipakai TIDAK memanggil `st.rerun()`. Jika ya, perlu di-handle.

### 6.4 File Akhir

```python
# settings_dialog.py — FIXED

@st.dialog("Pengaturan", width="large")
def show_settings_dialog() -> None:
    """Dialog pengaturan dengan navigasi kiri dan konten kanan."""
    col_nav, col_content = st.columns([1, 3])

    with col_nav:
        nav_items = {
            "umum": "Umum",
            "format_tor": "Format TOR",
            "lanjutan": "Lanjutan",
        }
        current = st.session_state.get("_settings_section", "umum")

        for key, label in nav_items.items():
            btn_type = "primary" if key == current else "secondary"
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state._settings_section = key
                st.rerun(scope="fragment")  # ← FIX: hanya rerun dialog

    with col_content:
        section = st.session_state.get("_settings_section", "umum")

        if section == "umum":
            _render_general_settings()
        elif section == "format_tor":
            _render_format_tor_settings()
        elif section == "lanjutan":
            _render_advanced_settings()
```

## 7. Output yang Diharapkan

- Klik "Pengaturan" → dialog terbuka
- Klik "Format TOR" di sidebar nav → konten berganti, dialog TETAP terbuka
- Klik "Lanjutan" → konten berganti, dialog TETAP terbuka
- Klik "Umum" → kembali ke default, dialog TETAP terbuka
- Klik [✕] atau di luar dialog → dialog tertutup (normal behavior)

## 8. Dependencies

- Task 10 (settings dialog sudah diimplementasi)

## 9. Acceptance Criteria

- [ ] Dialog TIDAK menutup saat klik navigasi section
- [ ] `st.rerun(scope="fragment")` digunakan — bukan `st.rerun()`
- [ ] Navigasi antar section (Umum → Format TOR → Lanjutan) berfungsi smooth
- [ ] Switch theme di section Umum tidak menutup dialog
- [ ] "Hapus Cache" di section Lanjutan tidak menutup dialog
- [ ] Dialog hanya menutup saat klik [✕] atau klik di luar
- [ ] Server start tanpa error

## 10. Estimasi

Low (15 menit — hanya ganti 1 baris + verifikasi)
