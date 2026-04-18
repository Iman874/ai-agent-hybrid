# Task 07 — Tambah Tab Mode: Hybrid Chat + Gemini Direct

## 1. Judul Task

Tambahkan tab-based mode selection: "Hybrid Chat" dan "Gemini Direct" dengan form input untuk Gemini-only mode.

## 2. Deskripsi

User merasa kurang fleksibel karena hanya ada mode Hybrid. Tambahkan `st.tabs()` agar user bisa memilih:
- **💬 Hybrid Chat**: Mode chat bolak-balik (existing) — local LLM + auto-escalation
- **🚀 Gemini Direct**: Mode form — user isi field TOR langsung, Gemini generate tanpa chat

## 3. Tujuan Teknis

- `st.tabs(["💬 Hybrid Chat", "🚀 Gemini Direct"])` di main area
- Tab Hybrid: pindahkan seluruh chat interface ke dalam tab ini (tanpa perubahan logic)
- Tab Gemini Direct: form input (text_input & text_area) untuk 7 field TOR + tombol Generate
- Gemini Direct memanggil `POST /api/v1/generate` dengan `data_override`
- TOR Preview ditampilkan per-tab (masing-masing punya state sendiri)
- Sidebar tetap berfungsi — progress hanya relevan untuk Hybrid tab

## 4. Scope

### Yang dikerjakan
- Refactor main area ke `st.tabs()`
- Tab 1 (Hybrid): migrasi chat UI yang sudah ada ke dalam tab
- Tab 2 (Gemini Direct): form input 7 field TOR + Generate button
- API call untuk Gemini Direct via `POST /api/v1/generate` (data_override)
- TOR Preview di Gemini Direct tab
- Download button di Gemini Direct tab

### Yang tidak dikerjakan
- Perubahan backend (sudah support `data_override`)
- Sidebar restructure (tetap sama, terkait Hybrid)

## 5. Langkah Implementasi

### Step 1: Tambah helper function untuk Gemini Direct

```python
def generate_direct(data: dict) -> dict:
    """Generate TOR langsung via Gemini tanpa chat."""
    try:
        resp = requests.post(f"{API_URL}/generate", json={
            "session_id": None,
            "mode": "standard",
            "data_override": data,
        }, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "Backend tidak bisa dihubungi."}
    except requests.Timeout:
        return {"error": "Request timeout."}
    except requests.HTTPError as e:
        try:
            error_data = e.response.json()
            return {"error": error_data.get("error", {}).get("message", str(e))}
        except Exception:
            return {"error": f"HTTP Error: {e.response.status_code}"}
```

### Step 2: Init state untuk Gemini Direct

Tambah di session state init:
```python
if "direct_tor" not in st.session_state:
    st.session_state.direct_tor = None
```

### Step 3: Wrap main area dengan tabs

```python
tab_hybrid, tab_direct = st.tabs(["💬 Hybrid Chat", "🚀 Gemini Direct"])

with tab_hybrid:
    # --- Existing chat UI pindah ke sini ---
    # (semua chat message render, TOR preview, chat input)
    ...

with tab_direct:
    st.subheader("🚀 Generate TOR Langsung")
    st.caption("Isi field di bawah, Gemini akan langsung membuat TOR tanpa proses chat.")

    with st.form("gemini_direct_form"):
        judul = st.text_input("Judul Kegiatan *", placeholder="Contoh: Workshop Penerapan AI untuk ASN")
        latar_belakang = st.text_area("Latar Belakang *", placeholder="Konteks dan alasan kegiatan ini diperlukan...", height=100)
        tujuan = st.text_area("Tujuan *", placeholder="Apa yang ingin dicapai...", height=80)
        ruang_lingkup = st.text_area("Ruang Lingkup *", placeholder="Batasan dan cakupan pekerjaan...", height=80)
        output = st.text_area("Output / Deliverable *", placeholder="Deliverable yang diharapkan...", height=80)
        timeline = st.text_input("Timeline *", placeholder="Contoh: 3 hari, 15-17 Juli 2026")
        estimasi_biaya = st.text_input("Estimasi Biaya (opsional)", placeholder="Contoh: Rp 50.000.000")

        submitted = st.form_submit_button("🚀 Generate TOR", use_container_width=True)

    if submitted:
        # Validasi minimal
        if not judul or not tujuan:
            st.error("❌ Minimal isi Judul dan Tujuan!")
        else:
            data = {
                "judul": judul or None,
                "latar_belakang": latar_belakang or None,
                "tujuan": tujuan or None,
                "ruang_lingkup": ruang_lingkup or None,
                "output": output or None,
                "timeline": timeline or None,
                "estimasi_biaya": estimasi_biaya or None,
            }
            with st.spinner("🔨 Gemini sedang membuat TOR..."):
                result = generate_direct(data)

            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.session_state.direct_tor = result
                st.rerun()

    # TOR Preview di tab Gemini Direct
    if st.session_state.direct_tor:
        tor = st.session_state.direct_tor
        st.divider()
        st.success("✅ TOR Berhasil Dibuat!")

        tor_doc = tor.get("tor_document", tor)
        content = tor_doc.get("content", "")
        meta = tor_doc.get("metadata", {})

        with st.expander("📋 Metadata", expanded=False):
            cols = st.columns(4)
            cols[0].metric("Model", meta.get("generated_by", "gemini"))
            cols[1].metric("Mode", meta.get("mode", "direct"))
            cols[2].metric("Words", meta.get("word_count", 0))
            cols[3].metric("Time", f"{meta.get('generation_time_ms', 0)}ms")

        st.markdown(content)

        st.download_button(
            label="⬇️ Download TOR (.md)",
            data=content,
            file_name="tor_document_direct.md",
            mime="text/markdown",
            use_container_width=True,
        )
```

### Step 4: Sidebar awareness

Tambah info mode di sidebar:
```python
# Di atas system info
st.caption("Mode aktif ditentukan oleh tab yang dipilih.")
```

### Step 5: Verifikasi

1. Buka app — 2 tab muncul
2. Tab Hybrid Chat: chat interface berfungsi seperti sebelumnya
3. Tab Gemini Direct: form muncul, isi minimal judul+tujuan, klik Generate → TOR muncul
4. Download berfungsi di kedua tab
5. New Session hanya reset Hybrid state

## 6. Output yang Diharapkan

Dua tab fungsional: Hybrid Chat (existing flow) dan Gemini Direct (form → instant TOR).

## 7. Dependencies

- **Task 01-05** — semua fitur sebelumnya selesai
- Backend: `POST /api/v1/generate` sudah support `data_override`

## 8. Acceptance Criteria

- [ ] Dua tab muncul: "💬 Hybrid Chat" dan "🚀 Gemini Direct"
- [ ] Tab Hybrid: semua fitur chat tetap berfungsi
- [ ] Tab Gemini Direct: form 7 field TOR muncul
- [ ] Validasi minimal: judul dan tujuan wajib diisi
- [ ] Klik Generate → Gemini API call → TOR preview
- [ ] Download .md berfungsi di tab Gemini Direct
- [ ] Metadata expander berfungsi
- [ ] Error handling saat Gemini gagal
- [ ] "Percakapan Baru" hanya reset tab Hybrid

## 9. Estimasi

**Medium** — ~1.5 jam
