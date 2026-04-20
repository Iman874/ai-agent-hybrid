"""Streaming service — wraps chat/decision engine into async event generator."""

import logging
import dataclasses
from typing import AsyncGenerator, Literal

logger = logging.getLogger("ai-agent-hybrid.stream")


@dataclasses.dataclass
class StreamEvent:
    type: Literal[
        "thinking_start", "thinking_token", "thinking_end",
        "token", "done", "error"
    ]
    token: str = ""
    response: dict | None = None
    error: str = ""


class StreamService:
    """Wraps chat_service.process_message into streaming events."""

    def __init__(self, chat_service, decision_engine):
        self.chat_service = chat_service
        self.decision_engine = decision_engine

    async def stream_message(
        self, session_id: str | None, message: str
    ) -> AsyncGenerator[StreamEvent, None]:
        """Process message and yield streaming events."""
        try:
            # Phase 1: Thinking
            yield StreamEvent(type="thinking_start")
            yield StreamEvent(type="thinking_token", token="Menganalisis pertanyaan...")

            # Phase 2: Process via decision engine (non-streaming for now)
            result = await self.decision_engine.route(
                session_id=session_id,
                message=message,
            )

            yield StreamEvent(type="thinking_end")

            # Phase 3: Stream response tokens
            response_text = ""
            if result.chat_response:
                response_text = result.chat_response.message
            elif result.generate_response:
                response_text = result.generate_response.tor_document.content if result.generate_response.tor_document else "TOR berhasil dibuat."

            # Simulate token streaming from full response
            words = response_text.split(" ")
            for i, word in enumerate(words):
                yield StreamEvent(type="token", token=word + (" " if i < len(words) - 1 else ""))

            # Phase 4: Done with full response data
            from app.api.routes.hybrid import _convert_to_api_response
            api_response = _convert_to_api_response(result)

            yield StreamEvent(
                type="done",
                response=api_response.model_dump(),
            )

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield StreamEvent(type="error", error=str(e))
