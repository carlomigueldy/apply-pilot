"""Synchronous Ollama LLM provider backed by ``langchain_ollama.ChatOllama``.

The ``langchain_ollama`` dependency is imported lazily on first use; if it is not
installed a clear :class:`NotImplementedError` is raised so the failure is
actionable. Everything is synchronous — no ``async``/``await``.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, TypeVar, cast

from pydantic import BaseModel

if TYPE_CHECKING:
    from applypilot.core.config import Settings

_T = TypeVar("_T", bound=BaseModel)


class OllamaLLMProvider:
    """LLM provider that calls a local Ollama server via LangChain.

    Args:
        settings: Optional :class:`~applypilot.core.config.Settings` override.
            Defaults to the process-wide cached settings instance.
    """

    name: str = "ollama"

    def __init__(self, settings: Settings | None = None) -> None:
        from applypilot.core.config import get_settings

        s = settings or get_settings()
        self._base_url: str = s.ollama_base_url.rstrip("/")
        self.model: str = s.ollama_model

    @cached_property
    def _llm(self) -> Any:
        """Lazily construct and memoise the ``ChatOllama`` client."""
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:  # pragma: no cover - depends on optional dep
            raise NotImplementedError(
                "Ollama LLM support requires the 'langchain-ollama' package. "
                "Install it (e.g. `pip install langchain-ollama`) to use "
                "llm_provider='ollama'."
            ) from exc

        return ChatOllama(model=self.model, base_url=self._base_url)

    def structured(self, prompt: str, schema: type[_T]) -> _T:
        """Return a validated ``schema`` instance via structured output."""
        result = self._llm.with_structured_output(schema).invoke(prompt)
        return cast("_T", result)

    def text(self, prompt: str) -> str:
        """Return a free-form text completion for ``prompt``."""
        content = self._llm.invoke(prompt).content
        return content if isinstance(content, str) else str(content)
