# Task 05 — TOR Preview, Download, dan Force Generate

## 1. Judul Task

Implementasi TOR preview panel (rendered markdown), metadata expander, download button, escalation warning, dan force generate button di sidebar.

## 2. Deskripsi

Ketika TOR berhasil di-generate, tampilkan preview rendered markdown di bawah chat, metadata (model, mode, word count, time), tombol download .md, dan warning jika via eskalasi. Juga tambah tombol force generate di sidebar.

## 3. Tujuan Teknis

- TOR preview: `st.markdown(tor_content)` + `st.success()`
- Metadata: `st.expander()` dengan 4 metrics
- Download: `st.download_button()` file .md
- Escalation warning: `st.warning()` jika escalation_info ada
- Force generate: `st.button()` di sidebar, panggil `force_generate()`

## 4. Scope

### Yang dikerjakan
- TOR preview section di main area
- Metadata expander
- Download button
- Escalation warning
- Force generate button di sidebar

### Yang tidak dikerjakan
- PDF export (ditunda ke v1.0)

## 5. Langkah Implementasi

### Step 1: TOR Preview (setelah chat history, sebelum chat input)

```python
# TOR Preview
if st.session_state.tor_document:
    st.divider()
    st.success("✅ TOR Berhasil Dibuat!")

    tor = st.session_state.tor_document

    # Metadata
    with st.expander("📋 Metadata", expanded=False):
        meta = tor["metadata"]
        cols = st.columns(4)
        cols[0].metric("Model", meta.get("generated_by", "unknown"))
        cols[1].metric("Mode", meta.get("mode", "standard"))
        cols[2].metric("Words", meta.get("word_count", 0))
        cols[3].metric("Time", f"{meta.get('generation_time_ms', 0)}ms")

    # TOR Content
    st.markdown(tor["content"])

    # Download
    st.download_button(
        label="⬇️ Download TOR (.md)",
        data=tor["content"],
        file_name="tor_document.md",
        mime="text/markdown",
        use_container_width=True,
    )

    # Escalation Warning
    if st.session_state.escalation_info:
        esc = st.session_state.escalation_info
        st.warning(
            f"⚠️ TOR ini dibuat via eskalasi.\n\n"
            f"**Rule**: {esc.get('triggered_by', 'unknown')}\n\n"
            f"**Alasan**: {esc.get('reason', '')}\n\n"
            "Beberapa bagian mungkin menggunakan asumsi."
        )
```

### Step 2: Force Generate di sidebar

Tambah di sidebar, setelah field tracker, sebelum system info:

```python
    # --- Force Generate ---
    if st.session_state.session_id and not st.session_state.tor_document:
        st.divider()
        if st.button("🚀 Force Generate TOR", use_container_width=True):
            with st.spinner("🔨 Generating TOR..."):
                data = force_generate(st.session_state.session_id)
            if handle_response(data):
                st.rerun()
    elif st.session_state.tor_document:
        st.divider()
        st.info("✅ TOR sudah di-generate")
```

### Step 3: Verifikasi

1. Chat sampai READY_TO_GENERATE → TOR muncul di bawah chat
2. Metadata expander bisa dibuka
3. Download button menghasilkan file .md
4. Force generate di sidebar → TOR generated
5. Escalation scenario → warning muncul

## 6. Output yang Diharapkan

TOR document rendered sebagai markdown di main area, dengan metadata, download button, dan optional escalation warning.

## 7. Dependencies

- **Task 03** — chat working + response handler
- **Task 04** — sidebar structure

## 8. Acceptance Criteria

- [ ] TOR preview muncul ketika `tor_document` ada
- [ ] Metadata expander menampilkan 4 metrics
- [ ] Download button menghasilkan file .md yang valid
- [ ] Force generate button muncul di sidebar (hanya saat session aktif, belum generate)
- [ ] Escalation warning muncul jika escalation_info ada
- [ ] `st.success()` muncul saat TOR generated

## 9. Estimasi

**Medium** — ~1 jam
