# Task 07: UI — Custom CSS Dark Theme

## Deskripsi
Injeksi custom CSS ke Streamlit untuk menghasilkan tampilan dark modern yang professional, mirip ChatGPT. Fokus pada warna, tipografi, spacing, dan chat bubble styling.

## Tujuan Teknis
1. Dark background (bukan Streamlit default white)
2. Sidebar dark dengan border yang jelas
3. Chat bubbles dengan rounded corners dan warna berbeda user/assistant
4. Button styling modern (rounded, hover effects)
5. Typography bersih (Inter/system fonts)
6. Progress bar dan metrics yang lebih stylish

## Scope
- **Dikerjakan**:
  - Blok `st.markdown("""<style>...</style>""", unsafe_allow_html=True)` di awal app
  - Dark theme: background, sidebar, chat area
  - Chat bubble styling
  - Button hover effects
  - Font overrides
  - Expander styling
  - Metric card styling
- **Tidak dikerjakan**:
  - Logika/fungsi baru
  - Layout changes (sudah di task05)

## Langkah Implementasi

### Step 1: Buat CSS block di awal `streamlit_app.py`

```python
def inject_custom_css():
    st.markdown("""
    <style>
        /* === GLOBAL === */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        /* === MAIN BACKGROUND === */
        .stApp {
            background-color: #0d1117;
            color: #e6edf3;
        }

        /* === SIDEBAR === */
        section[data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #30363d;
        }

        section[data-testid="stSidebar"] .stMarkdown {
            color: #c9d1d9;
        }

        /* === CHAT MESSAGES === */
        .stChatMessage {
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 8px;
        }

        /* User message */
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background-color: #1c2333;
            border: 1px solid #30363d;
        }

        /* Assistant message */
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            background-color: #0d1117;
            border: 1px solid #21262d;
        }

        /* === BUTTONS === */
        .stButton button {
            border-radius: 8px;
            background-color: #21262d;
            color: #c9d1d9;
            border: 1px solid #30363d;
            transition: all 0.2s ease;
            font-weight: 500;
        }

        .stButton button:hover {
            background-color: #30363d;
            border-color: #58a6ff;
            color: #ffffff;
        }

        /* Primary buttons */
        .stButton button[kind="primary"] {
            background-color: #238636;
            border-color: #2ea043;
        }

        /* === EXPANDERS === */
        .streamlit-expanderHeader {
            background-color: #161b22;
            border-radius: 8px;
            color: #c9d1d9;
        }

        /* === INPUTS === */
        .stTextInput input, .stTextArea textarea {
            background-color: #0d1117;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 8px;
        }

        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #58a6ff;
            box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.15);
        }

        /* === CHAT INPUT === */
        .stChatInput {
            border-radius: 12px;
        }

        .stChatInput textarea {
            background-color: #161b22 !important;
            color: #e6edf3 !important;
            border: 1px solid #30363d !important;
            border-radius: 12px !important;
        }

        /* === METRICS === */
        [data-testid="stMetricValue"] {
            color: #58a6ff;
            font-size: 1.2rem;
            font-weight: 600;
        }

        [data-testid="stMetricLabel"] {
            color: #8b949e;
        }

        /* === PROGRESS BAR === */
        .stProgress > div > div {
            background-color: #238636;
            border-radius: 4px;
        }

        /* === DIVIDERS === */
        hr {
            border-color: #21262d;
        }

        /* === SELECTBOX / RADIO === */
        .stSelectbox, .stRadio {
            color: #c9d1d9;
        }

        /* === DOWNLOAD BUTTON === */
        .stDownloadButton button {
            background-color: #0d419d;
            border-color: #1f6feb;
            color: white;
        }

        .stDownloadButton button:hover {
            background-color: #1f6feb;
        }

        /* === ALERTS === */
        .stSuccess { border-left-color: #238636; }
        .stWarning { border-left-color: #d29922; }
        .stError { border-left-color: #f85149; }
        .stInfo { border-left-color: #58a6ff; }

        /* === SCROLLBAR === */
        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #0d1117;
        }
        ::-webkit-scrollbar-thumb {
            background: #30363d;
            border-radius: 3px;
        }
    </style>
    """, unsafe_allow_html=True)
```

### Step 2: Call di awal app

```python
# Setelah st.set_page_config()
inject_custom_css()
```

## Output yang Diharapkan
- App terlihat dark dan modern
- Chat bubbles rounded dan berwarna berbeda
- Buttons punya hover effect
- Sidebar jelas terpisah dari main area
- Keseluruhan terasa "premium" dan professional

## Dependencies
- Task 05 (Layout harus sudah di-refactor dulu agar CSS targeting benar)

## Acceptance Criteria
- [ ] Background dark (#0d1117 atau sejenisnya)
- [ ] Sidebar dark dengan border
- [ ] Chat bubble user vs assistant berbeda warna
- [ ] Buttons rounded dengan hover effect
- [ ] Input fields styled (dark bg, light text)
- [ ] Progress bar berwarna hijau
- [ ] Font Inter loaded dari Google Fonts
- [ ] Scrollbar styled minimal
- [ ] Tidak ada elemen "blink" atau broken akibat CSS

## Estimasi
Medium
