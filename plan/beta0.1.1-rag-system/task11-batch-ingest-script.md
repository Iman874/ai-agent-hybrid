# Task 11 — Batch Ingest CLI Script

## 1. Judul Task

Buat `scripts/ingest_documents.py` — CLI script untuk batch ingest dokumen dari filesystem tanpa harus menjalankan API server.

## 2. Deskripsi

Script yang bisa dijalankan dari terminal untuk mengindex semua dokumen di folder `data/documents/` (atau folder lain yang ditentukan) ke ChromaDB. Berguna untuk initial setup sebelum server pertama kali dijalankan, atau untuk re-ingest massal.

## 3. Tujuan Teknis

- Jalankan dengan: `python scripts/ingest_documents.py --dir data/documents/examples --category tor_example`
- Support `--dir`, `--category`, dan `--help` argument
- Print progress dan summary ke console
- Inisialisasi database + RAGPipeline standalone (tanpa uvicorn)

## 4. Scope

### Yang dikerjakan
- `scripts/ingest_documents.py` — CLI batch ingest script
- `scripts/__init__.py` — (kosong)

### Yang tidak dikerjakan
- Web UI (tidak ada)
- Scheduling / cron (tidak ada di scope ini)

## 5. Langkah Implementasi

### Step 1: Buat `scripts/__init__.py`

```python
```

### Step 2: Buat `scripts/ingest_documents.py`

```python
#!/usr/bin/env python3
"""
CLI Script: Batch Ingest Documents ke RAG Vector Database

Usage:
    python scripts/ingest_documents.py \\
        --dir data/documents/examples \\
        --category tor_example

    python scripts/ingest_documents.py \\
        --dir data/documents/ \\
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

    # Print summary
    print("\n=== Ingest Summary ===")
    print(f"Status           : {result.status}")
    print(f"Files ingested   : {result.ingested_files}")
    print(f"Total chunks     : {result.total_chunks}")
    print(f"Collection size  : {result.collection_size} chunks (total)")
    print("\nDetail per file:")
    for detail in result.details:
        status_icon = "✓" if detail.status == "ingested" else "✗"
        print(f"  {status_icon} {detail.filename} → {detail.chunks} chunks [{detail.status}]")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Verifikasi (dengan dokumen contoh)

Pastikan ada minimal 1 file di `data/documents/examples/`:
```bash
# Buat file contoh jika belum ada
mkdir -p data/documents/examples
echo "# TOR Workshop AI\n\n## Latar Belakang\nIni adalah contoh TOR..." > data/documents/examples/contoh_tor.md
```

Jalankan script:
```bash
.\venv\Scripts\python.exe scripts/ingest_documents.py \
    --dir data/documents/examples \
    --category tor_example
```

## 6. Output yang Diharapkan

```
=== RAG Batch Ingest ===
Directory  : data/documents/examples
Category   : tor_example
ChromaDB   : ./data/chroma_db

Initializing database...

Ditemukan 1 file:
  - data/documents/examples/contoh_tor.md

Initializing RAG pipeline...

Ingesting 1 files...

=== Ingest Summary ===
Status           : success
Files ingested   : 1
Total chunks     : 8
Collection size  : 8 chunks (total)

Detail per file:
  ✓ contoh_tor.md → 8 chunks [ingested]

Done!
```

## 7. Dependencies

- **Task 08** — `RAGPipeline.ingest_files()`
- **Task 04 (beta0.1.0)** — `init_db()`
- **External** — Ollama + bge-m3 harus running

## 8. Acceptance Criteria

- [ ] `python scripts/ingest_documents.py --help` menampilkan usage yang jelas
- [ ] `python scripts/ingest_documents.py --dir data/documents/examples --category tor_example` berhasil dijalankan
- [ ] Setelah ingest, `GET /api/v1/rag/status` menunjukkan dokumen sudah masuk
- [ ] Jika directory tidak ditemukan → print error dan exit code 1
- [ ] Jika tidak ada file yang didukung → print warning dan exit code 0
- [ ] Summary menampilkan status per file (ingested/skipped/error)

## 9. Estimasi

**Low** — ~1 jam
