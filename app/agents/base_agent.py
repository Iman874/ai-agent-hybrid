from abc import ABC, abstractmethod

from app.agents.agent_context import AgentContext, AgentResult


class BaseAgent(ABC):
    name: str
    description: str
    system_prompt: str

    @abstractmethod
    async def process(self, context: AgentContext) -> AgentResult:
        ...

    @abstractmethod
    def build_messages(self, context: AgentContext) -> list[dict]:
        ...
