"""
Клавиатуры для администратора.
"""

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


class AdminKeyboards:
    """Клавиатуры для администратора."""

    STATS_BTN = "📊 Статистика"
    UPLOAD_BTN = "📤 Загрузить FAQ"
    DOWNLOAD_BTN = "📥 Скачать FAQ"
    TOP_QUESTIONS_BTN = "🔝 Топ вопросов"
    TOP_SEARCHES_BTN = "🔍 Топ запросов"
    FAILED_SEARCHES_BTN = "❌ Неудачные запросы"
    BACK_BTN = "⬅️ Назад"
    EXIT_BTN = "🚪 Выход"

    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Главное меню администратора."""
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=AdminKeyboards.STATS_BTN),
                    KeyboardButton(text=AdminKeyboards.TOP_QUESTIONS_BTN),
                ],
                [
                    KeyboardButton(text=AdminKeyboards.TOP_SEARCHES_BTN),
                    KeyboardButton(text=AdminKeyboards.FAILED_SEARCHES_BTN),
                ],
                [
                    KeyboardButton(text=AdminKeyboards.UPLOAD_BTN),
                    KeyboardButton(text=AdminKeyboards.DOWNLOAD_BTN),
                ],
                [KeyboardButton(text=AdminKeyboards.EXIT_BTN)],
            ],
            resize_keyboard=True,
        )

    @staticmethod
    def cancel() -> ReplyKeyboardMarkup:
        """Клавиатура отмены."""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=AdminKeyboards.BACK_BTN)],
            ],
            resize_keyboard=True,
        )

    @staticmethod
    def confirm_upload() -> InlineKeyboardMarkup:
        """Подтверждение загрузки FAQ."""
        builder = InlineKeyboardBuilder()

        builder.button(text="✅ Подтвердить", callback_data="confirm_upload")
        builder.button(text="❌ Отменить", callback_data="cancel_upload")

        builder.adjust(2)
        return builder.as_markup()
