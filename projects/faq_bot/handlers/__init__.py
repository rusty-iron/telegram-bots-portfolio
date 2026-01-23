"""Обработчики бота."""

from aiogram import Router

from handlers.start import router as start_router
from handlers.faq import router as faq_router
from handlers.search import router as search_router
from handlers.admin import router as admin_router


def get_all_routers() -> list[Router]:
    """Получение всех роутеров."""
    return [
        start_router,
        admin_router,
        faq_router,
        search_router,
    ]
