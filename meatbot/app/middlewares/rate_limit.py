"""
Middleware для ограничения частоты запросов (Rate Limiting)
"""

from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict

import structlog
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = structlog.get_logger()


class RateLimitMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов пользователей

    Защита от:
    - DoS атак (Denial of Service)
    - Spam
    - Bruteforce
    """

    def __init__(
        self,
        rate_limit: int = 30,  # Максимум запросов
        time_window: int = 60,  # За период в секундах
        admin_rate_limit: int = 100,  # Более высокий лимит для админов
    ):
        """
        Args:
            rate_limit: Максимальное количество запросов за time_window
            time_window: Временное окно в секундах
            admin_rate_limit: Лимит для администраторов
        """
        super().__init__()
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.admin_rate_limit = admin_rate_limit

        # Хранилище запросов: {user_id: [timestamp1, timestamp2, ...]}
        self._user_requests: Dict[int, list] = {}

        # Счетчик заблокированных запросов для мониторинга
        self._blocked_requests: Dict[int, int] = {}

    def _is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        from ..database import AdminUser, get_db

        try:
            with get_db() as db:
                admin = (
                    db.query(AdminUser)
                    .filter(AdminUser.telegram_id == user_id)
                    .first()
                )
                return admin is not None
        except Exception:
            return False

    def _clean_old_requests(self, user_id: int, current_time: datetime):
        """Удаляет старые запросы за пределами временного окна"""
        if user_id not in self._user_requests:
            return

        cutoff_time = current_time - timedelta(seconds=self.time_window)
        self._user_requests[user_id] = [
            req_time
            for req_time in self._user_requests[user_id]
            if req_time > cutoff_time
        ]

        # Удаляем пользователя из словаря, если нет запросов
        if not self._user_requests[user_id]:
            del self._user_requests[user_id]

    def _is_rate_limited(self, user_id: int) -> tuple[bool, int, int]:
        """
        Проверяет, превышен ли лимит запросов

        Returns:
            tuple[bool, int, int]: (is_limited, current_count, limit)
        """
        current_time = datetime.now()

        # Очищаем старые запросы
        self._clean_old_requests(user_id, current_time)

        # Инициализируем список запросов для пользователя
        if user_id not in self._user_requests:
            self._user_requests[user_id] = []

        # Получаем лимит для пользователя (выше для админов)
        limit = (
            self.admin_rate_limit
            if self._is_admin(user_id)
            else self.rate_limit
        )

        # Проверяем количество запросов
        current_count = len(self._user_requests[user_id])

        if current_count >= limit:
            # Увеличиваем счетчик заблокированных запросов
            self._blocked_requests[user_id] = (
                self._blocked_requests.get(user_id, 0) + 1
            )

            logger.warning(
                "rate_limit_exceeded",
                user_id=user_id,
                current_count=current_count,
                limit=limit,
                blocked_count=self._blocked_requests[user_id],
            )
            return True, current_count, limit

        # Добавляем текущий запрос
        self._user_requests[user_id].append(current_time)

        return False, current_count + 1, limit

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Обработчик middleware
        """
        # Получаем user_id из события
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None

        if user_id is None:
            # Если не можем определить пользователя, пропускаем
            return await handler(event, data)

        # Проверяем rate limit
        is_limited, current_count, limit = self._is_rate_limited(user_id)

        if is_limited:
            # Пользователь превысил лимит
            wait_time = self.time_window

            # Отправляем сообщение об ограничении
            if isinstance(event, Message):
                await event.answer(
                    f"⚠️ **Слишком много запросов!**\n\n"
                    f"Вы превысили лимит запросов ({limit} за {self.time_window} сек).\n"
                    f"Пожалуйста, подождите {wait_time} секунд и попробуйте снова.",
                    parse_mode="Markdown",
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    f"⚠️ Слишком много запросов! Подождите {wait_time} сек.",
                    show_alert=True,
                )

            # НЕ вызываем handler - блокируем запрос
            return

        # Логируем нормальную активность (опционально, только для отладки)
        # logger.debug(
        #     "rate_limit_check",
        #     user_id=user_id,
        #     current_count=current_count,
        #     limit=limit,
        # )

        # Передаем управление следующему handler
        return await handler(event, data)

    def get_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику по rate limiting

        Returns:
            Dict: Статистика
        """
        total_blocked = sum(self._blocked_requests.values())
        active_users = len(self._user_requests)

        return {
            "total_blocked_requests": total_blocked,
            "active_users": active_users,
            "blocked_users": len(self._blocked_requests),
            "top_blocked_users": sorted(
                self._blocked_requests.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10],
        }

    def reset_user(self, user_id: int):
        """Сбрасывает счетчики для пользователя"""
        if user_id in self._user_requests:
            del self._user_requests[user_id]
        if user_id in self._blocked_requests:
            del self._blocked_requests[user_id]

        logger.info("rate_limit_reset", user_id=user_id)
