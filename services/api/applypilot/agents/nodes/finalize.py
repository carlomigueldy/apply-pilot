"""``finalize`` node — terminal marker for a completed graph run.

Human review is handled out-of-band by the approval API, not by a LangGraph
interrupt, so the graph stays deterministic and free of resumable checkpoints.
By the time this node runs, ``persist_outputs`` has already advanced the
application to ``drafted``; this node is a no-op state passthrough that gives the
graph a single, named completion point for timing and observability.
"""

from __future__ import annotations

from typing import Any

from applypilot.agents.state import ApplicationGraphState


def finalize(state: ApplicationGraphState) -> dict[str, Any]:
    """Return an empty partial state, signalling successful completion."""
    return {}
