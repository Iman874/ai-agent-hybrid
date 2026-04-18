import aiosqlite
import logging
from pathlib import Path

logger = logging.getLogger("ai-agent-hybrid.db")

MIGRATION_DIR = Path(__file__).parent / "migrations"


async def init_db(db_path: str) -> None:
    """
    Inisialisasi database:
    1. Buat folder parent jika belum ada
    2. Connect ke SQLite
    3. Aktifkan WAL mode
    4. Jalankan semua file migration
    """
    # Auto-create parent directory
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # Enable WAL mode untuk concurrent access
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.execute("PRAGMA busy_timeout=5000")

        # Run semua migration files secara berurutan
        migration_files = sorted(MIGRATION_DIR.glob("*.sql"))
        for migration_file in migration_files:
            sql = migration_file.read_text(encoding="utf-8")
            await db.executescript(sql)
            logger.info(f"Migration applied: {migration_file.name}")

        await db.commit()
        logger.info(f"Database initialized at: {db_path}")


async def get_db_connection(db_path: str) -> aiosqlite.Connection:
    """Get a database connection (caller harus close sendiri)."""
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON")
    return db
