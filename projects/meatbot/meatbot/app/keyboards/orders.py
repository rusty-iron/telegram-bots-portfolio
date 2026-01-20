"""
Клавиатуры для оформления заказов
"""

from typing import Optional

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def get_phone_request_keyboard(
    has_saved_phone: bool = False,
) -> InlineKeyboardMarkup:
    """
    Клавиатура для запроса номера телефона

    Args:
        has_saved_phone: Есть ли сохраненный номер телефона

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками
    """
    buttons = []

    if has_saved_phone:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="✅ Использовать сохраненный номер",
                    callback_data="use_saved_phone",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="❌ Отменить заказ",
                callback_data="cancel_order",
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_phone_share_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для возможности поделиться номером телефона

    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопкой "Поделиться номером"
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📞 Поделиться номером телефона",
                    request_contact=True,
                )
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard


def get_address_request_keyboard(
    has_saved_address: bool = False,
) -> InlineKeyboardMarkup:
    """
    Клавиатура для запроса адреса с возможностью использовать сохраненный

    Args:
        has_saved_address: Есть ли сохраненный адрес

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками
    """
    buttons = []

    if has_saved_address:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="✅ Использовать сохраненный адрес",
                    callback_data="use_saved_address",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="❌ Отменить заказ",
                callback_data="cancel_order",
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_save_data_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для предложения сохранить данные

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками да/нет
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, сохранить",
                    callback_data="save_user_data_yes",
                ),
                InlineKeyboardButton(
                    text="❌ Нет, не нужно",
                    callback_data="save_user_data_no",
                ),
            ],
        ]
    )
    return keyboard


def get_payment_methods_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора способа оплаты

    Returns:
        InlineKeyboardMarkup: Клавиатура с вариантами оплаты
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💵 Наличные при получении",
                    callback_data="payment_method_cash",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Перевод на карту",
                    callback_data="payment_method_transfer",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить заказ",
                    callback_data="cancel_order",
                )
            ],
        ]
    )
    return keyboard


def get_order_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для подтверждения заказа

    Returns:
        InlineKeyboardMarkup: Клавиатура подтверждения
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить заказ",
                    callback_data="confirm_order",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Изменить данные",
                    callback_data="edit_order_data",
                ),
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data="cancel_order",
                ),
            ],
        ]
    )
    return keyboard


def get_skip_notes_keyboard(
    has_saved_notes: bool = False,
) -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой "Пропустить" для необязательных полей

    Args:
        has_saved_notes: Есть ли сохраненные комментарии

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой пропуска
    """
    buttons = []

    # Если есть сохраненные комментарии, добавляем кнопку использования
    if has_saved_notes:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="✅ Использовать сохраненные комментарии",
                    callback_data="use_saved_notes",
                )
            ]
        )

    buttons.extend(
        [
            [
                InlineKeyboardButton(
                    text="⏭️ Пропустить",
                    callback_data="skip_notes",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить заказ",
                    callback_data="cancel_order",
                )
            ],
        ]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_order_edit_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для редактирования данных заказа

    Returns:
        InlineKeyboardMarkup: Клавиатура редактирования
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📞 Изменить телефон",
                    callback_data="edit_phone",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📍 Изменить адрес",
                    callback_data="edit_address",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 Изменить комментарии",
                    callback_data="edit_notes",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Изменить способ оплаты",
                    callback_data="edit_payment_method",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Готово",
                    callback_data="order_edit_done",
                ),
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data="cancel_order",
                ),
            ],
        ]
    )
    return keyboard


def get_order_details_keyboard(
    order_id: int, order_status: Optional[str] = None
) -> InlineKeyboardMarkup:
    """
    Клавиатура для просмотра деталей заказа

    Args:
        order_id: ID заказа
        order_status: Статус заказа (для определения доступных действий)

    Returns:
        InlineKeyboardMarkup: Клавиатура с деталями заказа
    """
    # Определяем, можно ли отменить заказ (не для delivered и cancelled)
    can_cancel = order_status not in ["delivered", "cancelled"]

    # Первая строка кнопок
    first_row = [
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data=f"refresh_order_{order_id}",
        ),
    ]

    # Добавляем кнопку отмены только если заказ можно отменить
    if can_cancel:
        first_row.append(
            InlineKeyboardButton(
                text="❌ Отменить заказ",
                callback_data=f"cancel_order_{order_id}",
            )
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            first_row,
            [
                InlineKeyboardButton(
                    text="📦 В каталог",
                    callback_data="catalog",
                ),
                InlineKeyboardButton(
                    text="🛒 В корзину",
                    callback_data="cart",
                ),
            ],
        ]
    )
    return keyboard


def get_orders_list_keyboard(
    orders: list, page: int = 0, per_page: int = 5
) -> InlineKeyboardMarkup:
    """
    Клавиатура для списка заказов пользователя

    Args:
        orders: Список заказов
        page: Текущая страница
        per_page: Количество заказов на странице

    Returns:
        InlineKeyboardMarkup: Клавиатура со списком заказов
    """
    keyboard_buttons = []

    # Добавляем кнопки для заказов на текущей странице
    start_idx = page * per_page
    end_idx = start_idx + per_page

    for order in orders[start_idx:end_idx]:
        status_emoji = {
            "pending": "⏳",
            "confirmed": "✅",
            "processing": "🔄",
            "shipped": "🚚",
            "delivered": "📦",
            "cancelled": "❌",
        }.get(
            order["status"].value
            if hasattr(order["status"], "value")
            else order["status"],
            "❓",
        )

        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{status_emoji} {order['order_number']} - {order['total_amount']:.2f}₽",
                    callback_data=f"order_details_{order['id']}",
                )
            ]
        )

    # Добавляем кнопки навигации
    nav_buttons = []

    # Кнопка "Назад" если не первая страница
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"orders_page_{page - 1}",
            )
        )

    # Кнопка "Вперед" если есть еще заказы
    if end_idx < len(orders):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"orders_page_{page + 1}",
            )
        )

    if nav_buttons:
        keyboard_buttons.append(nav_buttons)

    # Добавляем кнопки навигации
    keyboard_buttons.extend(
        [
            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data="refresh_orders",
                ),
                InlineKeyboardButton(
                    text="📜 История заказов",
                    callback_data="orders_history",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📦 В каталог",
                    callback_data="catalog",
                ),
                InlineKeyboardButton(
                    text="🛒 В корзину",
                    callback_data="cart",
                ),
            ],
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_orders_history_keyboard(
    orders: list, page: int = 0, per_page: int = 5
) -> InlineKeyboardMarkup:
    """
    Клавиатура для истории заказов пользователя (delivered и cancelled)

    Args:
        orders: Список заказов
        page: Текущая страница
        per_page: Количество заказов на странице

    Returns:
        InlineKeyboardMarkup: Клавиатура со списком заказов
    """
    keyboard_buttons = []

    # Добавляем кнопки для заказов на текущей странице
    start_idx = page * per_page
    end_idx = start_idx + per_page

    for order in orders[start_idx:end_idx]:
        status_emoji = {
            "pending": "⏳",
            "confirmed": "✅",
            "processing": "🔄",
            "shipped": "🚚",
            "delivered": "📦",
            "cancelled": "❌",
        }.get(
            order["status"].value
            if hasattr(order["status"], "value")
            else order["status"],
            "❓",
        )

        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{status_emoji} {order['order_number']} - {order['total_amount']:.2f}₽",
                    callback_data=f"order_details_{order['id']}",
                )
            ]
        )

    # Добавляем кнопки навигации по страницам
    nav_buttons = []

    # Кнопка "Назад" если не первая страница
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"orders_history_page_{page - 1}",
            )
        )

    # Кнопка "Вперед" если есть еще заказы
    if end_idx < len(orders):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"orders_history_page_{page + 1}",
            )
        )

    if nav_buttons:
        keyboard_buttons.append(nav_buttons)

    # Добавляем кнопки навигации
    keyboard_buttons.extend(
        [
            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data="refresh_orders_history",
                ),
                InlineKeyboardButton(
                    text="🔙 К моим заказам",
                    callback_data="orders",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📦 В каталог",
                    callback_data="catalog",
                ),
                InlineKeyboardButton(
                    text="🛒 В корзину",
                    callback_data="cart",
                ),
            ],
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_admin_order_management_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура для управления заказом администратором

    Args:
        order_id: ID заказа

    Returns:
        InlineKeyboardMarkup: Клавиатура управления заказом
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"admin_confirm_order_{order_id}",
                ),
                InlineKeyboardButton(
                    text="🔄 В обработке",
                    callback_data=f"admin_processing_order_{order_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🚚 Отправлен",
                    callback_data=f"admin_shipped_order_{order_id}",
                ),
                InlineKeyboardButton(
                    text="📦 Доставлен",
                    callback_data=f"admin_delivered_order_{order_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=f"admin_cancel_order_{order_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data=f"admin_refresh_order_{order_id}",
                ),
                InlineKeyboardButton(
                    text="📋 Все заказы",
                    callback_data="admin_orders",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад в управление заказами",
                    callback_data="admin_orders",
                ),
            ],
        ]
    )
    return keyboard


def get_order_success_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для успешного создания заказа

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками навигации
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Мои заказы",
                    callback_data="orders",
                ),
                InlineKeyboardButton(
                    text="🏠 Назад в меню",
                    callback_data="back_to_menu",
                ),
            ],
        ]
    )
    return keyboard


def get_cancel_order_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для отмены заказа

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой отмены
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отменить заказ",
                    callback_data="cancel_order",
                )
            ],
        ]
    )
    return keyboard


def get_admin_orders_filter_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для фильтрации заказов в админ-панели

    Returns:
        InlineKeyboardMarkup: Клавиатура фильтров
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏳ Ожидают",
                    callback_data="admin_orders_filter_pending_0",
                ),
                InlineKeyboardButton(
                    text="✅ Подтверждены",
                    callback_data="admin_orders_filter_confirmed_0",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔄 В обработке",
                    callback_data="admin_orders_filter_processing_0",
                ),
                InlineKeyboardButton(
                    text="🚚 Отправлены",
                    callback_data="admin_orders_filter_shipped_0",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📦 Доставлены",
                    callback_data="admin_orders_filter_delivered_0",
                ),
                InlineKeyboardButton(
                    text="❌ Отменены",
                    callback_data="admin_orders_filter_cancelled_0",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📊 Все заказы",
                    callback_data="admin_orders_filter_all_0",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад в админ-панель",
                    callback_data="admin_main",
                ),
            ],
        ]
    )
    return keyboard
