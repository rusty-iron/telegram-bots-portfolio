"""
Handlers для работы с заказами
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    Message,
    ReplyKeyboardRemove,
)

from ..database import CartItem, User, get_db
from ..keyboards.orders import (
    get_address_request_keyboard,
    get_cancel_order_keyboard,
    get_order_details_keyboard,
    get_order_success_keyboard,
    get_orders_history_keyboard,
    get_orders_list_keyboard,
    get_payment_methods_keyboard,
    get_phone_request_keyboard,
    get_phone_share_keyboard,
    get_skip_notes_keyboard,
)
from ..services.order_service import OrderService
from ..utils.validation import (
    ValidationError,
    validate_address,
    validate_delivery_notes,
    validate_payment_method,
    validate_phone_number,
)

router = Router()
order_service = OrderService()


def mask_phone(phone: str) -> str:
    """Маскирует номер телефона для безопасного логирования (GDPR compliance)"""
    if not phone or len(phone) < 4:
        return "***"
    return phone[:2] + "*" * (len(phone) - 4) + phone[-2:]


class OrderStates(StatesGroup):
    """Состояния для оформления заказа"""

    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_delivery_notes = State()
    waiting_for_payment_method = State()
    waiting_for_confirmation = State()
    # Для ожидания документа подтверждения перевода
    waiting_for_payment_document = State()


@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Начало оформления заказа"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id
    if not user_id:
        await callback.answer(
            "Ошибка: пользователь не найден", show_alert=True
        )
        return

    logger.info("checkout_started", user_id=user_id)

    # Проверяем, что корзина не пуста
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        cart_items = (
            db.query(CartItem).filter(CartItem.user_id == user.id).all()
        )

        if not cart_items:
            await callback.answer("Корзина пуста", show_alert=True)
            return

        # Получаем данные пользователя внутри контекста БД
        saved_phone = user.phone

    # Начинаем процесс оформления заказа
    await state.set_state(OrderStates.waiting_for_phone)
    await state.update_data(
        user_id=user_id,
        cart_items_count=len(cart_items),
    )

    # Проверяем, есть ли сохраненный номер телефона
    has_saved_phone = bool(saved_phone)

    if not callback.message or isinstance(
        callback.message, InaccessibleMessage
    ):
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return

    assert isinstance(callback.message, Message)

    # Формируем текст сообщения
    text = (
        "🛒 **Оформление заказа**\n\n"
        "Для оформления заказа нам нужны ваши контактные данные.\n\n"
        "📞 **Введите номер телефона для связи:**\n"
        "Формат: +7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
    )

    if has_saved_phone:
        text += (
            f"💾 Ваш сохраненный номер: {saved_phone}\n\n"
            "Вы можете:\n"
            "• Нажать кнопку ниже для использования сохраненного номера\n"
            '• Или нажать кнопку "Поделиться номером" для автоматической отправки\n'
            "• Или ввести новый номер вручную"
        )
    else:
        text += (
            "Вы можете:\n"
            '• Нажать кнопку "Поделиться номером" для автоматической отправки\n'
            "• Или ввести номер вручную"
        )

    # Отправляем сообщение с inline клавиатурой
    await callback.message.edit_text(
        text,
        reply_markup=get_phone_request_keyboard(has_saved_phone),
        parse_mode="Markdown",
    )

    # Отправляем дополнительное сообщение с ReplyKeyboard для кнопки "Поделиться"
    await callback.message.answer(
        "👇 Нажмите на кнопку ниже или введите номер вручную:",
        reply_markup=get_phone_share_keyboard(),
    )

    await callback.answer()


@router.callback_query(
    F.data == "use_saved_phone", OrderStates.waiting_for_phone
)
async def use_saved_phone(callback: CallbackQuery, state: FSMContext):
    """Использование сохраненного номера телефона"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.phone:
            await callback.answer(
                "❌ Сохраненный номер не найден", show_alert=True
            )
            return

        phone = user.phone

        # Сохраняем телефон
        await state.update_data(phone=phone)
        await state.set_state(OrderStates.waiting_for_address)

        # Проверяем, есть ли сохраненный адрес
        has_saved_address = bool(user.delivery_address)

        if callback.message and not isinstance(
            callback.message, InaccessibleMessage
        ):
            assert isinstance(callback.message, Message)

            # Формируем текст
            text = (
                "✅ **Номер телефона принят!**\n\n"
                f"📞 Телефон: {phone}\n\n"
                "📍 **Введите адрес доставки:**\n"
                "Укажите полный адрес с улицей, домом и квартирой\n\n"
            )

            if has_saved_address:
                text += (
                    f"💾 Ваш сохраненный адрес: {user.delivery_address}\n\n"
                    "Вы можете использовать сохраненный адрес или ввести новый"
                )

            await callback.message.edit_text(
                text,
                reply_markup=get_address_request_keyboard(has_saved_address),
                parse_mode="Markdown",
            )

            # Убираем ReplyKeyboard с кнопкой "Поделиться"
            await callback.message.answer(
                "📝 Ожидаем ваш ответ...", reply_markup=ReplyKeyboardRemove()
            )

        await callback.answer("✅ Используем сохраненный номер")
        logger.info("saved_phone_used", user_id=user_id, phone=mask_phone(phone))


@router.message(OrderStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Обработка номера телефона через кнопку 'Поделиться номером'"""
    import structlog

    logger = structlog.get_logger()

    if not message.from_user:
        await message.answer("❌ Ошибка: пользователь не найден")
        return

    user_id = message.from_user.id

    if not message.contact:
        await message.answer("❌ Не удалось получить контакт")
        return

    # Получаем номер из контакта
    phone = message.contact.phone_number

    # Форматируем номер (добавляем + если его нет)
    if not phone.startswith("+"):
        phone = f"+{phone}"

    # Сохраняем телефон
    await state.update_data(phone=phone)
    await state.set_state(OrderStates.waiting_for_address)

    # Проверяем, есть ли сохраненный адрес
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        has_saved_address = bool(user.delivery_address) if user else False

        # Формируем текст
        text = (
            "✅ **Номер телефона принят!**\n\n"
            f"📞 Телефон: {phone}\n\n"
            "📍 **Введите адрес доставки:**\n"
            "Укажите полный адрес с улицей, домом и квартирой\n\n"
        )

        if has_saved_address and user:
            text += (
                f"💾 Ваш сохраненный адрес: {user.delivery_address}\n\n"
                "Вы можете использовать сохраненный адрес или ввести новый"
            )

        # Отправляем сообщение с удалением ReplyKeyboard
        await message.answer(
            text,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown",
        )

        # Отправляем inline клавиатуру отдельным сообщением
        await message.answer(
            "👇 Выберите действие:",
            reply_markup=get_address_request_keyboard(has_saved_address),
        )

    logger.info("phone_contact_received", user_id=user_id, phone=mask_phone(phone))


@router.message(OrderStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка номера телефона"""
    import structlog

    logger = structlog.get_logger()
    if not message.from_user:
        await message.answer("Ошибка: пользователь не найден")
        return

    user_id = message.from_user.id
    if not user_id:
        await message.answer("Ошибка: пользователь не найден")
        return

    try:
        # Валидируем номер телефона
        if not message.text:
            await message.answer("Пожалуйста, введите номер телефона")
            return
        phone = validate_phone_number(message.text)

        # Сохраняем телефон
        await state.update_data(phone=phone)
        await state.set_state(OrderStates.waiting_for_address)

        # Проверяем, есть ли сохраненный адрес
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            has_saved_address = bool(user.delivery_address) if user else False

            # Формируем текст
            text = (
                "✅ **Номер телефона принят!**\n\n"
                f"📞 Телефон: {phone}\n\n"
                "📍 **Введите адрес доставки:**\n"
                "Укажите полный адрес с улицей, домом и квартирой\n\n"
            )

            if has_saved_address and user:
                text += (
                    f"💾 Ваш сохраненный адрес: {user.delivery_address}\n\n"
                    "Вы можете использовать сохраненный адрес или ввести новый"
                )

            # Отправляем сообщение с удалением ReplyKeyboard
            await message.answer(
                text,
                reply_markup=ReplyKeyboardRemove(),
                parse_mode="Markdown",
            )

            # Отправляем inline клавиатуру отдельным сообщением
            await message.answer(
                "👇 Выберите действие:",
                reply_markup=get_address_request_keyboard(has_saved_address),
            )

        logger.info(
            "phone_validated", user_id=user_id, phone=phone
        )  # type: ignore

    except ValidationError as e:
        await message.answer(
            f"❌ **Ошибка в номере телефона:**\n\n{e.message}\n\n"
            "Попробуйте еще раз:",
            parse_mode="Markdown",
        )
        logger.warning(
            "phone_validation_failed", user_id=user_id, error=e.message  # type: ignore
        )


@router.callback_query(
    F.data == "use_saved_address", OrderStates.waiting_for_address
)
async def use_saved_address(callback: CallbackQuery, state: FSMContext):
    """Использование сохраненного адреса доставки"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.delivery_address:
            await callback.answer(
                "❌ Сохраненный адрес не найден", show_alert=True
            )
            return

        address = user.delivery_address

        # Сохраняем адрес
        await state.update_data(address=address)
        await state.set_state(OrderStates.waiting_for_delivery_notes)

        # Проверяем, есть ли сохраненные комментарии
        has_saved_notes = bool(user.delivery_notes)

        if callback.message and not isinstance(
            callback.message, InaccessibleMessage
        ):
            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                "✅ **Адрес принят!**\n\n"
                f"📍 Адрес: {address}\n\n"
                "📝 **Комментарии к доставке (необязательно):**\n"
                "Укажите дополнительную информацию для курьера, "
                "например, код домофона или ориентиры",
                reply_markup=get_skip_notes_keyboard(has_saved_notes),
                parse_mode="Markdown",
            )

        await callback.answer("✅ Используем сохраненный адрес")
        logger.info("saved_address_used", user_id=user_id, address=address)


@router.message(OrderStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка адреса доставки"""
    import structlog

    logger = structlog.get_logger()
    if not message.from_user:
        await message.answer("Ошибка: пользователь не найден")
        return

    user_id = message.from_user.id
    if not user_id:
        await message.answer("Ошибка: пользователь не найден")
        return

    try:
        # Валидируем адрес
        if not message.text:
            await message.answer("Пожалуйста, введите адрес доставки")
            return
        address = validate_address(message.text)

        # Сохраняем адрес
        await state.update_data(address=address)
        await state.set_state(OrderStates.waiting_for_delivery_notes)

        # Проверяем, есть ли сохраненные комментарии
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            has_saved_notes = bool(user.delivery_notes) if user else False

            await message.answer(
                "✅ **Адрес принят!**\n\n"
                f"📍 Адрес: {address}\n\n"
                "📝 **Комментарии к доставке (необязательно):**\n"
                "Укажите дополнительную информацию для курьера, "
                "например, код домофона или ориентиры",
                reply_markup=get_skip_notes_keyboard(has_saved_notes),
                parse_mode="Markdown",
            )

        logger.info(
            "address_validated", user_id=user_id, address=address
        )  # type: ignore

    except ValidationError as e:
        await message.answer(
            f"❌ **Ошибка в адресе:**\n\n{e.message}\n\n" "Попробуйте еще раз:",
            parse_mode="Markdown",
        )
        logger.warning(
            "address_validation_failed", user_id=user_id, error=e.message  # type: ignore
        )


@router.message(OrderStates.waiting_for_delivery_notes)
async def process_delivery_notes(message: Message, state: FSMContext):
    """Обработка комментариев к доставке"""
    import structlog

    logger = structlog.get_logger()
    if not message.from_user:
        await message.answer("Ошибка: пользователь не найден")
        return

    user_id = message.from_user.id
    if not user_id:
        await message.answer("Ошибка: пользователь не найден")
        return

    try:
        # Валидируем комментарии
        if not message.text:
            await message.answer(
                "Пожалуйста, введите комментарии или нажмите 'Пропустить'"
            )
            return
        notes = validate_delivery_notes(message.text)

        # Сохраняем комментарии
        await state.update_data(notes=notes)
        await state.set_state(OrderStates.waiting_for_payment_method)

        # Показываем выбор способа оплаты
        await message.answer(
            "✅ **Комментарии приняты!**\n\n"
            f"📝 Комментарии: {notes if notes else 'Не указаны'}\n\n"
            "💳 **Выберите способ оплаты:**",
            reply_markup=get_payment_methods_keyboard(),
            parse_mode="Markdown",
        )

        logger.info(
            "notes_validated", user_id=user_id, notes=notes
        )  # type: ignore

    except ValidationError as e:
        # Проверяем, есть ли сохраненные комментарии
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            has_saved_notes = bool(user.delivery_notes) if user else False

            await message.answer(
                f"❌ **Ошибка в комментариях:**\n\n{e.message}\n\n"
                "Попробуйте еще раз или нажмите 'Пропустить':",
                reply_markup=get_skip_notes_keyboard(has_saved_notes),
                parse_mode="Markdown",
            )
        logger.warning(
            "notes_validation_failed", user_id=user_id, error=e.message  # type: ignore
        )


@router.callback_query(
    F.data == "use_saved_notes", OrderStates.waiting_for_delivery_notes
)
async def use_saved_notes(callback: CallbackQuery, state: FSMContext):
    """Использование сохраненных комментариев к доставке"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.delivery_notes:
            await callback.answer(
                "❌ Сохраненные комментарии не найдены", show_alert=True
            )
            return

        notes = user.delivery_notes

        # Сохраняем комментарии
        await state.update_data(notes=notes)
        await state.set_state(OrderStates.waiting_for_payment_method)

        if callback.message and not isinstance(
            callback.message, InaccessibleMessage
        ):
            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                f"✅ **Комментарии приняты!**\n\n"
                f"📝 Комментарии: {notes}\n\n"
                "💳 **Выберите способ оплаты:**",
                reply_markup=get_payment_methods_keyboard(),
                parse_mode="Markdown",
            )

        await callback.answer("✅ Используем сохраненные комментарии")
        logger.info("saved_notes_used", user_id=user_id, notes=notes)


@router.callback_query(F.data == "skip_notes")
async def skip_notes(callback: CallbackQuery, state: FSMContext):
    """Пропуск комментариев к доставке"""
    await state.update_data(notes="")
    await state.set_state(OrderStates.waiting_for_payment_method)

    if callback.message and not isinstance(
        callback.message, InaccessibleMessage
    ):
        if not callback.message or isinstance(
            callback.message, InaccessibleMessage
        ):
            await callback.answer(
                "❌ Ошибка обработки запроса", show_alert=True
            )
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            "📝 **Комментарии пропущены**\n\n" "💳 **Выберите способ оплаты:**",
            reply_markup=get_payment_methods_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("payment_method_"))
async def select_payment_method(callback: CallbackQuery, state: FSMContext):
    """Выбор способа оплаты"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    try:
        # Извлекаем способ оплаты
        if not callback.data:
            await callback.answer("Ошибка: неверные данные", show_alert=True)
            return
        payment_method = callback.data.split("_")[2]
        validate_payment_method(payment_method)

        # Сохраняем способ оплаты
        await state.update_data(payment_method=payment_method)

        # Получаем все данные заказа
        data = await state.get_data()

        # Проверяем, что все необходимые данные есть
        required_fields = ["phone", "address"]
        missing_fields = [
            field
            for field in required_fields
            if field not in data or not data[field]
        ]

        if missing_fields:
            await callback.answer(
                f"❌ Отсутствуют данные: {', '.join(missing_fields)}. Начните оформление заказа заново.",
                show_alert=True,
            )
            await state.clear()
            return

        # Рассчитываем сумму заказа и подготавливаем данные
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                await callback.answer(
                    "Пользователь не найден", show_alert=True
                )
                return

            # Загружаем cart_items с продуктами
            cart_items = (
                db.query(CartItem)
                .join(CartItem.product)
                .filter(CartItem.user_id == user.id)
                .all()
            )

            total_price = sum(
                item.price_at_add * item.quantity for item in cart_items
            )

            # Подготавливаем данные для передачи в функции
            cart_data = []
            for item in cart_items:
                cart_data.append(
                    {
                        "product_name": item.product.name,
                        "quantity": item.quantity,
                        "price": item.price_at_add,
                        "total": item.price_at_add * item.quantity,
                    }
                )

        if payment_method == "cash":
            # Для наличных - сразу создаем заказ
            await create_cash_order(
                callback, state, data, cart_data, total_price
            )
        elif payment_method == "transfer":
            # Для перевода - показываем реквизиты и ждем документ
            await show_payment_details(
                callback, state, data, cart_data, total_price
            )

        logger.info(
            "payment_method_selected",
            user_id=user_id,  # type: ignore
            payment_method=payment_method,
        )

    except ValidationError as e:
        await callback.answer(f"Ошибка: {e.message}", show_alert=True)
        logger.warning(
            "payment_method_validation_failed",
            user_id=user_id,  # type: ignore
            error=e.message,
        )


async def create_cash_order(
    callback: CallbackQuery,
    state: FSMContext,
    data: dict,
    cart_data: list,
    total_price: float,
):
    """Создание заказа с наличной оплатой"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    try:
        # Создаем заказ
        delivery_data = {
            "phone": data["phone"],
            "address": data["address"],
            "notes": data.get("notes", ""),
        }

        order = order_service.create_order_from_cart(
            user_id=user_id,
            delivery_data=delivery_data,
            payment_method="cash",
        )

        if order:
            # Очищаем состояние
            await state.clear()

            # Формируем сообщение об успешном создании заказа
            success_message = (
                "🎉 **Заказ успешно создан!**\n\n"
                f"📋 **Номер заказа:** {order['order_number']}\n"
                f"💳 **Сумма:** {order['total_amount']}₽\n"
                f"💵 **Оплата:** наличными при получении\n\n"
                "📞 Мы свяжемся с вами для подтверждения заказа.\n"
                "🚚 Время доставки: 1-2 часа\n\n"
                "Спасибо за заказ! 🙏"
            )

            if callback.message and not isinstance(
                callback.message, InaccessibleMessage
            ):
                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

                assert isinstance(callback.message, Message)

                await callback.message.edit_text(
                    success_message,
                    reply_markup=get_order_success_keyboard(),
                    parse_mode="Markdown",
                )

            logger.info(
                "cash_order_created_successfully",
                user_id=user_id,  # type: ignore
                order_id=order["id"],
                order_number=order["order_number"],
            )

        else:
            if callback.message and not isinstance(
                callback.message, InaccessibleMessage
            ):
                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

                assert isinstance(callback.message, Message)

                await callback.message.edit_text(
                    "❌ **Ошибка при создании заказа**\n\n"
                    "Попробуйте еще раз или обратитесь в поддержку.",
                    parse_mode="Markdown",
                )

            logger.error(
                "cash_order_creation_failed", user_id=user_id
            )  # type: ignore

    except Exception as e:
        logger.error(
            # type: ignore
            "create_cash_order_error",
            user_id=user_id,
            error=str(e),
        )
        if callback.message and not isinstance(
            callback.message, InaccessibleMessage
        ):
            if not callback.message or isinstance(
                callback.message, InaccessibleMessage
            ):
                await callback.answer(
                    "❌ Ошибка обработки запроса", show_alert=True
                )
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                "❌ **Произошла ошибка**\n\n"
                "Попробуйте еще раз или обратитесь в поддержку.",
                parse_mode="Markdown",
            )

    await callback.answer()


async def show_payment_details(
    callback: CallbackQuery,
    state: FSMContext,
    data: dict,
    cart_data: list,
    total_price: float,
):
    """Показать реквизиты для перевода и ждать документ подтверждения"""
    import structlog

    from ..services.payment_settings_service import PaymentSettingsService

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    # Получаем настройки платежа из БД
    payment_service = PaymentSettingsService()

    # Получаем базовое сообщение с реквизитами
    payment_details = payment_service.get_payment_message(total_price)

    # Добавляем сводку заказа
    payment_details += (
        "\n\n📋 **Сводка заказа:**\n"
        f"📞 **Телефон:** {data['phone']}\n"
        f"📍 **Адрес:** {data['address']}\n"
        f"📝 **Комментарии:** {data.get('notes', 'Не указаны')}\n\n"
        "📦 **Товары в заказе:**\n"
    )

    for item in cart_data:
        payment_details += (
            f"• {item['product_name']} - {item['quantity']} шт. × "
            f"{item['price']:.2f}₽ = {item['total']:.2f}₽\n"
        )

    payment_details += (
        f"\n💳 **Итого: {total_price:.2f}₽**\n\n"
        "⏰ Заказ будет создан после подтверждения оплаты."
    )

    # Переходим в состояние ожидания документа
    await state.set_state(OrderStates.waiting_for_payment_document)

    if callback.message and not isinstance(
        callback.message, InaccessibleMessage
    ):
        if not callback.message or isinstance(
            callback.message, InaccessibleMessage
        ):
            await callback.answer(
                "❌ Ошибка обработки запроса", show_alert=True
            )
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            payment_details,
            parse_mode="Markdown",
        )

    logger.info(
        "payment_details_shown",
        user_id=user_id,  # type: ignore
        payment_method="transfer",
    )

    await callback.answer()


@router.message(OrderStates.waiting_for_payment_document)
async def process_payment_document(message: Message, state: FSMContext):
    """Обработка документа подтверждения оплаты"""
    import structlog

    logger = structlog.get_logger()
    if not message.from_user:
        await message.answer("Ошибка: пользователь не найден")
        return

    user_id = message.from_user.id

    try:
        # Проверяем, что пользователь отправил документ (фото или документ)
        if not (message.photo or message.document):
            await message.answer(
                "❌ Пожалуйста, отправьте фото или скриншот чека об оплате.\n\n"
                "Или нажмите 'Отменить заказ' если передумали.",
                reply_markup=get_cancel_order_keyboard(),
            )
            return

        # Получаем данные заказа
        data = await state.get_data()

        # Создаем заказ с оплаченным статусом
        delivery_data = {
            "phone": data["phone"],
            "address": data["address"],
            "notes": data.get("notes", ""),
        }

        order = order_service.create_order_from_cart(
            user_id=user_id,
            delivery_data=delivery_data,
            payment_method="transfer",
            payment_status="paid",  # Заказ сразу оплачен
        )

        if order:
            # Очищаем состояние
            await state.clear()

            # Формируем сообщение об успешном создании заказа
            success_message = (
                "🎉 **Заказ успешно создан и оплачен!**\n\n"
                f"📋 **Номер заказа:** {order['order_number']}\n"
                f"💳 **Сумма:** {order['total_amount']}₽\n"
                f"💳 **Оплата:** переводом на карту ✅\n\n"
                "📄 **Документ об оплате получен**\n"
                "📞 Мы свяжемся с вами для подтверждения заказа.\n"
                "🚚 Время доставки: 1-2 часа\n\n"
                "Спасибо за заказ! 🙏"
            )

            await message.answer(
                success_message,
                reply_markup=get_order_success_keyboard(),
                parse_mode="Markdown",
            )

            logger.info(
                "transfer_order_created_successfully",
                user_id=user_id,  # type: ignore
                order_id=order["id"],
                order_number=order["order_number"],
            )

        else:
            await message.answer(
                "❌ **Ошибка при создании заказа**\n\n"
                "Попробуйте еще раз или обратитесь в поддержку.",
                parse_mode="Markdown",
            )

            logger.error(
                "transfer_order_creation_failed", user_id=user_id
            )  # type: ignore

    except Exception as e:
        logger.error(
            # type: ignore
            "process_payment_document_error",
            user_id=user_id,
            error=str(e),
        )
        await message.answer(
            "❌ **Произошла ошибка**\n\n"
            "Попробуйте еще раз или обратитесь в поддержку.",
            parse_mode="Markdown",
        )


@router.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и создание заказа"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    try:
        # Получаем данные заказа
        data = await state.get_data()

        # Создаем заказ
        delivery_data = {
            "phone": data["phone"],
            "address": data["address"],
            "notes": data.get("notes", ""),
        }

        order = order_service.create_order_from_cart(
            user_id=user_id,
            delivery_data=delivery_data,
            payment_method=data["payment_method"],
        )

        if order:
            # Очищаем состояние
            await state.clear()

            # Формируем сообщение об успешном создании заказа
            payment_method_text = {
                "cash": "наличными при получении",
                "transfer": "переводом на карту",
            }[data["payment_method"]]

            success_message = (
                "🎉 **Заказ успешно создан!**\n\n"
                f"📋 **Номер заказа:** {order['order_number']}\n"
                f"💳 **Сумма:** {order['total_amount']:.2f}₽\n"
                f"💳 **Оплата:** {payment_method_text}\n\n"
                "📞 Мы свяжемся с вами для подтверждения заказа.\n"
                "🚚 Время доставки: 1-2 часа\n\n"
                "Спасибо за заказ! 🙏"
            )

            if callback.message:
                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

                assert isinstance(callback.message, Message)

                await callback.message.edit_text(
                    success_message,
                    parse_mode="Markdown",
                )

            logger.info(
                "order_created_successfully",
                user_id=user_id,  # type: ignore
                order_id=order["id"],
                order_number=order["order_number"],
            )

        else:
            if callback.message and not isinstance(
                callback.message, InaccessibleMessage
            ):
                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

                assert isinstance(callback.message, Message)

                await callback.message.edit_text(
                    "❌ **Ошибка при создании заказа**\n\n"
                    "Попробуйте еще раз или обратитесь в поддержку.",
                    parse_mode="Markdown",
                )

            logger.error(
                "order_creation_failed", user_id=user_id
            )  # type: ignore

    except Exception as e:
        logger.error(
            # type: ignore
            "confirm_order_error",
            user_id=user_id,
            error=str(e),
        )
        if callback.message and not isinstance(
            callback.message, InaccessibleMessage
        ):
            if not callback.message or isinstance(
                callback.message, InaccessibleMessage
            ):
                await callback.answer(
                    "❌ Ошибка обработки запроса", show_alert=True
                )
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                "❌ **Произошла ошибка**\n\n"
                "Попробуйте еще раз или обратитесь в поддержку.",
                parse_mode="Markdown",
            )

    await callback.answer()


@router.callback_query(F.data == "cancel_order")
async def cancel_order_process(callback: CallbackQuery, state: FSMContext):
    """Отмена процесса оформления заказа"""
    await state.clear()

    if callback.message and not isinstance(
        callback.message, InaccessibleMessage
    ):
        if not callback.message or isinstance(
            callback.message, InaccessibleMessage
        ):
            await callback.answer(
                "❌ Ошибка обработки запроса", show_alert=True
            )
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            "❌ **Оформление заказа отменено**\n\n"
            "Вы можете вернуться к покупкам в любое время!",
            parse_mode="Markdown",
        )
    await callback.answer()


@router.message(Command("orders"))
async def show_user_orders(message: Message):
    """Показать заказы пользователя"""
    import structlog

    logger = structlog.get_logger()
    if not message.from_user:
        await message.answer("Ошибка: пользователь не найден")
        return

    user_id = message.from_user.id
    if not user_id:
        await message.answer("Ошибка: пользователь не найден")
        return

    logger.info("user_orders_requested", user_id=user_id)  # type: ignore

    # Получаем только активные заказы пользователя (не delivered и не
    # cancelled)
    orders = order_service.get_user_orders(
        user_id=user_id, limit=50, active_only=True
    )

    logger.info(
        "user_orders_retrieved",
        user_id=user_id,  # type: ignore
        orders_count=len(orders) if orders else 0,
    )

    if not orders:
        await message.answer(
            "📋 **Активные заказы**\n\n"
            "У вас пока нет активных заказов.\n"
            "Используйте /catalog чтобы начать покупки!",
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
        }.get(order["status"].value, "❓")

        orders_text += (
            f"{status_emoji} **{order['order_number']}**\n"
            f"   💳 {order['total_amount']:.2f}₽\n"
            f"   📅 Заказ #{order['id']}\n\n"
        )

    if len(orders) > 5:
        orders_text += f"... и еще {len(orders) - 5} заказов\n\n"

    orders_text += "Нажмите на заказ для просмотра деталей:"

    await message.answer(
        orders_text,
        reply_markup=get_orders_list_keyboard(orders),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("order_details_"))
async def show_order_details(callback: CallbackQuery):
    """Показать детали заказа"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    try:
        if not callback.data:
            await callback.answer("Ошибка: неверные данные", show_alert=True)
            return
        order_id = int(callback.data.split("_")[2])

        # Получаем заказ (теперь это словарь)
        order = order_service.get_user_order(
            user_id=user_id, order_id=order_id
        )

        if not order:
            await callback.answer("Заказ не найден", show_alert=True)
            return

        # Формируем сообщение с деталями (работаем со словарем)
        status_text = {
            "pending": "⏳ Ожидает подтверждения",
            "confirmed": "✅ Подтвержден",
            "processing": "🔄 В обработке",
            "shipped": "🚚 Отправлен",
            "delivered": "📦 Доставлен",
            "cancelled": "❌ Отменен",
        }.get(order["status"].value, "❓ Неизвестный статус")

        payment_text = {
            "cash": "💵 Наличные при получении",
            "transfer": "💳 Перевод на карту",
        }.get(order["payment_method"].value, "❓ Неизвестный способ")

        details_text = (
            f"📋 **Заказ {order['order_number']}**\n\n"
            f"📅 **Заказ:** #{order['id']}\n"
            f"📊 **Статус:** {status_text}\n"
            f"💳 **Оплата:** {payment_text}\n\n"
            f"📞 **Телефон:** {order['delivery_phone']}\n"
            f"📍 **Адрес:** {order['delivery_address']}\n"
        )

        if order.get("delivery_notes"):
            details_text += f"📝 **Комментарии:** {order['delivery_notes']}\n"

        details_text += "\n📦 **Товары:**\n"

        for item in order["items"]:
            details_text += (
                f"• {item['product_name']} - {item['quantity']} шт. × "
                f"{item['product_price']:.2f}₽ = {item['total_price']:.2f}₽\n"
            )

        details_text += f"\n💳 **Итого:** {order['total_amount']:.2f}₽"

        if callback.message and not isinstance(
            callback.message, InaccessibleMessage
        ):
            assert isinstance(callback.message, Message)

            # Получаем статус заказа для клавиатуры
            order_status = (
                order["status"].value
                if hasattr(order["status"], "value")
                else order["status"]
            )

            await callback.message.edit_text(
                details_text,
                reply_markup=get_order_details_keyboard(
                    order["id"], order_status
                ),
                parse_mode="Markdown",
            )
        await callback.answer()

        logger.info(
            "order_details_shown",
            user_id=user_id,  # type: ignore
            order_id=order_id,
            order_number=order["order_number"],
        )

    except Exception as e:
        logger.error(
            "show_order_details_error",
            user_id=user_id,  # type: ignore
            error=str(e),
            callback_data=callback.data,
        )
        await callback.answer("Ошибка при загрузке заказа", show_alert=True)


@router.callback_query(F.data.startswith("refresh_order_"))
async def refresh_order(callback: CallbackQuery):
    """Обновить информацию о конкретном заказе"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    try:
        if not callback.data:
            await callback.answer("Ошибка: неверные данные", show_alert=True)
            return
        order_id = int(callback.data.split("_")[2])

        # Получаем обновленную информацию о заказе
        order = order_service.get_user_order(
            user_id=user_id, order_id=order_id
        )

        if not order:
            await callback.answer("Заказ не найден", show_alert=True)
            return

        # Формируем сообщение с деталями
        status_text = {
            "pending": "⏳ Ожидает подтверждения",
            "confirmed": "✅ Подтвержден",
            "processing": "🔄 В обработке",
            "shipped": "🚚 Отправлен",
            "delivered": "📦 Доставлен",
            "cancelled": "❌ Отменен",
        }.get(order["status"].value, "❓ Неизвестный статус")

        payment_text = {
            "cash": "💵 Наличные при получении",
            "transfer": "💳 Перевод на карту",
        }.get(order["payment_method"].value, "❓ Неизвестный способ")

        details_text = (
            f"📋 **Заказ {order['order_number']}**\n\n"
            f"📅 **Заказ:** #{order['id']}\n"
            f"📊 **Статус:** {status_text}\n"
            f"💳 **Оплата:** {payment_text}\n\n"
            f"📞 **Телефон:** {order['delivery_phone']}\n"
            f"📍 **Адрес:** {order['delivery_address']}\n"
        )

        if order.get("delivery_notes"):
            details_text += f"📝 **Комментарии:** {order['delivery_notes']}\n"

        details_text += "\n📦 **Товары:**\n"

        for item in order["items"]:
            details_text += (
                f"• {item['product_name']} - {item['quantity']} шт. × "
                f"{item['product_price']:.2f}₽ = {item['total_price']:.2f}₽\n"
            )

        details_text += f"\n💳 **Итого:** {order['total_amount']:.2f}₽"

        if callback.message and not isinstance(
            callback.message, InaccessibleMessage
        ):
            assert isinstance(callback.message, Message)

            # Получаем статус заказа для клавиатуры
            order_status = (
                order["status"].value
                if hasattr(order["status"], "value")
                else order["status"]
            )

            try:
                await callback.message.edit_text(
                    details_text,
                    reply_markup=get_order_details_keyboard(
                        order["id"], order_status
                    ),
                    parse_mode="Markdown",
                )
            except Exception as edit_error:
                # Игнорируем ошибку, если сообщение не изменилось
                if "message is not modified" not in str(edit_error):
                    raise

        await callback.answer("✅ Информация обновлена!")

        logger.info(
            "order_refreshed",
            user_id=user_id,  # type: ignore
            order_id=order_id,
            order_number=order["order_number"],
        )

    except Exception as e:
        logger.error(
            "refresh_order_error",
            user_id=user_id,  # type: ignore
            error=str(e),
            callback_data=callback.data,
        )
        await callback.answer("Ошибка при обновлении заказа", show_alert=True)


@router.callback_query(F.data.startswith("cancel_order_"))
async def cancel_user_order(callback: CallbackQuery):
    """Отмена заказа пользователем"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    try:
        if not callback.data:
            await callback.answer("Ошибка: неверные данные", show_alert=True)
            return
        order_id = int(callback.data.split("_")[2])

        # Отменяем заказ
        success = order_service.cancel_order(
            user_id=user_id, order_id=order_id
        )

        if success:
            if callback.message:
                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

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
                            InlineKeyboardButton(
                                text="🛒 В корзину",
                                callback_data="cart",
                            ),
                        ],
                        [
                            InlineKeyboardButton(
                                text="📋 Мои заказы",
                                callback_data="orders",
                            ),
                        ],
                    ]
                )

                await callback.message.edit_text(
                    "✅ **Заказ отменен**\n\n" "Ваш заказ был успешно отменен.",
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
            logger.info(
                "order_cancelled_by_user",
                user_id=user_id,  # type: ignore
                order_id=order_id,
            )
        else:
            if callback.message and not isinstance(
                callback.message, InaccessibleMessage
            ):
                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

                assert isinstance(callback.message, Message)

                await callback.message.edit_text(
                    "❌ **Не удалось отменить заказ**\n\n"
                    "Возможно, заказ уже обрабатывается или доставлен.",
                    parse_mode="Markdown",
                )

    except Exception as e:
        logger.error(
            "cancel_user_order_error",
            user_id=user_id,  # type: ignore
            error=str(e),
            callback_data=callback.data,
        )
        await callback.answer("Ошибка при отмене заказа", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "refresh_orders")
async def refresh_orders(callback: CallbackQuery):
    """Обновить список заказов"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    logger.info(
        "user_orders_refresh_requested", user_id=user_id
    )  # type: ignore

    # Получаем только активные заказы пользователя (не delivered и не
    # cancelled)
    orders = order_service.get_user_orders(
        user_id=user_id, limit=50, active_only=True
    )

    logger.info(
        "user_orders_refreshed",
        user_id=user_id,  # type: ignore
        orders_count=len(orders) if orders else 0,
    )

    if not orders:
        if callback.message and not isinstance(
            callback.message, InaccessibleMessage
        ):
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
        await callback.answer("✅ Список заказов обновлен!")
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
        }.get(order["status"].value, "❓")

        orders_text += (
            f"{status_emoji} **{order['order_number']}**\n"
            f"   💳 {order['total_amount']:.2f}₽\n"
            f"   📅 Заказ #{order['id']}\n\n"
        )

    if len(orders) > 5:
        orders_text += f"... и еще {len(orders) - 5} заказов\n\n"

    orders_text += "Нажмите на заказ для просмотра деталей:"

    if callback.message and not isinstance(
        callback.message, InaccessibleMessage
    ):
        assert isinstance(callback.message, Message)

        try:
            await callback.message.edit_text(
                orders_text,
                reply_markup=get_orders_list_keyboard(orders),
                parse_mode="Markdown",
            )
        except Exception as e:
            # Игнорируем ошибку, если сообщение не изменилось
            if "message is not modified" not in str(e):
                raise

    await callback.answer("✅ Список заказов обновлен!")


@router.callback_query(F.data.startswith("orders_page_"))
async def orders_pagination(callback: CallbackQuery):
    """Пагинация списка активных заказов"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    try:
        if not callback.data:
            await callback.answer("Ошибка: неверные данные", show_alert=True)
            return
        page = int(callback.data.split("_")[2])

        # Получаем только активные заказы пользователя
        orders = order_service.get_user_orders(
            user_id=user_id, limit=50, active_only=True
        )

        if not orders:
            await callback.answer(
                "Активные заказы не найдены", show_alert=True
            )
            return

        # Формируем сообщение со списком активных заказов
        orders_text = "📋 **Активные заказы:**\n\n"

        start_idx = page * 5
        end_idx = start_idx + 5

        for order in orders[start_idx:end_idx]:
            status_emoji = {
                "pending": "⏳",
                "confirmed": "✅",
                "processing": "🔄",
                "shipped": "🚚",
                "delivered": "📦",
                "cancelled": "❌",
            }.get(order["status"].value, "❓")

            orders_text += (
                f"{status_emoji} **{order['order_number']}**\n"
                f"   💳 {order['total_amount']:.2f}₽\n"
                f"   📅 Заказ #{order['id']}\n\n"
            )

        orders_text += "Нажмите на заказ для просмотра деталей:"

        if callback.message and not isinstance(
            callback.message, InaccessibleMessage
        ):
            if not callback.message or isinstance(
                callback.message, InaccessibleMessage
            ):
                await callback.answer(
                    "❌ Ошибка обработки запроса", show_alert=True
                )
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                orders_text,
                reply_markup=get_orders_list_keyboard(orders, page),
                parse_mode="Markdown",
            )
        await callback.answer()

    except Exception as e:
        logger.error(
            "orders_pagination_error",
            user_id=user_id,  # type: ignore
            error=str(e),
            callback_data=callback.data,
        )
        await callback.answer("Ошибка при загрузке страницы", show_alert=True)


@router.callback_query(F.data == "orders_history")
async def show_orders_history(callback: CallbackQuery):
    """Показать историю заказов (delivered и cancelled)"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    logger.info(
        "user_orders_history_requested", user_id=user_id
    )  # type: ignore

    # Получаем историю заказов пользователя
    orders = order_service.get_user_orders_history(user_id=user_id, limit=50)

    logger.info(
        "user_orders_history_retrieved",
        user_id=user_id,  # type: ignore
        orders_count=len(orders) if orders else 0,
    )

    if not orders:
        if callback.message and not isinstance(
            callback.message, InaccessibleMessage
        ):
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
                            text="🔙 К моим заказам",
                            callback_data="orders",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="📦 В каталог",
                            callback_data="catalog",
                        ),
                    ],
                ]
            )

            await callback.message.edit_text(
                "📜 **История заказов**\n\n"
                "У вас пока нет завершенных или отмененных заказов.",
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
        await callback.answer()
        return

    # Формируем сообщение со списком заказов из истории
    orders_text = "📜 **История заказов:**\n\n"

    for order in orders[:5]:  # Показываем первые 5 заказов
        status_emoji = {
            "pending": "⏳",
            "confirmed": "✅",
            "processing": "🔄",
            "shipped": "🚚",
            "delivered": "📦",
            "cancelled": "❌",
        }.get(order["status"].value, "❓")

        orders_text += (
            f"{status_emoji} **{order['order_number']}**\n"
            f"   💳 {order['total_amount']:.2f}₽\n"
            f"   📅 Заказ #{order['id']}\n\n"
        )

    if len(orders) > 5:
        orders_text += f"... и еще {len(orders) - 5} заказов\n\n"

    orders_text += "Нажмите на заказ для просмотра деталей:"

    if callback.message and not isinstance(
        callback.message, InaccessibleMessage
    ):
        assert isinstance(callback.message, Message)

        try:
            await callback.message.edit_text(
                orders_text,
                reply_markup=get_orders_history_keyboard(orders),
                parse_mode="Markdown",
            )
        except Exception as e:
            # Игнорируем ошибку, если сообщение не изменилось
            if "message is not modified" not in str(e):
                raise
    await callback.answer()


@router.callback_query(F.data == "refresh_orders_history")
async def refresh_orders_history(callback: CallbackQuery):
    """Обновить список истории заказов"""
    await show_orders_history(callback)
    await callback.answer("✅ История заказов обновлена!")


@router.callback_query(F.data.startswith("orders_history_page_"))
async def orders_history_pagination(callback: CallbackQuery):
    """Пагинация истории заказов"""
    import structlog

    logger = structlog.get_logger()
    user_id = callback.from_user.id

    try:
        if not callback.data:
            await callback.answer("Ошибка: неверные данные", show_alert=True)
            return
        page = int(callback.data.split("_")[3])

        # Получаем историю заказов пользователя
        orders = order_service.get_user_orders_history(
            user_id=user_id, limit=50
        )

        if not orders:
            await callback.answer("История заказов пуста", show_alert=True)
            return

        # Формируем сообщение со списком заказов
        orders_text = "📜 **История заказов:**\n\n"

        start_idx = page * 5
        end_idx = start_idx + 5

        for order in orders[start_idx:end_idx]:
            status_emoji = {
                "pending": "⏳",
                "confirmed": "✅",
                "processing": "🔄",
                "shipped": "🚚",
                "delivered": "📦",
                "cancelled": "❌",
            }.get(order["status"].value, "❓")

            orders_text += (
                f"{status_emoji} **{order['order_number']}**\n"
                f"   💳 {order['total_amount']:.2f}₽\n"
                f"   📅 Заказ #{order['id']}\n\n"
            )

        orders_text += "Нажмите на заказ для просмотра деталей:"

        if callback.message and not isinstance(
            callback.message, InaccessibleMessage
        ):
            if not callback.message or isinstance(
                callback.message, InaccessibleMessage
            ):
                await callback.answer(
                    "❌ Ошибка обработки запроса", show_alert=True
                )
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                orders_text,
                reply_markup=get_orders_history_keyboard(orders, page),
                parse_mode="Markdown",
            )
        await callback.answer()

    except Exception as e:
        logger.error(
            "orders_history_pagination_error",
            user_id=user_id,  # type: ignore
            error=str(e),
            callback_data=callback.data,
        )
        await callback.answer("Ошибка при загрузке страницы", show_alert=True)
