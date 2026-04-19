# Task 04: Sidebar UI — Dropdown Riwayat + Modal Dialog

> **Status**: [ ] Belum Dikerjakan
> **Estimasi**: High (2–3 jam)
> **Dependency**: Task 03 (state + client functions harus sudah ada)

## 1. Deskripsi

Menambahkan section "RIWAYAT" di sidebar berupa dropdown `st.selectbox` berisi 10 session terbaru, dilengkapi tombol "Lihat Semua" yang membuka modal dialog `@st.dialog()` menampilkan semua session.

## 2. Tujuan Teknis

- Sidebar menampilkan dropdown riwayat session
- Memilih session dari dropdown → load history view
- Tombol "Lihat Semua" → buka modal popup di tengah layar
- Modal menampilkan semua session dengan tombol "Buka" per item

## 3. Scope

**Yang dikerjakan:**
- `streamlit_app/components/sidebar.py` — tambah section riwayat + modal

**Yang tidak dikerjakan:**
- Tampilan read-only chat history (task05)
- Logika history view di `chat.py` (task05)

## 4. Langkah Implementasi

### 4.1 Tambah Import di `sidebar.py`

- [ ] Tambahkan import baru di bagian atas `sidebar.py`:

```diff
 from state import reset_session
+from state import load_history_session, back_to_active
 from api.client import fetch_models, check_health, force_generate, handle_response
+from api.client import fetch_session_list, fetch_session_detail
```

### 4.2 Tambah `_render_session_history()` di Sidebar

- [ ] Buat fungsi baru `_render_session_history()` di `sidebar.py`:

```python
def _render_session_history():
    """Dropdown 10 session terbaru + tombol Lihat Semua."""
    st.markdown('<p class="sidebar-label">RIWAYAT</p>', unsafe_allow_html=True)

    sessions = fetch_session_list(limit=10)

    if not sessions:
        st.caption("_Belum ada riwayat session._")
        return

    # Format label untuk dropdown
    def format_label(s: dict) -> str:
        icon = "✅" if s["state"] == "COMPLETED" else "⏳" if s["state"] in ("CHATTING", "NEW") else "⚡"
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
    if st.button("📋 Lihat Semua", use_container_width=True, key="btn_all_sessions"):
        show_all_sessions_dialog()
```

### 4.3 Buat Modal Dialog `show_all_sessions_dialog()`

- [ ] Buat fungsi modal dialog menggunakan `@st.dialog()`:

```python
@st.dialog("📋 Riwayat Session", width="large")
def show_all_sessions_dialog():
    """Modal dialog menampilkan semua session."""
    sessions = fetch_session_list(limit=50)

    if not sessions:
        st.info("Belum ada riwayat session.")
        return

    for s in sessions:
        # Status icon
        if s["state"] == "COMPLETED":
            icon = "✅"
        elif s["state"] in ("CHATTING", "NEW"):
            icon = "⏳"
        elif s["state"] == "ESCALATED":
            icon = "⚡"
        else:
            icon = "📄"

        title = s["title"] or f"Session {s['id'][:8]}"
        has_tor = "📝 TOR" if s["has_tor"] else ""
        date = s["updated_at"][:10] if s["updated_at"] else "—"

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{icon} {title}**")
            st.caption(f"{s['turn_count']} Turn · {s['state']} · {date} {has_tor}")
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
```

### 4.4 Integrasikan ke `render_sidebar()`

- [ ] Update fungsi `render_sidebar()` untuk menyertakan section riwayat:

```diff
 def render_sidebar():
     """Render seluruh konten sidebar."""
     with st.sidebar:
         _render_brand()
         _render_new_chat()
+        st.divider()
+        _render_session_history()
         st.divider()
         _render_model_selector()
         st.divider()
```

**Catatan posisi**: Riwayat ditempatkan **setelah tombol "Obrolan baru"** dan **sebelum Model selector** agar mudah diakses.

### 4.5 Update `_render_new_chat()` untuk Reset History View

- [ ] Pastikan tombol "Obrolan baru" juga keluar dari history view:

```diff
 def _render_new_chat():
     """Tombol obrolan baru."""
     if st.button("Obrolan baru", use_container_width=True, type="primary"):
         reset_session()
         st.rerun()
```

Ini sudah aman karena `reset_session()` di task03 sudah direset `is_viewing_history = False`.

## 5. Output yang Diharapkan

### Sidebar (normal state):
```
🤖 TOR Generator
[Obrolan baru]
────────────
RIWAYAT
┌─▼ Pilih session──────┐
│ ✅ Workshop Penerapan │
│ ✅ Pengadaan Server   │
│ ⏳ Rapat Koordinasi   │
└───────────────────────┘
[📋 Lihat Semua]
────────────
MODEL
...
```

### Modal Dialog:
```
╔═══════════════════════════════════╗
║     📋 Riwayat Session            ║
╠═══════════════════════════════════╣
║ ✅ Workshop Penerapan AI untuk... ║
║   8 Turn · COMPLETED · 2026-04   ║
║                           [Buka] ║
║───────────────────────────────────║
║ ⏳ Rapat Koordinasi BAPPENAS     ║
║   3 Turn · CHATTING · 2026-04    ║
║                           [Aktif]║
╚═══════════════════════════════════╝
```

## 6. Acceptance Criteria

- [ ] Section "RIWAYAT" muncul di sidebar.
- [ ] Dropdown menampilkan maksimal 10 session terbaru.
- [ ] Placeholder "— Pilih session —" adalah default (tidak ada session ter-select).
- [ ] Memilih session dari dropdown → halaman berubah ke history view mode.
- [ ] Klik "📋 Lihat Semua" → modal popup muncul di tengah layar.
- [ ] Modal menampilkan semua session (hingga 50) dengan info lengkap.
- [ ] Klik "Buka" di modal → load session dan tutup modal.
- [ ] Klik "Obrolan baru" dari history view → kembali ke state normal.
- [ ] Jika belum ada session, sidebar menampilkan "_Belum ada riwayat session._".
