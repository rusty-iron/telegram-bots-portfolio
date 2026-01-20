"""
Middleware для проверки прав администратора
"""

from datetime import datetime
from typing import Any, Awaitable, Callable, Dict

import structlog
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from ..database import AdminUser, get_db

logger = structlog.get_logger()


class AdminMiddleware(BaseMiddleware):
    """Middleware для проверки прав администратора"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Получаем пользователя из события
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None

        if not user_id:
            return await handler(event, data)

        # Проверяем, является ли пользователь администратором
        with get_db() as db:
            admin = (
                db.query(AdminUser)
                .filter(
                    AdminUser.telegram_id == user_id,
                    AdminUser.is_active.is_(True),
                )
                .first()
            )

            if admin:
                # Обновляем время последнего входа
                admin.last_login = datetime.utcnow()
                db.commit()

                # Создаем словарь с данными администратора для передачи в
                # обработчики
                admin_data = {
                    "id": admin.id,
                    "telegram_id": admin.telegram_id,
                    "username": admin.username,
                    "full_name": admin.full_name,
                    "role": (
                        admin.role.value
                        if hasattr(admin.role, "value")
                        else str(admin.role)
                    ),  # Безопасное преобразование enum в строку
                    "is_active": admin.is_active,
                    "last_login": admin.last_login.strftime("%d.%m.%Y %H:%M")
                    if admin.last_login
                    else "Неизвестно",
                    "created_at": admin.created_at,
                }

                # Добавляем информацию об администраторе в data
                data["admin"] = admin_data

                # Также добавляем напрямую в kwargs для совместимости
                kwargs = data.copy()
                kwargs["admin"] = admin_data

                logger.info(
                    "admin_access_granted",
                    admin_id=admin.id,
                    telegram_id=admin.telegram_id,
                    role=admin.role,
                )
            else:
                data["admin"] = None
                kwargs = data.copy()
                kwargs["admin"] = None
                logger.info("admin_access_denied", user_id=user_id)

        return await handler(event, data)


def require_admin(required_permission: str = None):
    """Декоратор для проверки прав администратора"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Ищем admin в kwargs или data
            admin = None
            for arg in args:
                if hasattr(arg, "get") and "admin" in arg:
                    admin = arg["admin"]
                    break

            if not admin:
                # Если это callback или message, отправляем ошибку
                for arg in args:
                    if isinstance(arg, (Message, CallbackQuery)):
                        await arg.answer("❌ У вас нет прав администратора!")
                        return
                return

            # Проверяем конкретное право, если указано
            if required_permission and not admin.has_permission(
                required_permission
            ):
                for arg in args:
                    if isinstance(arg, (Message, CallbackQuery)):
                        await arg.answer(
                            "❌ Недостаточно прав для выполнения этой операции!"
                        )
                        return
                return

            return await func(*args, **kwargs)

        return wrapper

    return decorator
