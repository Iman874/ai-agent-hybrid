import streamlit as st
import requests
import io
import markdown
from xhtml2pdf import pisa

# --- Page Config ---
st.set_page_config(
    page_title="TOR Generator — AI Agent Hybrid",
    page_icon="🤖",
    layout="wide",
)

# --- Constants ---
API_URL = "http://localhost:8000/api/v1"


# ============================================
# API HELPER FUNCTIONS
# ============================================

def send_message(session_id: str | None, message: str, options: dict = None) -> dict:
    """Kirim pesan ke hybrid endpoint."""
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    if options:
        payload["options"] = options

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
            error_data = e.response.json()
            return {"error": error_data.get("error", {}).get("message", str(e))}
        except Exception:
            return {"error": f"HTTP Error: {e.response.status_code}"}


def check_health() -> dict:
    """Cek status backend."""
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        return resp.json()
    except Exception:
        return {"status": "unreachable"}


def force_generate(session_id: str) -> dict:
    """Force generate TOR."""
    return send_message(session_id, "generate", options={"force_generate": True})


def generate_direct(data: dict) -> dict:
    """Generate TOR langsung via hybrid endpoint dengan data lengkap."""
    # Compose a comprehensive message from form data
    parts = []
    if data.get("judul"):
        parts.append(f"Judul kegiatan: {data['judul']}")
    if data.get("latar_belakang"):
        parts.append(f"Latar belakang: {data['latar_belakang']}")
    if data.get("tujuan"):
        parts.append(f"Tujuan: {data['tujuan']}")
    if data.get("ruang_lingkup"):
        parts.append(f"Ruang lingkup: {data['ruang_lingkup']}")
    if data.get("output"):
        parts.append(f"Output/deliverable: {data['output']}")
    if data.get("timeline"):
        parts.append(f"Timeline: {data['timeline']}")
    if data.get("estimasi_biaya"):
        parts.append(f"Estimasi biaya: {data['estimasi_biaya']}")

    message = "Buatkan TOR dengan data berikut:\n" + "\n".join(parts)

    # Send via hybrid with force_generate to skip chat
    return send_message(None, message, options={"force_generate": True})


def generate_from_document(file_bytes: bytes, filename: str, context: str = "") -> dict:
    """Upload file & generate TOR via document endpoint."""
    try:
        files = {"file": (filename, file_bytes)}
        data = {"context": context}
        resp = requests.post(
            f"{API_URL}/generate/from-document",
            files=files,
            data=data,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "Backend tidak bisa dihubungi."}
    except requests.Timeout:
        return {"error": "Request timeout. Dokumen mungkin terlalu besar atau LLM sibuk."}
    except requests.HTTPError as e:
        try:
            error_data = e.response.json()
            return {"error": error_data.get("error", {}).get("message", str(e))}
        except Exception:
            return {"error": f"HTTP Error: {e.response.status_code}"}


def handle_response(data: dict) -> bool:
    """Process API response dan update session state. Return True jika sukses."""
    if "error" in data:
        st.error(f"❌ {data['error']}")
        return False

    st.session_state.session_id = data["session_id"]
    st.session_state.current_state = data["state"]

    st.session_state.messages.append({
        "role": "assistant",
        "content": data["message"],
    })

    if data.get("tor_document"):
        st.session_state.tor_document = data["tor_document"]

    if data.get("escalation_info"):
        st.session_state.escalation_info = data["escalation_info"]

    return True


def export_to_pdf(md_text: str) -> bytes:
    """Konversi Markdown ke format PDF menggunakan xhtml2pdf."""
    html_content = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
    styled_html = f"""
    <html>
    <head>
    <style>
        body {{
            font-family: Helvetica, Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.5;
            color: #222;
        }}
        h1 {{ font-size: 18pt; color: #111; text-align: center; margin-bottom: 20px; }}
        h2 {{ font-size: 14pt; color: #333; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 25px; }}
        h3 {{ font-size: 12pt; color: #444; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 15px; margin-bottom: 15px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        p {{ margin-bottom: 10px; }}
    </style>
    </head>
    <body>
    {html_content}
    </body>
    </html>
    """
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(styled_html), dest=result)
    
    if pisa_status.err:
        return b""
    return result.getvalue()


# ============================================
# TOR PREVIEW COMPONENT (reusable)
# ============================================

def render_tor_preview(tor: dict, escalation_info: dict = None, key_suffix: str = ""):
    """Render TOR preview with metadata, download, and escalation warning."""
    st.divider()
    st.success("✅ TOR Berhasil Dibuat!")

    # Metadata expander
    with st.expander("📋 Metadata", expanded=False):
        meta = tor.get("metadata", {})
        cols = st.columns(4)
        cols[0].metric("Model", meta.get("generated_by", "unknown"))
        cols[1].metric("Mode", meta.get("mode", "standard"))
        cols[2].metric("Words", meta.get("word_count", 0))
        cols[3].metric("Time", f"{meta.get('generation_time_ms', 0)}ms")

    # TOR Content (rendered markdown)
    st.markdown(tor["content"])

    # Download buttons
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="⬇️ Download TOR (.md)",
            data=tor["content"],
            file_name=f"tor_document{key_suffix}.md",
            mime="text/markdown",
            use_container_width=True,
            key=f"download_md{key_suffix}",
        )
        
    with col2:
        pdf_bytes = export_to_pdf(tor["content"])
        st.download_button(
            label="⬇️ Download TOR (.pdf)",
            data=pdf_bytes,
            file_name=f"tor_document{key_suffix}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"download_pdf{key_suffix}",
            disabled=not pdf_bytes,
        )

    # Escalation warning
    if escalation_info:
        st.warning(
            f"⚠️ TOR ini dibuat via eskalasi.\n\n"
            f"**Rule**: {escalation_info.get('triggered_by', 'unknown')}\n\n"
            f"**Alasan**: {escalation_info.get('reason', '')}\n\n"
            "Beberapa bagian mungkin menggunakan asumsi."
        )


# ============================================
# INIT SESSION STATE
# ============================================

if "session_id" not in st.session_state:
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

if "direct_tor" not in st.session_state:
    st.session_state.direct_tor = None

if "doc_tor" not in st.session_state:
    st.session_state.doc_tor = None


# ============================================
# SIDEBAR
# ============================================

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

    # --- Progress (Hybrid only) ---
    state = st.session_state.current_state
    st.subheader("📊 Progress")
    score = state.get("completeness_score", 0.0)
    st.progress(score, text=f"Completeness: {score:.0%}")

    col1, col2 = st.columns(2)
    col1.metric("Turn", state.get("turn_count", 0))
    status_text = state.get("status", "NEW")
    col2.metric("Status", status_text[:12])

    st.divider()

    # --- Field Tracker ---
    st.subheader("📋 Fields")
    REQUIRED = ["judul", "latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"]
    OPTIONAL = ["estimasi_biaya"]
    filled = state.get("filled_fields", [])

    for f in REQUIRED:
        if f in filled:
            st.markdown(f"✅ **{f}**")
        else:
            st.markdown(f"❌ {f}")
    for f in OPTIONAL:
        if f in filled:
            st.markdown(f"✅ **{f}** _(opsional)_")
        else:
            st.markdown(f"⬜ {f} _(opsional)_")

    # --- Force Generate ---
    if st.session_state.session_id and not st.session_state.tor_document:
        st.divider()
        if st.button("🚀 Force Generate TOR", use_container_width=True):
            with st.spinner("🔨 Generating TOR..."):
                data = force_generate(st.session_state.session_id)
            if handle_response(data):
                st.rerun()
    elif st.session_state.tor_document:
        st.divider()
        st.info("✅ TOR sudah di-generate")

    st.divider()

    # --- System ---
    st.subheader("🔧 System")
    if st.session_state.session_id:
        st.text(f"Session: {st.session_state.session_id[:8]}...")
    else:
        st.text("Session: belum dimulai")

    health = check_health()
    h_status = health.get("status", "unreachable")
    if h_status == "healthy":
        st.success("API: 🟢 Connected")
    elif h_status == "unreachable":
        st.error("API: 🔴 Offline")
    else:
        st.warning(f"API: 🟡 {h_status}")


# ============================================
# MAIN AREA — TABS
# ============================================

st.title("💬 AI TOR Generator")
st.caption("Ceritakan kebutuhan Anda, AI akan bantu menyusun dokumen TOR profesional.")

tab_hybrid, tab_direct, tab_document = st.tabs([
    "💬 Hybrid Chat", "🚀 Gemini Direct", "📄 From Document"
])

# ============================================
# TAB 1: HYBRID CHAT
# ============================================

with tab_hybrid:
    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # TOR Preview (Hybrid)
    if st.session_state.tor_document:
        render_tor_preview(
            st.session_state.tor_document,
            st.session_state.escalation_info,
            key_suffix="_hybrid",
        )

    # Chat Input
    if prompt := st.chat_input("Ketik pesan Anda..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("🤔 AI sedang berpikir..."):
            data = send_message(st.session_state.session_id, prompt)

        if handle_response(data):
            st.rerun()


# ============================================
# TAB 2: GEMINI DIRECT
# ============================================

with tab_direct:
    st.subheader("🚀 Generate TOR Langsung")
    st.caption("Isi field di bawah, Gemini akan langsung membuat TOR tanpa proses chat.")

    with st.form("gemini_direct_form"):
        judul = st.text_input(
            "Judul Kegiatan *",
            placeholder="Contoh: Workshop Penerapan AI untuk ASN",
        )
        latar_belakang = st.text_area(
            "Latar Belakang *",
            placeholder="Konteks dan alasan kegiatan ini diperlukan...",
            height=100,
        )
        tujuan = st.text_area(
            "Tujuan *",
            placeholder="Apa yang ingin dicapai...",
            height=80,
        )
        ruang_lingkup = st.text_area(
            "Ruang Lingkup",
            placeholder="Batasan dan cakupan pekerjaan...",
            height=80,
        )
        output = st.text_area(
            "Output / Deliverable",
            placeholder="Deliverable yang diharapkan...",
            height=80,
        )
        timeline = st.text_input(
            "Timeline",
            placeholder="Contoh: 3 hari, 15-17 Juli 2026",
        )
        estimasi_biaya = st.text_input(
            "Estimasi Biaya (opsional)",
            placeholder="Contoh: Rp 50.000.000",
        )

        submitted = st.form_submit_button("🚀 Generate TOR", use_container_width=True)

    if submitted:
        if not judul or not tujuan:
            st.error("❌ Minimal isi **Judul** dan **Tujuan**!")
        else:
            form_data = {
                "judul": judul.strip() or None,
                "latar_belakang": latar_belakang.strip() or None,
                "tujuan": tujuan.strip() or None,
                "ruang_lingkup": ruang_lingkup.strip() or None,
                "output": output.strip() or None,
                "timeline": timeline.strip() or None,
                "estimasi_biaya": estimasi_biaya.strip() or None,
            }
            with st.spinner("🔨 Gemini sedang membuat TOR..."):
                result = generate_direct(form_data)

            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.session_state.direct_tor = result.get("tor_document") or result
                st.rerun()

    # TOR Preview (Direct)
    if st.session_state.direct_tor:
        tor = st.session_state.direct_tor
        render_tor_preview(tor, key_suffix="_direct")

        # Reset button
        if st.button("🔄 Generate Ulang", use_container_width=True):
            st.session_state.direct_tor = None
            st.rerun()


# ============================================
# TAB 3: FROM DOCUMENT
# ============================================

with tab_document:
    st.subheader("📄 Generate TOR dari Dokumen")
    st.caption(
        "Upload dokumen sumber (laporan, proposal, notulen), "
        "Gemini akan membaca dan membuat TOR secara otomatis."
    )

    uploaded_file = st.file_uploader(
        "Upload dokumen",
        type=["pdf", "txt", "md", "docx"],
        help="Format: PDF, TXT, MD, DOCX. Maks 20MB.",
    )

    doc_context = st.text_area(
        "Konteks tambahan (opsional)",
        placeholder="Contoh: Ini lanjutan workshop tahun lalu, "
                    "target peserta sama tapi materi ditingkatkan...",
        height=100,
    )

    if st.button("🚀 Generate TOR dari Dokumen",
                  use_container_width=True,
                  disabled=uploaded_file is None):
        if uploaded_file:
            file_bytes = uploaded_file.read()
            with st.spinner("🔨 Gemini sedang membaca dan membuat TOR..."):
                result = generate_from_document(
                    file_bytes, uploaded_file.name, doc_context
                )
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.session_state.doc_tor = result.get("tor_document", result)
                st.rerun()

    # TOR Preview (Document)
    if st.session_state.doc_tor:
        render_tor_preview(st.session_state.doc_tor, key_suffix="_doc")

        if st.button("🔄 Generate Ulang", key="reset_doc", use_container_width=True):
            st.session_state.doc_tor = None
            st.rerun()
