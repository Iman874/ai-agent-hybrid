import streamlit as st
import requests
import io
import markdown
from xhtml2pdf import pisa
from pathlib import Path

# --- Page Config ---
st.set_page_config(
    page_title="TOR Generator — AI Agent Hybrid",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Constants ---
API_URL = "http://localhost:8000/api/v1"
THEME_FILE = Path(__file__).parent / ".streamlit" / ".current_theme"

# --- Theme Definitions ---
THEMES = {
    "dark": {
        "base": "dark",
        "primaryColor": "#58a6ff",
        "backgroundColor": "#0d1117",
        "secondaryBackgroundColor": "#161b22",
        "textColor": "#e6edf3",
    },
    "light": {
        "base": "light",
        "primaryColor": "#0066cc",
        "backgroundColor": "#ffffff",
        "secondaryBackgroundColor": "#f5f5f5",
        "textColor": "#111111",
    },
}


def save_theme_pref(mode: str):
    """Simpan pilihan theme ke file agar persisten setelah restart."""
    THEME_FILE.write_text(mode)


def load_theme_pref() -> str:
    """Baca pilihan theme tersimpan. Default: 'system'."""
    if THEME_FILE.exists():
        val = THEME_FILE.read_text().strip()
        if val in ("system", "dark", "light"):
            return val
    return "system"


def apply_theme(mode: str):
    """Apply theme secara runtime via st._config — tanpa restart."""
    if mode == "system":
        # Streamlit default (ikuti browser/OS)
        # Kita set ke Streamlit defaults agar tidak ada override
        for key in ["base", "primaryColor", "backgroundColor",
                    "secondaryBackgroundColor", "textColor"]:
            try:
                st._config.set_option(f"theme.{key}", "")
            except Exception:
                pass
    elif mode in THEMES:
        for key, value in THEMES[mode].items():
            try:
                st._config.set_option(f"theme.{key}", value)
            except Exception:
                pass


# --- Apply theme SEBELUM render apapun ---
if "app_theme" not in st.session_state:
    st.session_state.app_theme = load_theme_pref()
apply_theme(st.session_state.app_theme)

# ============================================
# MINIMAL CSS — only truly custom elements
# ============================================
st.markdown("""
<style>
    /* Hide Streamlit branding (keep header for sidebar toggle) */
    #MainMenu, footer { visibility: hidden; }

    /* Chat bubbles — custom element */
    [data-testid="stChatMessage"] {
        border-radius: 14px;
        margin-bottom: 8px;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { border-radius: 3px; background: #30363d; }

    /* Sidebar section label */
    .sidebar-label {
        font-size: 0.70rem;
        font-weight: 700;
        letter-spacing: 0.08rem;
        opacity: 0.55;
        margin: 0.6rem 0 0.2rem 0;
    }

    /* Download buttons */
    .stDownloadButton button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ============================================
# API HELPER FUNCTIONS
# ============================================

def send_message(session_id: str | None, message: str, options: dict = None) -> dict:
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    opts = options or {}
    opts["chat_mode"] = st.session_state.get("chat_mode", "local")
    payload["options"] = opts
    try:
        resp = requests.post(f"{API_URL}/hybrid", json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "Backend tidak bisa dihubungi. Pastikan server berjalan di port 8000."}
    except requests.Timeout:
        return {"error": "Request timeout. LLM mungkin sedang sibuk, coba lagi."}
    except requests.HTTPError as e:
        try:
            return {"error": e.response.json().get("error", {}).get("message", str(e))}
        except Exception:
            return {"error": f"HTTP Error: {e.response.status_code}"}


def check_health() -> dict:
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        return resp.json()
    except Exception:
        return {"status": "unreachable"}


@st.cache_data(ttl=30)
def fetch_models() -> list[dict]:
    try:
        resp = requests.get(f"{API_URL}/models", timeout=5)
        return resp.json().get("models", [])
    except Exception:
        return []


def force_generate(session_id: str) -> dict:
    return send_message(session_id, "generate", options={"force_generate": True})


def generate_direct(data: dict) -> dict:
    parts = []
    for key, label in [
        ("judul", "Judul kegiatan"),
        ("latar_belakang", "Latar belakang"),
        ("tujuan", "Tujuan"),
        ("ruang_lingkup", "Ruang lingkup"),
        ("output", "Output/deliverable"),
        ("timeline", "Timeline"),
        ("estimasi_biaya", "Estimasi biaya"),
    ]:
        if data.get(key):
            parts.append(f"{label}: {data[key]}")
    message = "Buatkan TOR dengan data berikut:\n" + "\n".join(parts)
    return send_message(None, message, options={"force_generate": True})


def generate_from_document(file_bytes: bytes, filename: str, context: str = "") -> dict:
    try:
        resp = requests.post(
            f"{API_URL}/generate/from-document",
            files={"file": (filename, file_bytes)},
            data={"context": context},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "Backend tidak bisa dihubungi."}
    except requests.Timeout:
        return {"error": "Request timeout."}
    except requests.HTTPError as e:
        try:
            return {"error": e.response.json().get("error", {}).get("message", str(e))}
        except Exception:
            return {"error": f"HTTP Error: {e.response.status_code}"}


def handle_response(data: dict) -> bool:
    if "error" in data:
        st.error(f"❌ {data['error']}")
        return False
    st.session_state.session_id = data["session_id"]
    st.session_state.current_state = data["state"]
    st.session_state.messages.append({"role": "assistant", "content": data["message"]})
    if data.get("tor_document"):
        st.session_state.tor_document = data["tor_document"]
    if data.get("escalation_info"):
        st.session_state.escalation_info = data["escalation_info"]
    return True


def export_to_pdf(md_text: str) -> bytes:
    html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    styled = f"""<html><head><style>
        body {{ font-family: Helvetica, Arial, sans-serif; font-size: 12pt; line-height: 1.5; color: #222; }}
        h1 {{ font-size: 18pt; text-align: center; margin-bottom: 20px; }}
        h2 {{ font-size: 14pt; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 25px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f4f4f4; }}
    </style></head><body>{html}</body></html>"""
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(styled), dest=result)
    return b"" if pisa_status.err else result.getvalue()


def reset_session():
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.current_state = {
        "status": "NEW", "turn_count": 0,
        "completeness_score": 0.0,
        "filled_fields": [], "missing_fields": [],
    }
    st.session_state.tor_document = None
    st.session_state.escalation_info = None
    st.session_state.direct_tor = None
    st.session_state.doc_tor = None


# ============================================
# TOR PREVIEW COMPONENT
# ============================================

def render_tor_preview(tor: dict, escalation_info: dict = None, key_suffix: str = ""):
    st.divider()
    st.success("✅ TOR Berhasil Dibuat!")
    with st.expander("📋 Metadata", expanded=False):
        meta = tor.get("metadata", {})
        c = st.columns(4)
        c[0].metric("Model", meta.get("generated_by", "unknown"))
        c[1].metric("Mode", meta.get("mode", "standard"))
        c[2].metric("Words", meta.get("word_count", 0))
        c[3].metric("Time", f"{meta.get('generation_time_ms', 0)}ms")
    st.markdown(tor["content"])
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇️ Download (.md)", tor["content"],
            f"tor{key_suffix}.md", "text/markdown",
            use_container_width=True, key=f"dl_md{key_suffix}",
        )
    with c2:
        pdf = export_to_pdf(tor["content"])
        st.download_button(
            "⬇️ Download (.pdf)", pdf,
            f"tor{key_suffix}.pdf", "application/pdf",
            use_container_width=True, key=f"dl_pdf{key_suffix}",
            disabled=not pdf,
        )
    if escalation_info:
        st.warning(
            f"⚠️ TOR via eskalasi · **{escalation_info.get('triggered_by', '')}** · "
            f"{escalation_info.get('reason', '')}"
        )


# ============================================
# SESSION STATE INIT
# ============================================

if "session_id" not in st.session_state:
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.current_state = {
        "status": "NEW", "turn_count": 0,
        "completeness_score": 0.0,
        "filled_fields": [], "missing_fields": [],
    }
    st.session_state.tor_document = None
    st.session_state.escalation_info = None

if "direct_tor" not in st.session_state:
    st.session_state.direct_tor = None
if "doc_tor" not in st.session_state:
    st.session_state.doc_tor = None
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "local"


# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.title("🤖 TOR Generator")

    if st.button("✏️ Obrolan baru", use_container_width=True):
        reset_session()
        st.rerun()

    st.divider()

    # --- Model Selector ---
    st.markdown('<p class="sidebar-label">MODEL</p>', unsafe_allow_html=True)

    models = fetch_models()
    local_models  = [m for m in models if m["type"] == "local"  and m["status"] == "available"]
    gemini_models = [m for m in models if m["type"] == "gemini" and m["status"] == "available"]

    mode_opts, mode_map = [], {}
    if local_models:
        mode_opts.append("🖥️ Local LLM")
        mode_map["🖥️ Local LLM"] = "local"
    if gemini_models:
        mode_opts.append("✨ Gemini API")
        mode_map["✨ Gemini API"] = "gemini"

    if not mode_opts:
        st.error("Tidak ada model tersedia!")
    else:
        current_label = next(
            (lbl for lbl, m in mode_map.items() if m == st.session_state.chat_mode),
            mode_opts[0]
        )
        selected = st.radio(
            "Provider", mode_opts,
            index=mode_opts.index(current_label),
            label_visibility="collapsed",
        )
        new_mode = mode_map.get(selected, "local")

        if new_mode == "local" and local_models:
            chat_models = [
                m["id"] for m in local_models
                if "embed" not in m["id"].lower() and "nomic" not in m["id"].lower()
            ]
            if chat_models:
                st.selectbox("Model", chat_models, label_visibility="collapsed")

        if new_mode == "gemini" and gemini_models:
            st.caption(f"_{gemini_models[0]['id']}_")

        if new_mode != st.session_state.chat_mode:
            if st.session_state.session_id and st.session_state.messages:
                st.warning("⚠️ Ganti model = reset session")
                if st.button("Konfirmasi Reset", use_container_width=True):
                    st.session_state.chat_mode = new_mode
                    reset_session()
                    st.rerun()
            else:
                st.session_state.chat_mode = new_mode

    offline = [m for m in models if m["type"] == "local" and m["status"] == "offline"]
    if offline and not local_models:
        st.caption("⚠️ Ollama offline")

    st.divider()

    # --- Progress ---
    st.markdown('<p class="sidebar-label">PROGRESS</p>', unsafe_allow_html=True)
    state = st.session_state.current_state
    score = state.get("completeness_score", 0.0)
    st.progress(score, text=f"{score:.0%}")

    c1, c2 = st.columns(2)
    c1.metric("Turn", state.get("turn_count", 0))
    c2.metric("Status", state.get("status", "NEW")[:10])

    # --- Fields ---
    REQUIRED = ["judul", "latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"]
    OPTIONAL = ["estimasi_biaya"]
    filled = state.get("filled_fields", [])
    filled_count = sum(1 for f in REQUIRED if f in filled)

    with st.expander(f"📋 Fields ({filled_count}/{len(REQUIRED)})"):
        for f in REQUIRED:
            icon = "✅" if f in filled else "⭕"
            st.markdown(f"{icon} {f.replace('_', ' ').title()}")
        st.caption("_Opsional_")
        for f in OPTIONAL:
            icon = "✅" if f in filled else "◻️"
            st.markdown(f"{icon} {f.replace('_', ' ').title()}")

    # --- Force Generate (hanya tampil jika relevan) ---
    if st.session_state.session_id and not st.session_state.tor_document:
        st.divider()
        if st.button("🚀 Force Generate TOR", use_container_width=True):
            with st.spinner("Generating..."):
                data = force_generate(st.session_state.session_id)
            if handle_response(data):
                st.rerun()
    elif st.session_state.tor_document:
        st.divider()
        st.info("✅ TOR ready")

    st.divider()

    # --- System ---
    st.markdown('<p class="sidebar-label">SYSTEM</p>', unsafe_allow_html=True)
    health = check_health()
    h = health.get("status", "unreachable")
    if h == "healthy":
        st.caption("🟢 API Connected")
    elif h == "unreachable":
        st.caption("🔴 API Offline")
    else:
        st.caption(f"🟡 {h}")

    if st.session_state.session_id:
        st.caption(f"Session: `{st.session_state.session_id[:8]}...`")


# ============================================
# MAIN AREA — Header
# ============================================

col_title, col_menu = st.columns([9, 1])
with col_title:
    mode_display = "✨ Gemini" if st.session_state.chat_mode == "gemini" else "🖥️ Local"
    st.markdown(f"### TOR Generator · {mode_display}")
with col_menu:
    _OPTS = ["🖥 Ikuti Sistem", "🌙 Gelap", "☀️ Terang"]
    _MAP  = {"🖥 Ikuti Sistem": "system", "🌙 Gelap": "dark", "☀️ Terang": "light"}
    _REV  = {v: k for k, v in _MAP.items()}
    with st.popover("⋮"):
        st.caption("Tampilan")
        theme_pick = st.radio(
            "theme",
            _OPTS,
            index=_OPTS.index(_REV.get(st.session_state.app_theme, "🖥 Ikuti Sistem")),
            label_visibility="collapsed",
        )
        new_theme = _MAP[theme_pick]
        if new_theme != st.session_state.app_theme:
            st.session_state.app_theme = new_theme
            save_theme_pref(new_theme)
            apply_theme(new_theme)
            st.rerun()  # instant — tidak crash


# ============================================
# MAIN AREA — TABS
# ============================================

tab_chat, tab_direct, tab_document = st.tabs([
    "💬 Chat", "🚀 Gemini Direct", "📄 Dari Dokumen"
])


# === TAB: CHAT ===
with tab_chat:
    if not st.session_state.messages and not st.session_state.tor_document:
        st.markdown("")
        st.markdown("")
        st.markdown(
            "<h3 style='text-align:center; opacity:0.5;'>Ceritakan kebutuhan TOR Anda di sini 👇</h3>",
            unsafe_allow_html=True,
        )
        st.markdown("")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.tor_document:
        render_tor_preview(
            st.session_state.tor_document,
            st.session_state.escalation_info,
            key_suffix="_hybrid",
        )

    if prompt := st.chat_input("Tanyakan apa saja"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.spinner("🤔 AI sedang berpikir..."):
            data = send_message(st.session_state.session_id, prompt)
        if handle_response(data):
            st.rerun()


# === TAB: GEMINI DIRECT ===
with tab_direct:
    st.subheader("🚀 Generate TOR Langsung")
    st.caption("Isi field, Gemini langsung membuat TOR tanpa proses chat.")

    with st.form("gemini_direct_form"):
        judul  = st.text_input("Judul Kegiatan *", placeholder="Workshop Penerapan AI untuk ASN")
        latar  = st.text_area("Latar Belakang *", placeholder="Konteks dan alasan kegiatan...", height=100)
        tujuan = st.text_area("Tujuan *", placeholder="Apa yang ingin dicapai...", height=80)
        scope  = st.text_area("Ruang Lingkup", placeholder="Batasan cakupan pekerjaan...", height=80)
        output_f = st.text_area("Output / Deliverable", placeholder="Deliverable yang diharapkan...", height=80)
        timeline = st.text_input("Timeline", placeholder="3 hari, 15-17 Juli 2026")
        biaya  = st.text_input("Estimasi Biaya", placeholder="Rp 50.000.000")
        submitted = st.form_submit_button("🚀 Generate TOR", use_container_width=True)

    if submitted:
        if not judul or not tujuan:
            st.error("❌ Minimal isi **Judul** dan **Tujuan**!")
        else:
            with st.spinner("🔨 Generating..."):
                result = generate_direct({
                    "judul": judul.strip() or None,
                    "latar_belakang": latar.strip() or None,
                    "tujuan": tujuan.strip() or None,
                    "ruang_lingkup": scope.strip() or None,
                    "output": output_f.strip() or None,
                    "timeline": timeline.strip() or None,
                    "estimasi_biaya": biaya.strip() or None,
                })
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.session_state.direct_tor = result.get("tor_document") or result
                st.rerun()

    if st.session_state.direct_tor:
        render_tor_preview(st.session_state.direct_tor, key_suffix="_direct")
        if st.button("🔄 Generate Ulang", key="reset_direct"):
            st.session_state.direct_tor = None
            st.rerun()


# === TAB: FROM DOCUMENT ===
with tab_document:
    st.subheader("📄 Generate TOR dari Dokumen")
    st.caption("Upload dokumen sumber, Gemini otomatis membuat TOR.")

    uploaded_file = st.file_uploader(
        "Upload dokumen",
        type=["pdf", "txt", "md", "docx"],
        help="Format: PDF, TXT, MD, DOCX. Maks 20MB.",
    )
    doc_context = st.text_area(
        "Konteks tambahan (opsional)",
        placeholder="Contoh: Ini lanjutan workshop tahun lalu...",
        height=100,
    )

    if st.button("🚀 Generate TOR", use_container_width=True, disabled=uploaded_file is None):
        if uploaded_file:
            with st.spinner("🔨 Membaca dokumen..."):
                result = generate_from_document(uploaded_file.read(), uploaded_file.name, doc_context)
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.session_state.doc_tor = result.get("tor_document", result)
                st.rerun()

    if st.session_state.doc_tor:
        render_tor_preview(st.session_state.doc_tor, key_suffix="_doc")
        if st.button("🔄 Generate Ulang", key="reset_doc"):
            st.session_state.doc_tor = None
            st.rerun()
