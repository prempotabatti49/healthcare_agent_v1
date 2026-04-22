from __future__ import annotations

import logging
from typing import Optional

from openai import OpenAI

from app.config.secrets import get_secret
from app.config.settings import get_settings
from app.services.llm.base import BaseLLM, LLMMessage

logger = logging.getLogger(__name__)


class OpenAILLM(BaseLLM):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = OpenAI(api_key=get_secret("OPENAI_API_KEY"))
        self._model = settings.openai_model

    def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        payload = [{"role": m.role, "content": m.content} for m in messages]
        kwargs: dict = {"model": self._model, "messages": payload, "temperature": temperature}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    def provider_name(self) -> str:
        return f"openai/{self._model}"
