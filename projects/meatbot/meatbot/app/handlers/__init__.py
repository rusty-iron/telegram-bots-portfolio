"""
Импорт всех handlers
"""

from .admin import router as admin_router
from .cart import router as cart_router
from .catalog import router as catalog_router
from .commands import router as commands_router
from .orders import router as orders_router
from .start import router as start_router

__all__ = [
    "start_router",
    "commands_router",
    "catalog_router",
    "cart_router",
    "orders_router",
    "admin_router",
]
