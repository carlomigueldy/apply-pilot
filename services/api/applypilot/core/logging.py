"""Structured stdlib logging configuration for the ApplyPilot API."""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def configure_logging(level: int | str = logging.INFO) -> None:
    """Configure the root logger to emit structured records to stdout.

    Idempotent: repeated calls reuse the existing handler instead of stacking
    duplicate handlers. Intended to be called once at application startup.
    """
    global _CONFIGURED

    root = logging.getLogger()

    if _CONFIGURED:
        root.setLevel(level)
        return

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT))

    # Replace any pre-existing handlers so we own the output format.
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, ensuring logging is configured first."""
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(name)
