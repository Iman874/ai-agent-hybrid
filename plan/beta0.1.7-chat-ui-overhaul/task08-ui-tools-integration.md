# Task 08: UI — Integrasi Tools (Document & Direct) ke Sidebar

## Deskripsi
Memastikan fitur "From Document" dan "Gemini Direct" yang sebelumnya ada di tab terpisah kini berfungsi penuh sebagai expandable tools di sidebar, termasuk preview TOR yang muncul di area chat utama.

## Tujuan Teknis
1. "📄 From Document" → sidebar expander, result preview di main area
2. "🚀 Gemini Direct" → sidebar expander dengan form, result preview di main area
3. TOR preview dari tools muncul di main area (bukan di sidebar)
4. State management yang benar antara sidebar input dan main area output

## Scope
- **Dikerjakan**:
  - Finalisasi From Document expander + generate flow
  - Finalisasi Gemini Direct expander + form flow
  - TOR result dari tools ditampilkan di main area (setelah chat history)
  - State flags: `doc_tor`, `direct_tor` untuk kontrol display
  - Download buttons (MD + PDF) untuk hasil tools
- **Tidak dikerjakan**:
  - Layout structure (task05)
  - Model selector (task06)
  - CSS (task07)

## Langkah Implementasi

### Step 1: Sidebar — From Document Expander

```python
with st.sidebar:
    st.subheader("🛠️ Tools")

    with st.expander("📄 Generate dari Dokumen"):
        uploaded_file = st.file_uploader(
            "Upload dokumen",
            type=["pdf", "txt", "md", "docx"],
            help="PDF, TXT, MD, DOCX. Maks 20MB.",
            key="doc_upload",
        )
        doc_context = st.text_area(
            "Konteks tambahan",
            placeholder="Ini lanjutan workshop tahun lalu...",
            height=80,
            key="doc_context",
        )
        if st.button("🚀 Generate", key="btn_doc_gen",
                      use_container_width=True, disabled=not uploaded_file):
            file_bytes = uploaded_file.read()
            with st.spinner("Membaca dokumen..."):
                result = generate_from_document(file_bytes, uploaded_file.name, doc_context)
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.session_state.doc_tor = result.get("tor_document", result)
                st.rerun()
```

### Step 2: Sidebar — Gemini Direct Expander

```python
    with st.expander("🚀 Gemini Direct"):
        with st.form("direct_form"):
            judul = st.text_input("Judul *")
            tujuan = st.text_area("Tujuan *", height=60)
            latar = st.text_area("Latar Belakang", height=60)
            scope = st.text_area("Ruang Lingkup", height=60)
            output_f = st.text_area("Output", height=60)
            timeline = st.text_input("Timeline")
            biaya = st.text_input("Estimasi Biaya")
            submitted = st.form_submit_button("🚀 Generate TOR")

        if submitted:
            if not judul or not tujuan:
                st.error("Minimal isi Judul dan Tujuan!")
            else:
                form_data = {
                    "judul": judul, "tujuan": tujuan,
                    "latar_belakang": latar, "ruang_lingkup": scope,
                    "output": output_f, "timeline": timeline,
                    "estimasi_biaya": biaya,
                }
                with st.spinner("Gemini generating..."):
                    result = generate_direct(form_data)
                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.session_state.direct_tor = result.get("tor_document", result)
                    st.rerun()
```

### Step 3: Main Area — Tool Results Display

```python
# Di main area, setelah chat history:

# TOR dari Document
if st.session_state.doc_tor:
    st.info("📄 TOR dari Dokumen")
    render_tor_preview(st.session_state.doc_tor, key_suffix="_doc")
    if st.button("🔄 Reset", key="reset_doc"):
        st.session_state.doc_tor = None
        st.rerun()

# TOR dari Gemini Direct
if st.session_state.direct_tor:
    st.info("🚀 TOR dari Gemini Direct")
    render_tor_preview(st.session_state.direct_tor, key_suffix="_direct")
    if st.button("🔄 Reset", key="reset_direct"):
        st.session_state.direct_tor = None
        st.rerun()
```

## Output yang Diharapkan
- Sidebar punya 2 expander tools yang berfungsi penuh
- Klik generate di sidebar → result muncul di main area
- Download MD + PDF dari main area
- Reset button untuk clear result

## Dependencies
- Task 05 (Layout harus sudah ready)

## Acceptance Criteria
- [ ] "From Document" expander → upload + generate berfungsi
- [ ] "Gemini Direct" expander → form + generate berfungsi
- [ ] Hasil TOR muncul di main area (bukan sidebar)
- [ ] Download MD dan PDF berfungsi
- [ ] Reset button clear state dan rerun
- [ ] Tidak ada duplicate key errors

## Estimasi
Medium
