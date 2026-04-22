from __future__ import annotations

import logging
from typing import Optional

import anthropic

from app.config.secrets import get_secret
from app.config.settings import get_settings
from app.services.llm.base import BaseLLM, LLMMessage

logger = logging.getLogger(__name__)


class ClaudeLLM(BaseLLM):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=get_secret("ANTHROPIC_API_KEY"))
        self._model = settings.anthropic_model

    def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        # Anthropic separates system prompt from the messages array
        system_content = ""
        conversation: list[dict] = []

        for m in messages:
            if m.role == "system":
                system_content += m.content + "\n"
            else:
                conversation.append({"role": m.role, "content": m.content})

        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens or 2048,
            system=system_content.strip() or anthropic.NOT_GIVEN,
            messages=conversation,
            temperature=temperature,
        )
        return response.content[0].text if response.content else ""

    def provider_name(self) -> str:
        return f"anthropic/{self._model}"
