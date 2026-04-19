# Task 06: UI — Model Selector di Sidebar

## Deskripsi
Implementasi model selector di sidebar Streamlit yang memungkinkan user memilih "Local LLM" atau "Gemini API" sebagai chat provider. Selector ini mengirim `chat_mode` ke backend saat setiap request.

## Tujuan Teknis
1. Radio button untuk pilih provider type: `Local LLM` / `Gemini API`
2. Jika Local LLM: selectbox untuk pilih model Ollama (dari endpoint `/models`)
3. Jika Gemini API: tampilkan nama model Gemini (read-only)
4. Switch model mid-session = reset session (start baru)
5. Kirim `chat_mode` di setiap `send_message()` call

## Scope
- **Dikerjakan**:
  - Fetch model list dari `GET /api/v1/models`
  - Radio button di sidebar untuk Local/Gemini
  - Selectbox model jika Local (dari Ollama list)
  - Session state `chat_mode` dan `selected_model`
  - Warning saat switch model mid-session
  - Update `send_message()` untuk include `chat_mode` di options
- **Tidak dikerjakan**:
  - CSS/theme (task07)
  - Backend changes (sudah di task01-04)

## Langkah Implementasi

### Step 1: Tambah API helper

```python
def fetch_models() -> list[dict]:
    """Ambil daftar model dari backend."""
    try:
        resp = requests.get(f"{API_URL}/models", timeout=5)
        return resp.json().get("models", [])
    except Exception:
        return []
```

### Step 2: Init session state

```python
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "local"
if "selected_model" not in st.session_state:
    st.session_state.selected_model = None
```

### Step 3: Sidebar Model Selector

```python
with st.sidebar:
    st.subheader("⚙️ Chat Model")

    models = fetch_models()
    local_models = [m for m in models if m["type"] == "local" and m["status"] == "available"]
    gemini_models = [m for m in models if m["type"] == "gemini" and m["status"] == "available"]

    # Disable local if Ollama offline
    local_available = len(local_models) > 0
    gemini_available = len(gemini_models) > 0

    mode_options = []
    if local_available:
        mode_options.append("🖥️ Local LLM")
    if gemini_available:
        mode_options.append("✨ Gemini API")

    if not mode_options:
        st.error("Tidak ada model tersedia!")
    else:
        selected = st.radio("Provider", mode_options, label_visibility="collapsed")
        new_mode = "local" if "Local" in selected else "gemini"

        # Detect mode change mid-session
        if new_mode != st.session_state.chat_mode and st.session_state.session_id:
            st.warning("⚠️ Ganti model = session baru. Data chat akan di-reset.")
            if st.button("Confirm Switch", use_container_width=True):
                st.session_state.chat_mode = new_mode
                reset_session()

        st.session_state.chat_mode = new_mode

        # Show model name
        if new_mode == "local" and local_models:
            model_names = [m["id"] for m in local_models]
            selected_model = st.selectbox("Model", model_names)
            st.session_state.selected_model = selected_model
        elif new_mode == "gemini" and gemini_models:
            st.info(f"Model: {gemini_models[0]['id']}")
```

### Step 4: Update `send_message()`

```python
def send_message(session_id, message, options=None):
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id

    # Merge chat_mode into options
    opts = options or {}
    opts["chat_mode"] = st.session_state.get("chat_mode", "local")
    payload["options"] = opts

    ...
```

## Output yang Diharapkan
- Sidebar menampilkan radio button Local/Gemini
- Jika Ollama offline → Local LLM disabled
- Pilih Gemini → semua chat request dikirim dengan `chat_mode: "gemini"`
- Switch mid-session → warning + reset

## Dependencies
- Task 03 (endpoint `/models` harus ada)
- Task 05 (layout sidebar harus sudah di-refactor)

## Acceptance Criteria
- [ ] Radio button Local LLM / Gemini API ada di sidebar
- [ ] `fetch_models()` memanggil `GET /api/v1/models`
- [ ] Ollama offline → Local LLM tidak bisa dipilih
- [ ] Switch model mid-session → warning + reset session
- [ ] `send_message()` selalu mengirim `chat_mode` di options
- [ ] State `chat_mode` persisten di `st.session_state`

## Estimasi
Medium
