# Task 10: Component — Gemini Direct Form (`components/form_direct.py`)

## Status: 🔲 Pending

---

## 1. Judul Task

Membuat komponen tab Gemini Direct — form input untuk generate TOR langsung.

## 2. Deskripsi

Extract tab Gemini Direct dari monolit ke `components/form_direct.py`.
Form berisi 7 field (judul, latar_belakang, tujuan, ruang_lingkup, output,
timeline, estimasi_biaya) dengan validasi dan generate button.

## 3. Tujuan Teknis

- `render_direct_tab()` — entry function untuk tab Gemini Direct
- Form dengan validation (minimal judul + tujuan)
- Integrasi TOR preview setelah generate
- Tombol "Generate Ulang" untuk reset

## 4. Scope

**Yang dikerjakan:**
- `components/form_direct.py` — form + validation + generate

**Yang TIDAK dikerjakan:**
- API client (sudah di Task 04)
- TOR preview (sudah di Task 06)

## 5. Langkah Implementasi

### Step 1: Buat `components/form_direct.py`

```python
# streamlit_app/components/form_direct.py
"""Gemini Direct tab — form-based TOR generation without chat."""

import streamlit as st
from utils.icons import mi, mi_inline, banner_html
from api.client import generate_direct
from components.tor_preview import render_tor_preview
from config import FIELD_LABELS


def render_direct_tab():
    """Render tab Gemini Direct: form input + generate."""

    st.markdown(
        f"### {mi('auto_awesome', 24, 'var(--color-accent)')} Generate TOR Langsung",
        unsafe_allow_html=True,
    )
    st.caption("Isi field, Gemini langsung membuat TOR tanpa proses chat.")

    with st.form("gemini_direct_form"):
        judul = st.text_input(
            f"{FIELD_LABELS['judul']} *",
            placeholder="Workshop Penerapan AI untuk ASN",
        )
        latar = st.text_area(
            f"{FIELD_LABELS['latar_belakang']} *",
            placeholder="Konteks dan alasan kegiatan...",
            height=100,
        )
        tujuan = st.text_area(
            f"{FIELD_LABELS['tujuan']} *",
            placeholder="Apa yang ingin dicapai...",
            height=80,
        )
        scope = st.text_area(
            FIELD_LABELS["ruang_lingkup"],
            placeholder="Batasan cakupan pekerjaan...",
            height=80,
        )
        output_f = st.text_area(
            FIELD_LABELS["output"],
            placeholder="Deliverable yang diharapkan...",
            height=80,
        )
        timeline = st.text_input(
            FIELD_LABELS["timeline"],
            placeholder="3 hari, 15-17 Juli 2026",
        )
        biaya = st.text_input(
            FIELD_LABELS["estimasi_biaya"],
            placeholder="Rp 50.000.000",
        )
        submitted = st.form_submit_button(
            "Generate TOR",
            use_container_width=True,
        )

    if submitted:
        _handle_submit(judul, latar, tujuan, scope, output_f, timeline, biaya)

    # Show result jika ada
    if st.session_state.direct_tor:
        render_tor_preview(st.session_state.direct_tor, key_suffix="_direct")
        if st.button("Generate Ulang", key="reset_direct"):
            st.session_state.direct_tor = None
            st.rerun()


def _handle_submit(judul, latar, tujuan, scope, output_f, timeline, biaya):
    """Validate form dan call API generate."""
    if not judul or not tujuan:
        st.markdown(
            banner_html("error", "Minimal isi <strong>Judul</strong> dan <strong>Tujuan</strong>!", "error"),
            unsafe_allow_html=True,
        )
        return

    with st.spinner("Generating TOR..."):
        result = generate_direct({
            "judul": judul.strip() or None,
            "latar_belakang": latar.strip() or None,
            "tujuan": tujuan.strip() or None,
            "ruang_lingkup": scope.strip() or None,
            "output": output_f.strip() or None,
            "timeline": timeline.strip() or None,
            "estimasi_biaya": biaya.strip() or None,
        })

    if "error" in result:
        st.markdown(
            banner_html("error", result["error"], "error"),
            unsafe_allow_html=True,
        )
    else:
        st.session_state.direct_tor = result.get("tor_document") or result
        st.rerun()
```

### Step 2: Update `app.py`

```python
from components.form_direct import render_direct_tab

with tab_direct:
    render_direct_tab()
```

### Step 3: Test

1. Isi judul + tujuan → klik Generate → loading → TOR preview muncul
2. Tanpa judul → error banner merah muncul
3. Klik "Generate Ulang" → form reset

## 6. Output yang Diharapkan

```
streamlit_app/components/
├── form_direct.py    (~85 lines)
```

## 7. Dependencies

- **Task 01** — config (FIELD_LABELS)
- **Task 03** — `mi()`, `mi_inline()`, `banner_html()`
- **Task 04** — `generate_direct()`
- **Task 06** — `render_tor_preview()`

## 8. Acceptance Criteria

- [ ] Form menampilkan 7 field TOR dengan labels dari `FIELD_LABELS`
- [ ] Validasi: judul dan tujuan wajib diisi
- [ ] Error ditampilkan via `.banner-error` banner (bukan `st.error`)
- [ ] Klik Generate → spinner → TOR preview muncul
- [ ] TOR preview muncul setelah generate berhasil
- [ ] "Generate Ulang" button reset `direct_tor` dan rerun
- [ ] Tidak ada emoji — semua Material Icons

## 9. Estimasi

**Low** — Mostly form + validation logic yang sudah ada.
