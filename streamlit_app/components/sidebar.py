"""Sidebar UI - ChatGPT-style layout for tools and sessions."""

from __future__ import annotations

from typing import Any
from time import perf_counter

import streamlit as st
from utils.icons import mi
from utils.i18n import tr
from utils.notify import notify
from state import (
    reset_session,
    load_history_session,
    back_to_active,
    begin_ui_action,
    end_ui_action,
    next_ui_action_id,
    record_perf_sample,
)
from api.client import (
    check_health,
    fetch_models,
    fetch_session_list,
    fetch_session_detail,
    delete_session,
    invalidate_session_cache,
)
from components.settings_dialog import show_settings_dialog


def _has_state_changed(old_value: Any, new_value: Any) -> bool:
    """Helper kecil untuk konsisten cek perubahan state."""
    return old_value != new_value


def _safe_rerun_if_changed(changed: bool, scope: str | None = None) -> None:
    """Rerun hanya jika state berubah, dengan fallback global rerun."""
    if not changed:
        return
    if scope:
        try:
            st.rerun(scope=scope)
            return
        except TypeError:
            pass
        except Exception:
            pass
    st.rerun()


def render_sidebar() -> None:
    """Render seluruh konten sidebar dengan layout baru."""
    with st.sidebar:
        _render_model_selector()
        _render_new_chat()
        st.markdown("---")
        _render_session_list()
        st.markdown("---")
        _render_tools()
        _render_bottom()


def _render_model_selector() -> None:
    """Model selector dengan label nama dan provider."""
    models = fetch_models()
    options: list[dict] = []

    for model in models:
        if model.get("status") != "available":
            continue
        model_id = model.get("id", "")
        if "embed" in model_id.lower() or "nomic" in model_id.lower():
            continue
        provider = "Ollama" if model.get("type") == "local" else "Gemini"
        options.append({
            "id": model_id,
            "type": model.get("type"),
            "label": f"{model_id} · {provider}",
        })

    if not options:
        st.markdown(
            f"<small style='color:var(--color-text-subtle)'>"
            f"{mi('warning', 14, 'var(--color-warning)')} {tr('sidebar.model_unavailable', 'Model tidak tersedia')}</small>",
            unsafe_allow_html=True,
        )
        return

    labels = [opt["label"] for opt in options]

    current_id = st.session_state.get("active_model_id")
    current_idx = 0
    if current_id:
        match = next((i for i, opt in enumerate(options) if opt["id"] == current_id), None)
        current_idx = match if match is not None else 0

    selected_idx = st.selectbox(
        tr("sidebar.model_label", "Model AI"),
        range(len(labels)),
        format_func=lambda i: labels[i],
        index=current_idx,
        label_visibility="collapsed",
        key="model_selector",
    )

    if selected_idx >= len(options):
        selected_idx = 0

    selected = options[selected_idx]

    old_model_id = st.session_state.get("active_model_id")
    if _has_state_changed(old_model_id, selected["id"]):
        new_mode = "local" if selected["type"] == "local" else "gemini"
        if st.session_state.session_id and st.session_state.messages:
            notify(tr("sidebar.switch_model_warning", "Ganti model akan mereset sesi."), "warning", method="inline")
            if st.button(tr("sidebar.confirm_reset", "Konfirmasi Reset"), key="model_reset", use_container_width=True):
                action_id = next_ui_action_id("sidebar:model_reset")
                if begin_ui_action(action_id):
                    t0 = perf_counter()
                    try:
                        st.session_state.active_model_id = selected["id"]
                        st.session_state.chat_mode = new_mode
                        reset_session()
                    finally:
                        end_ui_action(action_id)
                        record_perf_sample("model_reset", (perf_counter() - t0) * 1000)
                    _safe_rerun_if_changed(True)
        else:
            st.session_state.active_model_id = selected["id"]
            st.session_state.chat_mode = new_mode


def _render_new_chat() -> None:
    """Tombol obrolan baru."""
    if st.button(
        tr("sidebar.new_chat", "Obrolan baru"),
        icon=":material/add:",
        use_container_width=True,
        type="primary",
        key="new_chat",
    ):
        action_id = next_ui_action_id("sidebar:new_chat")
        if begin_ui_action(action_id):
            t0 = perf_counter()
            changed = bool(
                st.session_state.session_id
                or st.session_state.messages
                or st.session_state.tor_document
                or st.session_state.direct_tor
                or st.session_state.doc_tor
                or st.session_state.escalation_info
                or st.session_state.is_viewing_history
                or st.session_state.history_session
                or st.session_state.active_tool != "chat"
            )
            try:
                reset_session()
            finally:
                end_ui_action(action_id)
                record_perf_sample("session_reset", (perf_counter() - t0) * 1000)
            _safe_rerun_if_changed(changed)


def _render_session_list() -> None:
    """Riwayat sesi dalam bentuk button list (anti-flicker)."""
    st.caption(tr("sidebar.history", "RIWAYAT"))

    loading = st.session_state.get("_loading_session_id")
    if loading:
        st.caption(tr("sidebar.loading_session", "_Memuat sesi..._"))
        return

    sessions = fetch_session_list(limit=4)

    if not sessions:
        st.markdown(
            "<div style='text-align:center;padding:16px 0;color:var(--color-text-subtle)'>"
            f"{mi('forum', 32, 'var(--color-text-subtle)')}<br>"
            f"<small>{tr('sidebar.empty_conversations', 'Belum ada percakapan')}<br>{tr('sidebar.empty_start_chat', 'Mulai obrolan baru')}</small>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    for session in sessions:
        title = session.get("title") or f"{tr('sidebar.session_prefix', 'Sesi')} {session['id'][:8]}"
        if len(title) > 32:
            title = title[:32] + "..."

        is_active = (
            session["id"] == st.session_state.session_id
            and not st.session_state.is_viewing_history
        )
        is_viewing = (
            st.session_state.is_viewing_history
            and st.session_state.history_session
            and st.session_state.history_session.get("id") == session["id"]
        )

        col_title, col_del = st.columns([5, 1])

        with col_title:
            if st.button(
                title,
                key=f"s_{session['id']}",
                use_container_width=True,
                type="primary" if (is_active or is_viewing) else "secondary",
                disabled=is_active,
            ):
                action_id = next_ui_action_id(f"sidebar:open_session:{session['id']}")
                if begin_ui_action(action_id):
                    t0 = perf_counter()
                    changed = False
                    try:
                        st.session_state._loading_session_id = session["id"]

                        if is_viewing:
                            back_to_active()
                            changed = True
                        else:
                            detail = fetch_session_detail(session["id"])
                            if detail:
                                load_history_session(detail)
                                changed = True
                            else:
                                notify(tr("sidebar.load_failed", "Gagal memuat sesi."), "error", method="inline")
                    finally:
                        st.session_state._loading_session_id = None
                        end_ui_action(action_id)
                        record_perf_sample("session_open", (perf_counter() - t0) * 1000)
                    _safe_rerun_if_changed(changed)

        with col_del:
            if not is_active:
                if st.button(
                    "",
                    icon=":material/close:",
                    key=f"del_{session['id']}",
                ):
                    action_id = next_ui_action_id(f"sidebar:delete_session:{session['id']}")
                    if begin_ui_action(action_id):
                        t0 = perf_counter()
                        changed = False
                        try:
                            if delete_session(session["id"]):
                                if is_viewing:
                                    back_to_active()
                                invalidate_session_cache()
                                changed = True
                            else:
                                notify(tr("sidebar.delete_failed", "Gagal menghapus sesi."), "error", method="inline")
                        finally:
                            end_ui_action(action_id)
                            record_perf_sample("session_delete", (perf_counter() - t0) * 1000)
                        _safe_rerun_if_changed(changed)

    if len(sessions) >= 4:
        if st.button(
            tr("sidebar.view_all", "Lihat semua"),
            icon=":material/arrow_forward:",
            key="all_sessions",
            use_container_width=True,
        ):
            show_all_sessions_dialog()


@st.dialog("Session History / Riwayat Session", width="large")
def show_all_sessions_dialog() -> None:
    """Modal dialog menampilkan semua sesi."""
    sessions = fetch_session_list(limit=50)

    if not sessions:
        notify(tr("sidebar.no_history", "Belum ada riwayat session."), "info", method="inline")
        return

    state_icons = {
        "COMPLETED": ("check_circle", "var(--color-success)"),
        "CHATTING": ("hourglass_empty", "var(--color-warning)"),
        "NEW": ("hourglass_empty", "var(--color-text-muted)"),
        "ESCALATED": ("bolt", "var(--color-accent)"),
    }

    for session in sessions:
        icon_name, icon_color = state_icons.get(
            session["state"], ("description", "var(--color-text-muted)")
        )
        state_icon = mi(icon_name, 18, icon_color, filled=True)

        title = session.get("title") or f"{tr('sidebar.session_prefix', 'Sesi')} {session['id'][:8]}"
        date = session["updated_at"][:10] if session.get("updated_at") else "-"

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{state_icon} {title}**", unsafe_allow_html=True)
            st.markdown(
                f"<small>{session['turn_count']} Turn - {session['state']} - {date}</small>",
                unsafe_allow_html=True,
            )
        with col2:
            is_current = session["id"] == st.session_state.session_id
            btn_label = tr("sidebar.current", "Aktif") if is_current else tr("sidebar.open", "Buka")
            btn_disabled = is_current and not st.session_state.is_viewing_history

            if st.button(
                btn_label,
                key=f"modal_open_{session['id']}",
                use_container_width=True,
                disabled=btn_disabled,
            ):
                action_id = next_ui_action_id(f"sidebar:modal_open:{session['id']}")
                if begin_ui_action(action_id):
                    t0 = perf_counter()
                    changed = False
                    try:
                        if is_current:
                            if st.session_state.is_viewing_history:
                                back_to_active()
                                changed = True
                        else:
                            detail = fetch_session_detail(session["id"])
                            if detail:
                                load_history_session(detail)
                                changed = True
                            else:
                                notify(tr("sidebar.load_failed", "Gagal memuat sesi."), "error", method="inline")
                    finally:
                        end_ui_action(action_id)
                        record_perf_sample("session_open", (perf_counter() - t0) * 1000)
                    _safe_rerun_if_changed(changed)

        st.divider()


def _render_tools() -> None:
    """Tools radio untuk memilih area kerja."""
    st.caption(tr("sidebar.tools", "ALAT"))

    tool_labels = {
        "chat": tr("sidebar.tool.chat", "Obrolan"),
        "generate_doc": tr("sidebar.tool.generate_doc", "Generate Dokumen"),
    }
    current = st.session_state.get("active_tool", "chat")
    keys = list(tool_labels.keys())

    selected = st.radio(
        tr("sidebar.tools", "ALAT"),
        keys,
        format_func=lambda k: tool_labels[k],
        index=keys.index(current) if current in keys else 0,
        label_visibility="collapsed",
        key="tool_radio",
    )

    if _has_state_changed(current, selected):
        action_id = next_ui_action_id("sidebar:tool_switch")
        if begin_ui_action(action_id):
            try:
                st.session_state.active_tool = selected
            finally:
                end_ui_action(action_id)
            _safe_rerun_if_changed(True)


def _render_bottom() -> None:
    """Section bawah: tombol pengaturan dan status API."""
    st.markdown("---")
    if st.button(
        tr("sidebar.settings", "Pengaturan"),
        icon=":material/settings:",
        use_container_width=True,
        key="btn_settings",
    ):
        show_settings_dialog()

    health = check_health()
    ok = health.get("status") == "healthy"
    dot = mi("circle", 6, "var(--color-success)" if ok else "var(--color-error)", filled=True)
    label = tr("sidebar.api_connected", "API Terhubung") if ok else tr("sidebar.api_disconnected", "API Terputus")
    sid = f" · {st.session_state.session_id[:8]}" if st.session_state.session_id else ""

    st.markdown(
        f"<small style='color:var(--color-text-subtle)'>{dot} {label}{sid}</small>",
        unsafe_allow_html=True,
    )
