"""
Handler для работы с корзиной
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ..database import CartItem, Product, User, get_db
from ..keyboards.cart import (
    get_cart_item_keyboard,
    get_quantity_selection_keyboard,
)

router = Router()


class CartStates(StatesGroup):
    """Состояния для работы с корзиной"""

    waiting_for_quantity = State()
    waiting_for_manual_quantity = State()


@router.message(Command("cart"))
async def show_cart(message: Message):
    """Показать корзину пользователя"""
    import structlog

    logger = structlog.get_logger()

    if not message.from_user:
        await message.answer("Ошибка: пользователь не найден")
        return

    user_id = message.from_user.id

    logger.info("show_cart_requested", user_id=user_id)

    with get_db() as db:
        # Получаем или создаем пользователя
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Получаем товары из корзины
        cart_items = (
            db.query(CartItem).filter(CartItem.user_id == user.id).all()
        )

        logger.info(
            "cart_items_found",
            user_id=user_id,
            cart_items_count=len(cart_items),
        )

        if not cart_items:
            await message.answer(
                "🛒 Ваша корзина пуста!\n\n"
                "Используйте /catalog чтобы добавить товары."
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
                        text=f"🥩 {product.name} ({item.quantity} шт)",
                        callback_data=f"manage_cart_item_{item.id}",
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
                    ),
                    InlineKeyboardButton(
                        text="📦 В каталог",
                        callback_data="catalog",
                    ),
                ],
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await message.answer(
            cart_text, reply_markup=keyboard, parse_mode="Markdown"
        )


@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    """Добавить товар в корзину - показать выбор количества"""
    import structlog

    logger = structlog.get_logger()

    try:
        # Validate callback data
        if not callback.data:
            await callback.answer("Некорректные данные запроса", show_alert=True)
            return

        parts = callback.data.split("_")
        if len(parts) < 4 or not parts[3].isdigit():
            await callback.answer("Некорректные данные запроса", show_alert=True)
            return

        product_id = int(parts[3])
        if not callback.from_user:
            await callback.answer("Ошибка: пользователь не найден", show_alert=True)
            return
        user_id = callback.from_user.id

        logger.info(
            "add_to_cart_requested",
            user_id=user_id,
            product_id=product_id,
            callback_data=callback.data,
        )

        with get_db() as db:
            # Получаем товар
            product = (
                db.query(Product).filter(Product.id == product_id).first()
            )
            if not product:
                logger.warning(
                    "add_to_cart_product_not_found",
                    user_id=user_id,
                    product_id=product_id,
                )
                await callback.answer("Товар не найден", show_alert=True)
                return

            # Проверяем наличие
            if not product.is_available:
                logger.warning(
                    "add_to_cart_product_unavailable",
                    user_id=user_id,
                    product_id=product_id,
                )
                await callback.answer("Товар недоступен", show_alert=True)
                return

            # Сохраняем данные товара в состоянии
            await state.update_data(
                product_id=product_id,
                product_name=product.name,
                product_price=float(product.price),
            )
            await state.set_state(CartStates.waiting_for_quantity)

            # Показываем клавиатуру выбора количества

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"🥩 **{product.name}**\n\n"
                f"💰 Цена: {product.price}₽ за {product.unit}\n\n"
                f"Выберите количество:",
                reply_markup=get_quantity_selection_keyboard(product_id),
                parse_mode="Markdown",
            )
            await callback.answer()

            logger.info(
                "add_to_cart_quantity_selection_shown",
                user_id=user_id,
                product_id=product_id,
                product_name=product.name,
            )

    except Exception as e:
        logger.error(
            "add_to_cart_error",
            user_id=callback.from_user.id if callback.from_user else None,
            error=str(e),
            callback_data=callback.data or "",
        )
        await callback.answer(
            "Произошла ошибка при добавлении товара", show_alert=True
        )


@router.callback_query(F.data.startswith("select_quantity_"))
async def select_quantity(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора количества товара"""
    import structlog

    logger = structlog.get_logger()

    try:
        # Парсим callback_data: select_quantity_{product_id}_{quantity}
        if not callback.data:
            await callback.answer("Некорректные данные запроса", show_alert=True)
            return

        parts = callback.data.split("_")
        if len(parts) < 4 or not parts[2].isdigit() or not parts[3].isdigit():
            await callback.answer("Некорректные данные запроса", show_alert=True)
            return

        product_id = int(parts[2])
        quantity = int(parts[3])

        if not callback.from_user:
            await callback.answer("Ошибка: пользователь не найден", show_alert=True)
            return

        user_id = callback.from_user.id

        logger.info(
            "select_quantity_requested",
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
        )

        # Получаем данные из состояния
        data = await state.get_data()
        if not data or data.get("product_id") != product_id:
            await callback.answer(
                "Сессия истекла. Попробуйте снова.", show_alert=True
            )
            return

        product_name = data["product_name"]
        product_price = data["product_price"]

        with get_db() as db:
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

            # Проверяем, есть ли уже в корзине
            existing_item = (
                db.query(CartItem)
                .filter(
                    CartItem.user_id == user.id,
                    CartItem.product_id == product_id,
                )
                .first()
            )

            if existing_item:
                existing_item.quantity += quantity
                logger.info(
                    "add_to_cart_quantity_increased",
                    user_id=user_id,
                    product_id=product_id,
                    added_quantity=quantity,
                    new_quantity=existing_item.quantity,
                )
            else:
                cart_item = CartItem(
                    user_id=user.id,
                    product_id=product_id,
                    quantity=quantity,
                    price_at_add=product_price,
                )
                db.add(cart_item)
                logger.info(
                    "add_to_cart_new_item_created",
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity,
                )

            db.commit()

        # Очищаем состояние
        await state.clear()

        # Создаем клавиатуру с кнопками навигации
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🛒 В корзину", callback_data="cart"
                    ),
                    InlineKeyboardButton(
                        text="📦 В каталог", callback_data="catalog"
                    ),
                ]
            ]
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            f"✅ **{product_name}** добавлен в корзину!\n\n"
            f"Количество: {quantity}\n"
            f"Цена: {product_price}₽ за шт\n"
            f"Итого: {product_price * quantity}₽",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        await callback.answer()

        logger.info(
            "add_to_cart_completed",
            user_id=user_id,
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
        )

    except Exception as e:
        logger.error(
            "select_quantity_error",
            user_id=callback.from_user.id if callback.from_user else None,
            error=str(e),
            callback_data=callback.data or "",
        )
        await callback.answer(
            "Произошла ошибка при добавлении товара", show_alert=True
        )


@router.callback_query(F.data == "cancel_quantity_selection")
async def cancel_quantity_selection(
    callback: CallbackQuery, state: FSMContext
):
    """Отмена выбора количества"""
    await state.clear()

    if not callback.message or isinstance(
            callback.message, InaccessibleMessage):
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return

    assert isinstance(callback.message, Message)

    await callback.message.edit_text("❌ Добавление товара в корзину отменено.")
    await callback.answer()


@router.callback_query(F.data.startswith("enter_quantity_"))
async def enter_quantity(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Ввести количество'"""
    if not callback.data:
        await callback.answer("Некорректные данные запроса", show_alert=True)
        return

    parts = callback.data.split("_")
    if len(parts) < 3 or not parts[2].isdigit():
        await callback.answer("Некорректные данные запроса", show_alert=True)
        return

    product_id = int(parts[2])

    # Проверяем, что мы в правильном состоянии
    data = await state.get_data()
    if not data or data.get("product_id") != product_id:
        await callback.answer(
            "Сессия истекла. Попробуйте снова.", show_alert=True
        )
        return

    await state.set_state(CartStates.waiting_for_manual_quantity)

    if not callback.message or isinstance(
            callback.message, InaccessibleMessage):
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return

    assert isinstance(callback.message, Message)

    await callback.message.edit_text(
        f"🥩 **{data['product_name']}**\n\n"
        f"💰 Цена: {data['product_price']}₽ за шт\n\n"
        f"Введите количество товара (от 1 до 99):",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(CartStates.waiting_for_manual_quantity)
async def process_manual_quantity(message: Message, state: FSMContext):
    """Обработка ручного ввода количества"""
    import structlog

    logger = structlog.get_logger()

    try:
        if message.text is None or not message.text.isdigit():
            await message.answer("❌ Пожалуйста, введите число от 1 до 99:")
            return

        quantity = int(message.text)
        if not message.from_user:
            await message.answer("Ошибка: пользователь не найден")
            return

        user_id = message.from_user.id

        if quantity < 1 or quantity > 99:
            await message.answer(
                "❌ Количество должно быть от 1 до 99. Попробуйте снова:"
            )
            return

        # Получаем данные из состояния
        data = await state.get_data()
        product_id = data["product_id"]
        product_name = data["product_name"]
        product_price = data["product_price"]

        logger.info(
            "manual_quantity_entered",
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
        )

        with get_db() as db:
            # Получаем или создаем пользователя
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                user = User(
                    id=user_id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            # Проверяем, есть ли уже в корзине
            existing_item = (
                db.query(CartItem)
                .filter(
                    CartItem.user_id == user.id,
                    CartItem.product_id == product_id,
                )
                .first()
            )

            if existing_item:
                existing_item.quantity += quantity
                logger.info(
                    "manual_add_to_cart_quantity_increased",
                    user_id=user_id,
                    product_id=product_id,
                    added_quantity=quantity,
                    new_quantity=existing_item.quantity,
                )
            else:
                cart_item = CartItem(
                    user_id=user.id,
                    product_id=product_id,
                    quantity=quantity,
                    price_at_add=product_price,
                )
                db.add(cart_item)
                logger.info(
                    "manual_add_to_cart_new_item_created",
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity,
                )

            db.commit()

        # Очищаем состояние
        await state.clear()

        # Создаем клавиатуру с кнопками навигации
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🛒 В корзину", callback_data="cart"
                    ),
                    InlineKeyboardButton(
                        text="📦 В каталог", callback_data="catalog"
                    ),
                ]
            ]
        )

        await message.answer(
            f"✅ **{product_name}** добавлен в корзину!\n\n"
            f"Количество: {quantity}\n"
            f"Цена: {product_price}₽ за шт\n"
            f"Итого: {product_price * quantity}₽",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

        logger.info(
            "manual_add_to_cart_completed",
            user_id=user_id,
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
        )

    except ValueError:
        await message.answer("❌ Пожалуйста, введите число от 1 до 99:")
    except Exception as e:
        logger.error(
            "manual_quantity_error",
            user_id=message.from_user.id if message.from_user else None,
            error=str(e),
        )
        await message.answer("❌ Произошла ошибка. Попробуйте снова.")
        await state.clear()


@router.callback_query(F.data.startswith("manage_cart_item_"))
async def manage_cart_item(callback: CallbackQuery):
    """Управление товаром в корзине"""
    if not callback.data:
        await callback.answer("Некорректные данные запроса", show_alert=True)
        return

    parts = callback.data.split("_")
    if len(parts) < 4 or not parts[3].isdigit():
        await callback.answer("Некорректные данные запроса", show_alert=True)
        return

    cart_item_id = int(parts[3])

    with get_db() as db:
        cart_item = (
            db.query(CartItem).filter(CartItem.id == cart_item_id).first()
        )
        if not cart_item:
            await callback.answer("Товар не найден в корзине", show_alert=True)
            return

        product = cart_item.product
        item_text = (
            f"🥩 **{product.name}**\n\n"
            f"💰 Цена: {cart_item.price_at_add}₽ за {product.unit}\n"
            f"📦 Количество: {cart_item.quantity}\n"
            f"💳 Итого: {cart_item.price_at_add * cart_item.quantity}₽\n\n"
            f"Выберите действие:"
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            item_text,
            reply_markup=get_cart_item_keyboard(
                cart_item_id, cart_item.quantity
            ),
            parse_mode="Markdown",
        )
        await callback.answer()


@router.callback_query(F.data.startswith("increase_quantity_"))
async def increase_quantity(callback: CallbackQuery):
    """Увеличить количество товара в корзине"""
    if not callback.data:
        await callback.answer("Некорректные данные запроса", show_alert=True)
        return

    parts = callback.data.split("_")
    if len(parts) < 3 or not parts[2].isdigit():
        await callback.answer("Некорректные данные запроса", show_alert=True)
        return

    cart_item_id = int(parts[2])

    with get_db() as db:
        cart_item = (
            db.query(CartItem).filter(CartItem.id == cart_item_id).first()
        )
        if not cart_item:
            await callback.answer("Товар не найден в корзине", show_alert=True)
            return

        cart_item.quantity += 1
        db.commit()

        product = cart_item.product
        item_text = (
            f"🥩 **{product.name}**\n\n"
            f"💰 Цена: {cart_item.price_at_add}₽ за {product.unit}\n"
            f"📦 Количество: {cart_item.quantity}\n"
            f"💳 Итого: {cart_item.price_at_add * cart_item.quantity}₽\n\n"
            f"Выберите действие:"
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            item_text,
            reply_markup=get_cart_item_keyboard(
                cart_item_id, cart_item.quantity
            ),
            parse_mode="Markdown",
        )
        await callback.answer("✅ Количество увеличено!")


@router.callback_query(F.data.startswith("decrease_quantity_"))
async def decrease_quantity(callback: CallbackQuery):
    """Уменьшить количество товара в корзине"""
    if not callback.data:
        await callback.answer("Некорректные данные запроса", show_alert=True)
        return

    parts = callback.data.split("_")
    if len(parts) < 3 or not parts[2].isdigit():
        await callback.answer("Некорректные данные запроса", show_alert=True)
        return

    cart_item_id = int(parts[2])

    with get_db() as db:
        cart_item = (
            db.query(CartItem).filter(CartItem.id == cart_item_id).first()
        )
        if not cart_item:
            await callback.answer("Товар не найден в корзине", show_alert=True)
            return

        if cart_item.quantity <= 1:
            await callback.answer("Минимальное количество: 1", show_alert=True)
            return

        cart_item.quantity -= 1
        db.commit()

        product = cart_item.product
        item_text = (
            f"🥩 **{product.name}**\n\n"
            f"💰 Цена: {cart_item.price_at_add}₽ за {product.unit}\n"
            f"📦 Количество: {cart_item.quantity}\n"
            f"💳 Итого: {cart_item.price_at_add * cart_item.quantity}₽\n\n"
            f"Выберите действие:"
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            item_text,
            reply_markup=get_cart_item_keyboard(
                cart_item_id, cart_item.quantity
            ),
            parse_mode="Markdown",
        )
        await callback.answer("✅ Количество уменьшено!")


@router.callback_query(F.data == "cart")
async def back_to_cart(callback: CallbackQuery):
    """Вернуться к корзине"""
    await show_cart(callback.message)


@router.callback_query(F.data.startswith("remove_from_cart_"))
async def remove_from_cart(callback: CallbackQuery):
    """Удалить товар из корзины"""
    if not callback.data:
        await callback.answer("Некорректные данные запроса", show_alert=True)
        return

    parts = callback.data.split("_")
    if len(parts) < 4 or not parts[3].isdigit():
        await callback.answer("Некорректные данные запроса", show_alert=True)
        return

    cart_item_id = int(parts[3])

    with get_db() as db:
        cart_item = (
            db.query(CartItem).filter(CartItem.id == cart_item_id).first()
        )
        if not cart_item:
            await callback.answer("Товар не найден в корзине", show_alert=True)
            return

        # Сохраняем название товара для использования после закрытия сессии
        product_name = cart_item.product.name
        db.delete(cart_item)
        db.commit()

    await callback.answer(f"❌ {product_name} удален из корзины!")

    # Обновляем корзину
    await show_cart(callback.message)


@router.callback_query(F.data == "refresh_cart")
async def refresh_cart(callback: CallbackQuery):
    """Обновить корзину"""
    await show_cart(callback.message)
