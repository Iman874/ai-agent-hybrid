# Task 05: UI Redesign — Layout Ala ChatGPT

## Deskripsi
Rewrite `streamlit_app.py` dengan layout baru: sidebar kiri berisi semua kontrol, area utama hanya menampilkan chat history + input. Hapus tab-based layout, pindahkan semua ke sidebar.

## Tujuan Teknis
1. Sidebar kiri: New Chat, Model Selector, Progress, Fields, Tools (Generate, Document, Direct), System
2. Area utama: bersih — hanya chat messages + chat input
3. Tools (Gemini Direct, From Document) diakses via `st.expander` di sidebar, bukan tab terpisah

## Scope
- **Dikerjakan**:
  - Rewrite layout `streamlit_app.py` dari tab-based → sidebar + main chat
  - Pindahkan semua kontrol ke sidebar
  - Gemini Direct & From Document → sidebar expanders atau dialog
  - Pertahankan semua fungsi helper (API calls, PDF export, TOR preview)
- **Tidak dikerjakan**:
  - Model selector logic (task06)
  - Custom CSS theme (task07)

## Langkah Implementasi

### Step 1: Restructure Sidebar

```python
with st.sidebar:
    st.title("🤖 TOR Generator")
    st.caption("AI Agent Hybrid v0.1.7")

    # --- New Chat ---
    if st.button("➕ Percakapan Baru", use_container_width=True):
        reset_session()

    st.divider()

    # --- Model Selector (placeholder, task06) ---
    st.subheader("⚙️ Model")
    st.info("Local LLM: qwen2.5:3b")  # placeholder

    st.divider()

    # --- Progress ---
    st.subheader("📊 Progress")
    score = state.get("completeness_score", 0.0)
    st.progress(score, text=f"{score:.0%}")
    col1, col2 = st.columns(2)
    col1.metric("Turn", state.get("turn_count", 0))
    col2.metric("Status", state.get("status", "NEW")[:12])

    st.divider()

    # --- Fields ---
    with st.expander("📋 Fields", expanded=False):
        for f in REQUIRED:
            st.markdown(f"{'✅' if f in filled else '❌'} {f}")
        for f in OPTIONAL:
            st.markdown(f"{'✅' if f in filled else '⬜'} {f} _(opsional)_")

    st.divider()

    # --- Tools ---
    st.subheader("🛠️ Tools")

    # Force Generate
    if session_id and not tor_document:
        if st.button("🚀 Force Generate TOR", use_container_width=True):
            ...

    # From Document (expander)
    with st.expander("📄 From Document"):
        uploaded_file = st.file_uploader(...)
        doc_context = st.text_area(...)
        if st.button("Generate dari Dokumen"):
            ...

    # Gemini Direct (expander)
    with st.expander("🚀 Gemini Direct"):
        with st.form("direct_form"):
            judul = st.text_input("Judul *")
            ...

    st.divider()

    # --- System ---
    st.subheader("🔧 System")
    st.text(f"Session: {session_id[:8]}..." if session_id else "Belum dimulai")
    # Health indicator
```

### Step 2: Main Area — Clean Chat

```python
# Main area: HANYA chat
st.title("💬 AI TOR Generator")

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# TOR Preview (inline setelah chat jika ada)
if st.session_state.tor_document:
    render_tor_preview(st.session_state.tor_document, ...)

# Chat input
if prompt := st.chat_input("Ketik pesan Anda..."):
    ...
```

### Step 3: Refactor session reset ke fungsi

```python
def reset_session():
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.current_state = {...}
    st.session_state.tor_document = None
    st.session_state.escalation_info = None
    st.session_state.direct_tor = None
    st.session_state.doc_tor = None
    st.rerun()
```

## Output yang Diharapkan
- Sidebar kiri solid dengan semua kontrol
- Area utama bersih — hanya chat bubbles + input
- Tools (From Document, Gemini Direct) tersembunyi di sidebar expanders
- Semua fungsi yang ada tetap bekerja

## Dependencies
- Tidak ada (bisa paralel dengan backend tasks)

## Acceptance Criteria
- [ ] Tidak ada tab di area utama — hanya chat
- [ ] Sidebar berisi: New Chat, Progress, Fields, Tools, System
- [ ] "From Document" berfungsi via sidebar expander
- [ ] "Gemini Direct" berfungsi via sidebar expander/form
- [ ] Chat input selalu di bawah
- [ ] TOR preview muncul inline di chat area
- [ ] Semua session state management benar

## Estimasi
High
