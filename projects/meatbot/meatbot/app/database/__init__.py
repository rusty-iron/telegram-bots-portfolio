"""
Модуль работы с базой данных MeatBot
"""

from contextlib import contextmanager

from sqlalchemy.orm import Session

from ..config import settings
from ..utils.db import create_sync_engine
from .base import Base
from .models import (
    AdminRole,
    AdminUser,
    CartItem,
    Category,
    Order,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentSettings,
    PaymentStatus,
    Product,
    User,
)

# Создаем engine для базы данных
engine = create_sync_engine(settings.database_url)


@contextmanager
def get_db():
    """Контекстный менеджер для работы с базой данных"""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


__all__ = [
    "Base",
    "User",
    "Category",
    "Product",
    "CartItem",
    "Order",
    "OrderItem",
    "OrderStatus",
    "PaymentStatus",
    "PaymentMethod",
    "PaymentSettings",
    "AdminUser",
    "AdminRole",
    "get_db",
]
