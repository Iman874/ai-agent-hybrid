# Task 05: Auto-Detect Style — Backend + Frontend Flow

> **Status**: [x] Selesai
> **Estimasi**: High (2–3 jam)
> **Dependency**: Task 02, Task 03, Task 04

## 1. Deskripsi

Implementasi flow 2-step "Auto-detect style dari dokumen" di tab "Dari Dokumen". Saat user memilih mode auto-detect:
1. **Step 1**: Upload dokumen → AI mengekstrak format/style → preview di dialog
2. **Step 2**: User konfirmasi → style disimpan → TOR di-generate dengan style baru

## 2. Tujuan Teknis

- Radio button di task04 diperluas dengan opsi "auto_detect"
- Frontend memanggil `POST /styles/extract` (sudah ada) untuk Step 1
- Dialog preview menampilkan hasil ekstraksi
- Setelah confirm, style disimpan via `POST /styles` dan TOR di-generate

## 3. Scope

**Yang dikerjakan:**
- `streamlit_app/components/form_document.py` — tambah mode auto_detect + dialog preview
- `streamlit_app/state.py` — tambah state key `doc_detected_style`, `doc_awaiting_confirm`

**Yang tidak dikerjakan:**
- Backend baru (semua endpoint sudah ada dari beta 0.1.9)

## 4. Langkah Implementasi

### 4.1 Update `state.py` — Tambah Auto-Detect Keys

- [x] Tambahkan di `defaults`:

```python
        "doc_detected_style": None,        # dict: hasil extraction dari AI
        "doc_awaiting_confirm": False,      # True = menunggu user confirm style
```

- [x] Tambahkan reset:

```python
    st.session_state.doc_detected_style = None
    st.session_state.doc_awaiting_confirm = False
```

### 4.2 Update Radio Button di `form_document.py`

- [x] Ubah `style_mode` radio (dari task04) untuk menambahkan opsi ketiga:

```python
    style_mode = st.radio(
        "Pilih format output",
        options=["active", "choose", "auto_detect"],
        format_func=lambda x: {
            "active": f"🎨 Pakai style aktif ({active_name})",
            "choose": "📋 Pilih style lain",
            "auto_detect": "🔍 Auto-detect format dari dokumen",
        }[x],
        horizontal=True,
        label_visibility="collapsed",
        key="doc_style_radio",
    )
```

- [x] Tambahkan section untuk auto-detect di bawah section "choose":

```python
    if style_mode == "auto_detect":
        st.caption(
            "💡 AI akan menganalisis format dokumen yang di-upload "
            "dan membuat style baru secara otomatis."
        )
        auto_style_name = st.text_input(
            "Nama style baru (opsional)",
            placeholder="Biarkan kosong, AI akan memberi nama otomatis",
            key="auto_style_name",
        )
```

### 4.3 Tambah Import

- [x] Tambahkan import baru:

```diff
-from api.client import generate_from_document
-from api.client import get_styles, get_active_style
+from api.client import generate_from_document, extract_style
+from api.client import get_styles, get_active_style, create_style
```

**Catatan**: Perlu cek apakah `create_style()` sudah ada di `client.py`. Jika belum, tambahkan:

```python
def create_style(style_data: dict) -> dict:
    """Simpan style baru ke backend."""
    try:
        resp = requests.post(f"{API_URL}/styles", json=style_data, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        return {"error": e.response.json().get("detail", str(e))}
    except Exception as e:
        return {"error": str(e)}
```

### 4.4 Update Generate Button Logic

- [x] Ubah tombol "Generate TOR" agar menangani auto-detect mode:

```python
    if st.button(
        "Generate TOR",
        use_container_width=True,
        disabled=uploaded_file is None,
    ):
        if uploaded_file:
            if style_mode == "auto_detect":
                _handle_auto_detect(uploaded_file, doc_context, auto_style_name)
            else:
                _handle_generate(uploaded_file, doc_context, selected_style_id)
```

### 4.5 Buat Fungsi `_handle_auto_detect()`

- [x] Tambahkan fungsi baru:

```python
def _handle_auto_detect(uploaded_file, context: str, custom_name: str = ""):
    """Step 1: Extract style dari dokumen via AI."""
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name

    with st.spinner("🔍 AI sedang menganalisis format dokumen..."):
        result = extract_style(file_bytes, filename)

    if "error" in result:
        st.markdown(
            banner_html("error", f"Gagal mengekstrak style: {result['error']}", "error"),
            unsafe_allow_html=True,
        )
        return

    # Override nama jika user custom
    if custom_name.strip():
        result["name"] = custom_name.strip()

    # Simpan hasil ke state untuk preview
    st.session_state.doc_detected_style = result
    st.session_state.doc_awaiting_confirm = True
    # Simpan juga file bytes dan context untuk Step 2
    st.session_state._doc_file_bytes = file_bytes
    st.session_state._doc_filename = filename
    st.session_state._doc_context = context
    st.rerun()
```

### 4.6 Tampilkan Preview + Confirm

- [x] Di `render_document_tab()`, setelah bagian style selector dan sebelum file uploader, tambahkan guard untuk menampilkan preview saat `doc_awaiting_confirm`:

```python
    # --- Auto-detect preview ---
    if st.session_state.get("doc_awaiting_confirm"):
        _render_detected_style_preview()
        return  # Jangan render form upload lagi
```

### 4.7 Buat `_render_detected_style_preview()`

```python
def _render_detected_style_preview():
    """Step 2: Preview style yang diekstrak dan konfirmasi."""
    detected = st.session_state.doc_detected_style

    if not detected:
        st.session_state.doc_awaiting_confirm = False
        st.rerun()
        return

    st.info(f"🔍 **Format Terdeteksi**: {detected.get('name', 'Unknown')}")

    # Tampilkan deskripsi
    if detected.get("description"):
        st.caption(detected["description"])

    # Tampilkan seksi yang ditemukan
    sections = detected.get("sections", [])
    if sections:
        st.markdown("**Seksi yang ditemukan:**")
        for s in sections:
            req = "🟢 wajib" if s.get("required") else "⚪ opsional"
            fmt = s.get("format_hint", "-")
            st.markdown(f"- **{s.get('title', 'Untitled')}** ({req}) — {fmt}")

    # Tampilkan config
    config = detected.get("config", {})
    if config:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Bahasa**: {config.get('language', 'id')}")
            st.markdown(f"**Formalitas**: {config.get('formality', 'formal')}")
        with col2:
            st.markdown(f"**Suara**: {config.get('voice', 'active')}")
            st.markdown(f"**Penomoran**: {config.get('numbering_style', 'numeric')}")

    # Tombol konfirmasi
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Simpan Style & Generate TOR", type="primary", use_container_width=True):
            _confirm_and_generate(detected)
    with col2:
        if st.button("❌ Abaikan, Pakai Style Aktif", use_container_width=True):
            _cancel_auto_detect()
```

### 4.8 Buat `_confirm_and_generate()` dan `_cancel_auto_detect()`

```python
def _confirm_and_generate(detected_style: dict):
    """Simpan style baru, lalu generate TOR."""
    with st.spinner("Menyimpan style baru..."):
        save_result = create_style(detected_style)

    if "error" in save_result:
        st.error(f"Gagal menyimpan style: {save_result['error']}")
        return

    # Generate TOR dengan style yang baru disimpan
    new_style_id = save_result.get("id", detected_style.get("id"))

    file_bytes = st.session_state.get("_doc_file_bytes")
    filename = st.session_state.get("_doc_filename", "unknown.txt")
    context = st.session_state.get("_doc_context", "")

    with st.spinner("Generating TOR dengan style baru..."):
        result = generate_from_document(
            file_bytes, filename, context, style_id=new_style_id,
        )

    # Cleanup state
    st.session_state.doc_detected_style = None
    st.session_state.doc_awaiting_confirm = False

    if "error" in result:
        st.markdown(
            banner_html("error", result["error"], "error"),
            unsafe_allow_html=True,
        )
    else:
        st.session_state.doc_tor = result.get("tor_document", result)
        st.session_state.doc_session_id = result.get("session_id", "")
        st.rerun()


def _cancel_auto_detect():
    """Batal auto-detect, kembali ke form normal."""
    file_bytes = st.session_state.get("_doc_file_bytes")
    filename = st.session_state.get("_doc_filename", "unknown.txt")
    context = st.session_state.get("_doc_context", "")

    st.session_state.doc_detected_style = None
    st.session_state.doc_awaiting_confirm = False

    # Langsung generate dengan active style
    if file_bytes:
        with st.spinner("Generating TOR dengan style aktif..."):
            result = generate_from_document(file_bytes, filename, context)

        if "error" in result:
            st.markdown(
                banner_html("error", result["error"], "error"),
                unsafe_allow_html=True,
            )
        else:
            st.session_state.doc_tor = result.get("tor_document", result)
            st.session_state.doc_session_id = result.get("session_id", "")
            st.rerun()
    else:
        st.rerun()
```

## 5. Output yang Diharapkan

### Flow Auto-Detect:
```
1. User pilih "🔍 Auto-detect format dari dokumen"
2. User upload file + klik "Generate TOR"
3. Spinner: "🔍 AI sedang menganalisis format dokumen..."
4. Preview muncul:
   ┌─────────────────────────────────────────┐
   │ 🔍 Format Terdeteksi: TOR Rapat BAPENAS│
   │ Deskripsi: Format untuk...              │
   │                                         │
   │ Seksi yang ditemukan:                   │
   │ - Latar Belakang (🟢 wajib) — paragraf  │
   │ - Maksud & Tujuan (🟢 wajib) — mixed   │
   │ - Ruang Lingkup (🟢 wajib) — bullet    │
   │ ...                                     │
   │                                         │
   │ Bahasa: id    Suara: passive            │
   │ Formalitas: formal  Penomoran: roman    │
   │                                         │
   │ ────────────────────────────────────     │
   │ [✅ Simpan Style & Generate TOR]         │
   │ [❌ Abaikan, Pakai Style Aktif]          │
   └─────────────────────────────────────────┘
5a. Klik "✅ Simpan" → style disimpan → TOR digenerate
5b. Klik "❌ Abaikan"→ TOR digenerate dengan active style
```

## 6. Acceptance Criteria

- [x] Radio button punya 3 opsi: active, choose, auto_detect.
- [x] Mode "auto_detect" menampilkan input nama style opsional.
- [x] Klik "Generate TOR" di mode auto_detect → extraction dipanggil via `extract_style()`.
- [x] Hasil extraction ditampilkan sebagai preview (sections, config).
- [x] "Simpan & Generate" → style disimpan + TOR digenerate dengan style baru.
- [x] "Abaikan" → TOR digenerate dengan active style (tanpa menyimpan).
- [x] Error handling: jika extract gagal → tampilkan error banner.
- [x] Jika file bytes hilang dari state → rerun (graceful fallback).
