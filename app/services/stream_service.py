"""Streaming service — wraps chat/decision engine into async event generator."""

import logging
import dataclasses
from typing import AsyncGenerator, Literal

logger = logging.getLogger("ai-agent-hybrid.stream")


@dataclasses.dataclass
class StreamEvent:
    type: Literal[
        "status",
        "thinking_start", "thinking_token", "thinking_end",
        "token", "done", "error"
    ]
    token: str = ""
    response: dict | None = None
    error: str = ""


class StreamService:
    """Delegates streaming events from ChatService."""

    def __init__(self, chat_service, decision_engine=None):
        self.chat_service = chat_service
        self.decision_engine = decision_engine

    async def stream_message(
        self, session_id: str | None, message: str
    ) -> AsyncGenerator[StreamEvent, None]:
        """Delegate ke ChatService.process_message_stream()."""
        try:
            async for event in self.chat_service.process_message_stream(
                session_id=session_id,
                message=message,
            ):
                yield event

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield StreamEvent(type="error", error=str(e))
