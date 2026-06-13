"""Shared helpers for application-graph nodes.

Every node is a plain synchronous function over
:class:`~applypilot.agents.state.ApplicationGraphState` that returns a *partial*
state dict. These helpers keep the individual node modules small and consistent:

* :func:`dump` — normalise a Pydantic model (or anything) into a JSON-safe value
  suitable for :func:`~applypilot.agents.grounding.build_context_block`.
* :func:`attr` — read a field from either a Pydantic model or a plain ``dict``.
* :func:`append_error` — accumulate a :class:`~applypilot.schemas.graph.GraphError`
  onto the state's ``errors`` channel (which has no LangGraph reducer, so the merge
  is performed manually here).
* :func:`clamp_unit` — coerce a value into the ``[0.0, 1.0]`` confidence range.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from applypilot.agents.state import ApplicationGraphState
from applypilot.schemas.graph import GraphError


def dump(obj: Any) -> Any:
    """Return a JSON-serialisable representation of *obj*.

    Pydantic models are rendered with ``model_dump(mode="json")`` so enums become
    their string values and UUIDs/datetimes become strings. ``None`` and plain
    JSON primitives pass through unchanged.
    """
    if obj is None:
        return None
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    return obj


def attr(obj: Any, name: str, default: Any = None) -> Any:
    """Read attribute/key *name* from a Pydantic model or a ``dict``.

    Returns *default* when *obj* is ``None`` or the field is absent.
    """
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def append_error(
    state: ApplicationGraphState,
    node: str,
    message: str,
    error_type: str = "GraphNodeError",
) -> list[Any]:
    """Return the state's ``errors`` list with a new :class:`GraphError` appended.

    The ``errors`` channel has no reducer, so callers must read-modify-write the
    full list. The existing errors are copied (never mutated in place) to respect
    the project's immutability convention.
    """
    errors: list[Any] = list(state.get("errors") or [])
    errors.append(GraphError(node=node, message=message, type=error_type))
    return errors


def clamp_unit(value: Any, default: float = 0.0) -> float:
    """Coerce *value* into the closed ``[0.0, 1.0]`` interval.

    Non-numeric values fall back to *default* (then clamped). Used to keep
    retrieval scores within the confidence bounds the schemas enforce.
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(0.0, min(1.0, number))
