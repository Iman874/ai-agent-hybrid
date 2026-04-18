import hashlib
import logging
from datetime import datetime
from pathlib import Path

from app.models.rag import Document, DocumentMetadata
from app.utils.errors import UnsupportedFormatError

logger = logging.getLogger("ai-agent-hybrid.rag.loader")


class DocumentLoader:
    """Load dokumen dari filesystem atau uploaded bytes."""

    SUPPORTED_EXTENSIONS = {".md", ".txt"}

    def load_from_directory(self, dir_path: str, category: str) -> list[Document]:
        """Load semua file yang didukung dari directory (recursive)."""
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Directory tidak ditemukan: {dir_path}")

        documents = []
        for file_path in sorted(path.rglob("*")):
            if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                try:
                    doc = self._load_file(file_path, category)
                    documents.append(doc)
                    logger.debug(f"Loaded: {file_path.name} ({doc.metadata.char_count} chars)")
                except Exception as e:
                    logger.warning(f"Gagal load file {file_path.name}: {e}")

        logger.info(f"Loaded {len(documents)} documents from {dir_path}")
        return documents

    def load_from_upload(self, filename: str, content: bytes, category: str) -> Document:
        """Load dari bytes hasil upload API."""
        ext = Path(filename).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported format: {filename}")
            raise UnsupportedFormatError(filename, self.SUPPORTED_EXTENSIONS)

        text = content.decode("utf-8")
        doc = self._create_document(filename, text, ext, category)
        logger.debug(f"Loaded from upload: {filename} ({doc.metadata.char_count} chars)")
        return doc

    def _load_file(self, path: Path, category: str) -> Document:
        text = path.read_text(encoding="utf-8")
        return self._create_document(path.name, text, path.suffix.lower(), category)

    def _load_file_by_path(self, file_path: str, category: str) -> Document:
        """Load dari absolute/relative path string."""
        path = Path(file_path)
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFormatError(path.name, self.SUPPORTED_EXTENSIONS)
        return self._load_file(path, category)

    def _create_document(
        self, filename: str, text: str, ext: str, category: str
    ) -> Document:
        doc_id = hashlib.sha256(
            f"{filename}:{text[:100]}".encode()
        ).hexdigest()[:16]

        return Document(
            id=doc_id,
            content=text,
            metadata=DocumentMetadata(
                source=filename,
                category=category,
                file_type=ext.lstrip("."),
                char_count=len(text),
                loaded_at=datetime.utcnow(),
            ),
        )
