from app.services.llm.base import BaseLLM, LLMMessage
from app.services.llm.openai_llm import OpenAILLM
from app.services.llm.claude_llm import ClaudeLLM
from app.config.settings import get_settings


def get_llm() -> BaseLLM:
    """Factory: returns the configured LLM provider."""
    settings = get_settings()
    if settings.llm_provider == "claude":
        return ClaudeLLM()
    return OpenAILLM()


__all__ = ["BaseLLM", "LLMMessage", "OpenAILLM", "ClaudeLLM", "get_llm"]
