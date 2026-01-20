"""
Клавиатуры для административной панели
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню администратора"""
    keyboard = [
        [InlineKeyboardButton(text="📦 Управление товарами", callback_data="admin_products")],
        [InlineKeyboardButton(text="📋 Категории", callback_data="admin_categories")],
        [InlineKeyboardButton(text="🛒 Управление заказами", callback_data="admin_orders")],
        [InlineKeyboardButton(text="💳 Настройки оплаты", callback_data="admin_payment_settings")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_products_management_keyboard() -> InlineKeyboardMarkup:
    """Меню управления товарами"""
    keyboard = [
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
        [
            InlineKeyboardButton(
                text="📝 Редактировать товар",
                callback_data="admin_edit_product",
            )
        ],
        [InlineKeyboardButton(text="🗑️ Удалить товар", callback_data="admin_delete_product")],
        [
            InlineKeyboardButton(
                text="🔄 Активировать товар",
                callback_data="admin_activate_product",
            )
        ],
        [InlineKeyboardButton(text="📸 Управление фото", callback_data="admin_manage_photos")],
        [InlineKeyboardButton(text="🔙 Назад в админку", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_categories_management_keyboard() -> InlineKeyboardMarkup:
    """Меню управления категориями"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="➕ Добавить категорию",
                callback_data="admin_add_category",
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 Редактировать категорию",
                callback_data="admin_edit_category",
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑️ Удалить категорию",
                callback_data="admin_delete_category",
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Активировать категорию",
                callback_data="admin_activate_category",
            )
        ],
        [InlineKeyboardButton(text="🔙 Назад в админку", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_product_list_keyboard(
    products: list, page: int = 0, per_page: int = 10, action: str = "view"
) -> InlineKeyboardMarkup:
    """Клавиатура со списком товаров с пагинацией"""
    keyboard = []

    # Показываем товары на текущей странице
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_products = products[start_idx:end_idx]

    # Определяем callback_data и текст кнопки в зависимости от действия
    action_config = {
        "view": ("admin_view_product_", "📦"),
        "edit": ("admin_edit_product_", "✏️"),
        "delete": ("admin_delete_product_", "🗑️"),
    }

    callback_prefix, icon = action_config.get(
        action, ("admin_view_product_", "📦"))

    for product in page_products:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{icon} {product.name}",
                    callback_data=f"{callback_prefix}{product.id}",
                )
            ]
        )

    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"admin_products_page_{
                    page - 1}"))

    if end_idx < len(products):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"admin_products_page_{
                    page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопка возврата
    keyboard.append([InlineKeyboardButton(
        text="🔙 Назад", callback_data="admin_products")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_category_list_keyboard(
    categories: list, page: int = 0, per_page: int = 5
) -> InlineKeyboardMarkup:
    """Клавиатура со списком категорий"""
    keyboard = []

    # Показываем категории на текущей странице
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_categories = categories[start_idx:end_idx]

    for category in page_categories:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"📋 {category.name}",
                    callback_data=f"admin_view_category_{category.id}",
                )
            ]
        )

    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"admin_categories_page_{page - 1}",
            )
        )

    if end_idx < len(categories):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"admin_categories_page_{page + 1}",
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопка возврата
    keyboard.append([InlineKeyboardButton(
        text="🔙 Назад", callback_data="admin_categories")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_product_actions_keyboard(
    product_id: int, is_active: bool = True, context: str = "general"
) -> InlineKeyboardMarkup:
    """Клавиатура действий с товаром"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✏️ Редактировать",
                callback_data=f"admin_edit_product_{product_id}",
            ),
        ],
    ]

    # Добавляем кнопку в зависимости от статуса товара
    if is_active:
        # Для активных товаров - кнопка "Удалить"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🗑️ Удалить",
                    callback_data=f"admin_delete_product_{product_id}",
                )
            ]
        )
    else:
        # Для неактивных товаров - кнопка "Активировать"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🔄 Активировать",
                    callback_data=f"admin_restore_product_{product_id}",
                )
            ]
        )

    # Добавляем кнопку возврата в зависимости от контекста
    if context == "photo_management":
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🔙 К управлению фото",
                    callback_data="admin_manage_photos",
                )
            ]
        )
    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🔙 К списку товаров",
                    callback_data="admin_list_products",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_category_actions_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с категорией"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✏️ Редактировать",
                callback_data=f"admin_edit_category_{category_id}",
            ),
            InlineKeyboardButton(
                text="🗑️ Удалить",
                callback_data=f"admin_delete_category_{category_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔄 Изменить статус",
                callback_data=f"admin_toggle_category_{category_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 К списку категорий",
                callback_data="admin_list_categories",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_photo_management_keyboard() -> InlineKeyboardMarkup:
    """Меню управления фотографиями товаров"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📸 Добавить фото к товару",
                callback_data="admin_add_photo",
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑️ Удалить фото товара",
                callback_data="admin_delete_photo",
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Просмотр товаров с фото",
                callback_data="admin_view_products_with_photos",
            )
        ],
        [InlineKeyboardButton(text="🔙 К управлению товарами", callback_data="admin_products")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_products_for_photo_keyboard(
    products: list,
    page: int = 0,
    per_page: int = 10,
    action: str = "add_photo",
) -> InlineKeyboardMarkup:
    """Клавиатура со списком товаров для управления фотографиями с пагинацией"""
    keyboard = []

    # Показываем товары на текущей странице
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_products = products[start_idx:end_idx]

    # Определяем callback_data и текст кнопки в зависимости от действия
    action_config = {
        "add_photo": ("admin_add_photo_to_", "📸", "📷"),
        "delete_photo": ("admin_delete_photo_from_", "🗑️", "❌"),
        "view_photos": ("admin_view_photo_product_", "👁️", "👁️"),
    }

    callback_prefix, icon_with_photo, icon_without_photo = action_config.get(
        action, ("admin_add_photo_to_", "📸", "📷")
    )

    for product in page_products:
        # Определяем иконку в зависимости от наличия фотографии
        icon = icon_with_photo if product.image_url else icon_without_photo

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{icon} {product.name}",
                    callback_data=f"{callback_prefix}{product.id}",
                )
            ]
        )

    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"admin_photo_page_{action}_{page - 1}",
            )
        )

    if end_idx < len(products):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"admin_photo_page_{action}_{page + 1}",
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопка возврата
    keyboard.append([InlineKeyboardButton(
        text="🔙 К управлению фото", callback_data="admin_manage_photos")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_category_list_keyboard_with_pagination(
    categories: list, page: int = 0, per_page: int = 10, action: str = "view"
) -> InlineKeyboardMarkup:
    """Клавиатура со списком категорий с пагинацией"""
    keyboard = []

    # Показываем категории на текущей странице
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_categories = categories[start_idx:end_idx]

    # Определяем callback_data и текст кнопки в зависимости от действия
    action_config = {
        "view": ("admin_view_category_", "📋"),
        "edit": ("admin_edit_category_", "✏️"),
        "delete": ("admin_delete_category_", "🗑️"),
        "activate": ("admin_activate_category_", "🔄"),
    }

    callback_prefix, icon = action_config.get(
        action, ("admin_view_category_", "📋"))

    for category in page_categories:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{icon} {category.name}",
                    callback_data=f"{callback_prefix}{category.id}",
                )
            ]
        )

    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"admin_category_page_{action}_{page - 1}",
            )
        )

    if end_idx < len(categories):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"admin_category_page_{action}_{page + 1}",
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопка возврата
    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔙 К управлению категориями",
                callback_data="admin_categories",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_product_list_keyboard_with_pagination(
    products: list, page: int = 0, per_page: int = 10, action: str = "view"
) -> InlineKeyboardMarkup:
    """Клавиатура со списком товаров с пагинацией"""
    keyboard = []

    # Показываем товары на текущей странице
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_products = products[start_idx:end_idx]

    # Определяем callback_data и текст кнопки в зависимости от действия
    action_config = {
        "view": ("admin_view_product_", "📦"),
        "edit": ("admin_edit_product_", "✏️"),
        "delete": ("admin_delete_product_", "🗑️"),
        "activate": ("admin_activate_product_", "🔄"),
    }

    callback_prefix, icon = action_config.get(
        action, ("admin_view_product_", "📦"))

    for product in page_products:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{icon} {product.name}",
                    callback_data=f"{callback_prefix}{product.id}",
                )
            ]
        )

    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"admin_product_page_{action}_{page - 1}",
            )
        )

    if end_idx < len(products):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"admin_product_page_{action}_{page + 1}",
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопка возврата
    keyboard.append([InlineKeyboardButton(
        text="🔙 К управлению товарами", callback_data="admin_products")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_payment_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек платежа"""
    keyboard = [
        [
            InlineKeyboardButton(text="🏦 Изменить банк", callback_data="admin_edit_bank"),
            InlineKeyboardButton(text="💳 Изменить карту", callback_data="admin_edit_card"),
        ],
        [
            InlineKeyboardButton(
                text="👤 Изменить получателя",
                callback_data="admin_edit_recipient",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📝 Изменить доп. информацию",
                callback_data="admin_edit_info",
            ),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад в админ-панель", callback_data="admin_main"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cancel_edit_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для отмены редактирования"""
    keyboard = [[InlineKeyboardButton(
        text="❌ Отменить", callback_data="cancel_payment_edit"), ], ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_to_payment_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура возврата к настройкам платежа"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔙 К настройкам оплаты",
                callback_data="admin_payment_settings",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата в админ-панель"""
    keyboard = [[InlineKeyboardButton(
        text="🔙 Назад в админку", callback_data="admin_main")], ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cancel_keyboard(
        back_callback: str = "admin_main") -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены для FSM состояний"""
    keyboard = [
        [InlineKeyboardButton(text="❌ Отменить", callback_data=back_callback)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_to_products_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура возврата к управлению товарами"""
    keyboard = [[InlineKeyboardButton(
        text="🔙 К управлению товарами", callback_data="admin_products")], ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_to_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура возврата к управлению категориями"""
    keyboard = [[InlineKeyboardButton(
        text="🔙 К управлению категориями", callback_data="admin_categories")], ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_to_orders_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура возврата к управлению заказами"""
    keyboard = [[InlineKeyboardButton(
        text="🔙 К управлению заказами", callback_data="admin_orders")], ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
