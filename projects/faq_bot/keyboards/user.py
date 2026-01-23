"""
Клавиатуры для пользователей.
"""

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


class UserKeyboards:
    """Клавиатуры для пользователей."""

    BACK_BTN = "⬅️ Назад"
    MAIN_MENU_BTN = "🏠 Главное меню"
    SEARCH_BTN = "🔍 Поиск"
    FAQ_BTN = "📚 FAQ"
    SUPPORT_BTN = "💬 Поддержка"

    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Главное меню пользователя."""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=UserKeyboards.FAQ_BTN)],
                [KeyboardButton(text=UserKeyboards.SEARCH_BTN)],
                [KeyboardButton(text=UserKeyboards.SUPPORT_BTN)],
            ],
            resize_keyboard=True,
        )

    @staticmethod
    def categories(categories: list[str]) -> InlineKeyboardMarkup:
        """Клавиатура категорий FAQ."""
        builder = InlineKeyboardBuilder()

        for category in categories:
            builder.button(
                text=category,
                callback_data=f"cat:{category[:50]}",
            )

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def questions(
        category: str, questions: list[str]
    ) -> InlineKeyboardMarkup:
        """Клавиатура вопросов категории."""
        builder = InlineKeyboardBuilder()

        for i, question in enumerate(questions):
            display_text = question[:60] + "..." if len(question) > 60 else question
            builder.button(
                text=display_text,
                callback_data=f"q:{i}",
            )

        builder.button(
            text=UserKeyboards.BACK_BTN,
            callback_data="back_to_categories",
        )

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def answer_navigation(category: str) -> InlineKeyboardMarkup:
        """Навигация после просмотра ответа."""
        builder = InlineKeyboardBuilder()

        builder.button(
            text=UserKeyboards.BACK_BTN,
            callback_data=f"back_to_cat:{category[:50]}",
        )
        builder.button(
            text=UserKeyboards.MAIN_MENU_BTN,
            callback_data="back_to_categories",
        )

        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def search_results(results: list) -> InlineKeyboardMarkup:
        """Клавиатура результатов поиска."""
        builder = InlineKeyboardBuilder()

        for i, result in enumerate(results):
            display_text = (
                result.question[:55] + "..."
                if len(result.question) > 55
                else result.question
            )
            builder.button(
                text=display_text,
                callback_data=f"sr:{i}",
            )

        builder.button(
            text=UserKeyboards.MAIN_MENU_BTN,
            callback_data="cancel_search",
        )

        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def back_to_search() -> InlineKeyboardMarkup:
        """Кнопка возврата к поиску."""
        builder = InlineKeyboardBuilder()

        builder.button(
            text="🔍 Новый поиск",
            callback_data="new_search",
        )
        builder.button(
            text=UserKeyboards.MAIN_MENU_BTN,
            callback_data="cancel_search",
        )

        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def support_contact(username: str) -> InlineKeyboardMarkup:
        """Кнопка связи с поддержкой."""
        builder = InlineKeyboardBuilder()

        builder.button(
            text="💬 Написать в поддержку",
            url=f"https://t.me/{username}",
        )

        return builder.as_markup()

    @staticmethod
    def cancel_search() -> ReplyKeyboardMarkup:
        """Клавиатура отмены поиска."""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="❌ Отмена")],
            ],
            resize_keyboard=True,
        )
