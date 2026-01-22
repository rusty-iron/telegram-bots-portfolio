"""Модуль middleware."""

from src.middlewares.throttling import ThrottlingMiddleware

__all__ = ["ThrottlingMiddleware"]
