"""
Обработчики команд бота.

Содержит обработчики для /start, /help, /cancel, /export.
"""

import logging
from io import BytesIO

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from src.config import settings
from src.keyboards.reply import get_cancel_keyboard, remove_keyboard
from src.states.form import FormStates
from src.utils.csv_handler import csv_handler

logger = logging.getLogger(__name__)
router = Router(name="commands")


# Текст приветствия
WELCOME_MESSAGE = """
👋 <b>Добро пожаловать!</b>

Я помогу вам оставить заявку. Это займёт всего пару минут.

Вам нужно будет указать:
• Ваше имя
• Контактный телефон
• Email для связи
• Сообщение (опционально)

Для начала заполнения нажмите /start
Для получения справки — /help
Для отмены — /cancel
"""

# Текст справки
HELP_MESSAGE = """
📚 <b>Справка по командам</b>

/start — начать заполнение заявки
/help — показать эту справку
/cancel — отменить заполнение формы

<b>Как заполнить заявку:</b>
1️⃣ Введите своё имя
2️⃣ Укажите номер телефона
3️⃣ Введите email
4️⃣ Напишите сообщение (можно пропустить)
5️⃣ Проверьте данные и подтвердите

💡 <b>Подсказки:</b>
• Используйте кнопку «⬅️ Назад» для возврата к предыдущему шагу
• Телефон можно отправить автоматически через кнопку
• Сообщение необязательно — его можно пропустить
"""

# Сообщение об отмене
CANCEL_MESSAGE = """
❌ <b>Заполнение формы отменено.</b>

Все введённые данные удалены.
Чтобы начать заново, отправьте /start
"""

# Сообщение для первого шага
START_FORM_MESSAGE = """
📝 <b>Шаг 1 из 4: Ваше имя</b>

Пожалуйста, введите ваше имя.

<i>Требования: от 2 до 50 символов</i>
"""


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /start.

    Приветствует пользователя и запускает процесс заполнения формы.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    user = message.from_user
    logger.info(f"Пользователь {user.id} ({user.full_name}) начал диалог")

    # Сбрасываем состояние и начинаем заново
    await state.clear()

    await message.answer(
        WELCOME_MESSAGE,
        parse_mode="HTML",
        reply_markup=remove_keyboard(),
    )

    # Сразу переходим к первому шагу
    await message.answer(
        START_FORM_MESSAGE,
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )

    await state.set_state(FormStates.name)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    Обработчик команды /help.

    Показывает справку по использованию бота.

    Args:
        message: Входящее сообщение.
    """
    logger.info(f"Пользователь {message.from_user.id} запросил справку")

    await message.answer(
        HELP_MESSAGE,
        parse_mode="HTML",
    )


@router.message(Command("cancel"))
@router.message(F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /cancel и кнопки отмены.

    Сбрасывает текущее состояние FSM.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    current_state = await state.get_state()

    if current_state is None:
        await message.answer(
            "🤷 Нечего отменять. Отправьте /start чтобы начать.",
            reply_markup=remove_keyboard(),
        )
        return

    logger.info(
        f"Пользователь {message.from_user.id} отменил заполнение "
        f"(состояние: {current_state})"
    )

    await state.clear()

    await message.answer(
        CANCEL_MESSAGE,
        parse_mode="HTML",
        reply_markup=remove_keyboard(),
    )


@router.message(Command("export"), StateFilter(None))
async def cmd_export(message: Message) -> None:
    """
    Обработчик команды /export.

    Отправляет CSV-файл с заявками администратору.
    Доступно только для администратора.

    Args:
        message: Входящее сообщение.
    """
    user_id = message.from_user.id

    # Проверяем права администратора
    if user_id != settings.admin_id:
        logger.warning(f"Попытка экспорта от пользователя {user_id} (не админ)")
        await message.answer(
            "⛔ У вас нет прав для выполнения этой команды."
        )
        return

    logger.info(f"Администратор {user_id} запросил экспорт данных")

    # Получаем содержимое файла
    csv_content = csv_handler.get_csv_content()

    if csv_content is None:
        await message.answer(
            "❌ Ошибка при чтении файла данных."
        )
        return

    applications_count = csv_handler.get_applications_count()

    if applications_count == 0:
        await message.answer(
            "📭 База заявок пуста. Нет данных для экспорта."
        )
        return

    # Отправляем файл
    document = BufferedInputFile(
        file=csv_content,
        filename="applications.csv",
    )

    await message.answer_document(
        document=document,
        caption=f"📊 Экспорт данных\n\nВсего заявок: {applications_count}",
    )

    logger.info(f"Экспортировано {applications_count} заявок")
