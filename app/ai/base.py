from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Abstract base class untuk semua LLM provider."""

    @abstractmethod
    async def chat(self, messages: list[dict]) -> dict:
        """
        Kirim chat completion.
        Args:
            messages: list of {"role": str, "content": str}
        Returns:
            {"content": str, "total_duration": int, "eval_count": int}
        """
        ...
