# Task 03 — Chat Interface: Messages + Input + API Call

## 1. Judul Task

Implementasi chat interface utama: render message bubbles, chat input, panggil API, dan handle response.

## 2. Deskripsi

Ini adalah core UI — chat bubbles untuk user dan assistant, input box di bawah, spinner saat API call, dan logic untuk update session state setelah response diterima.

## 3. Tujuan Teknis

- `st.chat_message("user")` dan `st.chat_message("assistant")` untuk render history
- `st.chat_input()` untuk input
- Saat user submit: append ke messages, panggil `send_message()`, handle response
- Update `st.session_state` dengan response data
- `st.rerun()` setelah response untuk refresh UI

## 4. Scope

### Yang dikerjakan
- Render chat history dari `st.session_state.messages`
- Chat input handler
- API call + spinner
- Response handler (update state)

### Yang tidak dikerjakan
- Sidebar (task lain)
- TOR preview (task lain)

## 5. Langkah Implementasi

### Step 1: Tambah response handler function

```python
def handle_response(data: dict) -> bool:
    """Process API response dan update session state. Return True jika sukses."""
    if "error" in data:
        st.error(f"❌ {data['error']}")
        return False

    # Update session
    st.session_state.session_id = data["session_id"]
    st.session_state.current_state = data["state"]

    # Append assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": data["message"],
    })

    # TOR generated?
    if data.get("tor_document"):
        st.session_state.tor_document = data["tor_document"]

    # Escalation?
    if data.get("escalation_info"):
        st.session_state.escalation_info = data["escalation_info"]

    return True
```

### Step 2: Render chat history

```python
# Main area
st.title("💬 AI TOR Generator")
st.caption("Ceritakan kebutuhan Anda, AI akan bantu menyusun dokumen TOR profesional.")

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
```

### Step 3: Chat input handler

```python
if prompt := st.chat_input("Ketik pesan Anda..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call API with spinner
    with st.spinner("🤔 AI sedang berpikir..."):
        data = send_message(st.session_state.session_id, prompt)

    # Handle response
    if handle_response(data):
        st.rerun()
```

### Step 4: Verifikasi

1. Jalankan backend: `make run`
2. Jalankan Streamlit: `make ui`
3. Ketik "Buat TOR workshop AI" → assistant merespons
4. Ketik followup → conversation berlanjut
5. Session state ter-update

## 6. Output yang Diharapkan

Chat interface yang berfungsi: user bisa mengetik, assistant merespons, history tersimpan.

## 7. Dependencies

- **Task 01** — session state init
- **Task 02** — `send_message()`, `handle_response()`

## 8. Acceptance Criteria

- [ ] Chat bubbles render untuk user dan assistant
- [ ] Chat input berfungsi
- [ ] API call berhasil (spinner muncul)
- [ ] Session ID tersimpan setelah response pertama
- [ ] Chat history persisten antar rerun
- [ ] Error ditampilkan via `st.error` jika API gagal

## 9. Estimasi

**Medium** — ~1 jam
