"""
Inline-клавиатуры для админ-панели.

Содержит функции создания клавиатур для навигации по админке,
просмотра заявок и управления статусами.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.utils.csv_manager import Lead, LeadStatus


# Callback data prefixes
class AdminCallback:
    """Префиксы для callback_data."""

    MENU = "admin_menu"
    LEADS_ALL = "leads_all"
    LEADS_NEW = "leads_new"
    LEADS_PROGRESS = "leads_progress"
    LEADS_COMPLETED = "leads_completed"
    EXPORT = "admin_export"
    VIEW_LEAD = "view_lead"
    SET_STATUS = "set_status"
    REPLY = "reply_lead"
    DELETE = "delete_lead"
    CONFIRM_DELETE = "confirm_delete"
    CANCEL_DELETE = "cancel_delete"
    PAGE = "page"
    BACK_TO_LIST = "back_to_list"


def get_admin_menu_keyboard(stats: dict[str, int]) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру главного меню админки.

    Args:
        stats: Статистика по заявкам {all, new, in_progress, completed}.

    Returns:
        InlineKeyboardMarkup: Клавиатура главного меню.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"📋 Все заявки ({stats['all']})",
                callback_data=f"{AdminCallback.LEADS_ALL}:1"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🆕 Новые ({stats['new']})",
                callback_data=f"{AdminCallback.LEADS_NEW}:1"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"⏳ В работе ({stats['in_progress']})",
                callback_data=f"{AdminCallback.LEADS_PROGRESS}:1"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"✅ Завершённые ({stats['completed']})",
                callback_data=f"{AdminCallback.LEADS_COMPLETED}:1"
            )
        ],
        [
            InlineKeyboardButton(
                text="💾 Экспорт в CSV",
                callback_data=AdminCallback.EXPORT
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_leads_list_keyboard(
    leads: list[Lead],
    category: str,
    current_page: int,
    total_pages: int,
    items_per_page: int = 10,
) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру со списком заявок и пагинацией.

    Args:
        leads: Список заявок для отображения на текущей странице.
        category: Категория заявок (all, new, progress, completed).
        current_page: Номер текущей страницы (начиная с 1).
        total_pages: Общее количество страниц.
        items_per_page: Количество заявок на странице.

    Returns:
        InlineKeyboardMarkup: Клавиатура со списком заявок.
    """
    keyboard = []

    # Кнопки заявок
    for lead in leads:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📖 #{lead.lead_id} {lead.short_name} | {lead.formatted_date}",
                callback_data=f"{AdminCallback.VIEW_LEAD}:{lead.lead_id}:{category}"
            )
        ])

    # Пагинация
    if total_pages > 1:
        pagination_row = []

        # Кнопка "Назад"
        if current_page > 1:
            pagination_row.append(
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"{AdminCallback.PAGE}:{category}:{current_page - 1}"
                )
            )

        # Номер страницы
        pagination_row.append(
            InlineKeyboardButton(
                text=f"{current_page}/{total_pages}",
                callback_data="noop"
            )
        )

        # Кнопка "Вперёд"
        if current_page < total_pages:
            pagination_row.append(
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"{AdminCallback.PAGE}:{category}:{current_page + 1}"
                )
            )

        keyboard.append(pagination_row)

    # Кнопка возврата в главное меню
    keyboard.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data=AdminCallback.MENU
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_lead_detail_keyboard(lead: Lead, category: str) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру для детального просмотра заявки.

    Args:
        lead: Объект заявки.
        category: Категория, из которой пришли (для возврата).

    Returns:
        InlineKeyboardMarkup: Клавиатура управления заявкой.
    """
    keyboard = []

    # Кнопки изменения статуса (показываем только те, в которые можно перейти)
    status_row = []

    if lead.status != LeadStatus.IN_PROGRESS.value:
        status_row.append(
            InlineKeyboardButton(
                text="⏳ В работу",
                callback_data=f"{AdminCallback.SET_STATUS}:{lead.lead_id}:progress:{category}"
            )
        )

    if lead.status != LeadStatus.COMPLETED.value:
        status_row.append(
            InlineKeyboardButton(
                text="✅ Завершить",
                callback_data=f"{AdminCallback.SET_STATUS}:{lead.lead_id}:completed:{category}"
            )
        )

    if status_row:
        keyboard.append(status_row)

    # Дополнительная строка со статусом "Новая" если заявка не новая
    if lead.status != LeadStatus.NEW.value:
        keyboard.append([
            InlineKeyboardButton(
                text="🆕 Вернуть в новые",
                callback_data=f"{AdminCallback.SET_STATUS}:{lead.lead_id}:new:{category}"
            )
        ])

    # Ответить клиенту
    keyboard.append([
        InlineKeyboardButton(
            text="💬 Ответить клиенту",
            callback_data=f"{AdminCallback.REPLY}:{lead.lead_id}:{category}"
        )
    ])

    # Удалить заявку
    keyboard.append([
        InlineKeyboardButton(
            text="🗑️ Удалить заявку",
            callback_data=f"{AdminCallback.DELETE}:{lead.lead_id}:{category}"
        )
    ])

    # Назад к списку
    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ К списку",
            callback_data=f"{AdminCallback.BACK_TO_LIST}:{category}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_delete_confirm_keyboard(lead_id: int, category: str) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру подтверждения удаления заявки.

    Args:
        lead_id: ID заявки.
        category: Категория для возврата.

    Returns:
        InlineKeyboardMarkup: Клавиатура подтверждения.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text="❌ Да, удалить",
                callback_data=f"{AdminCallback.CONFIRM_DELETE}:{lead_id}:{category}"
            ),
            InlineKeyboardButton(
                text="🔙 Отмена",
                callback_data=f"{AdminCallback.CANCEL_DELETE}:{lead_id}:{category}"
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cancel_reply_keyboard() -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру отмены ответа клиенту.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой отмены.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=AdminCallback.MENU
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
