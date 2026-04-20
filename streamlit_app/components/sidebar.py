# streamlit_app/components/sidebar.py
"""Sidebar UI — brand, model selector, progress, fields, system status."""

import streamlit as st
from utils.icons import mi, mi_inline
from utils.notify import notify
from state import reset_session, load_history_session, back_to_active
from api.client import check_health, force_generate, handle_response
from api.client import fetch_session_list, fetch_session_detail
from config import REQUIRED_FIELDS, OPTIONAL_FIELDS, FIELD_LABELS


def render_sidebar():
    """Render seluruh konten sidebar."""
    with st.sidebar:
        _render_brand()
        _render_new_chat()
        st.divider()
        _render_session_history()
        st.divider()
        _render_progress()
        _render_fields_checklist()
        _render_force_generate()
        st.divider()
        _render_system_status()


def _render_brand():
    """Logo dan nama aplikasi."""
    st.markdown(
        f'<h2 style="margin:0;">'
        f'{mi("smart_toy", 28, "var(--color-primary)")} TOR Generator'
        f'</h2>',
        unsafe_allow_html=True,
    )


def _render_session_history():
    """Dropdown 10 session terbaru + tombol Lihat Semua."""
    st.markdown('<p class="sidebar-label">RIWAYAT</p>', unsafe_allow_html=True)

    sessions = fetch_session_list(limit=10)

    if not sessions:
        st.caption("_Belum ada riwayat session._")
        return

    # Format label untuk dropdown
    def format_label(s: dict) -> str:
        state_icons = {
            "COMPLETED": "✅",
            "CHATTING": "⏳",
            "NEW": "⏳",
            "ESCALATED": "⚡",
        }
        icon = state_icons.get(s["state"], "📄")
        title = s["title"] or f"Session {s['id'][:8]}"
        # Potong title agar fit di sidebar
        if len(title) > 30:
            title = title[:30] + "..."
        return f"{icon} {title}"

    options = ["— Pilih session —"] + [format_label(s) for s in sessions]

    selected_idx = st.selectbox(
        "Riwayat session",
        range(len(options)),
        format_func=lambda i: options[i],
        label_visibility="collapsed",
        key="history_dropdown",
    )

    # Jika user memilih session (bukan placeholder)
    if selected_idx > 0:
        selected_session = sessions[selected_idx - 1]

        # Cek apakah ini session aktif saat ini
        if selected_session["id"] == st.session_state.session_id:
            # Kembali ke session aktif, bukan view history
            if st.session_state.is_viewing_history:
                back_to_active()
                st.rerun()
        else:
            # Load session lama sebagai history
            detail = fetch_session_detail(selected_session["id"])
            if detail:
                load_history_session(detail)
                st.rerun()

    # Tombol Lihat Semua
    if st.button("Lihat Semua", use_container_width=True, key="btn_all_sessions"):
        show_all_sessions_dialog()


@st.dialog("📋 Riwayat Session", width="large")
def show_all_sessions_dialog():
    """Modal dialog menampilkan semua session."""
    sessions = fetch_session_list(limit=50)

    if not sessions:
        notify("Belum ada riwayat session.", "info", method="inline")
        return

    state_icons = {
        "COMPLETED": ("check_circle", "var(--color-success)"),
        "CHATTING": ("hourglass_empty", "var(--color-warning)"),
        "NEW": ("hourglass_empty", "var(--color-text-muted)"),
        "ESCALATED": ("bolt", "var(--color-accent)"),
    }

    for s in sessions:
        icon_name, icon_color = state_icons.get(
            s["state"], ("description", "var(--color-text-muted)")
        )
        state_icon = mi(icon_name, 18, icon_color, filled=True)

        title = s["title"] or f"Session {s['id'][:8]}"
        has_tor = (
            f'{mi("article", 14, "var(--color-success)", filled=True)} TOR'
            if s["has_tor"]
            else ""
        )
        date = s["updated_at"][:10] if s["updated_at"] else "—"

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{state_icon} {title}**", unsafe_allow_html=True)
            st.markdown(
                f"<small>{s['turn_count']} Turn · {s['state']} · {date} {has_tor}</small>",
                unsafe_allow_html=True,
            )
        with col2:
            # Tombol berbeda tergantung apakah session aktif atau bukan
            is_current = s["id"] == st.session_state.session_id
            btn_label = "Aktif" if is_current else "Buka"
            btn_disabled = is_current and not st.session_state.is_viewing_history

            if st.button(
                btn_label,
                key=f"modal_open_{s['id']}",
                use_container_width=True,
                disabled=btn_disabled,
            ):
                if is_current:
                    back_to_active()
                else:
                    detail = fetch_session_detail(s["id"])
                    if detail:
                        load_history_session(detail)
                st.rerun()

        st.divider()



def _render_new_chat():
    """Tombol obrolan baru."""
    if st.button("Obrolan baru", use_container_width=True, type="primary"):
        reset_session()
        st.rerun()


def _render_progress():
    """Progress bar + turn count + status."""
    st.markdown('<p class="sidebar-label">PROGRESS</p>', unsafe_allow_html=True)

    state = st.session_state.current_state
    score = state.get("completeness_score", 0.0)
    st.progress(score, text=f"{score:.0%}")

    c1, c2 = st.columns(2)
    c1.metric("Turn", state.get("turn_count", 0))
    c2.metric("Status", state.get("status", "NEW")[:10])


def _render_fields_checklist():
    """Checklist field TOR yang sudah/belum terisi."""
    state = st.session_state.current_state
    filled = state.get("filled_fields", [])
    filled_count = sum(1 for f in REQUIRED_FIELDS if f in filled)

    with st.expander(f"Fields ({filled_count}/{len(REQUIRED_FIELDS)})"):
        for f in REQUIRED_FIELDS:
            if f in filled:
                icon = mi("check_circle", 16, "var(--color-success)", filled=True)
            else:
                icon = mi("radio_button_unchecked", 16, "var(--color-text-subtle)")
            label = FIELD_LABELS.get(f, f.replace("_", " ").title())
            st.markdown(f"{icon} {label}", unsafe_allow_html=True)

        st.caption("_Opsional_")
        for f in OPTIONAL_FIELDS:
            if f in filled:
                icon = mi("check_circle", 16, "var(--color-success)", filled=True)
            else:
                icon = mi("check_box_outline_blank", 16, "var(--color-text-subtle)")
            label = FIELD_LABELS.get(f, f.replace("_", " ").title())
            st.markdown(f"{icon} {label}", unsafe_allow_html=True)


def _render_force_generate():
    """Tombol force generate (hanya muncul jika relevant)."""
    if st.session_state.session_id and not st.session_state.tor_document:
        st.divider()
        if st.button("Force Generate TOR", use_container_width=True):
            with st.spinner("Generating..."):
                data = force_generate(st.session_state.session_id)
            if handle_response(data):
                st.rerun()
    elif st.session_state.tor_document:
        st.divider()
        st.markdown(
            mi_inline("task_alt", "TOR ready", 16, color="var(--color-success)"),
            unsafe_allow_html=True,
        )


def _render_system_status():
    """System status: API health + session ID."""
    st.markdown('<p class="sidebar-label">SYSTEM</p>', unsafe_allow_html=True)

    health = check_health()
    h = health.get("status", "unreachable")

    if h == "healthy":
        st.markdown(
            mi_inline("check_circle", "API Connected", 16, color="var(--color-success)"),
            unsafe_allow_html=True,
        )
    elif h == "unreachable":
        st.markdown(
            mi_inline("error", "API Offline", 16, color="var(--color-error)"),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            mi_inline("warning", h, 16, color="var(--color-warning)"),
            unsafe_allow_html=True,
        )

    if st.session_state.session_id:
        sid = st.session_state.session_id[:8]
        st.caption(f"Session: `{sid}...`")
