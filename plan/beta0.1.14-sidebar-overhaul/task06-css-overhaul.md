# Task 06: CSS Overhaul — Sidebar ChatGPT-Style Polish

## 1. Judul Task

CSS overhaul untuk sidebar — session buttons, tools radio, dividers, hover polish

## 2. Deskripsi

Menambahkan CSS overhaul di `components.css` agar sidebar terasa seperti ChatGPT: session buttons flat/transparent, hover halus, active subtle, dividers tipis, typography compact.

## 3. Tujuan Teknis

- Session list buttons: flat, transparent bg, text-left, hover halus
- Active session: subtle highlight (10% opacity), slightly bolder
- Tools radio: compact, small
- Model selectbox: compact
- Dividers: very subtle (40% opacity)
- Section captions: uppercase, smaller, spaced

## 4. Scope

**Yang dikerjakan:**
- `streamlit_app/styles/components.css` — tambah section CSS sidebar baru

**Yang tidak dikerjakan:**
- Konten sidebar (task 02)
- Base theme tokens (tidak diubah)

## 5. Langkah Implementasi

### 5.1 Hapus CSS Lama yang Tidak Dipakai

Hapus `.sidebar-label` style jika masih ada (diganti `.stCaption` override).

### 5.2 Tambah CSS Sidebar Baru

Tambahkan di akhir `components.css`:

```css
/* === SIDEBAR OVERHAUL (Beta 0.1.14) === */

/* Section captions (RIWAYAT, ALAT) — subtle uppercase */
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

/* Active session button — subtle highlight, slightly bolder */
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
```

## 6. Output yang Diharapkan

**UX Polish details:**
- Hover pada session: sangat halus (`6%` opacity) — bukan kontras keras
- Active session: subtle highlight (`10%` opacity primary color) — bukan solid block
- Dividers: 40% opacity — tipis, bukan garis tebal
- Font hierarchy: caption 0.65rem → buttons ~0.81rem → brand 1rem
- Spacing: `var(--space-2)` padding konsisten di semua sidebar buttons
- Transition: `var(--transition-fast)` (150ms) pada semua hover

## 7. Dependencies

- Task 02 (sidebar harus sudah pakai class/structure yang benar)

## 8. Acceptance Criteria

- [ ] Session buttons terlihat flat (transparent background, no border)
- [ ] Hover effect halus — tidak terlalu kontras
- [ ] Active session punya highlight ringan + font lebih tebal
- [ ] Tools radio compact — tidak makan banyak space
- [ ] Model selectbox compact
- [ ] Dividers tipis dan subtle
- [ ] Section captions (RIWAYAT, ALAT) uppercase, font kecil
- [ ] CSS lama `.sidebar-label` dihapus jika tidak dipakai lagi
- [ ] Tidak ada visual regression di bagian lain app

## 9. Estimasi

Medium (1 jam)
