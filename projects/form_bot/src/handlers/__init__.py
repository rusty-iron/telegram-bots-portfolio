"""Модуль обработчиков команд и состояний."""

from aiogram import Router

from src.handlers.admin import router as admin_router
from src.handlers.commands import router as commands_router
from src.handlers.form import router as form_router


def setup_routers() -> Router:
    """
    Настраивает и возвращает главный роутер с подключёнными обработчиками.

    Порядок подключения важен: admin роутер должен быть первым,
    чтобы команда /admin обрабатывалась до FSM состояний.

    Returns:
        Router: Настроенный роутер.
    """
    router = Router()
    router.include_router(admin_router)
    router.include_router(commands_router)
    router.include_router(form_router)
    return router


__all__ = ["setup_routers"]
