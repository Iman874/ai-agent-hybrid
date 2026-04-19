# streamlit_app/utils/formatters.py
"""Text and document formatting utilities.

DEPRECATED (beta 0.1.10): Export functions have been centralized to
the backend service at app/services/document_exporter.py.
Use the API endpoint GET /api/v1/export/{session_id} instead.
"""

import warnings
import io
import markdown
from xhtml2pdf import pisa


def export_to_pdf(md_text: str) -> bytes:
    """Convert markdown text ke PDF bytes.

    DEPRECATED: Gunakan backend API endpoint /api/v1/export/{session_id}?format=pdf

    Args:
        md_text: Markdown source text

    Returns:
        bytes: PDF binary data (kosong jika error)
    """
    warnings.warn(
        "export_to_pdf() is deprecated. Use backend API /api/v1/export/ instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    styled = f"""<html><head><style>
        body {{ font-family: 'Inter', Helvetica, Arial, sans-serif;
               font-size: 12pt; line-height: 1.5; color: #222; }}
        h1 {{ font-size: 18pt; text-align: center; margin-bottom: 20px; }}
        h2 {{ font-size: 14pt; border-bottom: 1px solid #ccc;
              padding-bottom: 5px; margin-top: 25px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f4f4f4; }}
    </style></head><body>{html}</body></html>"""
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(styled), dest=result)
    return b"" if pisa_status.err else result.getvalue()
