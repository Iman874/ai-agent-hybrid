import streamlit as st
import pandas as pd
from time import perf_counter

from api import client
from utils.icons import mi
from utils.i18n import tr
from utils.notify import notify
from state import begin_ui_action, end_ui_action, next_ui_action_id, record_perf_sample


def _rerun_if_changed(changed: bool) -> None:
    """Rerun hanya saat ada perubahan state/data.

    Prioritaskan rerun fragment agar dialog settings tidak tertutup.
    Fallback ke rerun global untuk kompatibilitas lintas versi/komponen.
    """
    if not changed:
        return

    try:
        st.rerun(scope="fragment")
    except TypeError:
        st.rerun()
    except Exception:
        st.rerun()


def render_format_tab():
    """Render tab konfigurasi format TOR."""
    render_format_settings(show_header=True)


def render_format_settings(show_header: bool = True):
    """Render pengaturan format TOR (tab/dialog)."""
    if show_header:
        st.markdown(
            mi("palette", 22) + f" **{tr('format.title', 'Konfigurasi Format TOR')}**",
            unsafe_allow_html=True,
        )
        st.markdown(tr("format.subtitle", "Pilih, buat, atau ekstrak gaya penulisan TOR yang akan digunakan oleh AI."))

    styles = client.get_styles()
    if not styles:
        st.caption(tr("format.loading", "Menunggu koneksi backend untuk memuat format..."))
        return

    if len(styles) == 0:
        return

    # --- Style Selector ---
    active_style_id = next((s["id"] for s in styles if s.get("is_active")), None)

    active_suffix = tr("format.active_suffix", "(Aktif)")
    options = {
        s["id"]: f"{s['name']} {active_suffix}" if s.get("is_active") else s["name"]
        for s in styles
    }

    col1, col2 = st.columns([3, 1])
    with col1:
        index = list(options.keys()).index(active_style_id) if active_style_id in options else 0
        selected_id = st.selectbox(
            tr("format.available", "Format yang Tersedia"),
            options=list(options.keys()),
            format_func=lambda x: options[x],
            index=index,
        )
    with col2:
        st.write("")
        st.write("")
        if selected_id != active_style_id:
            if st.button(tr("format.set_active", "Jadikan Aktif"), type="primary", use_container_width=True):
                action_id = next_ui_action_id(f"style:activate:{selected_id}")
                if begin_ui_action(action_id):
                    t0 = perf_counter()
                    try:
                        changed = client.set_active_style(selected_id)
                    finally:
                        end_ui_action(action_id)
                        record_perf_sample("style_activate", (perf_counter() - t0) * 1000)

                    if changed:
                        notify(tr("format.set_active_success", "Format aktif berhasil diubah."), "success")
                    else:
                        notify(tr("format.set_active_failed", "Gagal mengubah format aktif."), "error")
                    _rerun_if_changed(changed)

    st.divider()

    selected_style = next((s for s in styles if s["id"] == selected_id), None)
    if not selected_style:
        return

    is_default = _is_default_style(selected_style)

    # --- Header Style Detail ---
    st.markdown(
        mi("description", 18) + f" **{selected_style['name']}**",
        unsafe_allow_html=True,
    )
    if is_default:
        st.caption(tr("format.default_readonly", "Format bawaan sistem - read only, tidak bisa diedit."))
    else:
        st.caption(selected_style.get("description", ""))

    edit_key = f"edit_mode_{selected_id}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    st.divider()
    _render_readonly_view(selected_style)

    st.divider()
    _render_style_actions(selected_style, edit_key)

    if not is_default and st.session_state.get(edit_key):
        _render_edit_form(selected_style, edit_key)

    with st.expander(
        tr("format.advanced", "Pengaturan Lanjutan"),
        expanded=False,
    ):
        _render_extraction_section()


def _render_style_actions(selected_style: dict, edit_key: str) -> None:
    """Render action row: edit, clone, delete."""
    is_default = _is_default_style(selected_style)
    action_cols = st.columns([1, 1, 1, 3])

    with action_cols[0]:
        if not is_default:
            edit_label = (
                tr("format.done_edit", "Selesai Edit")
                if st.session_state[edit_key]
                else tr("format.edit_style", "Edit Style")
            )
            if st.button(edit_label, use_container_width=True):
                action_id = next_ui_action_id(f"style:toggle_edit:{selected_style['id']}")
                if begin_ui_action(action_id):
                    try:
                        st.session_state[edit_key] = not st.session_state[edit_key]
                    finally:
                        end_ui_action(action_id)
                    _rerun_if_changed(True)

    with action_cols[1]:
        with st.popover(tr("format.clone", "Tiru (Klon)")):
            new_name = st.text_input(
                tr("format.clone_name", "Nama Format Baru"),
                value=tr("format.clone_default_name", "Salinan {name}", name=selected_style["name"]),
                key="clone_name",
            )
            if st.button(tr("format.clone_button", "Buat Salinan"), key="btn_clone"):
                action_id = next_ui_action_id(f"style:clone:{selected_style['id']}")
                if begin_ui_action(action_id):
                    t0 = perf_counter()
                    try:
                        with st.spinner():
                            res = client.duplicate_style(selected_style["id"], new_name)
                            if "error" in res:
                                notify(res["error"], "error", method="inline")
                                changed = False
                            else:
                                changed = True
                    finally:
                        end_ui_action(action_id)
                        record_perf_sample("style_clone", (perf_counter() - t0) * 1000)
                    _rerun_if_changed(changed)

    with action_cols[2]:
        if not is_default:
            with st.popover(tr("format.delete", "Hapus"), help=tr("format.delete_help", "Hapus permanen")):
                notify(tr("format.delete_warning", "Tindakan ini tidak bisa dibatalkan."), "warning", method="inline")
                if selected_style.get("is_active"):
                    notify(
                        tr("format.delete_active_block", "Ubah aktif style ke format lain sebelum menghapus!"),
                        "error",
                        method="inline",
                    )
                else:
                    if st.button(tr("format.delete_confirm", "Ya, Hapus Sekarang"), type="primary", key="btn_delete"):
                        action_id = next_ui_action_id(f"style:delete:{selected_style['id']}")
                        if begin_ui_action(action_id):
                            t0 = perf_counter()
                            try:
                                res = client.delete_style(selected_style["id"])
                                if "error" in res:
                                    notify(res["error"], "error", method="inline")
                                    changed = False
                                else:
                                    changed = True
                            finally:
                                end_ui_action(action_id)
                                record_perf_sample("style_delete", (perf_counter() - t0) * 1000)
                            _rerun_if_changed(changed)


def _render_extraction_section() -> None:
    """Render extraction section for creating new style from document."""
    st.markdown(
        mi("auto_awesome", 18) + f" **{tr('format.extract_title', 'Ekstrak Format dari Dokumen')}**",
        unsafe_allow_html=True,
    )
    st.caption(tr("format.extract_caption", "Upload contoh dokumen TOR lalu AI menganalisis struktur dan gaya bahasa untuk disimpan sebagai style baru."))

    uploaded_file = st.file_uploader(
        tr("format.extract_upload", "Upload Dokumen TOR Referensi"),
        type=["pdf", "docx", "md", "txt"],
        key="format_extractor_uploader",
    )
    extract_name = st.text_input(
        tr("format.extract_name", "Nama style baru (opsional)"),
        placeholder=tr("format.extract_placeholder", "AI akan memberi nama otomatis jika kosong"),
        key="extract_style_name",
    )
    if uploaded_file:
        if st.button(tr("format.extract_button", "Ekstrak dengan AI"), type="primary"):
            action_id = next_ui_action_id("style:extract")
            if begin_ui_action(action_id):
                t0 = perf_counter()
                changed = False
                try:
                    with st.spinner(tr("format.extract_spinner", "AI sedang menganalisis gaya bahasa dan struktur... (15-30 detik)")):
                        file_bytes = uploaded_file.read()
                        res = client.extract_style(file_bytes, uploaded_file.name)
                        if "error" in res:
                            notify(
                                tr("format.extract_failed", "Gagal melakukan ekstraksi: {error}", error=res["error"]),
                                "error",
                                method="banner",
                            )
                        else:
                            if extract_name.strip():
                                res["name"] = extract_name.strip()

                            save_res = client.create_style(res)
                            if "error" in save_res:
                                notify(
                                    tr("format.save_failed", "Gagal menyimpan: {error}", error=save_res["error"]),
                                    "error",
                                    method="banner",
                                )
                            else:
                                notify(
                                    tr(
                                        "format.extract_saved",
                                        "Style \"{name}\" berhasil diekstrak dan disimpan!",
                                        name=save_res.get("name", res.get("name")),
                                    ),
                                    "success",
                                )
                                changed = True
                except Exception as e:
                    notify(
                        tr("format.unexpected_error", "Terjadi kesalahan: {error}", error=e),
                        "error",
                        method="banner",
                    )
                finally:
                    end_ui_action(action_id)
                    record_perf_sample("style_extract", (perf_counter() - t0) * 1000)
                _rerun_if_changed(changed)


def _render_readonly_view(selected_style: dict):
    """Tampilkan detail style dalam mode read-only."""
    st.markdown(
        mi("format_list_bulleted", 18) + f" **{tr('format.sections_title', 'Struktur Seksi')}**",
        unsafe_allow_html=True,
    )
    sections = selected_style.get("sections", [])
    if sections:
        items = []
        for i, section in enumerate(sections, 1):
            req = tr("format.required", "Wajib") if section.get("required") else tr("format.optional", "Opsional")
            items.append({
                tr("format.table_no", "No."): i,
                tr("format.table_section_name", "Nama Seksi"): section.get("title"),
                tr("format.table_type", "Tipe"): req,
                tr("format.table_format", "Format"): section.get("format_hint", "-"),
                tr("format.table_min_paragraph", "Min. Paragraf"): section.get("min_paragraphs", 1),
            })
        st.dataframe(pd.DataFrame(items), hide_index=True, use_container_width=True)

    st.markdown(
        mi("tune", 18) + f" **{tr('format.writing_style', 'Gaya Penulisan')}**",
        unsafe_allow_html=True,
    )
    config = selected_style.get("config", {})
    c1, c2, c3 = st.columns(3)
    c1.metric(tr("format.metric_language", "Bahasa"), config.get("language", "id").upper())
    c2.metric(tr("format.metric_formality", "Formalitas"), str(config.get("formality", "")).title().replace("_", " "))
    c3.metric(tr("format.metric_voice", "Voice"), config.get("voice", "").title())

    c1, c2, c3 = st.columns(3)
    c1.metric(tr("format.metric_min_words", "Min. Kata"), f"{config.get('min_word_count', '-')}")
    c2.metric(tr("format.metric_max_words", "Maks. Kata"), f"{config.get('max_word_count', '-')}")
    c3.metric(tr("format.metric_numbering", "Penomoran"), config.get("numbering_style", "-").title())

    with st.expander(tr("format.custom_instruction_view", "Lihat Instruksi Kustom")):
        st.write(config.get("custom_instructions", tr("format.custom_instruction_empty", "(Tidak ada instruksi khusus)")))


def _render_edit_form(selected_style: dict, edit_key: str):
    """Form edit inline untuk custom style."""
    st.markdown(
        mi("edit_note", 18) + f" **{tr('format.edit_mode', 'Mode Edit Style')}**",
        unsafe_allow_html=True,
    )

    selected_id = selected_style["id"]
    config = selected_style.get("config", {})
    sections = selected_style.get("sections", [])

    with st.form(key=f"edit_form_{selected_id}"):
        # --- Metadata ---
        st.subheader(tr("format.general_info", "Informasi Umum"))
        new_name = st.text_input(tr("format.style_name", "Nama Style"), value=selected_style.get("name", ""))
        new_desc = st.text_area(
            tr("format.description", "Deskripsi"),
            value=selected_style.get("description", ""),
            height=80,
        )

        st.divider()

        # --- Config ---
        st.subheader(tr("format.writing_subheader", "Gaya Penulisan"))

        lang_options = ["id", "en"]
        formality_options = ["formal", "semi_formal", "informal"]
        voice_options = ["active", "passive"]
        perspective_options = ["first_person", "third_person"]
        numbering_options = ["numeric", "roman", "none"]

        col1, col2 = st.columns(2)
        with col1:
            new_language = st.selectbox(
                tr("format.language", "Bahasa"),
                lang_options,
                index=_safe_index(lang_options, config.get("language", "id")),
            )
            new_voice = st.selectbox(
                tr("format.voice_sentence", "Voice (Kalimat)"),
                voice_options,
                index=_safe_index(voice_options, config.get("voice", "active")),
            )
            new_min_words = st.number_input(
                tr("format.min_words", "Minimal Kata"),
                value=int(config.get("min_word_count", 500)),
                min_value=100,
                step=50,
            )
        with col2:
            new_formality = st.selectbox(
                tr("format.formality", "Formalitas"),
                formality_options,
                index=_safe_index(formality_options, config.get("formality", "formal")),
            )
            new_perspective = st.selectbox(
                tr("format.perspective", "Perspektif"),
                perspective_options,
                index=_safe_index(perspective_options, config.get("perspective", "third_person")),
            )
            new_max_words = st.number_input(
                tr("format.max_words", "Maksimal Kata"),
                value=int(config.get("max_word_count", 3000)),
                min_value=500,
                step=100,
            )

        new_numbering = st.selectbox(
            tr("format.numbering", "Penomoran"),
            numbering_options,
            index=_safe_index(numbering_options, config.get("numbering_style", "numeric")),
        )
        new_custom_instructions = st.text_area(
            tr("format.custom_instruction", "Instruksi Kustom AI"),
            value=config.get("custom_instructions", ""),
            height=100,
        )

        st.divider()

        # --- Sections Edit ---
        st.subheader(tr("format.edit_sections", "Edit Seksi"))
        st.caption(tr("format.edit_sections_caption", "Ubah properti tiap seksi. Urutan seksi tidak bisa diubah dari sini."))

        format_hint_options = ["paragraphs", "bullet_points", "table", "mixed", ""]
        updated_sections = []

        for i, sec in enumerate(sections):
            section_title = sec.get("title", "(tanpa judul)")
            with st.expander(
                tr(
                    "format.section_title",
                    "Seksi {index}: {title}",
                    index=i + 1,
                    title=section_title,
                )
            ):
                s_title = st.text_input(
                    tr("format.section_title_label", "Judul Seksi"), value=sec.get("title", ""), key=f"s_title_{i}"
                )
                s_desc = st.text_area(
                    tr("format.section_instruction", "Instruksi untuk AI"),
                    value=sec.get("description", ""),
                    key=f"s_desc_{i}",
                    height=80,
                )
                s_required = st.checkbox(
                    tr("format.section_required", "Wajib Ada di Dokumen"),
                    value=sec.get("required", True),
                    key=f"s_req_{i}",
                )
                s_format = st.selectbox(
                    tr("format.section_format_hint", "Format Hint"),
                    format_hint_options,
                    index=_safe_index(format_hint_options, sec.get("format_hint", "") or ""),
                    key=f"s_fmt_{i}",
                )
                s_min_para = st.number_input(
                    tr("format.section_min_paragraph", "Min. Paragraf"),
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

        submitted = st.form_submit_button(tr("format.save_changes", "Simpan Perubahan"), type="primary")

    if submitted:
        action_id = next_ui_action_id(f"style:update:{selected_id}")
        if begin_ui_action(action_id):
            t0 = perf_counter()
            try:
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
                    notify(tr("format.save_failed", "Gagal menyimpan: {error}", error=result["error"]), "error")
                    changed = False
                else:
                    notify(tr("format.save_success", "Style berhasil disimpan!"), "success")
                    st.session_state[edit_key] = False
                    changed = True
            finally:
                end_ui_action(action_id)
                record_perf_sample("style_update", (perf_counter() - t0) * 1000)
            _rerun_if_changed(changed)


def _safe_index(options: list, value: str) -> int:
    """Kembalikan index dari value dalam list, atau 0 jika tidak ditemukan."""
    try:
        return options.index(value)
    except ValueError:
        return 0


def _is_default_style(style: dict) -> bool:
    """Normalisasi nilai is_default agar hanya style bawaan yang read-only."""
    raw_value = style.get("is_default", False)
    if isinstance(raw_value, str):
        return raw_value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(raw_value)
