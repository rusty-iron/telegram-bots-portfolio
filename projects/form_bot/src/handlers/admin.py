"""
Обработчики админ-панели.

Содержит логику для команды /admin, просмотра заявок,
изменения статусов, ответа клиентам и экспорта данных.
"""

import logging
from math import ceil

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from src.config import settings
from src.keyboards.admin import (
    AdminCallback,
    get_admin_menu_keyboard,
    get_cancel_reply_keyboard,
    get_delete_confirm_keyboard,
    get_lead_detail_keyboard,
    get_leads_list_keyboard,
)
from src.states.admin import AdminStates
from src.utils.csv_manager import Lead, LeadStatus, csv_manager

logger = logging.getLogger(__name__)
router = Router(name="admin")

# Количество заявок на странице
ITEMS_PER_PAGE = 10

# Тексты сообщений
MESSAGES = {
    "access_denied": "⛔ Доступ запрещён. Эта команда доступна только администратору.",
    "main_menu": "🎛️ <b>Админ-панель</b>\n\nВыберите раздел:",
    "no_leads": "📭 Заявок пока нет.",
    "no_leads_in_category": "📭 Нет заявок с этим статусом.",
    "lead_not_found": "❌ Заявка не найдена.",
    "status_changed": "✅ Статус изменён на: {status}",
    "reply_prompt": (
        "💬 <b>Ответ клиенту</b>\n\n"
        "Введите текст сообщения для отправки клиенту.\n"
        "Для отмены нажмите кнопку ниже или отправьте /cancel"
    ),
    "reply_sent": "✅ Ответ успешно отправлен клиенту.",
    "reply_failed": "❌ Не удалось отправить сообщение клиенту. Возможно, пользователь заблокировал бота.",
    "reply_cancelled": "❌ Отправка ответа отменена.",
    "delete_confirm": "⚠️ <b>Точно удалить заявку #{lead_id}?</b>\n\nЭто действие нельзя отменить.",
    "delete_success": "✅ Заявка #{lead_id} удалена.",
    "delete_failed": "❌ Не удалось удалить заявку.",
    "delete_cancelled": "🔙 Удаление отменено.",
    "export_success": "📄 <b>Экспорт данных</b>\n\nФайл с заявками (всего: {count})",
    "export_empty": "📭 База заявок пуста. Нет данных для экспорта.",
    "export_error": "❌ Ошибка при экспорте данных.",
    "client_message": (
        "💬 <b>Ответ от поддержки:</b>\n\n"
        "{message}\n\n"
        "Спасибо, что обратились к нам!"
    ),
}

# Заголовки списков по категориям
CATEGORY_TITLES = {
    "all": "📋 Все заявки",
    "new": "🆕 Новые заявки",
    "progress": "⏳ Заявки в работе",
    "completed": "✅ Завершённые заявки",
}


def is_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором.

    Args:
        user_id: Telegram ID пользователя.

    Returns:
        bool: True если пользователь админ.
    """
    return user_id == settings.admin_id


def get_leads_by_category(category: str) -> list[Lead]:
    """
    Возвращает заявки по категории.

    Args:
        category: Категория (all, new, progress, completed).

    Returns:
        list[Lead]: Список заявок.
    """
    if category == "all":
        return csv_manager.get_all_leads()
    elif category == "new":
        return csv_manager.get_leads_by_status(LeadStatus.NEW.value)
    elif category == "progress":
        return csv_manager.get_leads_by_status(LeadStatus.IN_PROGRESS.value)
    elif category == "completed":
        return csv_manager.get_leads_by_status(LeadStatus.COMPLETED.value)
    return []


def format_lead_detail(lead: Lead) -> str:
    """
    Форматирует детальную информацию о заявке.

    Args:
        lead: Объект заявки.

    Returns:
        str: Отформатированный текст.
    """
    return (
        f"{lead.status_emoji} <b>Заявка #{lead.lead_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>Имя:</b> {lead.name}\n"
        f"📱 <b>Телефон:</b> <code>{lead.phone}</code>\n"
        f"📧 <b>Email:</b> {lead.email}\n"
        f"💬 <b>Сообщение:</b>\n<i>{lead.message}</i>\n\n"
        f"⏰ <b>Создано:</b> {lead.formatted_full_date}\n"
        f"🔄 <b>Обновлено:</b> {lead.formatted_updated_at}\n"
        f"🆔 <b>User ID:</b> <code>{lead.user_id}</code>"
    )


def format_leads_list(leads: list[Lead], category: str, total_count: int) -> str:
    """
    Форматирует заголовок списка заявок.

    Args:
        leads: Список заявок.
        category: Категория.
        total_count: Общее количество заявок в категории.

    Returns:
        str: Заголовок списка.
    """
    title = CATEGORY_TITLES.get(category, "📋 Заявки")
    return f"<b>{title} ({total_count})</b>"


# ==================== КОМАНДА /admin ====================


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /admin.

    Показывает главное меню админ-панели.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    user_id = message.from_user.id

    if not is_admin(user_id):
        logger.warning(f"Попытка доступа к админке от пользователя {user_id}")
        await message.answer(MESSAGES["access_denied"])
        return

    # Очищаем состояние FSM
    await state.clear()

    logger.info(f"Admin {user_id} opened admin panel")

    stats = csv_manager.get_stats()

    await message.answer(
        MESSAGES["main_menu"],
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard(stats),
    )


# ==================== CALLBACK: ГЛАВНОЕ МЕНЮ ====================


@router.callback_query(F.data == AdminCallback.MENU)
async def callback_admin_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик возврата в главное меню админки.

    Args:
        callback: Callback query.
        state: Контекст FSM.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES["access_denied"], show_alert=True)
        return

    # Очищаем состояние
    await state.clear()

    stats = csv_manager.get_stats()

    await callback.message.edit_text(
        MESSAGES["main_menu"],
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard(stats),
    )
    await callback.answer()


# ==================== CALLBACK: СПИСКИ ЗАЯВОК ====================


@router.callback_query(F.data.startswith(AdminCallback.LEADS_ALL))
@router.callback_query(F.data.startswith(AdminCallback.LEADS_NEW))
@router.callback_query(F.data.startswith(AdminCallback.LEADS_PROGRESS))
@router.callback_query(F.data.startswith(AdminCallback.LEADS_COMPLETED))
async def callback_leads_list(callback: CallbackQuery) -> None:
    """
    Обработчик отображения списка заявок по категориям.

    Args:
        callback: Callback query.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES["access_denied"], show_alert=True)
        return

    data = callback.data
    parts = data.split(":")
    page = int(parts[1]) if len(parts) > 1 else 1

    # Определяем категорию по callback_data
    if data.startswith(AdminCallback.LEADS_ALL):
        category = "all"
    elif data.startswith(AdminCallback.LEADS_NEW):
        category = "new"
    elif data.startswith(AdminCallback.LEADS_PROGRESS):
        category = "progress"
    else:
        category = "completed"

    await show_leads_page(callback, category, page)


@router.callback_query(F.data.startswith(AdminCallback.PAGE))
async def callback_page(callback: CallbackQuery) -> None:
    """
    Обработчик пагинации.

    Args:
        callback: Callback query.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES["access_denied"], show_alert=True)
        return

    # Формат: page:category:page_number
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Ошибка навигации")
        return

    category = parts[1]
    page = int(parts[2])

    await show_leads_page(callback, category, page)


@router.callback_query(F.data.startswith(AdminCallback.BACK_TO_LIST))
async def callback_back_to_list(callback: CallbackQuery) -> None:
    """
    Обработчик возврата к списку заявок.

    Args:
        callback: Callback query.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES["access_denied"], show_alert=True)
        return

    # Формат: back_to_list:category
    parts = callback.data.split(":")
    category = parts[1] if len(parts) > 1 else "all"

    await show_leads_page(callback, category, 1)


async def show_leads_page(callback: CallbackQuery, category: str, page: int) -> None:
    """
    Показывает страницу со списком заявок.

    Args:
        callback: Callback query.
        category: Категория заявок.
        page: Номер страницы.
    """
    leads = get_leads_by_category(category)
    total_count = len(leads)

    if total_count == 0:
        stats = csv_manager.get_stats()
        await callback.message.edit_text(
            MESSAGES["no_leads_in_category"] if category != "all" else MESSAGES["no_leads"],
            reply_markup=get_admin_menu_keyboard(stats),
        )
        await callback.answer()
        return

    # Пагинация
    total_pages = ceil(total_count / ITEMS_PER_PAGE)
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_leads = leads[start_idx:end_idx]

    header = format_leads_list(page_leads, category, total_count)

    await callback.message.edit_text(
        header,
        parse_mode="HTML",
        reply_markup=get_leads_list_keyboard(
            page_leads, category, page, total_pages, ITEMS_PER_PAGE
        ),
    )
    await callback.answer()


# ==================== CALLBACK: ДЕТАЛЬНЫЙ ПРОСМОТР ====================


@router.callback_query(F.data.startswith(AdminCallback.VIEW_LEAD))
async def callback_view_lead(callback: CallbackQuery) -> None:
    """
    Обработчик просмотра детальной информации о заявке.

    Args:
        callback: Callback query.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES["access_denied"], show_alert=True)
        return

    # Формат: view_lead:lead_id:category
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Ошибка")
        return

    lead_id = int(parts[1])
    category = parts[2]

    lead = csv_manager.get_lead_by_id(lead_id)

    if not lead:
        await callback.answer(MESSAGES["lead_not_found"], show_alert=True)
        return

    logger.info(f"Admin {callback.from_user.id} viewed lead #{lead_id}")

    await callback.message.edit_text(
        format_lead_detail(lead),
        parse_mode="HTML",
        reply_markup=get_lead_detail_keyboard(lead, category),
    )
    await callback.answer()


# ==================== CALLBACK: ИЗМЕНЕНИЕ СТАТУСА ====================


@router.callback_query(F.data.startswith(AdminCallback.SET_STATUS))
async def callback_set_status(callback: CallbackQuery) -> None:
    """
    Обработчик изменения статуса заявки.

    Args:
        callback: Callback query.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES["access_denied"], show_alert=True)
        return

    # Формат: set_status:lead_id:status:category
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("Ошибка")
        return

    lead_id = int(parts[1])
    status_key = parts[2]
    category = parts[3]

    # Определяем новый статус
    status_map = {
        "new": LeadStatus.NEW.value,
        "progress": LeadStatus.IN_PROGRESS.value,
        "completed": LeadStatus.COMPLETED.value,
    }

    new_status = status_map.get(status_key)
    if not new_status:
        await callback.answer("Неизвестный статус", show_alert=True)
        return

    # Обновляем статус
    success = csv_manager.update_lead_status(lead_id, new_status)

    if not success:
        await callback.answer(MESSAGES["lead_not_found"], show_alert=True)
        return

    logger.info(
        f"Admin {callback.from_user.id} changed status of lead #{lead_id} to {new_status}"
    )

    # Показываем уведомление
    await callback.answer(
        MESSAGES["status_changed"].format(status=new_status),
        show_alert=True,
    )

    # Обновляем отображение заявки
    lead = csv_manager.get_lead_by_id(lead_id)
    if lead:
        await callback.message.edit_text(
            format_lead_detail(lead),
            parse_mode="HTML",
            reply_markup=get_lead_detail_keyboard(lead, category),
        )


# ==================== CALLBACK: ОТВЕТ КЛИЕНТУ ====================


@router.callback_query(F.data.startswith(AdminCallback.REPLY))
async def callback_reply_lead(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик начала ответа клиенту.

    Args:
        callback: Callback query.
        state: Контекст FSM.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES["access_denied"], show_alert=True)
        return

    # Формат: reply_lead:lead_id:category
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Ошибка")
        return

    lead_id = int(parts[1])
    category = parts[2]

    lead = csv_manager.get_lead_by_id(lead_id)
    if not lead:
        await callback.answer(MESSAGES["lead_not_found"], show_alert=True)
        return

    # Сохраняем данные в FSM
    await state.update_data(
        reply_lead_id=lead_id,
        reply_user_id=lead.user_id,
        reply_category=category,
    )
    await state.set_state(AdminStates.waiting_for_reply)

    logger.info(f"Admin {callback.from_user.id} started reply to lead #{lead_id}")

    await callback.message.edit_text(
        MESSAGES["reply_prompt"],
        parse_mode="HTML",
        reply_markup=get_cancel_reply_keyboard(),
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_reply, F.text)
async def process_reply_message(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обрабатывает текст ответа клиенту.

    Args:
        message: Входящее сообщение с текстом ответа.
        state: Контекст FSM.
        bot: Экземпляр бота.
    """
    if not is_admin(message.from_user.id):
        return

    # Проверяем отмену
    if message.text == "/cancel":
        await state.clear()
        await message.answer(MESSAGES["reply_cancelled"])

        # Показываем главное меню
        stats = csv_manager.get_stats()
        await message.answer(
            MESSAGES["main_menu"],
            parse_mode="HTML",
            reply_markup=get_admin_menu_keyboard(stats),
        )
        return

    data = await state.get_data()
    lead_id = data.get("reply_lead_id")
    user_id = data.get("reply_user_id")
    category = data.get("reply_category", "all")

    reply_text = message.text.strip()

    # Отправляем сообщение клиенту
    try:
        await bot.send_message(
            chat_id=user_id,
            text=MESSAGES["client_message"].format(message=reply_text),
            parse_mode="HTML",
        )

        logger.info(
            f"Admin {message.from_user.id} sent reply to user {user_id} (lead #{lead_id})"
        )

        await message.answer(MESSAGES["reply_sent"])

    except Exception as e:
        logger.error(f"Failed to send reply to user {user_id}: {e}")
        await message.answer(MESSAGES["reply_failed"])

    # Очищаем состояние и показываем заявку
    await state.clear()

    lead = csv_manager.get_lead_by_id(lead_id)
    if lead:
        await message.answer(
            format_lead_detail(lead),
            parse_mode="HTML",
            reply_markup=get_lead_detail_keyboard(lead, category),
        )


# ==================== CALLBACK: УДАЛЕНИЕ ЗАЯВКИ ====================


@router.callback_query(F.data.startswith(AdminCallback.DELETE))
async def callback_delete_lead(callback: CallbackQuery) -> None:
    """
    Обработчик запроса на удаление заявки.

    Args:
        callback: Callback query.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES["access_denied"], show_alert=True)
        return

    # Формат: delete_lead:lead_id:category
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Ошибка")
        return

    lead_id = int(parts[1])
    category = parts[2]

    await callback.message.edit_text(
        MESSAGES["delete_confirm"].format(lead_id=lead_id),
        parse_mode="HTML",
        reply_markup=get_delete_confirm_keyboard(lead_id, category),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(AdminCallback.CONFIRM_DELETE))
async def callback_confirm_delete(callback: CallbackQuery) -> None:
    """
    Обработчик подтверждения удаления заявки.

    Args:
        callback: Callback query.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES["access_denied"], show_alert=True)
        return

    # Формат: confirm_delete:lead_id:category
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Ошибка")
        return

    lead_id = int(parts[1])
    category = parts[2]

    success = csv_manager.delete_lead(lead_id)

    if success:
        logger.info(f"Admin {callback.from_user.id} deleted lead #{lead_id}")
        await callback.answer(
            MESSAGES["delete_success"].format(lead_id=lead_id),
            show_alert=True,
        )
    else:
        await callback.answer(MESSAGES["delete_failed"], show_alert=True)

    # Возвращаемся к списку
    await show_leads_page(callback, category, 1)


@router.callback_query(F.data.startswith(AdminCallback.CANCEL_DELETE))
async def callback_cancel_delete(callback: CallbackQuery) -> None:
    """
    Обработчик отмены удаления заявки.

    Args:
        callback: Callback query.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES["access_denied"], show_alert=True)
        return

    # Формат: cancel_delete:lead_id:category
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Ошибка")
        return

    lead_id = int(parts[1])
    category = parts[2]

    await callback.answer(MESSAGES["delete_cancelled"])

    # Возвращаемся к заявке
    lead = csv_manager.get_lead_by_id(lead_id)
    if lead:
        await callback.message.edit_text(
            format_lead_detail(lead),
            parse_mode="HTML",
            reply_markup=get_lead_detail_keyboard(lead, category),
        )


# ==================== CALLBACK: ЭКСПОРТ ====================


@router.callback_query(F.data == AdminCallback.EXPORT)
async def callback_export(callback: CallbackQuery) -> None:
    """
    Обработчик экспорта данных в CSV.

    Args:
        callback: Callback query.
    """
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES["access_denied"], show_alert=True)
        return

    stats = csv_manager.get_stats()

    if stats["all"] == 0:
        await callback.answer(MESSAGES["export_empty"], show_alert=True)
        return

    csv_content = csv_manager.get_csv_content()

    if csv_content is None:
        await callback.answer(MESSAGES["export_error"], show_alert=True)
        return

    logger.info(f"Admin {callback.from_user.id} exported {stats['all']} leads")

    document = BufferedInputFile(
        file=csv_content,
        filename="leads_export.csv",
    )

    await callback.message.answer_document(
        document=document,
        caption=MESSAGES["export_success"].format(count=stats["all"]),
        parse_mode="HTML",
    )
    await callback.answer("📄 Файл отправлен")


# ==================== ОБРАБОТКА noop ====================


@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery) -> None:
    """
    Обработчик для неактивных кнопок (номера страниц).

    Args:
        callback: Callback query.
    """
    await callback.answer()
