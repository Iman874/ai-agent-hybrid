import logging
from pathlib import Path
from app.utils.errors import DocumentParseError

logger = logging.getLogger("ai-agent-hybrid.document_parser")


class DocumentParser:
    """Ekstrak teks dari berbagai format dokumen."""

    SUPPORTED_FORMATS = [".pdf", ".txt", ".md", ".docx"]
    MAX_FILE_SIZE_MB = 20
    MIN_TEXT_LENGTH = 50

    @staticmethod
    async def parse(file_bytes: bytes, filename: str) -> str:
        """Parse file bytes ke plain text."""
        ext = Path(filename).suffix.lower()

        # Validate extension
        if ext not in DocumentParser.SUPPORTED_FORMATS:
            raise DocumentParseError(
                message=f"Format '{ext}' tidak didukung.",
                details=f"Format yang didukung: {', '.join(DocumentParser.SUPPORTED_FORMATS)}",
            )

        # Validate size
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > DocumentParser.MAX_FILE_SIZE_MB:
            raise DocumentParseError(
                message=f"File terlalu besar: {size_mb:.1f}MB (maks {DocumentParser.MAX_FILE_SIZE_MB}MB).",
            )

        # Parse based on extension
        if ext in (".txt", ".md"):
            text = DocumentParser._parse_text(file_bytes)
        elif ext == ".pdf":
            text = DocumentParser._parse_pdf(file_bytes)
        elif ext == ".docx":
            text = DocumentParser._parse_docx(file_bytes)

        # Validate content
        if len(text.strip()) < DocumentParser.MIN_TEXT_LENGTH:
            raise DocumentParseError(
                message="Dokumen terlalu pendek atau kosong.",
                details=f"Minimal {DocumentParser.MIN_TEXT_LENGTH} karakter.",
            )

        logger.info(f"Parsed '{filename}': {len(text)} chars")
        return text.strip()

    @staticmethod
    def _parse_text(file_bytes: bytes) -> str:
        """Parse TXT/MD file."""
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return file_bytes.decode("latin-1")
            except Exception:
                raise DocumentParseError(message="Tidak bisa membaca encoding file.")

    @staticmethod
    def _parse_pdf(file_bytes: bytes) -> str:
        """Extract text dari PDF via pypdf."""
        import io
        from pypdf import PdfReader

        try:
            reader = PdfReader(io.BytesIO(file_bytes))
        except Exception as e:
            raise DocumentParseError(
                message="Tidak bisa membaca file PDF.",
                details=str(e)[:200],
            )

        if reader.is_encrypted:
            raise DocumentParseError(
                message="PDF terproteksi password. Hapus proteksi dulu.",
            )

        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text.strip())

        if not pages:
            raise DocumentParseError(
                message="Tidak bisa mengekstrak teks dari PDF. "
                        "Kemungkinan PDF ini berisi scan/gambar (bukan teks).",
            )

        return "\n\n".join(pages)

    @staticmethod
    def _parse_docx(file_bytes: bytes) -> str:
        """Extract text dari DOCX via python-docx."""
        import io
        from docx import Document

        try:
            doc = Document(io.BytesIO(file_bytes))
        except Exception as e:
            raise DocumentParseError(
                message="Tidak bisa membaca file DOCX.",
                details=str(e)[:200],
            )

        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

        if not paragraphs:
            raise DocumentParseError(
                message="Dokumen DOCX kosong atau tidak berisi teks.",
            )

        return "\n\n".join(paragraphs)
