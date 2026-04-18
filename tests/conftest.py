import pytest
import pytest_asyncio
import asyncio
import os
from pathlib import Path

from app.db.database import init_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db_path(tmp_path):
    """Path ke temporary test database."""
    return str(tmp_path / "test_sessions.db")


@pytest_asyncio.fixture
async def initialized_db(test_db_path):
    """Database yang sudah di-init dengan schema."""
    await init_db(test_db_path)
    return test_db_path
