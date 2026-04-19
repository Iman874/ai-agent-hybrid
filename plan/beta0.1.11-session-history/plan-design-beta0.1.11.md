# Plan Design — Beta 0.1.11: Session History & Management

## 1. Latar Belakang

Saat ini, aplikasi TOR Generator hanya mendukung **satu session aktif** yang tersimpan di `st.session_state` di sisi Streamlit. Ketika user mengklik "Obrolan baru", session lama langsung hilang dari UI tanpa bisa dikunjungi kembali. Padahal data session (chat history, TOR result, extracted data) **sudah tersimpan di SQLite backend** — hanya belum ada interface untuk mengaksesnya kembali.

Fitur ini akan menambahkan **Session History** yang memungkinkan user melihat daftar session sebelumnya, membuka kembali result-nya (read-only), sambil memastikan hanya **1 session yang aktif** pada satu waktu.

> **Catatan Multi-User**: Saat ini belum ada user management/login. Aturan "1 active session" berlaku per-instance aplikasi. Ketika fitur login ditambahkan di versi mendatang, aturan ini akan menjadi "1 active session **per user**" — tidak perlu perubahan arsitektur tambahan.

## 2. Prinsip Desain

1. **1 Active Session Rule**: Hanya boleh ada 1 session dalam state `CHATTING` / `NEW` / `GENERATING` pada satu waktu. Session lama yang sudah `COMPLETED` atau `ESCALATED` bersifat **read-only** (hanya bisa dilihat, tidak bisa dilanjutkan chat).
2. **Session History = Arsip**: Daftar session lama ditampilkan sebagai arsip. User bisa klik untuk melihat chat history + TOR yang pernah di-generate.
3. **Data Sudah Ada di DB**: Tidak perlu infrastruktur baru. Tabel `sessions` dan `chat_messages` di SQLite sudah menampung semua informasi yang dibutuhkan.

## 3. Arsitektur UI — Dropdown + Modal

### 3.1 Sidebar: Dropdown Riwayat (Top 10)

Di sidebar, di bawah tombol "Obrolan baru", ditambahkan **dropdown `st.selectbox`** berisi 10 session terbaru. User bisa langsung memilih session dari sini untuk melihat arsipnya.

```
┌──────────────────────┐
│ 🤖 TOR Generator     │
│ [Obrolan baru]       │
│                      │
│ RIWAYAT              │
│ ┌──────────────────┐ │
│ │ ▼ Pilih session  │ │  ← st.selectbox (10 terbaru)
│ │  Workshop AI...  │ │
│ │  Pengadaan Srv...│ │
│ │  Rapat Koordin...│ │
│ └──────────────────┘ │
│ [📋 Lihat Semua]     │  ← Tombol buka modal
│ ─────────────────── │
│ MODEL                │
│ ...                  │
└──────────────────────┘
```

- **Dropdown** menampilkan 10 session terbaru (`updated_at DESC`)
- Setiap item format: `"{status_icon} {title} — {date}"`
- Item pertama (default) = "— Pilih session —" (placeholder)
- Ketika user memilih session → halaman utama berubah ke **History View Mode** (read-only)

### 3.2 Modal Dialog: Lihat Semua Session

Ketika user klik tombol **"📋 Lihat Semua"**, muncul **`st.dialog`** (popup di tengah layar) yang menampilkan semua session dengan detail lebih lengkap.

```
┌─────────────────────────────────────────┐
│           📋 Riwayat Session            │
│─────────────────────────────────────────│
│                                         │
│  ✅ Workshop Penerapan AI untuk ASN     │
│     8 Turn · Completed · 19 Apr 2026   │
│     [Buka]                              │
│                                         │
│  ✅ Pengadaan Server Data Center        │
│     12 Turn · Completed · 18 Apr 2026  │
│     [Buka]                              │
│                                         │
│  ⏳ Rapat Koordinasi BAPPENAS          │
│     3 Turn · Chatting · 17 Apr 2026    │
│     [Lanjutkan]  ← hanya jika CHATTING │
│                                         │
│  ✅ Capacity Building Transformasi...   │
│     6 Turn · Completed · 16 Apr 2026   │
│     [Buka]                              │
│                                         │
│              [Tutup]                    │
└─────────────────────────────────────────┘
```

Fitur modal:
- Menampilkan **semua session** (tidak terbatas 10)
- Status icon: ✅ = COMPLETED, ⏳ = CHATTING/NEW, ⚡ = ESCALATED
- Info: title, turn count, state, tanggal
- Tombol "Buka" → load history view (read-only)
- Session yang masih `CHATTING` dan merupakan session aktif saat ini → tombol "Lanjutkan" (kembali ke session tersebut)
- Tombol "Tutup" untuk menutup modal

## 4. Arsitektur Backend

```
┌──────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                │
│                                                  │
│  [BARU] GET /api/v1/sessions?limit=20            │
│    → List semua session, urut terbaru            │
│    → Return: id, title, state, created_at,       │
│      turn_count, has_tor                         │
│                                                  │
│  [EXISTING] GET /api/v1/session/{id}             │
│    → Detail session + chat history (sudah ada)   │
│                                                  │
│  [MODIF] SessionManager                          │
│    → Tambah method list_all()                    │
│    → Tambah method update_title()                │
│    → Modif create() → auto-set title nanti       │
│                                                  │
│  [BARU] Migration 005                            │
│    → ALTER TABLE sessions ADD COLUMN title        │
└──────────────────────────────────────────────────┘
```

### 4.1 API Response Model — `SessionListItem`

```python
class SessionListItem(BaseModel):
    id: str
    title: str | None           # Potong 40 char dari pesan pertama user
    state: str                  # "COMPLETED", "CHATTING", dsb
    turn_count: int
    created_at: str
    updated_at: str
    has_tor: bool               # True jika generated_tor IS NOT NULL
```

### 4.2 `SessionManager.list_all()`

```python
async def list_all(self, limit: int = 50) -> list[dict]:
    """List semua session, urut dari terbaru, dengan preview title."""
    query = """
        SELECT s.id, s.title, s.state, s.turn_count, 
               s.created_at, s.updated_at,
               CASE WHEN s.generated_tor IS NOT NULL THEN 1 ELSE 0 END as has_tor
        FROM sessions s
        ORDER BY s.updated_at DESC
        LIMIT ?
    """
    ...
```

### 4.3 Auto-Title dari Pesan Pertama

Ketika user mengirim pesan pertama di session baru, backend otomatis mengupdate kolom `title` dengan **40 karakter pertama** dari pesan user. Ini dilakukan di `ChatService` atau `SessionManager` setelah `append_message` pertama.

```python
# Di ChatService, setelah append message pertama
if session.turn_count == 0:
    title = message[:40].strip()
    if len(message) > 40:
        title += "..."
    await self.session_mgr.update(session_id, title=title)
```

### 4.4 DB Migration

**File**: `app/db/migrations/005_session_title.sql`

```sql
-- Migration 005: Add title column to sessions
ALTER TABLE sessions ADD COLUMN title TEXT DEFAULT NULL;
```

> **Catatan**: `ALTER TABLE ... ADD COLUMN` aman dijalankan berulang di SQLite — jika kolom sudah ada, akan diabaikan oleh `IF NOT EXISTS` (perlu penanganan error di code).

## 5. Arsitektur Frontend

### 5.1 State Changes — `state.py`

```python
# TAMBAHAN defaults:
"is_viewing_history": False,        # True = sedang lihat arsip
"history_session": None,            # dict: session detail + chat history
"session_list": [],                 # cache list session dari API
"show_all_sessions": False,         # toggle untuk modal dialog
```

Fungsi baru:

```python
def load_history_session(session_id: str):
    """Load session lama ke mode read-only."""
    ...

def back_to_active():
    """Kembali dari history view ke session aktif."""
    ...
```

### 5.2 API Client — `client.py`

```python
def fetch_session_list(limit: int = 10) -> list[dict]:
    """Ambil daftar session terbaru dari backend."""
    ...

def fetch_session_detail(session_id: str) -> dict | None:
    """Ambil detail session + chat history."""
    ...
```

### 5.3 Sidebar — `sidebar.py`

Di `render_sidebar()`, setelah `_render_new_chat()`, tambah:

```python
def _render_session_history():
    """Dropdown 10 session terbaru + tombol Lihat Semua."""
    sessions = fetch_session_list(limit=10)
    
    # Dropdown selectbox
    options = ["— Pilih session —"] + [format_session_label(s) for s in sessions]
    selected = st.selectbox("RIWAYAT", options, label_visibility="visible")
    
    if selected != "— Pilih session —":
        # Load history view
        load_history_session(sessions[selected_index])
        st.rerun()
    
    # Tombol buka modal
    if st.button("📋 Lihat Semua", use_container_width=True):
        show_all_sessions_dialog()
```

### 5.4 Modal Dialog — `sidebar.py` (atau komponen terpisah)

Menggunakan `@st.dialog("Riwayat Session")` decorator (Streamlit ≥ 1.35):

```python
@st.dialog("📋 Riwayat Session", width="large")
def show_all_sessions_dialog():
    """Modal dialog menampilkan semua session."""
    sessions = fetch_session_list(limit=50)
    
    for s in sessions:
        col1, col2 = st.columns([4, 1])
        with col1:
            icon = "✅" if s["state"] == "COMPLETED" else "⏳"
            st.markdown(f"**{icon} {s['title'] or 'Untitled'}**")
            st.caption(f"{s['turn_count']} Turn · {s['state']} · {s['created_at']}")
        with col2:
            if st.button("Buka", key=f"open_{s['id']}"):
                load_history_session(s["id"])
                st.rerun()
    
    if st.button("Tutup", use_container_width=True):
        st.rerun()
```

### 5.5 History View Mode — `chat.py`

Ketika `is_viewing_history = True`:

```python
def render_chat_tab():
    if st.session_state.is_viewing_history:
        _render_history_view()
        return
    # ... kode normal existing ...

def _render_history_view():
    """Tampilkan session lama dalam mode read-only."""
    hist = st.session_state.history_session
    
    # Banner info
    st.info("📋 Anda melihat arsip session. Chat dalam mode read-only.")
    
    # Tombol kembali
    if st.button("← Kembali ke Obrolan Aktif"):
        back_to_active()
        st.rerun()
    
    # Render chat history (read-only, tanpa chat_input)
    for msg in hist["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # TOR Preview jika ada
    if hist.get("generated_tor"):
        render_tor_preview(...)
```

## 6. Roadmap Task

| Task | File Target | Deskripsi |
|------|------------|-----------|
| **task01** | `005_session_title.sql`, `session_manager.py` | DB migration kolom `title` + method `list_all()` + auto-title logic |
| **task02** | `session.py` (routes), `responses.py` | API endpoint `GET /sessions` + response model `SessionListItem` |
| **task03** | `state.py`, `client.py` | State management history + API client functions |
| **task04** | `sidebar.py` | Dropdown riwayat (10 terbaru) + tombol "Lihat Semua" + modal dialog |
| **task05** | `chat.py`, `tor_preview.py` | Read-only history view + banner + back button |
| **task06** | `tests/` | Unit test `list_all()` + Integration test API + mock UI flow |

## 7. Batasan & Keputusan

| Keputusan | Alasan |
|---|---|
| **Dropdown di sidebar (bukan list panjang)** | Hemat ruang sidebar, UX lebih bersih. 10 session cukup untuk quick-access. |
| **Modal dialog untuk "Lihat Semua"** | Feedback user: popup di tengah layar lebih natural daripada halaman terpisah. Menggunakan `@st.dialog()`. |
| **Session lama tidak bisa resume chat** | Membutuhkan reload context LLM yang kompleks. Untuk MVP, cukup view-only. |
| **Title auto dari 40 char pesan pertama** | Lebih simpel dari AI-generated title. Cukup deskriptif untuk identifikasi. |
| **1 active session per instance (untuk sekarang)** | Belum ada user management. Ketika login ditambahkan, aturan menjadi per-user tanpa perubahan arsitektur. |
| **`@st.dialog` (Streamlit ≥ 1.35)** | Sudah tersedia di `streamlit>=1.38.0` yang ada di `requirements.txt`. |
