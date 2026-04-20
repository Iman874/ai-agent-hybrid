import streamlit as st
import pandas as pd
from api import client
from utils.icons import mi
from utils.notify import notify


def render_format_tab():
    st.markdown(
        mi("palette", 22) + " **Konfigurasi Format TOR**",
        unsafe_allow_html=True,
    )
    st.markdown("Pilih, buat, atau ekstrak gaya penulisan TOR yang akan digunakan oleh AI.")

    styles = client.get_styles()
    if not styles:
        notify(
            "Menunggu koneksi backend untuk memuat format...",
            "warning",
            icon="sync",
            method="inline",
        )
        return

    if len(styles) == 0:
        return

    # --- Style Selector ---
    active_style_id = next((s["id"] for s in styles if s.get("is_active")), None)

    options = {
        s["id"]: f"{s['name']} {'(Aktif)' if s.get('is_active') else ''}"
        for s in styles
    }

    col1, col2 = st.columns([3, 1])
    with col1:
        index = list(options.keys()).index(active_style_id) if active_style_id in options else 0
        selected_id = st.selectbox(
            "Format yang Tersedia",
            options=list(options.keys()),
            format_func=lambda x: options[x],
            index=index,
        )
    with col2:
        st.write("")
        st.write("")
        if selected_id != active_style_id:
            if st.button("Jadikan Aktif", type="primary", use_container_width=True):
                if client.set_active_style(selected_id):
                    notify("Format aktif berhasil diubah.", "success")
                    st.rerun()
                else:
                    notify("Gagal mengubah format aktif.", "error")

    st.divider()

    selected_style = next((s for s in styles if s["id"] == selected_id), None)
    if not selected_style:
        return

    is_default = selected_style.get("is_default", False)

    # --- Header Style Detail ---
    st.markdown(
        mi("description", 18) + f" **{selected_style['name']}**",
        unsafe_allow_html=True,
    )
    if is_default:
        st.caption("Format bawaan sistem — read only, tidak bisa diedit.")
    else:
        st.caption(selected_style.get("description", ""))

    # --- Action Row ---
    edit_key = f"edit_mode_{selected_id}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    action_cols = st.columns([1, 1, 1, 3])

    with action_cols[0]:
        if not is_default:
            edit_label = "Selesai Edit" if st.session_state[edit_key] else "Edit Style"
            if st.button(edit_label, use_container_width=True):
                st.session_state[edit_key] = not st.session_state[edit_key]
                st.rerun()

    with action_cols[1]:
        with st.popover("Tiru (Klon)"):
            new_name = st.text_input("Nama Format Baru", value=f"Salinan {selected_style['name']}", key="clone_name")
            if st.button("Buat Salinan", key="btn_clone"):
                with st.spinner():
                    res = client.duplicate_style(selected_style["id"], new_name)
                    if "error" in res:
                        notify(res["error"], "error", method="inline")
                    else:
                        st.rerun()

    with action_cols[2]:
        if not is_default:
            with st.popover("Hapus", help="Hapus permanen"):
                notify("Tindakan ini tidak bisa dibatalkan.", "warning", method="inline")
                if selected_style.get("is_active"):
                    notify(
                        "Ubah aktif style ke format lain sebelum menghapus!",
                        "error",
                        method="inline",
                    )
                else:
                    if st.button("Ya, Hapus Sekarang", type="primary", key="btn_delete"):
                        res = client.delete_style(selected_style["id"])
                        if "error" in res:
                            notify(res["error"], "error", method="inline")
                        else:
                            st.rerun()

    st.divider()

    # --- EDIT FORM (hanya untuk custom style) ---
    if not is_default and st.session_state.get(edit_key):
        _render_edit_form(selected_style, edit_key)
    else:
        # --- READ-ONLY VIEW ---
        _render_readonly_view(selected_style)

    # --- Extraction Section ---
    st.divider()
    st.markdown(
        mi("auto_awesome", 18) + " **Ekstrak Format dari Dokumen**",
        unsafe_allow_html=True,
    )
    notify(
        "Upload contoh dokumen TOR → AI menganalisis struktur dan format → "
        "Simpan sebagai style baru yang bisa Anda pakai.",
        "info",
        icon="auto_awesome",
        method="inline",
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
                        notify(
                            f"Gagal melakukan ekstraksi: {res['error']}",
                            "error",
                            method="banner",
                        )
                    else:
                        if extract_name.strip():
                            res["name"] = extract_name.strip()

                        save_res = client.create_style(res)
                        if "error" in save_res:
                            notify(
                                f"Gagal menyimpan: {save_res['error']}",
                                "error",
                                method="banner",
                            )
                        else:
                            notify(
                                f"Style \"{save_res.get('name', res.get('name'))}\" berhasil diekstrak dan disimpan!",
                                "success",
                            )
                            st.rerun()
                except Exception as e:
                    notify(f"Terjadi kesalahan: {e}", "error", method="banner")


def _render_readonly_view(selected_style: dict):
    """Tampilkan detail style dalam mode read-only."""
    st.markdown(
        mi("format_list_bulleted", 18) + " **Struktur Seksi**",
        unsafe_allow_html=True,
    )
    sections = selected_style.get("sections", [])
    if sections:
        items = []
        for i, section in enumerate(sections, 1):
            req = "Wajib" if section.get("required") else "Opsional"
            items.append({
                "No.": i,
                "Nama Seksi": section.get("title"),
                "Tipe": req,
                "Format": section.get("format_hint", "-"),
                "Min. Paragraf": section.get("min_paragraphs", 1),
            })
        st.dataframe(pd.DataFrame(items), hide_index=True, use_container_width=True)

    st.markdown(
        mi("tune", 18) + " **Gaya Penulisan**",
        unsafe_allow_html=True,
    )
    config = selected_style.get("config", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Bahasa", config.get("language", "id").upper())
    c2.metric("Formalitas", str(config.get("formality", "")).title().replace("_", " "))
    c3.metric("Voice", config.get("voice", "").title())

    c1, c2, c3 = st.columns(3)
    c1.metric("Min. Kata", f"{config.get('min_word_count', '-')}")
    c2.metric("Maks. Kata", f"{config.get('max_word_count', '-')}")
    c3.metric("Penomoran", config.get("numbering_style", "-").title())

    with st.expander("Lihat Instruksi Kustom"):
        st.write(config.get("custom_instructions", "(Tidak ada instruksi khusus)"))


def _render_edit_form(selected_style: dict, edit_key: str):
    """Form edit inline untuk custom style."""
    st.markdown(
        mi("edit_note", 18) + " **Mode Edit Style**",
        unsafe_allow_html=True,
    )

    selected_id = selected_style["id"]
    config = selected_style.get("config", {})
    sections = selected_style.get("sections", [])

    with st.form(key=f"edit_form_{selected_id}"):
        # --- Metadata ---
        st.subheader("Informasi Umum")
        new_name = st.text_input("Nama Style", value=selected_style.get("name", ""))
        new_desc = st.text_area(
            "Deskripsi",
            value=selected_style.get("description", ""),
            height=80,
        )

        st.divider()

        # --- Config ---
        st.subheader("Gaya Penulisan")

        lang_options = ["id", "en"]
        formality_options = ["formal", "semi_formal", "informal"]
        voice_options = ["active", "passive"]
        perspective_options = ["first_person", "third_person"]
        numbering_options = ["numeric", "roman", "none"]

        col1, col2 = st.columns(2)
        with col1:
            new_language = st.selectbox(
                "Bahasa",
                lang_options,
                index=_safe_index(lang_options, config.get("language", "id")),
            )
            new_voice = st.selectbox(
                "Voice (Kalimat)",
                voice_options,
                index=_safe_index(voice_options, config.get("voice", "active")),
            )
            new_min_words = st.number_input(
                "Minimal Kata",
                value=int(config.get("min_word_count", 500)),
                min_value=100,
                step=50,
            )
        with col2:
            new_formality = st.selectbox(
                "Formalitas",
                formality_options,
                index=_safe_index(formality_options, config.get("formality", "formal")),
            )
            new_perspective = st.selectbox(
                "Perspektif",
                perspective_options,
                index=_safe_index(perspective_options, config.get("perspective", "third_person")),
            )
            new_max_words = st.number_input(
                "Maksimal Kata",
                value=int(config.get("max_word_count", 3000)),
                min_value=500,
                step=100,
            )

        new_numbering = st.selectbox(
            "Penomoran",
            numbering_options,
            index=_safe_index(numbering_options, config.get("numbering_style", "numeric")),
        )
        new_custom_instructions = st.text_area(
            "Instruksi Kustom AI",
            value=config.get("custom_instructions", ""),
            height=100,
        )

        st.divider()

        # --- Sections Edit ---
        st.subheader("Edit Seksi")
        st.caption("Ubah properti tiap seksi. Urutan seksi tidak bisa diubah dari sini.")

        format_hint_options = ["paragraphs", "bullet_points", "table", "mixed", ""]
        updated_sections = []

        for i, sec in enumerate(sections):
            with st.expander(f"Seksi {i+1}: {sec.get('title', '(tanpa judul)')}"):
                s_title = st.text_input(
                    "Judul Seksi", value=sec.get("title", ""), key=f"s_title_{i}"
                )
                s_desc = st.text_area(
                    "Instruksi untuk AI",
                    value=sec.get("description", ""),
                    key=f"s_desc_{i}",
                    height=80,
                )
                s_required = st.checkbox(
                    "Wajib Ada di Dokumen",
                    value=sec.get("required", True),
                    key=f"s_req_{i}",
                )
                s_format = st.selectbox(
                    "Format Hint",
                    format_hint_options,
                    index=_safe_index(format_hint_options, sec.get("format_hint", "") or ""),
                    key=f"s_fmt_{i}",
                )
                s_min_para = st.number_input(
                    "Min. Paragraf",
                    value=int(sec.get("min_paragraphs", 1)),
                    min_value=0,
                    step=1,
                    key=f"s_para_{i}",
                )
                updated_sections.append({
                    **sec,
                    "title": s_title,
                    "description": s_desc,
                    "required": s_required,
                    "format_hint": s_format,
                    "min_paragraphs": s_min_para,
                })

        submitted = st.form_submit_button("Simpan Perubahan", type="primary")

    if submitted:
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
                "min_word_count": int(new_min_words),
                "max_word_count": int(new_max_words),
                "numbering_style": new_numbering,
                "custom_instructions": new_custom_instructions,
            },
        }
        result = client.update_style(selected_id, updates)
        if "error" in result:
            notify(f"Gagal menyimpan: {result['error']}", "error")
        else:
            notify("Style berhasil disimpan!", "success")
            st.session_state[edit_key] = False
            st.rerun()


def _safe_index(options: list, value: str) -> int:
    """Kembalikan index dari value dalam list, atau 0 jika tidak ditemukan."""
    try:
        return options.index(value)
    except ValueError:
        return 0
