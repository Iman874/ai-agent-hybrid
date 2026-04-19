# streamlit_app/utils/icons.py
"""Material Symbols helper functions.

Semua fungsi menghasilkan HTML string untuk digunakan dengan
st.markdown(..., unsafe_allow_html=True).

Referensi icon: https://fonts.google.com/icons
Font family: Material Symbols Outlined
"""


def mi(
    name: str,
    size: int = 20,
    color: str | None = None,
    filled: bool = False,
) -> str:
    """Render Material Symbol icon sebagai inline HTML <span>.

    Args:
        name: Nama icon (e.g. "chat", "auto_awesome", "check_circle")
        size: Ukuran font dalam pixel (default: 20)
        color: CSS color value (e.g. "#3fb950", "var(--color-success)")
        filled: Jika True, icon ditampilkan dengan fill solid

    Returns:
        HTML string: <span class="material-symbols-outlined" ...>name</span>

    Example:
        >>> mi("check_circle", 24, "var(--color-success)", filled=True)
        '<span class="material-symbols-outlined" style="font-size:24px;...">check_circle</span>'
    """
    style_parts = [f"font-size:{size}px", "vertical-align:middle"]
    if color:
        style_parts.append(f"color:{color}")
    if filled:
        style_parts.append("font-variation-settings:'FILL' 1")
    style = ";".join(style_parts)
    return f'<span class="material-symbols-outlined" style="{style}">{name}</span>'


def mi_inline(
    name: str,
    text: str,
    size: int = 20,
    gap: int = 6,
    color: str | None = None,
    filled: bool = False,
) -> str:
    """Render Material Icon + teks dalam satu baris inline-flex.

    Args:
        name: Nama icon Material Symbol
        text: Teks yang ditampilkan di samping icon
        size: Ukuran icon (px)
        gap: Jarak antara icon dan teks (px)
        color: Warna icon (CSS value)
        filled: Icon filled atau outlined

    Returns:
        HTML string dengan flex container

    Example:
        >>> mi_inline("smart_toy", "TOR Generator", 24)
        '<span style="display:inline-flex;..."><span ...>smart_toy</span> TOR Generator</span>'
    """
    icon = mi(name, size, color, filled)
    return (
        f'<span style="display:inline-flex;align-items:center;gap:{gap}px;">'
        f'{icon} {text}'
        f'</span>'
    )


def banner_html(
    icon: str,
    text: str,
    variant: str = "info",
    icon_size: int = 20,
) -> str:
    """Render status banner HTML (success/error/warning/info).

    Menggunakan CSS class dari components.css: .banner + .banner-{variant}

    Args:
        icon: Nama Material Symbol (e.g. "task_alt", "error", "warning")
        text: Pesan yang ditampilkan
        variant: "success" | "error" | "warning" | "info"
        icon_size: Ukuran icon (px)

    Returns:
        HTML string dengan class .banner .banner-{variant}

    Example:
        >>> banner_html("task_alt", "TOR Berhasil Dibuat!", "success")
        '<div class="banner banner-success">...<span...>task_alt</span> TOR Berhasil Dibuat!</div>'
    """
    color_map = {
        "success": "var(--color-success)",
        "error": "var(--color-error)",
        "warning": "var(--color-warning)",
        "info": "var(--color-info)",
    }
    icon_color = color_map.get(variant, color_map["info"])
    icon_html = mi(icon, icon_size, icon_color, filled=True)
    return f'<div class="banner banner-{variant}">{icon_html} {text}</div>'
