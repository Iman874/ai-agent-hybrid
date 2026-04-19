# Task 09: Component — Chat Tab (`components/chat.py`)

## Status: 🔲 Pending

---

## 1. Judul Task

Membuat komponen tab Chat dengan empty state, message list, dan chat input.

## 2. Deskripsi

Extract tab Chat dari monolit ke `components/chat.py`. Upgrade empty state
menjadi desain profesional dengan Material Icon `forum` besar di tengah.
Tambahkan loading state yang lebih baik.

## 3. Tujuan Teknis

- `render_chat_tab()` — entry function untuk tab Chat
- Empty state menggunakan `.empty-state` CSS class + `forum` icon (64px)
- Loading state menggunakan `st.spinner` dengan teks deskriptif
- Message list + TOR preview + chat input

## 4. Scope

**Yang dikerjakan:**
- `components/chat.py` — chat tab UI lengkap
- Empty state visual yang profesional
- Integration dengan `tor_preview.py`

**Yang TIDAK dikerjakan:**
- API client (sudah di Task 04)
- TOR preview component (sudah di Task 06)
- Sidebar (Task 07)

## 5. Langkah Implementasi

### Step 1: Buat `components/chat.py`

```python
# streamlit_app/components/chat.py
"""Chat tab — interactive TOR building via conversation."""

import streamlit as st
from utils.icons import mi
from api.client import send_message, handle_response
from components.tor_preview import render_tor_preview


def render_chat_tab():
    """Render tab Chat: empty state / messages / TOR preview / input."""

    # Empty state
    if not st.session_state.messages and not st.session_state.tor_document:
        _render_empty_state()

    # Message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # TOR Preview (jika sudah di-generate)
    if st.session_state.tor_document:
        render_tor_preview(
            st.session_state.tor_document,
            st.session_state.escalation_info,
            key_suffix="_hybrid",
        )

    # Chat input
    if prompt := st.chat_input("Tanyakan apa saja..."):
        _handle_user_input(prompt)


def _render_empty_state():
    """Render empty state dengan Material Icon besar dan pesan terarah."""
    icon = mi("forum", 64, "var(--color-text-subtle)")
    st.markdown(
        f'''
        <div class="empty-state">
            {icon}
            <h3>Ceritakan kebutuhan TOR Anda</h3>
            <p>
                Mulai chat untuk menyusun Term of Reference<br>
                dengan bantuan AI secara interaktif.
            </p>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def _handle_user_input(prompt: str):
    """Process user input: append message, call API, handle response."""
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Show user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call API
    with st.spinner("AI sedang memproses permintaan..."):
        data = send_message(st.session_state.session_id, prompt)

    # Handle response
    if handle_response(data):
        st.rerun()
```

### Step 2: Update `app.py`

```python
from components.chat import render_chat_tab

tab_chat, tab_direct, tab_doc = st.tabs(["Chat", "Gemini Direct", "Dari Dokumen"])

with tab_chat:
    render_chat_tab()
```

### Step 3: Test

1. Buka tab Chat → empty state muncul dengan icon `forum` besar
2. Ketik pesan → loading spinner muncul → response ditampilkan
3. Jika TOR di-generate → `render_tor_preview()` tampil di bawah chat

## 6. Output yang Diharapkan

```
streamlit_app/components/
├── chat.py          (~65 lines)
```

Empty state visual:
```
         [forum icon 64px, muted]

     Ceritakan kebutuhan TOR Anda

   Mulai chat untuk menyusun Term of
   Reference dengan bantuan AI
   secara interaktif.
```

## 7. Dependencies

- **Task 01** — config, state
- **Task 03** — `mi()`
- **Task 04** — `send_message`, `handle_response`
- **Task 06** — `render_tor_preview()`

## 8. Acceptance Criteria

- [ ] Empty state menampilkan icon `forum` (64px, muted) + teks deskriptif
- [ ] Empty state menggunakan CSS class `.empty-state`
- [ ] Messages tampil dalam `st.chat_message` bubble
- [ ] Chat input berfungsi — mengirim pesan ke API
- [ ] Loading spinner muncul saat menunggu response
- [ ] TOR preview muncul setelah generate
- [ ] Tidak ada emoji — semua Material Icons

## 9. Estimasi

**Medium** — Logic agak banyak (empty state + message handling + TOR preview).
