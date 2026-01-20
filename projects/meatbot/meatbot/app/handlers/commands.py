"""
Основные команды бота
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ..database import User, get_db

router = Router()


@router.message(Command("start"))
async def start_command(message: Message):
    """Обработчик команды /start"""
    if not message.from_user:
        await message.answer("Ошибка: пользователь не найден")
        return

    user_id = message.from_user.id

    # Регистрируем пользователя в базе данных
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                is_active=True,
            )
            db.add(user)
            db.commit()

    welcome_text = (
        "🥩 **Добро пожаловать в MeatBot!**\n\n"
        "Я помогу вам заказать свежие мясные изделия прямо из Telegram!\n\n"
        "Выберите действие:"
    )

    # Создаем inline клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Каталог товаров", callback_data="catalog"
                ),
                InlineKeyboardButton(
                    text="🛒 Моя корзина", callback_data="cart"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📋 Мои заказы", callback_data="orders"
                ),
            ],
            [
                InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
                InlineKeyboardButton(text="📞 О боте", callback_data="about"),
            ],
        ]
    )

    await message.answer(
        welcome_text, parse_mode="Markdown", reply_markup=keyboard
    )


@router.message(Command("help"))
async def help_command(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "ℹ️ **Помощь по MeatBot**\n\n"
        "**Основные команды:**\n"
        "🛒 /catalog - Просмотр каталога товаров\n"
        "🛒 /cart - Просмотр корзины\n"
        "📋 /orders - Просмотр моих заказов\n"
        "ℹ️ /help - Эта справка\n\n"
        "**Как заказать:**\n"
        "1. Используйте /catalog для просмотра товаров\n"
        "2. Выберите категорию и товар\n"
        "3. Добавьте товар в корзину\n"
        "4. Используйте /cart для оформления заказа\n"
        "5. Используйте /orders для просмотра заказов\n\n"
        "**Поддержка:**\n"
        "Если у вас есть вопросы, обратитесь к администратору."
    )

    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("about"))
async def about_command(message: Message):
    """Обработчик команды /about"""
    about_text = (
        "🥩 **О MeatBot**\n\n"
        "MeatBot - это Telegram-бот для заказа свежих мясных изделий.\n\n"
        "**Возможности:**\n"
        "• Просмотр каталога товаров\n"
        "• Добавление товаров в корзину\n"
        "• Оформление заказов\n"
        "• Уведомления о статусе заказа\n\n"
        "**Версия:** 1.0.0\n"
        "**Разработчик:** MeatBot Team"
    )

    await message.answer(about_text, parse_mode="Markdown")


# Обработчики для inline кнопок
# Обработчик catalog перенесен в catalog.py для лучшей организации


@router.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Назад в меню'"""
    await callback.answer()

    welcome_text = (
        "🥩 **Добро пожаловать в MeatBot!**\n\n"
        "Я помогу вам заказать свежие мясные изделия прямо из Telegram!\n\n"
        "Выберите действие:"
    )

    # Создаем inline клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Каталог товаров", callback_data="catalog"
                ),
                InlineKeyboardButton(
                    text="🛒 Моя корзина", callback_data="cart"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📋 Мои заказы", callback_data="orders"
                ),
            ],
            [
                InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
                InlineKeyboardButton(text="📞 О боте", callback_data="about"),
            ],
        ]
    )

    if not callback.message or isinstance(
            callback.message, InaccessibleMessage):
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return

    assert isinstance(callback.message, Message)

    await callback.message.edit_text(
        welcome_text, parse_mode="Markdown", reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Назад в главное меню'"""
    await callback.answer()

    welcome_text = (
        "🥩 **Добро пожаловать в MeatBot!**\n\n"
        "Я помогу вам заказать свежие мясные изделия прямо из Telegram!\n\n"
        "Выберите действие:"
    )

    # Создаем inline клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Каталог товаров", callback_data="catalog"
                ),
                InlineKeyboardButton(
                    text="🛒 Моя корзина", callback_data="cart"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📋 Мои заказы", callback_data="orders"
                ),
            ],
            [
                InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
                InlineKeyboardButton(text="📞 О боте", callback_data="about"),
            ],
        ]
    )

    if not callback.message or isinstance(
            callback.message, InaccessibleMessage):
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return

    assert isinstance(callback.message, Message)

    await callback.message.edit_text(
        welcome_text, parse_mode="Markdown", reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "cart")
async def cart_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Моя корзина'"""
    import structlog

    logger = structlog.get_logger()

    logger.info(
        "cart_button_clicked",
        user_id=callback.from_user.id,
        username=callback.from_user.username,
    )

    await callback.answer()

    # Получаем корзину пользователя напрямую
    from ..database import CartItem, User, get_db

    user_id = callback.from_user.id

    with get_db() as db:
        logger.info("cart_callback_db_session_started", user_id=user_id)

        # Получаем или создаем пользователя
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Получаем товары из корзины
        cart_items = (
            db.query(CartItem).filter(CartItem.user_id == user.id).all()
        )

        logger.info(
            "cart_callback_items_found",
            user_id=user_id,
            cart_items_count=len(cart_items),
        )

        if not cart_items:
            # Создаем клавиатуру с кнопкой "Назад в меню" для пустой корзины
            empty_cart_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад в меню", callback_data="back_to_menu"
                        )
                    ]
                ]
            )

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                "🛒 Ваша корзина пуста!\n\n"
                "Используйте /catalog чтобы добавить товары.",
                parse_mode="Markdown",
                reply_markup=empty_cart_keyboard,
            )
            return

        # Формируем сообщение с товарами
        total_price = 0
        cart_text = "🛒 **Ваша корзина:**\n\n"

        keyboard_buttons = []
        for item in cart_items:
            product = item.product
            item_total = item.price_at_add * item.quantity
            total_price += item_total

            cart_text += f"🥩 **{product.name}**\n"
            cart_text += f"   💰 {
                item.price_at_add}₽ × {
                item.quantity} = {item_total}₽\n\n"

            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"❌ {product.name}",
                        callback_data=f"remove_from_cart_{item.id}",
                    )
                ]
            )

        cart_text += f"💳 **Итого: {total_price}₽**"

        # Добавляем кнопки управления
        keyboard_buttons.extend(
            [
                [
                    InlineKeyboardButton(
                        text="🛒 Оформить заказ", callback_data="checkout"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 Обновить корзину",
                        callback_data="refresh_cart",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад в меню", callback_data="back_to_menu"
                    )
                ],
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            cart_text, reply_markup=keyboard, parse_mode="Markdown"
        )


@router.callback_query(lambda c: c.data == "refresh_cart")
async def refresh_cart_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Обновить корзину'"""
    import structlog

    logger = structlog.get_logger()

    logger.info(
        "refresh_cart_clicked",
        user_id=callback.from_user.id,
        username=callback.from_user.username,
    )

    await callback.answer()

    # Вызываем тот же код, что и в cart_callback
    from ..database import CartItem, User, get_db

    user_id = callback.from_user.id

    with get_db() as db:
        logger.info("refresh_cart_db_session_started", user_id=user_id)

        # Получаем или создаем пользователя
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Получаем товары из корзины
        cart_items = (
            db.query(CartItem).filter(CartItem.user_id == user.id).all()
        )

        logger.info(
            "refresh_cart_items_found",
            user_id=user_id,
            cart_items_count=len(cart_items),
        )

        if not cart_items:
            # Создаем клавиатуру с кнопкой "Назад в меню" для пустой корзины
            empty_cart_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад в меню", callback_data="back_to_menu"
                        )
                    ]
                ]
            )

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                "🛒 Ваша корзина пуста!\n\n"
                "Используйте /catalog чтобы добавить товары.",
                parse_mode="Markdown",
                reply_markup=empty_cart_keyboard,
            )
            return

        # Формируем сообщение с товарами
        total_price = 0
        cart_text = "🛒 **Ваша корзина:**\n\n"

        keyboard_buttons = []
        for item in cart_items:
            product = item.product
            item_total = item.price_at_add * item.quantity
            total_price += item_total

            cart_text += f"🥩 **{product.name}**\n"
            cart_text += f"   💰 {
                item.price_at_add}₽ × {
                item.quantity} = {item_total}₽\n\n"

            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"❌ {product.name}",
                        callback_data=f"remove_from_cart_{item.id}",
                    )
                ]
            )

        cart_text += f"💳 **Итого: {total_price}₽**"

        # Добавляем кнопки управления
        keyboard_buttons.extend(
            [
                [
                    InlineKeyboardButton(
                        text="🛒 Оформить заказ", callback_data="checkout"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 Обновить корзину",
                        callback_data="refresh_cart",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад в меню", callback_data="back_to_menu"
                    )
                ],
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            cart_text, reply_markup=keyboard, parse_mode="Markdown"
        )


@router.callback_query(
    lambda c: c.data and c.data.startswith("remove_from_cart_")
)
async def remove_from_cart_callback(callback: CallbackQuery):
    """Обработчик кнопки удаления товара из корзины"""
    import structlog

    logger = structlog.get_logger()

    # Извлекаем ID товара из callback_data
    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    item_id = int(callback.data.replace("remove_from_cart_", ""))

    logger.info(
        "remove_from_cart_clicked",
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        item_id=item_id,
    )

    await callback.answer()

    from ..database import CartItem, User, get_db

    user_id = callback.from_user.id

    with get_db() as db:
        logger.info(
            "remove_from_cart_db_session_started",
            user_id=user_id,
            item_id=item_id,
        )

        # Получаем пользователя
        user = db.query(User).filter(User.id == user_id).first()
        if not user:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                "❌ Пользователь не найден!", parse_mode="Markdown"
            )
            return

        # Получаем товар из корзины
        cart_item = (
            db.query(CartItem)
            .filter(CartItem.id == item_id, CartItem.user_id == user.id)
            .first()
        )

        if not cart_item:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                "❌ Товар не найден в корзине!", parse_mode="Markdown"
            )
            return

        product_name = cart_item.product.name
        logger.info(
            "cart_item_found_for_removal",
            user_id=user_id,
            item_id=item_id,
            product_name=product_name,
        )

        # Удаляем товар из корзины
        db.delete(cart_item)
        db.commit()

        logger.info(
            "cart_item_removed",
            user_id=user_id,
            item_id=item_id,
            product_name=product_name,
        )

        # Получаем обновленный список товаров в корзине
        cart_items = (
            db.query(CartItem).filter(CartItem.user_id == user.id).all()
        )

        logger.info(
            "cart_after_removal",
            user_id=user_id,
            remaining_items_count=len(cart_items),
        )

        if not cart_items:
            # Создаем клавиатуру с кнопкой "Назад в меню" для пустой корзины
            empty_cart_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад в меню", callback_data="back_to_menu"
                        )
                    ]
                ]
            )

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                "🛒 Ваша корзина пуста!\n\n"
                "Используйте /catalog чтобы добавить товары.",
                parse_mode="Markdown",
                reply_markup=empty_cart_keyboard,
            )
            return

        # Формируем сообщение с товарами
        total_price = 0
        cart_text = "🛒 **Ваша корзина:**\n\n"

        keyboard_buttons = []
        for item in cart_items:
            product = item.product
            item_total = item.price_at_add * item.quantity
            total_price += item_total

            cart_text += f"🥩 **{product.name}**\n"
            cart_text += f"   💰 {
                item.price_at_add}₽ × {
                item.quantity} = {item_total}₽\n\n"

            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"❌ {product.name}",
                        callback_data=f"remove_from_cart_{item.id}",
                    )
                ]
            )

        cart_text += f"💳 **Итого: {total_price}₽**"

        # Добавляем кнопки управления
        keyboard_buttons.extend(
            [
                [
                    InlineKeyboardButton(
                        text="🛒 Оформить заказ", callback_data="checkout"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 Обновить корзину",
                        callback_data="refresh_cart",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад в меню", callback_data="back_to_menu"
                    )
                ],
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            cart_text, reply_markup=keyboard, parse_mode="Markdown"
        )


@router.callback_query(lambda c: c.data == "help")
async def help_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Помощь'"""
    await callback.answer()
    help_text = (
        "ℹ️ **Помощь по MeatBot**\n\n"
        "**Основные команды:**\n"
        "🛒 /catalog - Просмотр каталога товаров\n"
        "🛒 /cart - Просмотр корзины\n"
        "📋 /orders - Просмотр моих заказов\n"
        "ℹ️ /help - Эта справка\n\n"
        "**Как заказать:**\n"
        "1. Используйте кнопку 'Каталог товаров'\n"
        "2. Выберите категорию и товар\n"
        "3. Добавьте товар в корзину\n"
        "4. Используйте кнопку 'Моя корзина' для оформления\n"
        "5. Используйте кнопку 'Мои заказы' для просмотра заказов\n\n"
        "**Поддержка:**\n"
        "Если у вас есть вопросы, обратитесь к администратору."
    )

    # Создаем клавиатуру с кнопкой "Назад в меню"
    help_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад в меню", callback_data="back_to_menu"
                )
            ]
        ]
    )

    if not callback.message or isinstance(
            callback.message, InaccessibleMessage):
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return

    assert isinstance(callback.message, Message)

    await callback.message.edit_text(
        help_text, parse_mode="Markdown", reply_markup=help_keyboard
    )


@router.callback_query(lambda c: c.data == "orders")
async def orders_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Мои заказы'"""
    import structlog

    from ..keyboards.orders import get_orders_list_keyboard
    from ..services.order_service import OrderService

    logger = structlog.get_logger()
    order_service = OrderService()

    await callback.answer()

    user_id = callback.from_user.id
    if not user_id:

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.answer("Ошибка: пользователь не найден")
        return

    logger.info("user_orders_requested", user_id=user_id)

    # Получаем только активные заказы пользователя
    orders = order_service.get_user_orders(
        user_id=user_id, limit=50, active_only=True)

    logger.info(
        "user_orders_retrieved",
        user_id=user_id,
        orders_count=len(orders) if orders else 0,
    )

    if not orders:
        if callback.message and not isinstance(
                callback.message, InaccessibleMessage):
            assert isinstance(callback.message, Message)

            # Создаем клавиатуру с кнопками навигации
            from aiogram.types import (
                InlineKeyboardButton,
                InlineKeyboardMarkup,
            )

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📦 В каталог",
                            callback_data="catalog",
                        ),
                    ],
                ]
            )

            await callback.message.edit_text(
                "📋 **Активные заказы**\n\n"
                "У вас пока нет активных заказов.\n"
                "Используйте /catalog чтобы начать покупки!",
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
        return

    # Формируем сообщение со списком активных заказов
    orders_text = "📋 **Активные заказы:**\n\n"

    for order in orders[:5]:  # Показываем первые 5 заказов
        status_emoji = {
            "pending": "⏳",
            "confirmed": "✅",
            "processing": "🔄",
            "shipped": "🚚",
            "delivered": "📦",
            "cancelled": "❌",
        }.get(
            order["status"].value if hasattr(
                order["status"],
                "value") else order["status"],
            "❓")

        orders_text += (
            f"{status_emoji} **{order['order_number']}**\n"
            f"   💳 {order['total_amount']:.2f}₽\n"
            f"   📅 Заказ #{order['id']}\n\n"
        )

    if len(orders) > 5:
        orders_text += f"... и еще {len(orders) - 5} заказов\n\n"

    orders_text += "Нажмите на заказ для просмотра деталей:"

    if callback.message and not isinstance(
            callback.message, InaccessibleMessage):
        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            orders_text,
            reply_markup=get_orders_list_keyboard(orders),
            parse_mode="Markdown",
        )


@router.callback_query(lambda c: c.data == "about")
async def about_callback(callback: CallbackQuery):
    """Обработчик кнопки 'О боте'"""
    await callback.answer()
    about_text = (
        "🥩 **О MeatBot**\n\n"
        "MeatBot - это Telegram-бот для заказа свежих мясных изделий.\n\n"
        "**Возможности:**\n"
        "• Просмотр каталога товаров\n"
        "• Добавление товаров в корзину\n"
        "• Оформление заказов\n"
        "• Уведомления о статусе заказа\n\n"
        "**Версия:** 1.0.0\n"
        "**Разработчик:** MeatBot Team"
    )

    # Создаем клавиатуру с кнопкой "Назад в меню"
    about_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад в меню", callback_data="back_to_menu"
                )
            ]
        ]
    )

    if not callback.message or isinstance(
            callback.message, InaccessibleMessage):
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return

    assert isinstance(callback.message, Message)

    await callback.message.edit_text(
        about_text, parse_mode="Markdown", reply_markup=about_keyboard
    )
