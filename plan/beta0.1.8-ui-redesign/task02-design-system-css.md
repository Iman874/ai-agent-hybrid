# Task 02: Design System CSS — Tokens, Typography & Component Styles

## Status: 🔲 Pending

---

## 1. Judul Task

Membuat file CSS design system (`base.css` + `components.css`) dan style loader.

## 2. Deskripsi

Buat design system berbasis CSS custom properties (variables) yang mendefinisikan
warna, spacing, typography, radius, shadow, dan semantic colors untuk kedua theme
(dark + light). Juga buat CSS khusus untuk custom-styled components.

## 3. Tujuan Teknis

- Buat `styles/base.css` — design system tokens (CSS variables)
- Buat `styles/components.css` — styling untuk custom components
- Buat `styles/loader.py` — CSS injection helper + Google Fonts loader
- Semua warna/spacing di UI harus menggunakan variabel, bukan hardcoded

## 4. Scope

**Yang dikerjakan:**
- CSS variables untuk dark theme (default) dan light theme override
- Typography setup (Google Fonts: Inter + JetBrains Mono)
- Component styles: chat bubble, sidebar label, empty state, banners, scrollbar
- `loader.py` yang membaca `.css` files dan inject ke Streamlit

**Yang TIDAK dikerjakan:**
- Material Icons (Task 03)
- Theme switching logic (Task 05)
- Komponen UI Python (Task 06-11)

## 5. Langkah Implementasi

### Step 1: Buat `styles/base.css`

```css
/* ============================================
   BASE.CSS — Design System Tokens
   ============================================ */

/* === DARK THEME (default) === */
:root {
  /* Brand */
  --color-primary:       #58a6ff;
  --color-primary-hover:  #79b8ff;
  --color-accent:         #a78bfa;

  /* Surface */
  --color-bg:             #0d1117;
  --color-bg-elevated:    #161b22;
  --color-bg-card:        #1c2028;
  --color-bg-input:       #21262d;

  /* Text */
  --color-text:           #e6edf3;
  --color-text-muted:     #8b949e;
  --color-text-subtle:    #6e7681;

  /* Border */
  --color-border:         #30363d;
  --color-border-hover:   #484f58;

  /* Semantic */
  --color-success:        #3fb950;
  --color-warning:        #d29922;
  --color-error:          #f85149;
  --color-info:           #58a6ff;

  /* Spacing (8px base) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-8: 48px;

  /* Border radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 20px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,.3);
  --shadow-md: 0 4px 12px rgba(0,0,0,.4);
  --shadow-lg: 0 8px 24px rgba(0,0,0,.5);

  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  --text-xs:   0.75rem;
  --text-sm:   0.8125rem;
  --text-base: 0.875rem;
  --text-lg:   1rem;
  --text-xl:   1.25rem;
  --text-2xl:  1.5rem;
  --text-3xl:  1.875rem;

  /* Transition */
  --transition-fast: 150ms ease;
  --transition-base: 250ms ease;
}

/* === LIGHT THEME OVERRIDE === */
:root[data-theme="light"],
body.light-theme {
  --color-primary:       #0066cc;
  --color-primary-hover:  #0052a3;
  --color-accent:         #7c3aed;

  --color-bg:             #ffffff;
  --color-bg-elevated:    #f6f8fa;
  --color-bg-card:        #ffffff;
  --color-bg-input:       #f0f2f5;

  --color-text:           #1f2328;
  --color-text-muted:     #656d76;
  --color-text-subtle:    #8b949e;

  --color-border:         #d0d7de;
  --color-border-hover:   #afb8c1;

  --color-success:        #1a7f37;
  --color-warning:        #9a6700;
  --color-error:          #cf222e;
  --color-info:           #0969da;

  --shadow-sm: 0 1px 2px rgba(0,0,0,.08);
  --shadow-md: 0 4px 12px rgba(0,0,0,.1);
  --shadow-lg: 0 8px 24px rgba(0,0,0,.12);
}
```

### Step 2: Buat `styles/components.css`

```css
/* ============================================
   COMPONENTS.CSS — Custom Component Styles
   ============================================ */

/* --- Hide Streamlit branding --- */
#MainMenu, footer { visibility: hidden; }

/* --- Chat bubbles --- */
[data-testid="stChatMessage"] {
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-2);
  padding: var(--space-3) var(--space-4);
}

/* --- Sidebar section label --- */
.sidebar-label {
  font-family: var(--font-sans);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08rem;
  text-transform: uppercase;
  color: var(--color-text-subtle);
  margin: var(--space-4) 0 var(--space-2) 0;
}

/* --- Empty state --- */
.empty-state {
  text-align: center;
  padding: var(--space-8) var(--space-5);
  color: var(--color-text-muted);
}
.empty-state h3 {
  font-family: var(--font-sans);
  font-weight: 600;
  font-size: var(--text-xl);
  margin-top: var(--space-4);
  color: var(--color-text-muted);
}
.empty-state p {
  font-size: var(--text-base);
  line-height: 1.6;
  color: var(--color-text-subtle);
}

/* --- Status banners --- */
.banner {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-weight: 500;
  font-size: var(--text-base);
  margin: var(--space-3) 0;
}
.banner-success {
  background: color-mix(in srgb, var(--color-success) 10%, transparent);
  border-left: 3px solid var(--color-success);
  color: var(--color-success);
}
.banner-error {
  background: color-mix(in srgb, var(--color-error) 10%, transparent);
  border-left: 3px solid var(--color-error);
  color: var(--color-error);
}
.banner-warning {
  background: color-mix(in srgb, var(--color-warning) 10%, transparent);
  border-left: 3px solid var(--color-warning);
  color: var(--color-warning);
}
.banner-info {
  background: color-mix(in srgb, var(--color-info) 10%, transparent);
  border-left: 3px solid var(--color-info);
  color: var(--color-info);
}

/* --- Scrollbar --- */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  border-radius: 3px;
  background: var(--color-border);
}

/* --- Download buttons --- */
.stDownloadButton button {
  border-radius: var(--radius-md) !important;
}

/* --- Thinking animation --- */
@keyframes pulse-thinking {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}
.thinking-indicator {
  animation: pulse-thinking 1.5s ease-in-out infinite;
}

/* --- Material icon alignment fix --- */
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  vertical-align: middle;
}
```

### Step 3: Buat `styles/loader.py`

```python
# streamlit_app/styles/loader.py
"""CSS and font injection for Streamlit."""

import streamlit as st
from pathlib import Path

STYLES_DIR = Path(__file__).parent


def inject_styles():
    """Inject Google Fonts, Material Icons, dan custom CSS ke halaman."""
    base_css = (STYLES_DIR / "base.css").read_text()
    components_css = (STYLES_DIR / "components.css").read_text()

    st.markdown(f"""
    <!-- Google Fonts: Inter + JetBrains Mono -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

    <!-- Material Symbols Outlined -->
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL@20..48,100..700,0..1" rel="stylesheet">

    <style>
    {base_css}
    {components_css}
    </style>
    """, unsafe_allow_html=True)
```

### Step 4: Update `app.py` untuk test styling

```python
# Di app.py, tambahkan:
from styles.loader import inject_styles

inject_styles()

# Test banner styles
st.markdown('<div class="banner banner-success">Success banner test</div>', unsafe_allow_html=True)
st.markdown('<div class="banner banner-error">Error banner test</div>', unsafe_allow_html=True)
st.markdown('<div class="banner banner-warning">Warning banner test</div>', unsafe_allow_html=True)
```

### Step 5: Test visual

Jalankan `streamlit run streamlit_app/app.py` dan verifikasi:
- Font Inter ter-load
- CSS variables bekerja (warna, spacing)
- Banner styles render dengan benar

## 6. Output yang Diharapkan

```
streamlit_app/styles/
├── __init__.py
├── base.css         (~90 lines — CSS variables)
├── components.css   (~100 lines — component styles)
└── loader.py        (~30 lines — injection helper)
```

## 7. Dependencies

- **Task 01** — folder structure harus ada

## 8. Acceptance Criteria

- [ ] `base.css` berisi CSS variables untuk dark (default) dan light theme
- [ ] `components.css` berisi styles untuk: chat bubble, sidebar label, empty state, banners, scrollbar, thinking animation
- [ ] `loader.py` berhasil inject CSS + Google Fonts + Material Symbols ke halaman
- [ ] Font "Inter" ter-load di browser (verifikasi via DevTools)
- [ ] Banner `.banner-success`, `.banner-error`, `.banner-warning` render dengan warna dan border-left yang benar
- [ ] Tidak ada CSS yang meng-override komponen native Streamlit (expander, radio, selectbox)

## 9. Estimasi

**Medium** — Perlu menulis CSS design system lengkap + test visual.
