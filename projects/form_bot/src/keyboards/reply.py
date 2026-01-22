"""
Reply-клавиатуры для бота.

Содержит функции создания клавиатур для различных этапов опроса.
"""

from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


# Константы для текста кнопок
BACK_BUTTON = "⬅️ Назад"
CANCEL_BUTTON = "❌ Отмена"
CONFIRM_BUTTON = "✅ Всё верно"
RESTART_BUTTON = "🔄 Начать заново"
SEND_CONTACT_BUTTON = "📱 Отправить контакт"
SKIP_BUTTON = "⏭ Пропустить"


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с кнопкой отмены для первого шага.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с одной кнопкой отмены.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_back_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с кнопками «Назад» и «Отмена».

    Returns:
        ReplyKeyboardMarkup: Клавиатура для навигации.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BACK_BUTTON)],
            [KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для ввода телефона с возможностью отправки контакта.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопкой отправки контакта.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SEND_CONTACT_BUTTON, request_contact=True)],
            [KeyboardButton(text=BACK_BUTTON)],
            [KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с возможностью пропустить шаг (для сообщения).

    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопкой пропуска.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SKIP_BUTTON)],
            [KeyboardButton(text=BACK_BUTTON)],
            [KeyboardButton(text=CANCEL_BUTTON)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_confirm_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура подтверждения данных.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопками подтверждения.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CONFIRM_BUTTON)],
            [KeyboardButton(text=RESTART_BUTTON)],
            [KeyboardButton(text=BACK_BUTTON)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """
    Удаляет клавиатуру.

    Returns:
        ReplyKeyboardRemove: Объект для удаления клавиатуры.
    """
    return ReplyKeyboardRemove()
