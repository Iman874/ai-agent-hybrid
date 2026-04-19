# Task 10: Perbaikan UI — Fix Broken CSS, Theme Toggle & Auto-Restart

## Status
Iterasi ke-5 — masalah utama: theme toggle tidak bisa auto-apply tanpa restart manual.

---

## Masalah yang Masih Ada

| # | Masalah | Root Cause |
|---|---------|-----------|
| 1 | Ganti theme → harus restart manual | config.toml dibaca saat startup, tidak di-watch Streamlit |
| 2 | Tidak ada mode "Ikuti Sistem" | Belum diimplementasi dengan benar |
| 3 | ui chat terasa berat / kurang rapi | Beberapa elemen visual belum polish |

---

## Root Cause & Solusi Final

### Problem: config.toml tidak di-reload saat runtime
Streamlit membaca `config.toml` hanya saat proses start. Kita tidak bisa
mengubah theme tanpa restart proses.

### Solusi: `os.execv()` untuk auto-restart proses
Python bisa menggantikan proses saat ini dengan proses baru menggunakan:

```python
import os, sys

def restart_app():
    os.execv(sys.executable, sys.argv)
```

`os.execv()` menggantikan proses saat ini dengan pemanggilan ulang yang
identik — termasuk membaca ulang `config.toml`. Ini bukan subprocess baru,
tapi penggantian proses total (PID berubah tapi proses lama mati).

### Mode "Ikuti Sistem"
Jika `[theme]` section **tidak ada** di `config.toml`, Streamlit akan
mengikuti preferensi browser/OS via `prefers-color-scheme` media query 
secara otomatis — ini adalah Streamlit built-in behavior.

Jadi:
- Sistem = tulis config.toml **tanpa** `[theme]` section
- Gelap   = tulis config.toml dengan `base = "dark"`
- Terang  = tulis config.toml dengan `base = "light"`

---

## Langkah Implementasi (Final)

### Step 1: `write_theme_config(mode)` — 3 mode

```python
def write_theme_config(mode: str):
    if mode == "system":
        # Hapus [theme] section — Streamlit ikuti OS
        CONFIG_PATH.write_text('[server]\nheadless = true\n')
    elif mode == "dark":
        CONFIG_PATH.write_text(
            '[theme]\nbase = "dark"\n'
            'primaryColor = "#58a6ff"\n'
            'backgroundColor = "#0d1117"\n'
            'secondaryBackgroundColor = "#161b22"\n'
            'textColor = "#e6edf3"\n\n'
            '[server]\nheadless = true\n'
        )
    else:  # light
        CONFIG_PATH.write_text(
            '[theme]\nbase = "light"\n'
            'primaryColor = "#0066cc"\n'
            'backgroundColor = "#ffffff"\n'
            'secondaryBackgroundColor = "#f5f5f5"\n'
            'textColor = "#111111"\n\n'
            '[server]\nheadless = true\n'
        )
```

### Step 2: `restart_app()` — auto-restart proses

```python
import os, sys

def restart_app():
    """Restart proses Streamlit agar config.toml ter-apply."""
    os.execv(sys.executable, sys.argv)
```

### Step 3: Theme Popover — 3 opsi + auto-restart

```python
with col_menu:
    with st.popover("⋮"):
        st.caption("Tampilan")
        theme_pick = st.radio(
            "theme",
            ["🖥 Ikuti Sistem", "🌙 Gelap", "☀️ Terang"],
            index=...,
            label_visibility="collapsed",
        )
        new_theme = {"🖥 Ikuti Sistem": "system",
                     "🌙 Gelap": "dark",
                     "☀️ Terang": "light"}[theme_pick]
        
        if new_theme != st.session_state.app_theme:
            write_theme_config(new_theme)
            st.session_state.app_theme = new_theme
            restart_app()   # ← auto-restart, tidak perlu manual
```

### Step 4: Simpan pilihan theme ke session (persist via query param)

`os.execv` me-reset semua session state. Solusi: simpan pilihan theme
ke file sebelum restart, baca saat startup.

```python
THEME_FILE = Path(__file__).parent / ".streamlit" / ".current_theme"

def save_theme_pref(mode: str):
    THEME_FILE.write_text(mode)

def load_theme_pref() -> str:
    if THEME_FILE.exists():
        return THEME_FILE.read_text().strip()
    return "dark"  # default

# Di session state init:
if "app_theme" not in st.session_state:
    st.session_state.app_theme = load_theme_pref()
```

---

## Output yang Diharapkan

- Klik "🌙 Gelap" → auto-restart → dark mode
- Klik "☀️ Terang" → auto-restart → light mode  
- Klik "🖥 Ikuti Sistem" → auto-restart → ikuti browser/OS
- Pilihan tema persisten: restart manual pun tetap ingat pilihan
- UI bersih, BaseWeb components semua ikut theme

---

## Acceptance Criteria
- [x] Expander arrows render normal
- [x] Forms di main area (tabs)
- [x] Sidebar bersih: model, progress, fields, system
- [x] Gap kosong di sidebar dihilangkan
- [ ] Theme toggle: 3 opsi (Sistem / Gelap / Terang)
- [ ] Auto-restart saat ganti theme (via `os.execv`)
- [ ] Pilihan theme persisten setelah restart
- [ ] Mode "Ikuti Sistem" benar-benar ikuti browser/OS

## Dependencies
- Task 05-08 (selesai)

## Estimasi
Rendah — perubahan bersih dan terlokalisir
