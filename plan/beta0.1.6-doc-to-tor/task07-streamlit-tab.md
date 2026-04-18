# Task 07 — Streamlit Tab: 📄 From Document

## 1. Judul Task

Tambah tab ke-3 "📄 From Document" di Streamlit UI untuk file upload dan document-to-TOR generation.

## 2. Deskripsi

Tambah tab baru di `streamlit_app.py` yang berisi file uploader, text area konteks tambahan, dan tombol Generate. Hasil TOR ditampilkan via `render_tor_preview()` reusable component.

## 3. Tujuan Teknis

- Tab ke-3: "📄 From Document" muncul di UI
- `st.file_uploader()` support PDF, TXT, MD, DOCX (max 20MB)
- `st.text_area()` untuk konteks tambahan
- Tombol Generate → panggil `POST /api/v1/generate/from-document`
- TOR preview ditampilkan
- Download .md berfungsi

## 4. Scope

### Yang dikerjakan
- Modifikasi `streamlit_app.py` — tambah tab ke-3
- Helper function `generate_from_document()` untuk API call
- State `doc_tor` untuk simpan hasil

### Yang tidak dikerjakan
- Backend (sudah selesai di task sebelumnya)

## 5. Langkah Implementasi

### Step 1: Tambah helper function

```python
def generate_from_document(file_bytes: bytes, filename: str, context: str = "") -> dict:
    """Upload file & generate TOR via document endpoint."""
    try:
        files = {"file": (filename, file_bytes)}
        data = {"context": context}
        resp = requests.post(
            f"{API_URL}/generate/from-document",
            files=files,
            data=data,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "Backend tidak bisa dihubungi."}
    except requests.Timeout:
        return {"error": "Request timeout. Dokumen mungkin terlalu besar."}
    except requests.HTTPError as e:
        try:
            error_data = e.response.json()
            return {"error": error_data.get("error", {}).get("message", str(e))}
        except Exception:
            return {"error": f"HTTP Error: {e.response.status_code}"}
```

### Step 2: Init state

```python
if "doc_tor" not in st.session_state:
    st.session_state.doc_tor = None
```

### Step 3: Update tabs

```python
tab_hybrid, tab_direct, tab_document = st.tabs([
    "💬 Hybrid Chat", "🚀 Gemini Direct", "📄 From Document"
])
```

### Step 4: Tab content

```python
with tab_document:
    st.subheader("📄 Generate TOR dari Dokumen")
    st.caption(
        "Upload dokumen sumber (laporan, proposal, notulen), "
        "Gemini akan membaca dan membuat TOR secara otomatis."
    )

    uploaded_file = st.file_uploader(
        "Upload dokumen",
        type=["pdf", "txt", "md", "docx"],
        help="Format: PDF, TXT, MD, DOCX. Maks 20MB.",
    )

    doc_context = st.text_area(
        "Konteks tambahan (opsional)",
        placeholder="Contoh: Ini lanjutan workshop tahun lalu, "
                    "target peserta sama tapi materi ditingkatkan...",
        height=100,
    )

    if st.button("🚀 Generate TOR dari Dokumen",
                  use_container_width=True,
                  disabled=uploaded_file is None):
        if uploaded_file:
            file_bytes = uploaded_file.read()
            with st.spinner("🔨 Gemini sedang membaca dan membuat TOR..."):
                result = generate_from_document(
                    file_bytes, uploaded_file.name, doc_context
                )
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.session_state.doc_tor = result.get("tor_document", result)
                st.rerun()

    # TOR Preview (Document)
    if st.session_state.doc_tor:
        render_tor_preview(st.session_state.doc_tor, key_suffix="_doc")

        if st.button("🔄 Generate Ulang", key="reset_doc", use_container_width=True):
            st.session_state.doc_tor = None
            st.rerun()
```

## 6. Output yang Diharapkan

Tab "📄 From Document" muncul dengan file uploader, konteks, dan tombol generate. Upload file → TOR muncul di bawah.

## 7. Dependencies

- **Task 06** — endpoint `POST /api/v1/generate/from-document` berfungsi
- **Task 05 (beta 0.1.5)** — `render_tor_preview()` reusable component

## 8. Acceptance Criteria

- [ ] Tab "📄 From Document" muncul sebagai tab ke-3
- [ ] File uploader support PDF, TXT, MD, DOCX
- [ ] Konteks tambahan text area berfungsi
- [ ] Generate button disabled kalau belum upload file
- [ ] Spinner muncul saat processing
- [ ] TOR preview rendered via `render_tor_preview()`
- [ ] Download .md berfungsi
- [ ] Error handling: file terlalu besar, format salah, backend down
- [ ] "Generate Ulang" button reset state

## 9. Estimasi

**Medium** — ~1 jam
