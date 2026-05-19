"""
GreenVerify AI — application entry point.

Starts the FastAPI server using uvicorn. This module can be invoked directly
with ``python -m greenverify.api.main`` or via the installed console script.

Environment variables:
    HOST: Bind address (default: 0.0.0.0).
    PORT: Bind port (default: 8000).
    LOG_LEVEL: Logging level — debug, info, warning, error (default: info).
"""

from __future__ import annotations

import logging
import os
import sys

# Ensure the package is importable when running as a script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from .routes import create_app  # noqa: E402


def configure_logging() -> None:
    """Configure root logger with structured output."""
    log_level = os.getenv("LOG_LEVEL", "info").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    """Create the FastAPI application and start the uvicorn server."""
    configure_logging()
    logger = logging.getLogger(__name__)

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    app = create_app()

    logger.info(
        "Starting GreenVerify AI server — host=%s, port=%s",
        host,
        port,
    )

    try:
        import uvicorn
        uvicorn.run(app, host=host, port=port)
    except ImportError:
        logger.error(
            "uvicorn is required to run GreenVerify AI. "
            "Install it with: pip install uvicorn[standard]"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
