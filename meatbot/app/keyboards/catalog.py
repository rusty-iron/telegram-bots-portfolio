"""
Keyboards for catalog functionality
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_catalog_products_keyboard(
    products: list, category_id: int, page: int = 0, per_page: int = 10
) -> InlineKeyboardMarkup:
    """Клавиатура со списком товаров в каталоге с пагинацией"""
    keyboard = []

    # Показываем товары на текущей странице
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_products = products[start_idx:end_idx]

    for product in page_products:
        # Определяем иконку в зависимости от наличия фотографии
        icon = "📸" if product.image_url else "🥩"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{icon} {product.name} - {product.price}₽",
                    callback_data=f"product_{product.id}",
                )
            ]
        )

    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"category_{category_id}_page_{page - 1}",
            )
        )

    if end_idx < len(products):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"category_{category_id}_page_{page + 1}",
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопка возврата
    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔙 Назад к каталогу", callback_data="catalog"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
