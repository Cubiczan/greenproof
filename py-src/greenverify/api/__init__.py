"""
GreenVerify AI API layer.

FastAPI application, route definitions, and HTTP middleware.
"""

from .routes import create_app

__all__ = [
    "create_app",
]
