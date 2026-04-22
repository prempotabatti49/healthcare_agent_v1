"""Abstract base for all LLM providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMMessage:
    role: str   # "system" | "user" | "assistant"
    content: str


class BaseLLM(ABC):
    """
    Minimal interface every LLM provider must satisfy.
    Keeps the rest of the codebase provider-agnostic.
    """

    @abstractmethod
    def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send a conversation and return the assistant reply as a string."""
        ...

    @abstractmethod
    def provider_name(self) -> str: ...
