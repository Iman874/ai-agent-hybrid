# 📘 Plan Design — Beta 0.1.12
# Document Upload → Style Selection & Auto-Creation

> **Codename**: `doc-upload-style`
> **Versi**: Beta 0.1.12
> **Tanggal**: 2026-04-20
> **Status**: Draft — Menunggu Review
> **Prasyarat**: Beta 0.1.11 (Session History) + Beta 0.1.9 (TOR Format System) selesai

---

## 1. Masalah yang Ditemukan

### 1.1 Apa yang Terjadi Saat Ini

Saat user mengupload dokumen di tab **"Dari Dokumen"** (`form_document.py`), alur saat ini:

```
Upload dokumen → Parse text → Build prompt → Gemini generate TOR → Tampilkan hasil
```

**Masalah kritis:**

| # | Masalah | Dampak |
|---|---------|--------|
| 1 | **Format style TIDAK digunakan** di `generate_doc.py` | TOR yang dihasilkan dari dokumen **tidak mengikuti** active style yang dipilih user di Tab Format |
| 2 | **Tidak ada opsi memilih/membuat style** saat upload | User tidak bisa menentukan "gunakan format style apa" untuk dokumen yang di-upload |
| 3 | **Tidak ada auto-detect style** dari dokumen sumber | Jika dokumen sumber *sudah punya* format TOR tertentu, sistem **tidak mengenali** dan **tidak menawarkan** untuk menjadikannya style baru |

### 1.2 Root Cause (Analisis Teknis)

**File: `app/api/routes/generate_doc.py`** — Line 47-52:

```python
# Step 4: Build prompt
prompt = GeminiPromptBuilder.build_from_document(
    document_text=document_text,
    user_context=context,
    rag_examples=rag_examples,
    # ❌ format_spec TIDAK di-pass!
    # ❌ Padahal build_from_document() sudah support parameter format_spec
)
```

Bandingkan dengan `generate_service.py` (Line 90-99), yang **sudah benar**:

```python
# ✅ Sudah ada di GenerateService
active_style = self.style_manager.get_active_style()
format_spec = active_style.to_prompt_spec()
prompt = self.prompt_builder.build_standard(data=data, rag_examples=rag_examples, format_spec=format_spec)
```

**Kesimpulan**: `generate_doc.py` adalah modul yang dibangun **sebelum** TOR Format System (beta 0.1.9), sehingga belum di-wire ke `StyleManager`.

### 1.3 Dimensi Masalah Tambahan

Selain itu, ada pertanyaan UX yang lebih besar:

> Saat user upload dokumen referensi, **apakah sistem harus otomatis mengenali bahwa dokumen** itu punya "style" tertentu, lalu menawarkan user untuk **membuat style baru** dari format dokumen tersebut?

Saat ini:
- Tab "Format TOR" punya fitur **Extract dari Dokumen** → bisa upload TOR referensi → AI analisis format → simpan sebagai style baru
- Tab "Dari Dokumen" HANYA generate TOR dari isi dokumen → **tidak menyentuh style system sama sekali**

Kedua fitur ini **terpisah total** dan user harus tahu flow yang berbeda:
- Mau **meniru format**? → Tab Format TOR → Extract
- Mau **mengambil konten**? → Tab Dari Dokumen → Generate

**Ini membingungkan**. User mungkin berpikir: "Saya upload dokumen → TOR saya pasti pakai format dari dokumen itu" — padahal **bukan**.

---

## 2. Solusi yang Diusulkan

### 2.1 Empat Peningkatan

```
┌─────────────────────────────────────────────────────────────────────┐
│                 PERBAIKAN BETA 0.1.12                               │
│                                                                     │
│  [A] Wire active style ke generate_doc.py                           │
│      → TOR dari dokumen mengikuti format aktif                      │
│                                                                     │
│  [B] Tambah parameter style_id di API endpoint                      │
│      → Backend siap menerima style spesifik                         │
│                                                                     │
│  [C] Auto-detect & Extract tetap di tab "Format TOR"                │
│      → Extraction disempurnakan: extract → simpan → otomatis        │
│                                                                     │
│  [D] Tab "Dari Dokumen" tetap SIMPEL                                │
│      → Hanya info text style aktif, tanpa selector kompleks         │
│      → Fitur extract/auto-detect TIDAK ada di sini                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Prinsip Pemisahan Tab

| Tab | Tanggung Jawab | UX |
|-----|----------------|----|
| **Format TOR** | Manage styles: CRUD, extract dari dokumen | Fitur lengkap style management |
| **Dari Dokumen** | Upload dokumen → generate TOR | **Simpel**: hanya info style aktif + upload + generate |

### 2.3 Alur UX Baru

**Tab "Dari Dokumen" (Simpel):**
```
### 📤 Generate TOR dari Dokumen
Upload dokumen sumber, Gemini otomatis membuat TOR.
🎨 Format yang digunakan: Format TOR Standar — ubah di tab Format TOR

Upload dokumen: [Choose File]
Konteks tambahan: [__________]

[Generate TOR]
```

**Tab "Format TOR" — Extraction Flow:**
```
[... existing style selector, viewer, editor ...]

────────────────────────────
✨ Ekstrak Format dari Dokumen
Upload contoh dokumen TOR → AI menganalisis → Simpan sebagai style baru

Upload Dokumen TOR Referensi: [Choose File]
Nama style baru (opsional): [___________]
[Ekstrak dengan AI]

→ Sukses: "Style 'TOR Rapat BAPPENAS' berhasil diekstrak dan disimpan!"
```

---

## 3. Arsitektur Perubahan

### 3.1 File yang Dimodifikasi

| # | File | Perubahan | Tipe |
|---|------|-----------|------|
| 1 | `app/api/routes/generate_doc.py` | Wire `style_manager`, inject `format_spec` + `style_id` param | MODIFY |
| 2 | `streamlit_app/state.py` | Tambah state keys | MODIFY |
| 3 | `streamlit_app/api/client.py` | Update `generate_from_document()` + tambah `create_style()` | MODIFY |
| 4 | `streamlit_app/components/form_document.py` | **Simplify**: hapus style selector, hanya info text style aktif | MODIFY |
| 5 | `streamlit_app/components/format_tab.py` | Perbaiki extraction flow — otomatis simpan style baru | MODIFY |

### 3.2 Tidak Ada File Baru

Semua infrastruktur yang dibutuhkan **sudah ada** dari Beta 0.1.9:
- `StyleManager` ✅
- `StyleExtractor` ✅
- `TORStyle.to_prompt_spec()` ✅
- API endpoints CRUD styles ✅
- `GeminiPromptBuilder.build_from_document(format_spec=...)` ✅

Kita hanya perlu **meng-wire backend** dan **merapikan UX** (memindahkan fitur ke tab yang tepat).

---

## 4. Detail Teknis per Komponen

### 4.1 Backend — `generate_doc.py` Update

```python
# SEBELUM (saat ini):
prompt = GeminiPromptBuilder.build_from_document(
    document_text=document_text,
    user_context=context,
    rag_examples=rag_examples,
)

# SESUDAH:
style_manager = request.app.state.style_manager

# Tentukan style: spesifik, atau active
if style_id:
    style = style_manager.get_style(style_id)
else:
    style = style_manager.get_active_style()

format_spec = style.to_prompt_spec()

prompt = GeminiPromptBuilder.build_from_document(
    document_text=document_text,
    user_context=context,
    rag_examples=rag_examples,
    format_spec=format_spec,             # ← FIX: sekarang di-pass
)

# Post-process juga harus pakai style
processed = post_processor.process(gemini_response.text, style=style)
```

### 4.2 API Endpoint — Parameter Baru

```python
@router.post("/generate/from-document", response_model=GenerateResponse)
async def generate_from_document(
    request: Request,
    file: UploadFile = File(...),
    context: str = Form(""),
    style_id: str = Form(None, description="ID style TOR (optional, default = aktif)"),
    auto_detect_style: bool = Form(False, description="Jika True, AI mengekstrak style dari dokumen dulu"),
):
```

### 4.3 Auto-Detect Flow (Backend)

Jika `auto_detect_style=True`, sebelum generate TOR, lakukan:

```python
if auto_detect_style:
    # 1. Gunakan StyleExtractor yang sudah ada
    style_extractor = request.app.state.style_extractor
    detected_style = await style_extractor.extract_from_text(document_text)

    # 2. Return dulu ke frontend untuk preview
    return {
        "action": "style_detected",
        "detected_style": detected_style.model_dump(),
        "document_preview": document_text[:500],
    }
```

> **Catatan**: Ini memerlukan 2-step flow di frontend:
> 1. Request pertama: auto_detect → return style preview
> 2. Request kedua: confirm style → generate TOR

### 4.4 Frontend — `form_document.py` (Disimplifikasi)

Tab "Dari Dokumen" **disederhanakan** — tanpa style selector, tanpa auto-detect.
Hanya menampilkan info text style aktif:

```python
    # Info style aktif (read-only)
    active = get_active_style()
    active_name = active.get("name", "Default") if active else "Default"
    st.caption(f"🎨 Format yang digunakan: **{active_name}** — ubah di tab Format TOR")
```

Semua fungsi auto-detect (`_handle_auto_detect()`, `_render_detected_style_preview()`, dll) **dihapus** dari file ini.

### 4.5 Frontend — `format_tab.py` (Extraction Diperbaiki)

Section extraction di tab Format TOR diperbaiki agar **otomatis menyimpan** style baru setelah extract:

```python
    # Extraction section di format_tab.py
    if uploaded_file:
        if st.button("Ekstrak dengan AI", type="primary"):
            with st.spinner("AI sedang menganalisis..."):
                res = client.extract_style(file_bytes, uploaded_file.name)
                if custom_name:
                    res["name"] = custom_name
                # Simpan style baru (PERBAIKAN — sebelumnya tidak disimpan)
                save_res = client.create_style(res)
                st.success(f"Style '{save_res['name']}' berhasil disimpan!")
                st.rerun()
```
```

---

## 6. Endpoint yang Diperlukan (Sudah Ada)

Semua endpoint yang diperlukan **sudah tersedia** dari Beta 0.1.9:

| Endpoint | Kegunaan | Status |
|----------|----------|--------|
| `GET /api/v1/styles` | Fetch list styles untuk dropdown | ✅ Ada |
| `GET /api/v1/styles/active` | Get active style name | ✅ Ada |
| `POST /api/v1/styles/extract` | Extract style dari dokumen | ✅ Ada |
| `POST /api/v1/styles` | Simpan style baru | ✅ Ada |
| `POST /api/v1/styles/{id}/activate` | Set style sebagai aktif | ✅ Ada |

---

## 7. Resiko & Mitigasi

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| Auto-detect menambah latency (2x Gemini call: detect + generate) | UX lambat ~10-15 detik | Tampilkan progress bar 2 tahap: "Menganalisis format..." → "Generating TOR..." |
| Dokumen non-TOR di-upload dengan auto-detect | Style yang dihasilkan tidak berguna | Tampilkan confidence score dari extraction, warning jika rendah |
| Style extracted bertumpuk di storage | Clutter | Beri label `source: "extracted"`, bisa di-filter/hapus nanti |

---

## 8. Batasan Scope Beta 0.1.12

| Termasuk | Tidak Termasuk |
|----------|----------------|
| ✅ Wire active style ke generate_doc | ❌ Per-session style selection (scope v0.2+) |
| ✅ Parameter `style_id` di API endpoint | ❌ Batch upload multi-dokumen |
| ✅ Tab "Dari Dokumen" simpel (info text saja) | ❌ Style selector inline di tab "Dari Dokumen" |
| ✅ Tab "Format TOR" extraction diperbaiki | ❌ Merge style dari beberapa dokumen |
| ✅ Hapus duplikasi fitur upload antar tab | ❌ Auto-detect di tab "Dari Dokumen" |

---

## 9. Task Breakdown Estimasi

| # | Task | Scope | Estimasi |
|---|------|-------|----------|
| 1 | **Wire style to generate_doc** — Inject `format_spec` dan `post_processor(style=)` di `generate_doc.py` | Backend fix kritis | Low |
| 2 | **API parameter extension** — Tambah `style_id` di endpoint | Backend | Low |
| 3 | **State & client update** — State keys + update `generate_from_document()` di client | Frontend infra | Low |
| 4 | **UI style selector** — Radio + dropdown di `form_document.py` *(interim, dihapus di task 7)* | UI | Medium |
| 5 | **Auto-detect flow** — 2-step UX di `form_document.py` *(interim, dihapus di task 7)* | UI + Backend | High |
| 6 | **Unit & Integration Testing** — Test endpoint `generate_doc` dengan style | Backend test only | Medium |
| 7 | **Fix UI placement** — Simplify tab "Dari Dokumen", perbaiki extraction di tab "Format TOR" | UI cleanup | Medium |

> **Catatan**: Task 4-5 memasang fitur interim. Task 7 membersihkan: memindahkan extraction ke tab Format TOR dan menyederhanakan tab Dari Dokumen. Testing UI dilakukan manual oleh user.

---

## 10. Verification Plan

### 10.1 Unit & Integration Tests (Dikerjakan oleh Developer)

```bash
# Test bahwa generate_doc sekarang memakai active style
pytest tests/test_generate_doc_style.py -v

# Test auto-detect flow (mock Gemini response)
pytest tests/test_doc_auto_detect.py -v
```

**Test cases yang wajib ada:**

| # | Test Case | Tipe |
|---|-----------|------|
| 1 | `generate_doc` endpoint menggunakan active style (bukan fallback) | Integration |
| 2 | `generate_doc` endpoint menerima `style_id` spesifik dan menggunakannya | Integration |
| 3 | `generate_doc` dengan `style_id` invalid → return 404 | Integration |
| 4 | `generate_doc` dengan `auto_detect_style=True` → return `action: style_detected` | Integration |
| 5 | `PostProcessor.process()` menerima style dari generate_doc flow | Unit |
| 6 | Auto-detect flow: mock Gemini → valid `TORStyle` di-return | Unit |

### 10.2 Manual UI Testing (Dikerjakan oleh User)

User akan melakukan testing UI secara mandiri setelah implementasi selesai. Developer **tidak** melakukan UI testing.
