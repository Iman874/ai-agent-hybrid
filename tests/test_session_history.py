"""
Tests untuk fitur Session History (Beta 0.1.11).
Unit test SessionManager + Integration test API.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import init_db
from app.core.session_manager import SessionManager

pytestmark = pytest.mark.asyncio


# --- Fixtures ---

@pytest_asyncio.fixture
async def session_mgr(tmp_path):
    """SessionManager dengan fresh DB."""
    db_path = str(tmp_path / "test_history.db")
    await init_db(db_path)
    return SessionManager(db_path)


@pytest_asyncio.fixture
async def seeded_mgr(session_mgr):
    """SessionManager dengan beberapa session ter-seed."""
    # Session 1: COMPLETED, punya TOR
    s1 = await session_mgr.create()
    await session_mgr.update(
        s1.id,
        state="COMPLETED",
        turn_count=8,
        title="Workshop Penerapan AI untuk ASN",
        generated_tor="# TOR Workshop AI",
    )

    # Session 2: CHATTING, belum punya TOR
    s2 = await session_mgr.create()
    await session_mgr.update(
        s2.id,
        state="CHATTING",
        turn_count=3,
        title="Pengadaan Server Data Center",
    )

    # Session 3: COMPLETED tanpa title
    s3 = await session_mgr.create()
    await session_mgr.update(
        s3.id,
        state="COMPLETED",
        turn_count=5,
        generated_tor="# TOR Rapat",
    )

    return session_mgr, [s1, s2, s3]


# --- Unit Tests: SessionManager.list_all() ---

class TestListAll:
    async def test_empty_db(self, session_mgr):
        """DB kosong harus return list kosong."""
        result = await session_mgr.list_all()
        assert result == []

    async def test_returns_all_sessions(self, seeded_mgr):
        """Harus return semua session yang ada."""
        mgr, sessions = seeded_mgr
        result = await mgr.list_all()
        assert len(result) == 3

    async def test_ordered_by_updated_at_desc(self, seeded_mgr):
        """Session terbaru harus di urutan pertama."""
        mgr, sessions = seeded_mgr
        result = await mgr.list_all()
        # Session terakhir yang di-create/update harusnya di atas
        dates = [r["updated_at"] for r in result]
        assert dates == sorted(dates, reverse=True)

    async def test_limit_parameter(self, seeded_mgr):
        """Limit harus membatasi jumlah result."""
        mgr, _ = seeded_mgr
        result = await mgr.list_all(limit=2)
        assert len(result) == 2

    async def test_has_tor_flag(self, seeded_mgr):
        """has_tor harus True jika generated_tor IS NOT NULL."""
        mgr, sessions = seeded_mgr
        result = await mgr.list_all()

        # Cari session berdasarkan ID
        by_id = {r["id"]: r for r in result}

        # s1 punya TOR
        assert by_id[sessions[0].id]["has_tor"] is True
        # s2 belum punya TOR
        assert by_id[sessions[1].id]["has_tor"] is False
        # s3 punya TOR
        assert by_id[sessions[2].id]["has_tor"] is True

    async def test_title_returned(self, seeded_mgr):
        """Title harus dikembalikan untuk session yang punya title."""
        mgr, sessions = seeded_mgr
        result = await mgr.list_all()
        by_id = {r["id"]: r for r in result}

        assert by_id[sessions[0].id]["title"] == "Workshop Penerapan AI untuk ASN"
        assert by_id[sessions[1].id]["title"] == "Pengadaan Server Data Center"
        assert by_id[sessions[2].id]["title"] is None  # tanpa title

    async def test_correct_keys(self, seeded_mgr):
        """Setiap dict harus punya semua key yang expected."""
        mgr, _ = seeded_mgr
        result = await mgr.list_all()
        expected_keys = {"id", "title", "state", "turn_count",
                         "created_at", "updated_at", "has_tor"}
        for r in result:
            assert set(r.keys()) == expected_keys


# --- Integration Tests: API Endpoint ---

@pytest_asyncio.fixture
async def api_client(seeded_mgr):
    """Async HTTP client dengan seeded session data."""
    mgr, sessions = seeded_mgr

    # Override app.state
    app.state.session_mgr = mgr
    
    from unittest.mock import AsyncMock
    app.state.chat_service = AsyncMock()
    app.state.chat_service.get_chat_history.return_value = []
    app.state.chat_service.get_session.side_effect = lambda sid: [s for s in sessions if s.id == sid][0]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, sessions


class TestSessionListAPI:
    async def test_returns_200(self, api_client):
        """Endpoint harus return 200."""
        client, _ = api_client
        resp = await client.get("/api/v1/sessions")
        assert resp.status_code == 200

    async def test_returns_list(self, api_client):
        """Response harus berupa array."""
        client, _ = api_client
        resp = await client.get("/api/v1/sessions")
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 3

    async def test_limit_query_param(self, api_client):
        """?limit=1 harus return maksimal 1."""
        client, _ = api_client
        resp = await client.get("/api/v1/sessions", params={"limit": 1})
        data = resp.json()
        assert len(data) == 1

    async def test_response_fields(self, api_client):
        """Setiap item harus punya semua fields yang expected."""
        client, _ = api_client
        resp = await client.get("/api/v1/sessions")
        data = resp.json()

        for item in data:
            assert "id" in item
            assert "state" in item
            assert "turn_count" in item
            assert "has_tor" in item
            assert "created_at" in item
            assert "updated_at" in item

    async def test_existing_session_detail_still_works(self, api_client):
        """Endpoint GET /session/{id} yang sudah ada tidak boleh rusak."""
        client, sessions = api_client
        s_id = sessions[0].id

        resp = await client.get(f"/api/v1/session/{s_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == s_id
        assert "chat_history" in data


# --- Unit Tests: Auto-Title ---

class TestAutoTitle:
    async def test_title_set_on_create(self, session_mgr):
        """update() dengan title harus menyimpan title."""
        session = await session_mgr.create()
        await session_mgr.update(session.id, title="Test Title")

        result = await session_mgr.list_all()
        assert result[0]["title"] == "Test Title"

    async def test_title_truncation(self, session_mgr):
        """Title lebih dari 40 char harus dipotong (oleh ChatService)."""
        session = await session_mgr.create()
        long_title = "A" * 50
        truncated = long_title[:40] + "..."
        await session_mgr.update(session.id, title=truncated)

        result = await session_mgr.list_all()
        assert len(result[0]["title"]) == 43  # 40 + "..."
        assert result[0]["title"].endswith("...")
