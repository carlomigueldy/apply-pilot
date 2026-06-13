"""Minimal synchronous background worker stub.

A real task loop (graph runs, embeddings, etc.) is added in a later phase. For
now this simply confirms the worker process can start and stay alive.
"""

from __future__ import annotations

import time

from applypilot.core.logging import configure_logging, get_logger

logger = get_logger(__name__)

_IDLE_SECONDS = 5.0


def main() -> None:
    """Start the worker and idle in a loop until interrupted."""
    configure_logging()
    logger.info("worker started")
    try:
        while True:
            time.sleep(_IDLE_SECONDS)
    except KeyboardInterrupt:
        logger.info("worker stopping")


if __name__ == "__main__":
    main()
