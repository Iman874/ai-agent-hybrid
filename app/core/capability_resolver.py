import logging
from dataclasses import dataclass

logger = logging.getLogger("ai-agent-hybrid.capability")


@dataclass
class ModelCapabilities:
    """Kemampuan sebuah model LLM."""
    supports_text: bool = True
    supports_image_input: bool = False
    supports_streaming: bool = True


class ModelCapabilityResolver:
    """
    Menentukan kemampuan model berdasarkan nama dan provider.

    Rules:
    - Gemini → supports_image_input = True (hampir semua model Gemini support vision)
    - Ollama → pattern match ke KNOWN_VISION_MODELS
    - Unknown → fail-safe: supports_image_input = False
    """

    KNOWN_VISION_MODELS: list[str] = [
        "llava",
        "bakllava",
        "moondream",
        "cogvlm",
        "llama3.2-vision",
        "minicpm-v",
        "internvl",
        "llava-phi3",
        "llava-llama3",
    ]

    def resolve(self, model_id: str, provider: str) -> ModelCapabilities:
        """Resolve capabilities berdasarkan model_id dan provider."""
        if provider == "google":
            return self._resolve_gemini(model_id)
        elif provider == "ollama":
            return self._resolve_ollama(model_id)
        else:
            logger.warning(
                f"Unknown provider '{provider}' for model '{model_id}'. "
                "Using fail-safe (text-only)."
            )
            return ModelCapabilities()

    def _resolve_gemini(self, model_id: str) -> ModelCapabilities:
        """Gemini: hampir semua model support vision."""
        return ModelCapabilities(
            supports_text=True,
            supports_image_input=True,
            supports_streaming=True,
        )

    def _resolve_ollama(self, model_id: str) -> ModelCapabilities:
        """Ollama: pattern match nama model ke known vision models."""
        model_lower = model_id.lower()
        is_vision = any(vm in model_lower for vm in self.KNOWN_VISION_MODELS)

        if is_vision:
            logger.debug(f"Model '{model_id}' matched as vision model.")

        return ModelCapabilities(
            supports_text=True,
            supports_image_input=is_vision,
            supports_streaming=True,
        )
