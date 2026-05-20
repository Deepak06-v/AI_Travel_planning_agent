"""Central logging setup for CLI and services."""

import logging
import os
import sys
from typing import Optional

_CONFIGURED = False


def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure root logger once (idempotent).

    Level from ``level`` arg, ``LOG_LEVEL`` env, or INFO by default.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    resolved = (level or os.environ.get("LOG_LEVEL") or "INFO").upper()
    numeric = getattr(logging, resolved, logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )

    root = logging.getLogger()
    root.setLevel(numeric)
    root.addHandler(handler)

    # Reduce noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)

    _CONFIGURED = True
