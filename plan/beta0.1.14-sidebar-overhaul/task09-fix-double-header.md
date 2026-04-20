# Task 09: Fix Double Header — Conditional Render by Active Tool

## 1. Judul Task

Fix double header: "Generator TOR" hanya tampil di mode Obrolan, skip di Generate Dokumen

## 2. Deskripsi

Bug: saat user memilih alat "Generate Dokumen", header "Generator TOR" tetap muncul DAN `form_document.py` menampilkan header "Generate TOR dari Dokumen" → double header. Fix: render header hanya di mode Obrolan.

## 3. Tujuan Teknis

- `render_header()` mengecek `active_tool` sebelum render
- Jika `active_tool == "chat"` → tampilkan header "Generator TOR"
- Jika `active_tool == "generate_doc"` → skip (form_document.py punya header sendiri)

## 4. Scope

**Yang dikerjakan:**
- `streamlit_app/components/header.py` — tambah kondisi `active_tool`

**Yang tidak dikerjakan:**
- `form_document.py` (header internal tidak diubah)
- Sidebar (tidak terkait)

## 5. Langkah Implementasi

### 5.1 Update `render_header()`

```python
# streamlit_app/components/header.py

def render_header():
    """Render top bar — hanya tampil di mode Obrolan.
    Di mode Generate Dokumen, form_document.py sudah punya header sendiri.
    """
    tool = st.session_state.get("active_tool", "chat")

    # Hanya tampilkan header di mode Obrolan
    if tool == "chat":
        icon = mi("smart_toy", 20, "var(--color-primary)")
        st.markdown(
            f'<h3 style="margin:0;display:flex;align-items:center;gap:8px;">'
            f'{icon} Generator TOR</h3>',
            unsafe_allow_html=True,
        )
```

### 5.2 Verifikasi

Pastikan `app.py` tetap memanggil `render_header()` SEBELUM render konten:

```python
render_sidebar()
render_header()         # ← akan skip jika active_tool != "chat"

tool = st.session_state.get("active_tool", "chat")
if tool == "chat":
    render_chat_tab()
elif tool == "generate_doc":
    render_document_tab()  # ← punya header sendiri di line 23-26
```

## 6. Output yang Diharapkan

**Mode Obrolan:**
```
[smart_toy] Generator TOR
─────────────────────────
[forum] Ceritakan kebutuhan TOR Anda...
```

**Mode Generate Dokumen:**
```
[upload_file] Generate TOR dari Dokumen
Upload dokumen sumber, Gemini otomatis membuat TOR.
```

→ **TIDAK ADA** "Generator TOR" di atas saat mode Generate Dokumen.

## 7. Dependencies

- Task 01 (state: `active_tool` tersedia)
- Task 04 (header simplify sudah dilakukan)

## 8. Acceptance Criteria

- [ ] Mode Obrolan: header "Generator TOR" tampil
- [ ] Mode Generate Dokumen: header "Generator TOR" TIDAK tampil
- [ ] Tidak ada double header di mode apapun
- [ ] Switching alat → header muncul/hilang sesuai mode
- [ ] Server start tanpa error

## 9. Estimasi

Low (15 menit)
