"""
Middleware для обработки ошибок в aiogram
"""

import traceback
from typing import Any, Awaitable, Callable, Dict

import structlog
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = structlog.get_logger()


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware для глобальной обработки ошибок"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as exc:
            # Логируем ошибку с контекстом
            user_id = None
            chat_id = None
            message_text = None

            if isinstance(event, Message):
                user_id = event.from_user.id if event.from_user else None
                chat_id = event.chat.id
                message_text = event.text
            elif isinstance(event, CallbackQuery):
                user_id = event.from_user.id if event.from_user else None
                chat_id = event.message.chat.id if event.message else None
                message_text = event.data

            logger.error(
                "handler_error",
                error=str(exc),
                error_type=type(exc).__name__,
                user_id=user_id,
                chat_id=chat_id,
                message_text=message_text,
                exc_info=traceback.format_exc(),
            )

            # Отправляем пользователю понятное сообщение об ошибке
            try:
                if isinstance(event, Message):
                    await event.answer(
                        "❌ Произошла ошибка при обработке вашего запроса. "
                        "Попробуйте еще раз или обратитесь к администратору."
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "❌ Произошла ошибка. Попробуйте еще раз.",
                        show_alert=True,
                    )
            except Exception as send_error:
                logger.error(
                    "failed_to_send_error_message",
                    error=str(send_error),
                    original_error=str(exc),
                )

            # Не пробрасываем исключение дальше, чтобы бот продолжал работать
            return None
