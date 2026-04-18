# Task 09 — CostController: Rate Limiting untuk Gemini API

## 1. Judul Task

Implementasikan `CostController` — class yang menegakkan batas panggilan Gemini per session dan per jam, serta logging setiap API call.

## 2. Deskripsi

Gemini punya biaya per token dan free tier limit. CostController mencegah penyalahgunaan dengan membatasi max call per session (default 3) dan max call per hour (default 20). Juga men-log setiap call ke `gemini_call_log` untuk auditing.

## 3. Tujuan Teknis

- `check(session_id)` — raise `RateLimitError` jika melebihi batas
- `log_call(...)` — insert record ke `gemini_call_log`
- Gunakan `SessionManager.get()` untuk cek `gemini_calls_count` per session
- Query `gemini_call_log` untuk cek global hourly count

## 4. Scope

### Yang dikerjakan
- `app/core/cost_controller.py` — class `CostController`

### Yang tidak dikerjakan
- UI untuk menampilkan usage
- Billing integration

## 5. Langkah Implementasi

### Step 1: Buat `app/core/cost_controller.py`

```python
import logging
from datetime import datetime, timedelta
import aiosqlite

from app.core.session_manager import SessionManager
from app.config import Settings
from app.utils.errors import RateLimitError

logger = logging.getLogger("ai-agent-hybrid.cost")


class CostController:
    """Rate limiting dan cost tracking untuk Gemini API calls."""

    def __init__(self, session_mgr: SessionManager, settings: Settings):
        self.session_mgr = session_mgr
        self.db_path = session_mgr.db_path
        self.max_per_session = settings.max_gemini_calls_per_session
        self.max_per_hour = settings.max_gemini_calls_per_hour

    async def check(self, session_id: str) -> None:
        """Raise RateLimitError jika melebihi batas."""
        # Check per-session limit
        session = await self.session_mgr.get(session_id)
        if session.gemini_calls_count >= self.max_per_session:
            raise RateLimitError(
                f"Batas {self.max_per_session} panggilan Gemini per session tercapai.",
                details=f"session_id: {session_id}, calls: {session.gemini_calls_count}"
            )

        # Check global hourly limit
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM gemini_call_log WHERE called_at > ? AND success = TRUE",
                (one_hour_ago.isoformat(),)
            )
            row = await cursor.fetchone()
            hourly_count = row[0]

        if hourly_count >= self.max_per_hour:
            raise RateLimitError(
                f"Batas {self.max_per_hour} panggilan Gemini per jam tercapai. "
                "Coba lagi dalam beberapa menit.",
                details=f"hourly_count: {hourly_count}"
            )

        logger.debug(
            f"Cost check passed: session={session.gemini_calls_count}/{self.max_per_session}, "
            f"hourly={hourly_count}/{self.max_per_hour}"
        )

    async def log_call(
        self, session_id: str, model: str, mode: str,
        prompt_tokens: int, completion_tokens: int,
        duration_ms: int, success: bool, error_msg: str | None = None
    ) -> None:
        """Log setiap panggilan Gemini untuk tracking."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO gemini_call_log "
                "(session_id, model, mode, prompt_tokens, completion_tokens, "
                "duration_ms, success, error_message) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, model, mode, prompt_tokens, completion_tokens,
                 duration_ms, success, error_msg)
            )
            await db.commit()
        logger.debug(
            f"Logged Gemini call: session={session_id}, model={model}, "
            f"success={success}, tokens={prompt_tokens}+{completion_tokens}"
        )
```

### Step 2: Verifikasi

```python
import asyncio, os
from app.db.database import init_db
from app.core.session_manager import SessionManager
from app.core.cost_controller import CostController
from app.config import Settings
from app.utils.errors import RateLimitError

TEST_DB = "./data/test_cost.db"

async def test():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    await init_db(TEST_DB)

    settings = Settings()
    settings.max_gemini_calls_per_session = 2
    session_mgr = SessionManager(TEST_DB)
    cost = CostController(session_mgr, settings)

    # Create session
    session = await session_mgr.create()

    # Test 1: Check passes (0 calls)
    await cost.check(session.id)
    print("Test 1: cost check OK (0 calls)")

    # Test 2: Log call
    await cost.log_call(session.id, "gemini-2.0-flash", "standard", 100, 200, 1500, True)
    print("Test 2: log call OK")

    # Test 3: After 2 calls, should raise
    await session_mgr.update(session.id, gemini_calls_count=2)
    try:
        await cost.check(session.id)
        assert False, "Should have raised"
    except RateLimitError as e:
        assert e.code == "E003"
        print(f"Test 3: rate limit OK — {e.message}")

    os.remove(TEST_DB)
    print("ALL COST CONTROLLER TESTS PASSED")

asyncio.run(test())
```

## 6. Output yang Diharapkan

```
Test 1: cost check OK (0 calls)
Test 2: log call OK
Test 3: rate limit OK — Batas 2 panggilan Gemini per session tercapai.
ALL COST CONTROLLER TESTS PASSED
```

## 7. Dependencies

- **Task 02** — `RateLimitError`
- **Task 03** — `gemini_call_log` table
- **beta0.1.0** — `SessionManager`, `Settings`

## 8. Acceptance Criteria

- [ ] `check()` pass jika session calls < max dan hourly calls < max
- [ ] `check()` raise `RateLimitError` jika session limit tercapai
- [ ] `check()` raise `RateLimitError` jika hourly limit tercapai
- [ ] `log_call()` insert record ke `gemini_call_log`
- [ ] Error call di-log dengan `success=False` dan `error_message`

## 9. Estimasi

**Medium** — ~1.5 jam
