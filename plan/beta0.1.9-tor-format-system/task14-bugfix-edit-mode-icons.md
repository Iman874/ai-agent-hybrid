# Task 14: Bugfix — Edit Mode Custom Style + Ikon Material Design

## 1. Judul Task
Fix Editing Custom Style & Ganti Emoji dengan Material Symbols

## 2. Deskripsi
Terdapat dua bug yang ditemukan pasca-implementasi Task 10–11:

1. **Bug Editing**: UI `format_tab.py` tidak menyediakan form edit untuk custom styles yang dibuat sendiri. Padahal hanya `_default` (is_default=True) yang seharusnya locked. Custom styles harus fully editable (nama, deskripsi, sections, dan config gaya penulisan).
2. **Bug Icon**: Komponen-komponen di `format_tab.py` masih menggunakan emoji Unicode biasa (`📝`, `✨`, `⭐`), bukan `<span class="material-symbols-outlined">` yang sudah di-load melalui Google Fonts di `loader.py`. Ini inkonsisten dengan design system Beta 0.1.8.

## 3. Tujuan Teknis

1. Menambahkan **Edit Mode** di `format_tab.py` yang tampil hanya ketika style yang dipilih bukan default (`is_default == False`).
2. Mengganti semua emoji dengan HTML `<span class="material-symbols-outlined">icon_name</span>` yang di-render via `st.markdown(..., unsafe_allow_html=True)`.

## 4. Scope

### Yang dikerjakan:
- Modifikasi `streamlit_app/components/format_tab.py`:
  - Tambah form edit inline dengan `st.form` atau state toggle `edit_mode`
  - Form mencakup: nama style, deskripsi, config (language, formality, voice, perspective, min/max word, numbering, custom_instructions)
  - Form untuk sections: loop dgn text_input per field (title, required toggle, format_hint selectbox, min_paragraphs number_input, description textarea)
  - Tombol "Simpan" memanggil `client.update_style()`
  - Ganti semua emoji menjadi Material Symbols HTML

### Yang tidak dikerjakan:
- Drag-and-drop reorder sections (Streamlit limitation)
- Menambah/menghapus sections dari edit form (scope terlalu besar, bisa jadi Task 15)
- Perubahan pada backend (routes, models, dsb sudah benar)

## 5. Langkah Implementasi

### 5.1 Tambah state toggle edit mode

```python
# Init di awal fungsi atau session_state
edit_key = f"edit_mode_{selected_id}"
if edit_key not in st.session_state:
    st.session_state[edit_key] = False
```

### 5.2 Tampilkan tombol "Edit Style" hanya jika non-default

```python
if not is_default:
    btn_label = icon("edit") + " Edit Style"
    if st.button(btn_label, key="btn_toggle_edit"):
        st.session_state[edit_key] = not st.session_state[edit_key]
        st.rerun()
```

### 5.3 Buat helper function untuk Material Icons

```python
def icon(name: str) -> str:
    """Render Material Symbol sebagai HTML inline."""
    return f'<span class="material-symbols-outlined" style="vertical-align:middle;font-size:1.1rem">{name}</span>'
```

Gunakan `st.markdown(icon("edit_note") + " Judul", unsafe_allow_html=True)` di seluruh komponen.

### 5.4 Buat edit form (untuk non-default)

```python
if st.session_state.get(edit_key) and not is_default:
    with st.form(key=f"edit_form_{selected_id}"):
        st.markdown("### Edit Style")
        
        new_name = st.text_input("Nama Style", value=selected_style["name"])
        new_desc = st.text_area("Deskripsi", value=selected_style.get("description", ""))
        
        st.divider()
        st.subheader("Gaya Penulisan")
        
        config = selected_style.get("config", {})
        new_language = st.selectbox("Bahasa", ["id", "en"], 
                          index=["id", "en"].index(config.get("language", "id")))
        new_formality = st.selectbox("Formalitas", ["formal", "semi_formal", "informal"],
                          index=["formal", "semi_formal", "informal"].index(config.get("formality", "formal")))
        new_voice = st.selectbox("Voice", ["active", "passive"],
                          index=["active", "passive"].index(config.get("voice", "active")))
        new_perspective = st.selectbox("Perspektif", ["first_person", "third_person"],
                          index=["first_person", "third_person"].index(config.get("perspective", "third_person")))
        
        col1, col2 = st.columns(2)
        with col1:
            new_min_words = st.number_input("Minimal Kata", 
                              value=config.get("min_word_count", 500), min_value=100, step=50)
        with col2:
            new_max_words = st.number_input("Maksimal Kata",
                              value=config.get("max_word_count", 3000), min_value=500, step=100)
        
        new_numbering = st.selectbox("Penomoran", ["numeric", "roman", "none"],
                          index=["numeric", "roman", "none"].index(config.get("numbering_style", "numeric")))
        new_custom_instructions = st.text_area("Instruksi Kustom AI",
                          value=config.get("custom_instructions", ""), height=100)
        
        st.divider()
        st.subheader("Edit Sections")
        
        sections = selected_style.get("sections", [])
        updated_sections = []
        for i, sec in enumerate(sections):
            with st.expander(f"Seksi {i+1}: {sec.get('title', '')}"):
                s_title = st.text_input("Judul Seksi", value=sec.get("title", ""), key=f"s_title_{i}")
                s_desc = st.text_area("Instruksi AI", value=sec.get("description", ""), key=f"s_desc_{i}", height=80)
                s_required = st.checkbox("Wajib Ada", value=sec.get("required", True), key=f"s_req_{i}")
                s_format = st.selectbox("Format Hint", ["paragraphs", "bullet_points", "table", "mixed", ""],
                              index=["paragraphs", "bullet_points", "table", "mixed", ""].index(
                                  sec.get("format_hint", "") or ""), key=f"s_fmt_{i}")
                s_min_para = st.number_input("Min. Paragraf", value=sec.get("min_paragraphs", 1),
                              min_value=0, step=1, key=f"s_para_{i}")
                updated_sections.append({
                    **sec,
                    "title": s_title,
                    "description": s_desc,
                    "required": s_required,
                    "format_hint": s_format,
                    "min_paragraphs": s_min_para
                })
        
        if st.form_submit_button("Simpan Perubahan", type="primary"):
            updates = {
                "name": new_name,
                "description": new_desc,
                "sections": updated_sections,
                "config": {
                    **config,
                    "language": new_language,
                    "formality": new_formality,
                    "voice": new_voice,
                    "perspective": new_perspective,
                    "min_word_count": new_min_words,
                    "max_word_count": new_max_words,
                    "numbering_style": new_numbering,
                    "custom_instructions": new_custom_instructions,
                }
            }
            result = client.update_style(selected_id, updates)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success("Style berhasil disimpan!")
                st.session_state[edit_key] = False
                st.rerun()
```

### 5.5 Ganti semua emoji di format_tab.py

Ganti:
- `st.header("Konfigurasi Format TOR")` → `st.markdown(icon("palette") + " **Konfigurasi Format TOR**", unsafe_allow_html=True)`
- `st.subheader(f"📝 {name}")` → `st.markdown(icon("description") + f" **{name}**", unsafe_allow_html=True)`
- `st.subheader("✨ Ekstrak Format...")` → `st.markdown(icon("auto_awesome") + " **Ekstrak Format dari Dokumen Baru**", unsafe_allow_html=True)`
- `"⭐ (Aktif)"` di options dict → `"(Aktif)"` dalam teks biasa untuk selectbox (karena selectbox Streamlit tidak support HTML)
- `"📄 Extract dari Dokumen"` label button → jadi plain text (button di Streamlit tidak render HTML)

**Catatan penting**: Streamlit widget label (button, selectbox, header) tidak support HTML. `st.markdown(..., unsafe_allow_html=True)` hanya bisa dipakai untuk teks/judul non-widget. Untuk judul dan deskripsi bisa menggunakan Material Symbols, untuk label widget gunakan teks biasa.

## 6. Output yang Diharapkan

- Tab "Format TOR" menampilkan tombol "Edit Style" hanya untuk custom styles (bukan default).
- Klik "Edit Style" membuka form inline berisi semua field editable.
- Klik "Simpan" memanggil API update dan me-refresh page.
- Judul dan label non-widget menggunakan icon Material Symbols (bukan emoji).
- Default style tetap tampil read-only (tanpa tombol edit).

## 7. Dependencies

- [task10-ui-format-tab.md]
- [task11-ui-extract-flow.md]
- [task12-frontend-api-client.md] (`update_style()` sudah tersedia)

## 8. Acceptance Criteria

- [ ] Pilih custom style → tombol "Edit Style" muncul.
- [ ] Pilih default style → TIDAK ada tombol "Edit Style".
- [ ] Form edit menampilkan nilai terkini dari style yang dipilih (pre-filled).
- [ ] Submit form → API `PUT /styles/{id}` berhasil dipanggil → response 200.
- [ ] Judul tab dan subheader menggunakan `<span class="material-symbols-outlined">` bukan emoji unicode.
- [ ] Streamlit widget labels tetap menggunakan teks biasa (bukan HTML).

## 9. Estimasi

Medium
