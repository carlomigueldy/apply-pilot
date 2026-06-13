"""Synchronous Anthropic LLM provider backed by ``langchain_anthropic.ChatAnthropic``.

The ``langchain_anthropic`` dependency is imported lazily on first use so the
rest of the application does not require it when a different provider is active.
Everything is synchronous — no ``async``/``await``.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, TypeVar, cast

from pydantic import BaseModel

if TYPE_CHECKING:
    from applypilot.core.config import Settings

_T = TypeVar("_T", bound=BaseModel)

# Used when the configured ``llm_model`` does not look like a Claude model
# (e.g. it still holds the fake default).
_DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicLLMProvider:
    """LLM provider that calls the Anthropic Messages API via LangChain.

    Args:
        settings: Optional :class:`~applypilot.core.config.Settings` override.
            Defaults to the process-wide cached settings instance.

    Raises:
        ValueError: If ``anthropic_api_key`` is not configured in settings.
    """

    name: str = "anthropic"

    def __init__(self, settings: Settings | None = None) -> None:
        from applypilot.core.config import get_settings

        s = settings or get_settings()
        if not s.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured in settings")
        self._api_key: str = s.anthropic_api_key
        self.model: str = _resolve_model(s.llm_model)

    @cached_property
    def _llm(self) -> Any:
        """Lazily construct and memoise the ``ChatAnthropic`` client."""
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=self.model, api_key=self._api_key)

    def structured(self, prompt: str, schema: type[_T]) -> _T:
        """Return a validated ``schema`` instance via structured output."""
        result = self._llm.with_structured_output(schema).invoke(prompt)
        return cast("_T", result)

    def text(self, prompt: str) -> str:
        """Return a free-form text completion for ``prompt``."""
        content = self._llm.invoke(prompt).content
        return content if isinstance(content, str) else str(content)


def _resolve_model(configured: str | None) -> str:
    """Return a usable Claude model id, defaulting when ``configured`` looks unset.

    The fake default (``fake-applypilot-v1``) and any non-Claude value fall back
    to :data:`_DEFAULT_MODEL`; an explicit ``claude-*`` model is kept as-is.
    """
    name = (configured or "").strip()
    if not name or "fake" in name.lower() or not name.lower().startswith("claude"):
        return _DEFAULT_MODEL
    return name
