#!/usr/bin/env python3
"""
CLI Script: Batch Ingest Documents ke RAG Vector Database

Usage:
    python scripts/ingest_documents.py \
        --dir data/documents/examples \
        --category tor_example

    python scripts/ingest_documents.py \
        --dir data/documents/ \
        --category guideline
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Tambahkan root project ke sys.path agar import app.* bisa berjalan
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Settings
from app.db.database import init_db
from app.rag.pipeline import RAGPipeline
from app.rag.document_tracker import RAGDocumentTracker

VALID_CATEGORIES = ["tor_template", "tor_example", "guideline"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Batch ingest dokumen TOR ke ChromaDB vector database."
    )
    parser.add_argument(
        "--dir", required=True,
        help="Path ke folder yang berisi dokumen .md atau .txt"
    )
    parser.add_argument(
        "--category", required=True,
        choices=VALID_CATEGORIES,
        help=f"Kategori dokumen: {', '.join(VALID_CATEGORIES)}"
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Override chromadb path (default: dari .env / config)"
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    print(f"=== RAG Batch Ingest ===")
    print(f"Directory  : {args.dir}")
    print(f"Category   : {args.category}")

    # Validasi directory
    dir_path = Path(args.dir)
    if not dir_path.exists():
        print(f"ERROR: Directory tidak ditemukan: {args.dir}")
        sys.exit(1)

    if not dir_path.is_dir():
        print(f"ERROR: Path bukan directory: {args.dir}")
        sys.exit(1)

    # Init settings
    settings = Settings()
    if args.db_path:
        settings.chroma_db_path = args.db_path
        print(f"ChromaDB   : {args.db_path} (override)")
    else:
        print(f"ChromaDB   : {settings.chroma_db_path}")

    # Init database
    print("\nInitializing database...")
    await init_db(settings.session_db_path)
    tracker = RAGDocumentTracker(settings.session_db_path)

    # Cari file-file yang akan di-ingest
    supported_exts = {".md", ".txt"}
    files = sorted([
        str(f) for f in dir_path.rglob("*")
        if f.is_file() and f.suffix.lower() in supported_exts
    ])

    if not files:
        print(f"WARNING: Tidak ada file .md atau .txt ditemukan di {args.dir}")
        sys.exit(0)

    print(f"\nDitemukan {len(files)} file:")
    for f in files:
        print(f"  - {f}")

    # Init RAG pipeline
    print("\nInitializing RAG pipeline...")
    pipeline = RAGPipeline(settings)

    # Ingest
    print(f"\nIngesting {len(files)} files...")
    result = await pipeline.ingest_files(files, args.category)

    # Update Tracking for ingested files
    print("\nUpdating SQLite Tracking metadata...")
    for detail in result.details:
        if detail.status == "ingested":
            # For local files, we'll hash the filename to find doc_id as simple bypass,
            # or just use details from loader since we don't have the doc_id returned easily.
            # actually we don't have doc_id exposed directly from `result`, tracking should ideally 
            # be inside `ingest_files` or we generate id similarly.
            doc_id = detail.filename # simple fallback for now if not tracked in pipeline internals
            await tracker.upsert(
                doc_id=doc_id,
                filename=detail.filename,
                category=args.category,
                file_type=detail.filename.split('.')[-1],
                char_count=detail.char_count,
                chunk_count=detail.chunks
            )

    # Print summary
    print("\n=== Ingest Summary ===")
    print(f"Status           : {result.status}")
    print(f"Files ingested   : {result.ingested_files}")
    print(f"Total chunks     : {result.total_chunks}")
    print(f"Collection size  : {result.collection_size} chunks (total)")
    print("\nDetail per file:")
    for detail in result.details:
        status_icon = "v" if detail.status == "ingested" else "x"
        print(f"  {status_icon} {detail.filename} -> {detail.chunks} chunks [{detail.status}]")

    print("\nDone!")


if __name__ == "__main__":
    import os
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
