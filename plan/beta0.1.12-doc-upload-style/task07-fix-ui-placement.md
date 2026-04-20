# Task 07: Perbaiki Penempatan Fitur UI — Format Tab & Dari Dokumen Tab

> **Status**: [x] Selesai
> **Estimasi**: Medium (1–2 jam)
> **Dependency**: Task 04, Task 05

## 1. Deskripsi

Saat ini terdapat **duplikasi** dan **salah penempatan** fitur antara dua tab:

| Tab | Masalah |
|-----|---------|
| **Format TOR** (`format_tab.py`) | Ada section "Ekstrak Format dari Dokumen Baru" + file uploader (line 120-148). Ini **duplikat** dan membingungkan karena fitur extraction sudah ada di tab "Dari Dokumen" (auto-detect). |
| **Dari Dokumen** (`form_document.py`) | Ada section besar **"Format Output TOR"** lengkap dengan radio button 3 opsi + style selector (line 24-80). Ini **terlalu berat** untuk tab yang tujuannya hanya upload + generate. |

**Apa yang salah secara UX:**
- User melihat "Upload dokumen" di **dua tempat** (Format TOR tab DAN Dari Dokumen tab)
- Section "Format Output TOR" yang besar mengambil terlalu banyak ruang di tab "Dari Dokumen"
- Fitur auto-detect style seharusnya **cukup di tab Format TOR saja**, karena itu tentang manajemen style

## 2. Tujuan Teknis

### Prinsip Pemisahan Tanggung Jawab:

| Tab | Tanggung Jawab | Perubahan |
|-----|----------------|-----------|
| **Format TOR** | Manage styles: lihat, edit, buat, duplikasi, **extract dari dokumen** | Pertahankan extraction feature (sudah benar di sini), hapus yang duplikat jika ada |
| **Dari Dokumen** | Upload dokumen → generate TOR (simpel) | **Hapus section "Format Output TOR"** yang besar. Cukup info text kecil menunjukkan style aktif saat ini, tanpa radio button / tanpa fitur extract di sini |

## 3. Scope

**Yang dikerjakan:**
- `streamlit_app/components/form_document.py` — simplify: hapus radio button / style selector, ganti dengan info text sederhana
- `streamlit_app/components/format_tab.py` — perbaiki section extraction agar hasilnya bisa langsung menjadi style baru yang **disimpan** (saat ini extract tapi tidak save)

**Yang tidak dikerjakan:**
- Perubahan backend
- Perubahan state management (state keys tetap ada, hanya tidak dipakai di form_document)

## 4. Langkah Implementasi

### 4.1 Simplify `form_document.py` — Hapus Style Selector

- [x] **Hapus** seluruh section "Format Output TOR" (line 24-80) termasuk:
  - Radio button `doc_style_mode`
  - Style dropdown `doc_selected_style_id`
  - Auto-detect section + `auto_style_name`

- [x] **Ganti** dengan info text sederhana (1-2 baris):

```python
    # --- Info Style Aktif ---
    active = get_active_style()
    active_name = active.get("name", "Default") if active else "Default"
    st.caption(f"🎨 Format yang digunakan: **{active_name}** — ubah di tab Format TOR")
```

### 4.2 Simplify `_handle_generate()` — Hapus `style_id` Parameter di UI

- [x] Fungsi `_handle_generate()` tetap menerima `style_id` (agar backward compatible dengan API), tapi **selalu pass None** dari UI sehingga backend pakai active style:

```python
    if st.button(
        "Generate TOR",
        use_container_width=True,
        disabled=uploaded_file is None,
    ):
        if uploaded_file:
            _handle_generate(uploaded_file, doc_context)
```

- [x] Signature `_handle_generate()` bisa disimplify kembali:

```python
def _handle_generate(uploaded_file, context: str):
    """Process uploaded file dan generate TOR (pakai active style)."""
    with st.spinner("Membaca dokumen dan generating TOR..."):
        result = generate_from_document(
            uploaded_file.read(),
            uploaded_file.name,
            context,
        )
    # ... rest unchanged
```

### 4.3 Hapus Auto-Detect Functions dari `form_document.py`

- [x] **Hapus** fungsi-fungsi auto-detect yang sudah tidak diperlukan di file ini:
  - `_handle_auto_detect()`
  - `_render_detected_style_preview()`
  - `_confirm_and_generate()`
  - `_cancel_auto_detect()`

- [x] **Hapus** import yang tidak terpakai lagi:
  - `extract_style`
  - `create_style`
  - `get_styles`

- [x] Import yang **tetap dipertahankan**:

```python
from api.client import generate_from_document
from api.client import get_active_style
```

### 4.4 Perbaiki Extraction di `format_tab.py`

- [x] Section "Ekstrak Format dari Dokumen Baru" (line 120-148) **sudah benar tempatnya** di tab Format TOR, tapi perlu diperbaiki:

**Masalah saat ini**: Setelah `extract_style()` berhasil, hasilnya langsung di-`rerun()` tanpa menyimpan style baru ke backend. Perbaiki flow:

```python
    # --- Extraction Section ---
    st.divider()
    st.markdown(
        icon("auto_awesome") + " **Ekstrak Format dari Dokumen**",
        unsafe_allow_html=True,
    )
    st.info(
        "Upload contoh dokumen TOR → AI menganalisis struktur dan format → "
        "Simpan sebagai style baru yang bisa Anda pakai."
    )

    uploaded_file = st.file_uploader(
        "Upload Dokumen TOR Referensi",
        type=["pdf", "docx", "md", "txt"],
        key="format_extractor_uploader",
    )

    extract_name = st.text_input(
        "Nama style baru (opsional)",
        placeholder="AI akan memberi nama otomatis jika kosong",
        key="extract_style_name",
    )

    if uploaded_file:
        if st.button("Ekstrak dengan AI", type="primary"):
            with st.spinner("AI sedang menganalisis gaya bahasa dan struktur... (15-30 detik)"):
                try:
                    file_bytes = uploaded_file.read()
                    res = client.extract_style(file_bytes, uploaded_file.name)
                    if "error" in res:
                        st.error(f"Gagal melakukan ekstraksi: {res['error']}")
                    else:
                        # Override nama jika user set
                        if extract_name.strip():
                            res["name"] = extract_name.strip()

                        # Simpan style baru
                        save_res = client.create_style(res)
                        if "error" in save_res:
                            st.error(f"Gagal menyimpan: {save_res['error']}")
                        else:
                            st.success(
                                f"✅ Style **\"{save_res.get('name', res.get('name'))}\"** "
                                "berhasil diekstrak dan disimpan!"
                            )
                            st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
```

### 4.5 Pastikan `create_style` Ada di `client.py`

- [x] Cek apakah `client.create_style()` sudah ada. Jika belum, tambahkan:

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

### 4.6 Pastikan `POST /styles` Ada di Backend

- [x] Cek apakah `app/api/routes/styles.py` sudah punya endpoint `POST /styles`. Jika belum, tambahkan:

```python
@router.post("/", response_model=TORStyle)
async def create_style_endpoint(
    style_data: dict,
    manager: StyleManager = Depends(get_style_manager)
):
    """Membuat style baru dari data lengkap."""
    from app.models.tor_style import TORStyle
    style = TORStyle(**style_data)
    return manager.create_style(style)
```

## 5. Output yang Diharapkan

### Tab "Dari Dokumen" — SESUDAH (Simpel):

```
### 📤 Generate TOR dari Dokumen
Upload dokumen sumber, Gemini otomatis membuat TOR.
🎨 Format yang digunakan: Format TOR Standar — ubah di tab Format TOR

Upload dokumen: [Choose File]
Konteks tambahan: [__________]

[Generate TOR]
```

### Tab "Format TOR" — SESUDAH (Extraction disempurnakan):

```
🎨 Konfigurasi Format TOR
[... existing style selector, viewer, editor ...]

────────────────────────────
✨ Ekstrak Format dari Dokumen
Upload contoh dokumen TOR → AI menganalisis → Simpan sebagai style baru

Upload Dokumen TOR Referensi: [Choose File]
Nama style baru: [___________]
[Ekstrak dengan AI]
```

## 6. Acceptance Criteria

- [x] Tab "Dari Dokumen" **tidak lagi** memiliki radio button / style selector.
- [x] Tab "Dari Dokumen" menampilkan nama style aktif sebagai info text saja.
- [x] Tab "Dari Dokumen" tidak memiliki fitur auto-detect / extraction.
- [x] Tab "Format TOR" tetap memiliki section extraction.
- [x] Extraction di tab "Format TOR" **menyimpan** style baru setelah berhasil diekstrak.
- [x] User bisa memasukkan nama custom untuk style yang diekstrak.
- [x] Tidak ada duplikasi fitur upload antara dua tab.
- [x] Server start tanpa error.
