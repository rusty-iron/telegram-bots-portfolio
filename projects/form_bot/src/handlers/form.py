"""
Обработчики состояний FSM для формы сбора заявок.

Содержит логику последовательного опроса пользователя
с валидацией данных и навигацией.
"""

import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from src.config import settings
from src.keyboards.reply import (
    BACK_BUTTON,
    CONFIRM_BUTTON,
    RESTART_BUTTON,
    SKIP_BUTTON,
    get_back_keyboard,
    get_cancel_keyboard,
    get_confirm_keyboard,
    get_phone_keyboard,
    get_skip_keyboard,
)
from src.states.form import FormStates
from src.utils.csv_handler import csv_handler
from src.utils.validators import (
    normalize_phone,
    validate_email,
    validate_message,
    validate_name,
    validate_phone,
)

logger = logging.getLogger(__name__)
router = Router(name="form")


# Шаблоны сообщений
MESSAGES = {
    "name": """
📝 <b>Шаг 1 из 4: Ваше имя</b>

Пожалуйста, введите ваше имя.

<i>Требования: от 2 до 50 символов</i>
""",
    "phone": """
📱 <b>Шаг 2 из 4: Номер телефона</b>

Введите номер телефона или отправьте его через кнопку.

<i>Формат: +79991234567 или 89991234567</i>
""",
    "email": """
📧 <b>Шаг 3 из 4: Email</b>

Введите адрес электронной почты.

<i>Формат: example@mail.com</i>
""",
    "message": """
💬 <b>Шаг 4 из 4: Сообщение</b>

Напишите ваше сообщение или комментарий.
Можно пропустить этот шаг.

<i>Максимум 500 символов</i>
""",
    "confirm": """
✅ <b>Проверьте введённые данные:</b>

👤 <b>Имя:</b> {name}
📱 <b>Телефон:</b> {phone}
📧 <b>Email:</b> {email}
💬 <b>Сообщение:</b> {message}

Всё верно?
""",
    "success": """
🎉 <b>Заявка успешно отправлена!</b>

Спасибо за обращение. Мы свяжемся с вами в ближайшее время.

Чтобы оставить ещё одну заявку, отправьте /start
""",
    "error": """
❌ <b>Произошла ошибка при сохранении заявки.</b>

Пожалуйста, попробуйте позже или обратитесь в поддержку.
""",
}


# Шаблон уведомления администратору
ADMIN_NOTIFICATION = """
📨 <b>Новая заявка!</b>

👤 <b>Имя:</b> {name}
📱 <b>Телефон:</b> {phone}
📧 <b>Email:</b> {email}
💬 <b>Сообщение:</b> {message}

🆔 User ID: <code>{user_id}</code>
"""


# ==================== ОБРАБОТЧИКИ ВВОДА ИМЕНИ ====================


@router.message(FormStates.name, F.text)
async def process_name(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод имени.

    Args:
        message: Входящее сообщение с именем.
        state: Контекст FSM.
    """
    name = message.text.strip()

    # Валидация
    is_valid, error_message = validate_name(name)

    if not is_valid:
        await message.answer(
            f"⚠️ {error_message}\n\nПопробуйте ещё раз:",
            reply_markup=get_cancel_keyboard(),
        )
        return

    # Сохраняем и переходим к следующему шагу
    await state.update_data(name=name)

    logger.info(f"Пользователь {message.from_user.id} ввёл имя: {name}")

    await message.answer(
        MESSAGES["phone"],
        parse_mode="HTML",
        reply_markup=get_phone_keyboard(),
    )

    await state.set_state(FormStates.phone)


# ==================== ОБРАБОТЧИКИ ВВОДА ТЕЛЕФОНА ====================


@router.message(FormStates.phone, F.text == BACK_BUTTON)
async def phone_back(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает кнопку «Назад» на шаге ввода телефона.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    await message.answer(
        MESSAGES["name"],
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )
    await state.set_state(FormStates.name)


@router.message(FormStates.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает отправку контакта (кнопка «Отправить контакт»).

    Args:
        message: Входящее сообщение с контактом.
        state: Контекст FSM.
    """
    phone = message.contact.phone_number

    # Нормализуем номер
    if not phone.startswith("+"):
        phone = "+" + phone

    await state.update_data(phone=phone)

    logger.info(f"Пользователь {message.from_user.id} отправил контакт: {phone}")

    await message.answer(
        MESSAGES["email"],
        parse_mode="HTML",
        reply_markup=get_back_keyboard(),
    )

    await state.set_state(FormStates.email)


@router.message(FormStates.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ручной ввод телефона.

    Args:
        message: Входящее сообщение с номером телефона.
        state: Контекст FSM.
    """
    phone = message.text.strip()

    # Валидация
    is_valid, error_message = validate_phone(phone)

    if not is_valid:
        await message.answer(
            f"⚠️ {error_message}\n\nПопробуйте ещё раз:",
            reply_markup=get_phone_keyboard(),
        )
        return

    # Нормализуем и сохраняем
    phone = normalize_phone(phone)
    await state.update_data(phone=phone)

    logger.info(f"Пользователь {message.from_user.id} ввёл телефон: {phone}")

    await message.answer(
        MESSAGES["email"],
        parse_mode="HTML",
        reply_markup=get_back_keyboard(),
    )

    await state.set_state(FormStates.email)


# ==================== ОБРАБОТЧИКИ ВВОДА EMAIL ====================


@router.message(FormStates.email, F.text == BACK_BUTTON)
async def email_back(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает кнопку «Назад» на шаге ввода email.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    await message.answer(
        MESSAGES["phone"],
        parse_mode="HTML",
        reply_markup=get_phone_keyboard(),
    )
    await state.set_state(FormStates.phone)


@router.message(FormStates.email, F.text)
async def process_email(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод email.

    Args:
        message: Входящее сообщение с email.
        state: Контекст FSM.
    """
    email = message.text.strip().lower()

    # Валидация
    is_valid, error_message = validate_email(email)

    if not is_valid:
        await message.answer(
            f"⚠️ {error_message}\n\nПопробуйте ещё раз:",
            reply_markup=get_back_keyboard(),
        )
        return

    # Сохраняем и переходим к следующему шагу
    await state.update_data(email=email)

    logger.info(f"Пользователь {message.from_user.id} ввёл email: {email}")

    await message.answer(
        MESSAGES["message"],
        parse_mode="HTML",
        reply_markup=get_skip_keyboard(),
    )

    await state.set_state(FormStates.message)


# ==================== ОБРАБОТЧИКИ ВВОДА СООБЩЕНИЯ ====================


@router.message(FormStates.message, F.text == BACK_BUTTON)
async def message_back(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает кнопку «Назад» на шаге ввода сообщения.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    await message.answer(
        MESSAGES["email"],
        parse_mode="HTML",
        reply_markup=get_back_keyboard(),
    )
    await state.set_state(FormStates.email)


@router.message(FormStates.message, F.text == SKIP_BUTTON)
async def message_skip(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает пропуск ввода сообщения.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    await state.update_data(message="—")

    logger.info(f"Пользователь {message.from_user.id} пропустил ввод сообщения")

    await show_confirmation(message, state)


@router.message(FormStates.message, F.text)
async def process_message(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод сообщения.

    Args:
        message: Входящее сообщение с текстом.
        state: Контекст FSM.
    """
    text = message.text.strip()

    # Валидация
    is_valid, error_message = validate_message(text)

    if not is_valid:
        await message.answer(
            f"⚠️ {error_message}\n\nПопробуйте ещё раз:",
            reply_markup=get_skip_keyboard(),
        )
        return

    # Сохраняем
    await state.update_data(message=text)

    logger.info(f"Пользователь {message.from_user.id} ввёл сообщение")

    await show_confirmation(message, state)


async def show_confirmation(message: Message, state: FSMContext) -> None:
    """
    Показывает форму подтверждения данных.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    data = await state.get_data()

    confirm_text = MESSAGES["confirm"].format(
        name=data.get("name", "—"),
        phone=data.get("phone", "—"),
        email=data.get("email", "—"),
        message=data.get("message", "—"),
    )

    await message.answer(
        confirm_text,
        parse_mode="HTML",
        reply_markup=get_confirm_keyboard(),
    )

    await state.set_state(FormStates.confirm)


# ==================== ОБРАБОТЧИКИ ПОДТВЕРЖДЕНИЯ ====================


@router.message(FormStates.confirm, F.text == BACK_BUTTON)
async def confirm_back(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает кнопку «Назад» на этапе подтверждения.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    await message.answer(
        MESSAGES["message"],
        parse_mode="HTML",
        reply_markup=get_skip_keyboard(),
    )
    await state.set_state(FormStates.message)


@router.message(FormStates.confirm, F.text == RESTART_BUTTON)
async def confirm_restart(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает кнопку «Начать заново».

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    await state.clear()

    logger.info(f"Пользователь {message.from_user.id} начал заново")

    await message.answer(
        MESSAGES["name"],
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )

    await state.set_state(FormStates.name)


@router.message(FormStates.confirm, F.text == CONFIRM_BUTTON)
async def confirm_submit(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обрабатывает подтверждение и сохраняет заявку.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
        bot: Экземпляр бота для отправки уведомлений.
    """
    user_id = message.from_user.id
    data = await state.get_data()

    # Сохраняем в CSV
    success = csv_handler.save_application(
        user_id=user_id,
        name=data.get("name", ""),
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        message=data.get("message", ""),
    )

    if success:
        logger.info(f"Заявка от пользователя {user_id} успешно сохранена")

        await message.answer(
            MESSAGES["success"],
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )

        # Отправляем уведомление администратору
        await notify_admin(bot, user_id, data)
    else:
        logger.error(f"Ошибка сохранения заявки от пользователя {user_id}")

        await message.answer(
            MESSAGES["error"],
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )

    # Очищаем состояние
    await state.clear()


async def notify_admin(bot: Bot, user_id: int, data: dict) -> None:
    """
    Отправляет уведомление администратору о новой заявке.

    Args:
        bot: Экземпляр бота.
        user_id: ID пользователя, оставившего заявку.
        data: Данные заявки.
    """
    try:
        notification_text = ADMIN_NOTIFICATION.format(
            name=data.get("name", "—"),
            phone=data.get("phone", "—"),
            email=data.get("email", "—"),
            message=data.get("message", "—"),
            user_id=user_id,
        )

        await bot.send_message(
            chat_id=settings.admin_id,
            text=notification_text,
            parse_mode="HTML",
        )

        logger.info(f"Уведомление о заявке отправлено администратору")

    except Exception as e:
        logger.error(f"Ошибка отправки уведомления администратору: {e}")
