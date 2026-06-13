"""Synchronous OpenAI LLM provider backed by ``langchain_openai.ChatOpenAI``.

The ``langchain_openai`` dependency is imported lazily on first use so the rest
of the application does not require it when a different provider is active.
Everything is synchronous — no ``async``/``await``.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, TypeVar, cast

from pydantic import BaseModel

if TYPE_CHECKING:
    from applypilot.core.config import Settings

_T = TypeVar("_T", bound=BaseModel)


class OpenAILLMProvider:
    """LLM provider that calls the OpenAI Chat Completions API via LangChain.

    Args:
        settings: Optional :class:`~applypilot.core.config.Settings` override.
            Defaults to the process-wide cached settings instance.

    Raises:
        ValueError: If ``openai_api_key`` is not configured in settings.
    """

    name: str = "openai"

    def __init__(self, settings: Settings | None = None) -> None:
        from applypilot.core.config import get_settings

        s = settings or get_settings()
        if not s.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured in settings")
        self._api_key: str = s.openai_api_key
        self.model: str = s.llm_model

    @cached_property
    def _llm(self) -> Any:
        """Lazily construct and memoise the ``ChatOpenAI`` client."""
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=self.model, api_key=self._api_key)

    def structured(self, prompt: str, schema: type[_T]) -> _T:
        """Return a validated ``schema`` instance via structured output."""
        result = self._llm.with_structured_output(schema).invoke(prompt)
        return cast("_T", result)

    def text(self, prompt: str) -> str:
        """Return a free-form text completion for ``prompt``."""
        content = self._llm.invoke(prompt).content
        return content if isinstance(content, str) else str(content)
