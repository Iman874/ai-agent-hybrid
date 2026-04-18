import pytest
from app.core.session_manager import SessionManager
from app.models.tor import TORData
from app.utils.errors import SessionNotFoundError


@pytest.mark.asyncio
class TestSessionManager:
    async def test_create_session(self, initialized_db):
        mgr = SessionManager(initialized_db)
        session = await mgr.create()
        assert session.id is not None
        assert session.state == "NEW"
        assert session.turn_count == 0

    async def test_get_session(self, initialized_db):
        mgr = SessionManager(initialized_db)
        created = await mgr.create()
        fetched = await mgr.get(created.id)
        assert fetched.id == created.id

    async def test_get_not_found(self, initialized_db):
        mgr = SessionManager(initialized_db)
        with pytest.raises(SessionNotFoundError):
            await mgr.get("non-existent-uuid")

    async def test_update_session(self, initialized_db):
        mgr = SessionManager(initialized_db)
        session = await mgr.create()
        await mgr.update(session.id, state="CHATTING", turn_count=1)
        updated = await mgr.get(session.id)
        assert updated.state == "CHATTING"
        assert updated.turn_count == 1

    async def test_update_extracted_data(self, initialized_db):
        mgr = SessionManager(initialized_db)
        session = await mgr.create()
        data = TORData(judul="Workshop AI", tujuan="Belajar")
        await mgr.update(session.id, extracted_data=data)
        updated = await mgr.get(session.id)
        assert updated.extracted_data.judul == "Workshop AI"
        assert updated.extracted_data.tujuan == "Belajar"

    async def test_append_and_get_messages(self, initialized_db):
        mgr = SessionManager(initialized_db)
        session = await mgr.create()
        await mgr.append_message(session.id, "user", "Halo")
        await mgr.append_message(session.id, "assistant", "Hai!", "NEED_MORE_INFO")
        history = await mgr.get_chat_history(session.id)
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].role == "assistant"
        assert history[1].parsed_status == "NEED_MORE_INFO"
