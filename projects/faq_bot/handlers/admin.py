"""
Обработчики админ-панели.
"""

import json
import logging
from io import BytesIO

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from keyboards.user import UserKeyboards
from keyboards.admin import AdminKeyboards
from states.admin import AdminStates
from utils.faq_loader import FAQLoader
from utils.search import FAQSearch
from utils.stats import StatsManager

router = Router(name="admin")
logger = logging.getLogger(__name__)


class AdminFilter:
    """Фильтр для проверки администратора."""

    def __init__(self, admin_id: int):
        self.admin_id = admin_id

    def __call__(self, message: Message) -> bool:
        return message.from_user.id == self.admin_id


@router.message(Command("admin"))
async def cmd_admin(
    message: Message,
    state: FSMContext,
    admin_id: int,
) -> None:
    """Обработчик команды /admin."""
    if message.from_user.id != admin_id:
        await message.answer("У вас нет доступа к админ-панели.")
        return

    await state.set_state(AdminStates.main_menu)

    await message.answer(
        "🔐 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=AdminKeyboards.main_menu(),
    )


@router.message(F.text == AdminKeyboards.EXIT_BTN, AdminStates.main_menu)
async def exit_admin(message: Message, state: FSMContext) -> None:
    """Выход из админ-панели."""
    await state.clear()
    await message.answer(
        "Вы вышли из админ-панели.",
        reply_markup=UserKeyboards.main_menu(),
    )


@router.message(F.text == AdminKeyboards.BACK_BTN)
async def back_to_admin_menu(
    message: Message,
    state: FSMContext,
    admin_id: int,
) -> None:
    """Возврат в меню админки."""
    if message.from_user.id != admin_id:
        return

    await state.set_state(AdminStates.main_menu)
    await message.answer(
        "🔐 Админ-панель",
        reply_markup=AdminKeyboards.main_menu(),
    )


@router.message(F.text == AdminKeyboards.STATS_BTN, AdminStates.main_menu)
async def show_stats(
    message: Message,
    admin_id: int,
    stats: StatsManager,
) -> None:
    """Показать статистику."""
    if message.from_user.id != admin_id:
        return

    total_users = await stats.get_total_users()
    users_today = await stats.get_users_today()
    total_views = await stats.get_total_faq_views()
    total_searches = await stats.get_total_searches()
    total_support = await stats.get_total_support_requests()

    text = (
        "📊 Статистика бота\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"👤 Активных сегодня: {users_today}\n"
        f"📖 Просмотров FAQ: {total_views}\n"
        f"🔍 Поисковых запросов: {total_searches}\n"
        f"💬 Обращений в поддержку: {total_support}"
    )

    await message.answer(text)


@router.message(F.text == AdminKeyboards.TOP_QUESTIONS_BTN, AdminStates.main_menu)
async def show_top_questions(
    message: Message,
    admin_id: int,
    stats: StatsManager,
) -> None:
    """Показать топ вопросов."""
    if message.from_user.id != admin_id:
        return

    top = await stats.get_top_questions(10)

    if not top:
        await message.answer("Пока нет данных о просмотрах.")
        return

    lines = ["🔝 Топ-10 популярных вопросов:\n"]
    for i, (question, count) in enumerate(top, 1):
        short_q = question[:50] + "..." if len(question) > 50 else question
        lines.append(f"{i}. {short_q} ({count})")

    await message.answer("\n".join(lines))


@router.message(F.text == AdminKeyboards.TOP_SEARCHES_BTN, AdminStates.main_menu)
async def show_top_searches(
    message: Message,
    admin_id: int,
    stats: StatsManager,
) -> None:
    """Показать топ поисковых запросов."""
    if message.from_user.id != admin_id:
        return

    top = await stats.get_top_searches(10)

    if not top:
        await message.answer("Пока нет поисковых запросов.")
        return

    lines = ["🔍 Топ-10 поисковых запросов:\n"]
    for i, (query, count) in enumerate(top, 1):
        lines.append(f"{i}. \"{query}\" ({count})")

    await message.answer("\n".join(lines))


@router.message(F.text == AdminKeyboards.FAILED_SEARCHES_BTN, AdminStates.main_menu)
async def show_failed_searches(
    message: Message,
    admin_id: int,
    stats: StatsManager,
) -> None:
    """Показать неудачные поисковые запросы."""
    if message.from_user.id != admin_id:
        return

    failed = await stats.get_failed_searches(10)

    if not failed:
        await message.answer("Нет неудачных поисковых запросов.")
        return

    lines = ["❌ Топ-10 запросов без результатов:\n"]
    for i, (query, count) in enumerate(failed, 1):
        lines.append(f"{i}. \"{query}\" ({count})")

    lines.append("\n💡 Рассмотрите добавление этих тем в FAQ.")

    await message.answer("\n".join(lines))


@router.message(F.text == AdminKeyboards.UPLOAD_BTN, AdminStates.main_menu)
async def request_faq_file(
    message: Message,
    state: FSMContext,
    admin_id: int,
) -> None:
    """Запросить файл FAQ."""
    if message.from_user.id != admin_id:
        return

    await state.set_state(AdminStates.awaiting_faq_file)

    await message.answer(
        "📤 Загрузка FAQ\n\n"
        "Отправьте JSON файл с FAQ в формате:\n"
        "```json\n"
        '{\n'
        '  "Категория 1": {\n'
        '    "Вопрос?": "Ответ"\n'
        '  }\n'
        '}\n'
        "```",
        parse_mode="Markdown",
        reply_markup=AdminKeyboards.cancel(),
    )


@router.message(F.document, AdminStates.awaiting_faq_file)
async def process_faq_file(
    message: Message,
    state: FSMContext,
    bot: Bot,
    admin_id: int,
    faq_loader: FAQLoader,
) -> None:
    """Обработка загруженного файла FAQ."""
    if message.from_user.id != admin_id:
        return

    document = message.document

    if not document.file_name.endswith(".json"):
        await message.answer("Файл должен иметь расширение .json")
        return

    if document.file_size > 1024 * 1024:
        await message.answer("Файл слишком большой. Максимум 1 МБ.")
        return

    try:
        file = await bot.get_file(document.file_id)
        file_content = await bot.download_file(file.file_path)
        content = file_content.read().decode("utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as e:
        await message.answer(f"Ошибка парсинга JSON: {e}")
        return
    except Exception as e:
        logger.error(f"Ошибка загрузки файла: {e}")
        await message.answer("Ошибка загрузки файла. Попробуйте еще раз.")
        return

    is_valid, error = faq_loader.validate_json(data)
    if not is_valid:
        await message.answer(f"Ошибка валидации: {error}")
        return

    categories_count = len(data)
    questions_count = sum(len(q) for q in data.values())

    await state.set_state(AdminStates.confirming_upload)
    await state.update_data(pending_faq=data)

    await message.answer(
        f"✅ Файл валиден\n\n"
        f"📁 Категорий: {categories_count}\n"
        f"❓ Вопросов: {questions_count}\n\n"
        f"Подтвердить загрузку?",
        reply_markup=AdminKeyboards.confirm_upload(),
    )


@router.callback_query(F.data == "confirm_upload", AdminStates.confirming_upload)
async def confirm_upload(
    callback: CallbackQuery,
    state: FSMContext,
    admin_id: int,
    faq_loader: FAQLoader,
    faq_search: FAQSearch,
) -> None:
    """Подтверждение загрузки FAQ."""
    if callback.from_user.id != admin_id:
        await callback.answer("Нет доступа", show_alert=True)
        return

    data = await state.get_data()
    pending_faq = data.get("pending_faq")

    if not pending_faq:
        await callback.answer("Данные не найдены", show_alert=True)
        return

    success = faq_loader.save(pending_faq)

    if success:
        faq_search.update_data(pending_faq)
        await callback.message.edit_text("✅ FAQ успешно обновлен!")
        logger.info(f"FAQ обновлен администратором {callback.from_user.id}")
    else:
        await callback.message.edit_text("❌ Ошибка сохранения FAQ")

    await state.set_state(AdminStates.main_menu)
    await callback.message.answer(
        "🔐 Админ-панель",
        reply_markup=AdminKeyboards.main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_upload")
async def cancel_upload(
    callback: CallbackQuery,
    state: FSMContext,
    admin_id: int,
) -> None:
    """Отмена загрузки FAQ."""
    if callback.from_user.id != admin_id:
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AdminStates.main_menu)
    await callback.message.edit_text("Загрузка отменена.")
    await callback.message.answer(
        "🔐 Админ-панель",
        reply_markup=AdminKeyboards.main_menu(),
    )
    await callback.answer()


@router.message(F.text == AdminKeyboards.DOWNLOAD_BTN, AdminStates.main_menu)
async def download_faq(
    message: Message,
    admin_id: int,
    faq_loader: FAQLoader,
) -> None:
    """Скачать текущий FAQ."""
    if message.from_user.id != admin_id:
        return

    if not faq_loader.data:
        await message.answer("FAQ пуст.")
        return

    content = faq_loader.export_json()
    file = BufferedInputFile(
        content.encode("utf-8"),
        filename="faq.json",
    )

    await message.answer_document(
        file,
        caption="📥 Текущий FAQ",
    )
