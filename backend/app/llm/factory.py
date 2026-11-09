"""Factory function for LLM providers."""
import logging
from app.llm.base import LLMProvider
from app.config import settings

logger = logging.getLogger(__name__)


def get_provider() -> LLMProvider:
    """
    Return the appropriate LLM provider based on the LLM_PROVIDER environment variable.

    Supported values:
    - "mock": MockProvider (no API key required)
    - "gemini": GeminiProvider (requires GEMINI_API_KEY)
    - "openai": OpenAIProvider (requires OPENAI_API_KEY)
    - "anthropic": AnthropicProvider (requires ANTHROPIC_API_KEY)
    - "ollama": OllamaProvider (requires local Ollama server)
    """
    provider_name = settings.LLM_PROVIDER.lower().strip()
    logger.info(f"Loading LLM provider: {provider_name}")

    try:
        if provider_name == "gemini":
            from app.llm.gemini import GeminiProvider
            return GeminiProvider()
        elif provider_name == "openai":
            from app.llm.openai import OpenAIProvider
            return OpenAIProvider()
        elif provider_name == "anthropic":
            from app.llm.anthropic import AnthropicProvider
            return AnthropicProvider()
        elif provider_name == "ollama":
            from app.llm.ollama import OllamaProvider
            return OllamaProvider()
        else:
            # Default to mock
            if provider_name != "mock":
                logger.warning(f"Unknown provider '{provider_name}', falling back to mock")
            from app.llm.mock import MockProvider
            return MockProvider()
    except Exception as e:
        logger.error(f"Failed to initialize provider '{provider_name}': {e}. Using mock.")
        from app.llm.mock import MockProvider
        return MockProvider()
