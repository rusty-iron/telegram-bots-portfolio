"""
Keyboards for cart functionality
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_quantity_selection_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для выбора количества товара"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="1", callback_data=f"select_quantity_{product_id}_1"
            ),
            InlineKeyboardButton(
                text="2", callback_data=f"select_quantity_{product_id}_2"
            ),
            InlineKeyboardButton(
                text="3", callback_data=f"select_quantity_{product_id}_3"
            ),
        ],
        [
            InlineKeyboardButton(
                text="5", callback_data=f"select_quantity_{product_id}_5"
            ),
            InlineKeyboardButton(
                text="10", callback_data=f"select_quantity_{product_id}_10"
            ),
            InlineKeyboardButton(
                text="15", callback_data=f"select_quantity_{product_id}_15"
            ),
        ],
        [
            InlineKeyboardButton(
                text="✏️ Ввести количество",
                callback_data=f"enter_quantity_{product_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Отмена", callback_data="cancel_quantity_selection"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cart_item_keyboard(
    cart_item_id: int, current_quantity: int
) -> InlineKeyboardMarkup:
    """Клавиатура для управления товаром в корзине"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="➖", callback_data=f"decrease_quantity_{cart_item_id}"
            ),
            InlineKeyboardButton(
                text=f"Количество: {current_quantity}",
                callback_data=f"change_quantity_{cart_item_id}",
            ),
            InlineKeyboardButton(
                text="➕", callback_data=f"increase_quantity_{cart_item_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="❌ Удалить",
                callback_data=f"remove_from_cart_{cart_item_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔄 Обновить корзину", callback_data="cart"
            ),
            InlineKeyboardButton(
                text="🔙 Назад в корзину", callback_data="cart"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_quantity_change_keyboard(cart_item_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для изменения количества товара в корзине"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="1", callback_data=f"set_quantity_{cart_item_id}_1"
            ),
            InlineKeyboardButton(
                text="2", callback_data=f"set_quantity_{cart_item_id}_2"
            ),
            InlineKeyboardButton(
                text="3", callback_data=f"set_quantity_{cart_item_id}_3"
            ),
        ],
        [
            InlineKeyboardButton(
                text="5", callback_data=f"set_quantity_{cart_item_id}_5"
            ),
            InlineKeyboardButton(
                text="10", callback_data=f"set_quantity_{cart_item_id}_10"
            ),
            InlineKeyboardButton(
                text="15", callback_data=f"set_quantity_{cart_item_id}_15"
            ),
        ],
        [
            InlineKeyboardButton(
                text="✏️ Ввести количество",
                callback_data=f"enter_cart_quantity_{cart_item_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=f"back_to_cart_item_{cart_item_id}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
