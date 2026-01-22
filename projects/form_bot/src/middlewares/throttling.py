"""
Middleware для защиты от флуда (throttling).

Ограничивает частоту обращений от одного пользователя.
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from src.config import settings

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов.

    Attributes:
        rate: Минимальный интервал между сообщениями в секундах.
        user_last_message: Словарь с временем последнего сообщения пользователя.
    """

    def __init__(self, rate: float = None) -> None:
        """
        Инициализирует middleware.

        Args:
            rate: Минимальный интервал в секундах. По умолчанию из настроек.
        """
        self.rate = rate or settings.throttle_rate
        self.user_last_message: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Обрабатывает входящее событие с проверкой на флуд.

        Args:
            handler: Следующий обработчик в цепочке.
            event: Входящее событие Telegram.
            data: Дополнительные данные.

        Returns:
            Any: Результат работы обработчика или None при блокировке.
        """
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id
        current_time = event.date.timestamp()

        # Проверяем время последнего сообщения
        last_time = self.user_last_message.get(user_id, 0)
        time_diff = current_time - last_time

        if time_diff < self.rate:
            logger.warning(
                f"Throttling: user_id={user_id}, "
                f"diff={time_diff:.2f}s < rate={self.rate}s"
            )
            # Не отвечаем на слишком частые сообщения
            return None

        # Обновляем время последнего сообщения
        self.user_last_message[user_id] = current_time

        # Периодически очищаем старые записи
        self._cleanup_old_records(current_time)

        return await handler(event, data)

    def _cleanup_old_records(self, current_time: float) -> None:
        """
        Очищает устаревшие записи о пользователях.

        Args:
            current_time: Текущее время в timestamp.
        """
        # Удаляем записи старше 1 часа
        threshold = current_time - 3600
        self.user_last_message = {
            user_id: last_time
            for user_id, last_time in self.user_last_message.items()
            if last_time > threshold
        }
