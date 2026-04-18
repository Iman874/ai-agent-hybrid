# Task 04 — Sidebar: Progress, Field Tracker, Session Info

## 1. Judul Task

Implementasi sidebar lengkap: tombol "Percakapan Baru", progress bar completeness, field tracker (✅/❌), session info, dan health status indicator.

## 2. Deskripsi

Sidebar memberikan konteks real-time ke user: seberapa lengkap data, field mana yang sudah/belum terisi, dan status koneksi ke backend. Juga berisi tombol navigasi.

## 3. Tujuan Teknis

- "Percakapan Baru" button → reset semua session state
- Progress bar `st.progress()` dari `completeness_score`
- Turn counter dan status display
- Field tracker: required fields ✅/❌, optional ⬜
- Session ID display (truncated)
- Health check indicator (🟢/🟡/🔴)

## 4. Scope

### Yang dikerjakan
- Seluruh sidebar UI
- New session logic
- Health check call

### Yang tidak dikerjakan
- Force generate button (task terpisah)

## 5. Langkah Implementasi

### Step 1: Sidebar structure

```python
with st.sidebar:
    st.title("🤖 TOR Generator")
    st.caption("AI Agent Hybrid v0.1.0")

    # --- New Session ---
    if st.button("🔄 Percakapan Baru", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.session_state.current_state = {
            "status": "NEW", "turn_count": 0,
            "completeness_score": 0.0,
            "filled_fields": [], "missing_fields": [],
        }
        st.session_state.tor_document = None
        st.session_state.escalation_info = None
        st.rerun()

    st.divider()

    # --- Progress ---
    state = st.session_state.current_state
    st.subheader("📊 Progress")
    score = state.get("completeness_score", 0.0)
    st.progress(score, text=f"Completeness: {score:.0%}")

    col1, col2 = st.columns(2)
    col1.metric("Turn", state.get("turn_count", 0))
    col2.metric("Status", state.get("status", "NEW")[:12])

    st.divider()

    # --- Field Tracker ---
    st.subheader("📋 Fields")
    REQUIRED = ["judul", "latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"]
    OPTIONAL = ["estimasi_biaya"]
    filled = state.get("filled_fields", [])

    for f in REQUIRED:
        st.markdown(f"✅ **{f}**" if f in filled else f"❌ {f}")
    for f in OPTIONAL:
        st.markdown(f"✅ **{f}** _(opsional)_" if f in filled else f"⬜ {f} _(opsional)_")

    st.divider()

    # --- System ---
    st.subheader("🔧 System")
    if st.session_state.session_id:
        st.text(f"Session: {st.session_state.session_id[:8]}...")
    else:
        st.text("Session: belum dimulai")

    health = check_health()
    status = health.get("status", "unreachable")
    if status == "healthy":
        st.success("API: 🟢 Connected")
    elif status == "unreachable":
        st.error("API: 🔴 Offline")
    else:
        st.warning(f"API: 🟡 {status}")
```

### Step 2: Verifikasi

1. Sidebar muncul dengan semua section
2. Klik "Percakapan Baru" → state reset, chat kosong
3. Setelah chat 1 turn → progress bar update, field tracker update
4. Health indicator sesuai status backend

## 6. Output yang Diharapkan

Sidebar yang informatif dengan progress real-time dan field tracker yang update otomatis setiap turn.

## 7. Dependencies

- **Task 01** — session state init
- **Task 02** — `check_health()`
- **Task 03** — chat working (untuk test progress update)

## 8. Acceptance Criteria

- [ ] "Percakapan Baru" reset semua state
- [ ] Progress bar menampilkan `completeness_score`
- [ ] Turn counter dan status ter-display
- [ ] Field tracker menunjukkan ✅/❌ untuk setiap field
- [ ] Session ID truncated ter-display
- [ ] Health check indicator berfungsi (🟢/🟡/🔴)

## 9. Estimasi

**Medium** — ~1 jam
