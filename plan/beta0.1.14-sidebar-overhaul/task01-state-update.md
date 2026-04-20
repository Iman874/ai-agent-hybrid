# Task 01: State Update — Tambah State Keys Baru & Update reset_session()

## 1. Judul Task

Tambah `active_tool`, `active_model_id`, `_loading_session_id` ke state & update `reset_session()`

## 2. Deskripsi

Menyiapkan fondasi state management untuk navigasi tool-based (bukan tab-based) dan model selector di sidebar. Semua task selanjutnya bergantung pada perubahan ini.

## 3. Tujuan Teknis

- Tambah 3 state keys baru di `init_session_state()`
- Update `reset_session()` agar mereset `active_tool` & `_loading_session_id`
- `active_model_id` dan `chat_mode` TIDAK direset (preferensi model tetap)

## 4. Scope

**Yang dikerjakan:**
- `streamlit_app/state.py`

**Yang tidak dikerjakan:**
- Sidebar UI (task 02)
- App.py layout (task 03)

## 5. Langkah Implementasi

### 5.1 Tambah Defaults Baru di `init_session_state()`

Tambahkan 3 key baru ke `defaults` dict:

```python
defaults = {
    ...
    "active_tool": "chat",            # "chat" | "generate_doc"
    "active_model_id": None,          # e.g. "gemma4:e2b"
    "_loading_session_id": None,      # anti-flicker guard
    ...
}
```

Letakkan setelah `session_list` dan sebelum doc style keys.

### 5.2 Update `reset_session()`

Tambahkan reset untuk `active_tool` dan `_loading_session_id`:

```python
def reset_session():
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.current_state = {
        "status": "NEW",
        "turn_count": 0,
        "completeness_score": 0.0,
        "filled_fields": [],
        "missing_fields": [],
    }
    st.session_state.tor_document = None
    st.session_state.escalation_info = None
    st.session_state.direct_tor = None
    st.session_state.doc_tor = None
    st.session_state.is_viewing_history = False
    st.session_state.history_session = None
    st.session_state._loading_session_id = None
    # Reset tool ke default
    st.session_state.active_tool = "chat"
    # active_model_id → TIDAK direset (preferensi model tetap)
    # chat_mode → TIDAK direset
    # Reset doc style selection
    st.session_state.doc_style_mode = "active"
    st.session_state.doc_selected_style_id = None
    st.session_state.doc_detected_style = None
    st.session_state.doc_awaiting_confirm = False
```

## 6. Output yang Diharapkan

```python
# Setelah init_session_state():
st.session_state.active_tool == "chat"
st.session_state.active_model_id == None
st.session_state._loading_session_id == None

# Setelah reset_session():
st.session_state.active_tool == "chat"        # direset
st.session_state._loading_session_id == None   # direset
st.session_state.active_model_id == "gemma4:e2b"  # TETAP (tidak direset)
```

## 7. Dependencies

Tidak ada (task pertama)

## 8. Acceptance Criteria

- [ ] `init_session_state()` mengandung 3 key baru
- [ ] `reset_session()` mereset `active_tool` ke `"chat"`
- [ ] `reset_session()` mereset `_loading_session_id` ke `None`
- [ ] `reset_session()` TIDAK mereset `active_model_id`
- [ ] `reset_session()` TIDAK mereset `chat_mode`
- [ ] App start tanpa error
- [ ] Existing tests tetap PASS

## 9. Estimasi

Low (15–30 menit)
