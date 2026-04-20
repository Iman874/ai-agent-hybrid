"""Simple runtime i18n helper for Streamlit UI (ID/EN)."""

from __future__ import annotations

from typing import Any

import streamlit as st

DEFAULT_LANGUAGE = "id"
SUPPORTED_LANGUAGES = ("id", "en")

TRANSLATIONS: dict[str, dict[str, str]] = {
    "id": {
        "common.default": "Default",
        "common.edit": "Edit",
        "header.title": "Generator TOR",
        "settings.dialog_title": "Pengaturan",
        "settings.nav.general": "Umum",
        "settings.nav.format_tor": "Format TOR",
        "settings.nav.advanced": "Lanjutan",
        "settings.section.appearance": "Penampilan",
        "settings.theme.label": "Tema",
        "settings.theme.system": "Default sistem",
        "settings.theme.dark": "Gelap",
        "settings.theme.light": "Terang",
        "settings.section.language": "Bahasa",
        "settings.language.label": "Bahasa",
        "settings.language.id": "Bahasa Indonesia",
        "settings.language.en": "English",
        "settings.section.format_tor": "Format TOR",
        "settings.section.advanced": "Pengaturan Lanjutan",
        "settings.advanced.caption": "Pengaturan teknis untuk developer.",
        "settings.advanced.api_endpoint": "API Endpoint",
        "settings.advanced.cache": "Cache",
        "settings.advanced.clear_cache": "Hapus Cache",
        "settings.cache_cleared": "Cache berhasil dihapus.",
        "sidebar.model_label": "Model AI",
        "sidebar.model_unavailable": "Model tidak tersedia",
        "sidebar.switch_model_warning": "Ganti model akan mereset sesi.",
        "sidebar.confirm_reset": "Konfirmasi Reset",
        "sidebar.new_chat": "Obrolan baru",
        "sidebar.history": "RIWAYAT",
        "sidebar.loading_session": "_Memuat sesi..._",
        "sidebar.empty_conversations": "Belum ada percakapan",
        "sidebar.empty_start_chat": "Mulai obrolan baru",
        "sidebar.session_prefix": "Sesi",
        "sidebar.load_failed": "Gagal memuat sesi.",
        "sidebar.delete_failed": "Gagal menghapus sesi.",
        "sidebar.view_all": "Lihat semua",
        "sidebar.dialog_title": "Riwayat Session",
        "sidebar.no_history": "Belum ada riwayat session.",
        "sidebar.current": "Aktif",
        "sidebar.open": "Buka",
        "sidebar.tools": "ALAT",
        "sidebar.tool.chat": "Obrolan",
        "sidebar.tool.generate_doc": "Generate Dokumen",
        "sidebar.settings": "Pengaturan",
        "sidebar.api_connected": "API Terhubung",
        "sidebar.api_disconnected": "API Terputus",
        "chat.input_placeholder": "Tanyakan apa saja...",
        "chat.empty_title": "Ceritakan kebutuhan TOR Anda",
        "chat.empty_desc": "Mulai chat untuk menyusun Term of Reference dengan bantuan AI secara interaktif.",
        "chat.processing_previous": "Permintaan sebelumnya masih diproses.",
        "chat.processing_spinner": "AI sedang memproses permintaan...",
        "chat.history_not_available": "Data session tidak tersedia.",
        "chat.back": "Kembali",
        "chat.back_to_active": "Kembali ke Obrolan Aktif",
        "chat.history_banner": "Arsip session: {title}. Status: {status} · {turns} Turn. Mode read-only, tidak bisa mengirim pesan baru.",
        "chat.history_empty": "_Session ini tidak memiliki riwayat chat._",
        "chat.history_prefix": "Session",
        "chat.fallback_caption": "Jika tombol export di atas error, gunakan fallback di bawah:",
        "chat.fallback_download_md": "Download .md (fallback)",
        "doc.history_view_info": "Anda sedang melihat arsip session. Kembali ke obrolan aktif untuk menggunakan fitur ini.",
        "doc.title": "Generate TOR dari Dokumen",
        "doc.subtitle": "Upload dokumen sumber, Gemini otomatis membuat TOR.",
        "doc.active_format_caption": "Format yang digunakan: **{active_name}** - ubah di Pengaturan > Format TOR",
        "doc.upload_label": "Upload dokumen",
        "doc.upload_help": "Format: PDF, TXT, MD, DOCX. Maks 20MB.",
        "doc.context_label": "Konteks tambahan (opsional)",
        "doc.context_placeholder": "Contoh: Ini lanjutan workshop tahun lalu...",
        "doc.generate_button": "Generate TOR",
        "doc.generate_again": "Generate Ulang",
        "doc.spinner": "Membaca dokumen dan generating TOR...",
        "format.title": "Konfigurasi Format TOR",
        "format.subtitle": "Pilih, buat, atau ekstrak gaya penulisan TOR yang akan digunakan oleh AI.",
        "format.loading": "Menunggu koneksi backend untuk memuat format...",
        "format.available": "Format yang Tersedia",
        "format.active_suffix": "(Aktif)",
        "format.set_active": "Jadikan Aktif",
        "format.set_active_success": "Format aktif berhasil diubah.",
        "format.set_active_failed": "Gagal mengubah format aktif.",
        "format.default_readonly": "Format bawaan sistem - read only, tidak bisa diedit.",
        "format.advanced": "Pengaturan Lanjutan",
        "format.edit_style": "Edit Style",
        "format.done_edit": "Selesai Edit",
        "format.clone": "Tiru (Klon)",
        "format.clone_name": "Nama Format Baru",
        "format.clone_default_name": "Salinan {name}",
        "format.clone_button": "Buat Salinan",
        "format.delete": "Hapus",
        "format.delete_help": "Hapus permanen",
        "format.delete_warning": "Tindakan ini tidak bisa dibatalkan.",
        "format.delete_active_block": "Ubah aktif style ke format lain sebelum menghapus!",
        "format.delete_confirm": "Ya, Hapus Sekarang",
        "format.extract_title": "Ekstrak Format dari Dokumen",
        "format.extract_caption": "Upload contoh dokumen TOR lalu AI menganalisis struktur dan gaya bahasa untuk disimpan sebagai style baru.",
        "format.extract_upload": "Upload Dokumen TOR Referensi",
        "format.extract_name": "Nama style baru (opsional)",
        "format.extract_placeholder": "AI akan memberi nama otomatis jika kosong",
        "format.extract_button": "Ekstrak dengan AI",
        "format.extract_spinner": "AI sedang menganalisis gaya bahasa dan struktur... (15-30 detik)",
        "format.extract_failed": "Gagal melakukan ekstraksi: {error}",
        "format.unexpected_error": "Terjadi kesalahan: {error}",
        "format.save_failed": "Gagal menyimpan: {error}",
        "format.extract_saved": "Style \"{name}\" berhasil diekstrak dan disimpan!",
        "format.sections_title": "Struktur Seksi",
        "format.required": "Wajib",
        "format.optional": "Opsional",
        "format.table_no": "No.",
        "format.table_section_name": "Nama Seksi",
        "format.table_type": "Tipe",
        "format.table_format": "Format",
        "format.table_min_paragraph": "Min. Paragraf",
        "format.writing_style": "Gaya Penulisan",
        "format.metric_language": "Bahasa",
        "format.metric_formality": "Formalitas",
        "format.metric_voice": "Voice",
        "format.metric_min_words": "Min. Kata",
        "format.metric_max_words": "Maks. Kata",
        "format.metric_numbering": "Penomoran",
        "format.custom_instruction_view": "Lihat Instruksi Kustom",
        "format.custom_instruction_empty": "(Tidak ada instruksi khusus)",
        "format.edit_mode": "Mode Edit Style",
        "format.general_info": "Informasi Umum",
        "format.style_name": "Nama Style",
        "format.description": "Deskripsi",
        "format.writing_subheader": "Gaya Penulisan",
        "format.language": "Bahasa",
        "format.voice_sentence": "Voice (Kalimat)",
        "format.min_words": "Minimal Kata",
        "format.formality": "Formalitas",
        "format.perspective": "Perspektif",
        "format.max_words": "Maksimal Kata",
        "format.numbering": "Penomoran",
        "format.custom_instruction": "Instruksi Kustom AI",
        "format.edit_sections": "Edit Seksi",
        "format.edit_sections_caption": "Ubah properti tiap seksi. Urutan seksi tidak bisa diubah dari sini.",
        "format.section_title": "Seksi {index}: {title}",
        "format.section_title_label": "Judul Seksi",
        "format.section_instruction": "Instruksi untuk AI",
        "format.section_required": "Wajib Ada di Dokumen",
        "format.section_format_hint": "Format Hint",
        "format.section_min_paragraph": "Min. Paragraf",
        "format.save_changes": "Simpan Perubahan",
        "format.save_success": "Style berhasil disimpan!",
    },
    "en": {
        "common.default": "Default",
        "common.edit": "Edit",
        "header.title": "TOR Generator",
        "settings.dialog_title": "Settings",
        "settings.nav.general": "General",
        "settings.nav.format_tor": "TOR Format",
        "settings.nav.advanced": "Advanced",
        "settings.section.appearance": "Appearance",
        "settings.theme.label": "Theme",
        "settings.theme.system": "System default",
        "settings.theme.dark": "Dark",
        "settings.theme.light": "Light",
        "settings.section.language": "Language",
        "settings.language.label": "Language",
        "settings.language.id": "Bahasa Indonesia",
        "settings.language.en": "English",
        "settings.section.format_tor": "TOR Format",
        "settings.section.advanced": "Advanced Settings",
        "settings.advanced.caption": "Technical settings for developers.",
        "settings.advanced.api_endpoint": "API Endpoint",
        "settings.advanced.cache": "Cache",
        "settings.advanced.clear_cache": "Clear Cache",
        "settings.cache_cleared": "Cache cleared successfully.",
        "sidebar.model_label": "AI Model",
        "sidebar.model_unavailable": "Model not available",
        "sidebar.switch_model_warning": "Changing model will reset the session.",
        "sidebar.confirm_reset": "Confirm Reset",
        "sidebar.new_chat": "New chat",
        "sidebar.history": "HISTORY",
        "sidebar.loading_session": "_Loading session..._",
        "sidebar.empty_conversations": "No conversations yet",
        "sidebar.empty_start_chat": "Start a new chat",
        "sidebar.session_prefix": "Session",
        "sidebar.load_failed": "Failed to load session.",
        "sidebar.delete_failed": "Failed to delete session.",
        "sidebar.view_all": "View all",
        "sidebar.dialog_title": "Session History",
        "sidebar.no_history": "No session history yet.",
        "sidebar.current": "Current",
        "sidebar.open": "Open",
        "sidebar.tools": "TOOLS",
        "sidebar.tool.chat": "Chat",
        "sidebar.tool.generate_doc": "Generate Document",
        "sidebar.settings": "Settings",
        "sidebar.api_connected": "API Connected",
        "sidebar.api_disconnected": "API Disconnected",
        "chat.input_placeholder": "Ask anything...",
        "chat.empty_title": "Describe your TOR requirements",
        "chat.empty_desc": "Start a chat to build Terms of Reference interactively with AI.",
        "chat.processing_previous": "The previous request is still being processed.",
        "chat.processing_spinner": "AI is processing your request...",
        "chat.history_not_available": "Session data is unavailable.",
        "chat.back": "Back",
        "chat.back_to_active": "Back to Active Chat",
        "chat.history_banner": "Session archive: {title}. Status: {status} · {turns} turns. Read-only mode, you cannot send new messages.",
        "chat.history_empty": "_This session has no chat history._",
        "chat.history_prefix": "Session",
        "chat.fallback_caption": "If export buttons above fail, use the fallback below:",
        "chat.fallback_download_md": "Download .md (fallback)",
        "doc.history_view_info": "You are viewing a session archive. Return to active chat to use this feature.",
        "doc.title": "Generate TOR from Document",
        "doc.subtitle": "Upload a source document and Gemini will generate a TOR.",
        "doc.active_format_caption": "Current format: **{active_name}** - change in Settings > TOR Format",
        "doc.upload_label": "Upload document",
        "doc.upload_help": "Formats: PDF, TXT, MD, DOCX. Max 20MB.",
        "doc.context_label": "Additional context (optional)",
        "doc.context_placeholder": "Example: This is a continuation of last year's workshop...",
        "doc.generate_button": "Generate TOR",
        "doc.generate_again": "Generate Again",
        "doc.spinner": "Reading document and generating TOR...",
        "format.title": "TOR Format Configuration",
        "format.subtitle": "Choose, create, or extract TOR writing styles used by AI.",
        "format.loading": "Waiting for backend connection to load formats...",
        "format.available": "Available Formats",
        "format.active_suffix": "(Active)",
        "format.set_active": "Set Active",
        "format.set_active_success": "Active format updated successfully.",
        "format.set_active_failed": "Failed to update active format.",
        "format.default_readonly": "System default format - read-only, cannot be edited.",
        "format.advanced": "Advanced Settings",
        "format.edit_style": "Edit Style",
        "format.done_edit": "Finish Editing",
        "format.clone": "Clone",
        "format.clone_name": "New Format Name",
        "format.clone_default_name": "Copy of {name}",
        "format.clone_button": "Create Copy",
        "format.delete": "Delete",
        "format.delete_help": "Delete permanently",
        "format.delete_warning": "This action cannot be undone.",
        "format.delete_active_block": "Switch active style before deleting this one!",
        "format.delete_confirm": "Yes, Delete Now",
        "format.extract_title": "Extract Format from Document",
        "format.extract_caption": "Upload a TOR sample and AI will analyze structure and writing style to save as a new style.",
        "format.extract_upload": "Upload TOR Reference Document",
        "format.extract_name": "New style name (optional)",
        "format.extract_placeholder": "AI will auto-name if left empty",
        "format.extract_button": "Extract with AI",
        "format.extract_spinner": "AI is analyzing writing style and structure... (15-30 seconds)",
        "format.extract_failed": "Failed to extract: {error}",
        "format.unexpected_error": "An unexpected error occurred: {error}",
        "format.save_failed": "Failed to save: {error}",
        "format.extract_saved": "Style \"{name}\" extracted and saved successfully!",
        "format.sections_title": "Section Structure",
        "format.required": "Required",
        "format.optional": "Optional",
        "format.table_no": "No.",
        "format.table_section_name": "Section Name",
        "format.table_type": "Type",
        "format.table_format": "Format",
        "format.table_min_paragraph": "Min. Paragraph",
        "format.writing_style": "Writing Style",
        "format.metric_language": "Language",
        "format.metric_formality": "Formality",
        "format.metric_voice": "Voice",
        "format.metric_min_words": "Min Words",
        "format.metric_max_words": "Max Words",
        "format.metric_numbering": "Numbering",
        "format.custom_instruction_view": "View Custom Instructions",
        "format.custom_instruction_empty": "(No custom instructions)",
        "format.edit_mode": "Edit Style Mode",
        "format.general_info": "General Information",
        "format.style_name": "Style Name",
        "format.description": "Description",
        "format.writing_subheader": "Writing Style",
        "format.language": "Language",
        "format.voice_sentence": "Voice (Sentence)",
        "format.min_words": "Minimum Words",
        "format.formality": "Formality",
        "format.perspective": "Perspective",
        "format.max_words": "Maximum Words",
        "format.numbering": "Numbering",
        "format.custom_instruction": "Custom AI Instructions",
        "format.edit_sections": "Edit Sections",
        "format.edit_sections_caption": "Update each section properties. Section ordering cannot be changed here.",
        "format.section_title": "Section {index}: {title}",
        "format.section_title_label": "Section Title",
        "format.section_instruction": "Instructions for AI",
        "format.section_required": "Required in Document",
        "format.section_format_hint": "Format Hint",
        "format.section_min_paragraph": "Min. Paragraph",
        "format.save_changes": "Save Changes",
        "format.save_success": "Style saved successfully!",
    },
}


def _safe_get_session_state() -> Any:
    """Get Streamlit session_state safely for non-runtime contexts (tests/import)."""
    try:
        return st.session_state
    except Exception:
        return {}


def get_language() -> str:
    """Return active app language with safe fallback."""
    state = _safe_get_session_state()
    try:
        language = state.get("app_language", DEFAULT_LANGUAGE)
    except Exception:
        language = DEFAULT_LANGUAGE

    if language not in SUPPORTED_LANGUAGES:
        return DEFAULT_LANGUAGE
    return language


def set_language(language: str) -> str:
    """Persist selected language to session state and return normalized value."""
    normalized = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE

    try:
        st.session_state.app_language = normalized
    except Exception:
        try:
            st.session_state["app_language"] = normalized
        except Exception:
            pass

    return normalized


def tr(key: str, default: str | None = None, **kwargs: Any) -> str:
    """Translate key by active language with fallback: selected -> id -> default/key."""
    lang = get_language()
    text = TRANSLATIONS.get(lang, {}).get(key)

    if text is None:
        text = TRANSLATIONS.get(DEFAULT_LANGUAGE, {}).get(key)

    if text is None:
        text = default if default is not None else key

    if kwargs:
        try:
            return str(text).format(**kwargs)
        except Exception:
            return str(text)

    return str(text)
