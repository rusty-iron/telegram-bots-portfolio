"""
Обработчики для административной панели
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

import structlog
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

from ..database import AdminUser, Category, Order, Product, User, get_db
from ..keyboards.admin import (
    get_admin_main_keyboard,
    get_back_to_products_keyboard,
    get_cancel_keyboard,
    get_categories_management_keyboard,
    get_category_actions_keyboard,
    get_category_list_keyboard_with_pagination,
    get_photo_management_keyboard,
    get_product_actions_keyboard,
    get_product_list_keyboard,
    get_product_list_keyboard_with_pagination,
    get_products_for_photo_keyboard,
    get_products_management_keyboard,
)
from ..keyboards.orders import (
    get_admin_order_management_keyboard,
    get_admin_orders_filter_keyboard,
)
from ..services.order_service import OrderService

logger = structlog.get_logger()
router = Router()
order_service = OrderService()


async def get_admin_info(user_id: int) -> Optional[dict]:
    """Получить информацию об администраторе"""
    try:
        with get_db() as db:
            admin = db.query(AdminUser).filter(
                AdminUser.telegram_id == user_id).first()
            if not admin or not admin.is_active:
                return None

            # admin.role может быть либо enum, либо строкой в зависимости от
            # версии БД
            role_value = admin.role.value if hasattr(
                admin.role, 'value') else admin.role

            return {
                "id": admin.id,
                "telegram_id": admin.telegram_id,
                "username": admin.username,
                "full_name": admin.full_name,
                "role": role_value,
                "is_active": admin.is_active,
            }
    except Exception as e:
        logger.error("get_admin_info_error", user_id=user_id, error=str(e))
        return None


def check_admin_permission(admin: dict, permission: str) -> bool:
    """Проверка прав администратора"""
    if not admin:
        return False

    admin_role = admin.get("role")
    if not admin_role:
        return False

    # Определяем права для каждой роли
    permissions = {
        "super_admin": [
            "manage_catalog",
            "manage_orders",
            "manage_users",
            "manage_admins",
            "manage_settings",
            "view_statistics",
            "manage_promotions",
        ],
        "admin": [
            "manage_catalog",
            "manage_orders",
            "manage_settings",
            "view_statistics",
            "manage_promotions",
        ],
        "moderator": ["manage_catalog", "view_statistics"],
    }

    return permission in permissions.get(admin_role, [])


class AddProductStates(StatesGroup):
    """Состояния для добавления товара"""

    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_unit = State()
    waiting_for_category = State()


class AddCategoryStates(StatesGroup):
    """Состояния для добавления категории"""

    waiting_for_name = State()
    waiting_for_description = State()


class EditProductStates(StatesGroup):
    """Состояния для редактирования товара"""

    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_unit = State()
    waiting_for_category = State()


class EditCategoryStates(StatesGroup):
    """Состояния для редактирования категории"""

    waiting_for_name = State()
    waiting_for_description = State()


class PhotoManagementStates(StatesGroup):
    """Состояния для управления фотографиями товаров"""

    waiting_for_product_selection = State()
    waiting_for_photo_upload = State()


@router.message(Command("admin"))
async def admin_command(message: Message, admin=None, **kwargs):
    """Команда /admin для входа в административную панель"""
    if not admin:
        await message.answer("❌ У вас нет прав администратора!")
        return

    welcome_text = (
        f"👋 Добро пожаловать, {admin.get('full_name', 'Администратор')}!\n\n"
        f"🔐 Роль: {admin.get('role', 'Неизвестно')}\n"
        f"📅 Последний вход: {admin.get('last_login', 'Неизвестно')}\n\n"
        f"Выберите действие:"
    )

    await message.answer(welcome_text, reply_markup=get_admin_main_keyboard())


@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery, admin=None, **kwargs):
    """Статистика админ панели"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "view_statistics"):
        await callback.answer("❌ Недостаточно прав!")
        return

    with get_db() as db:
        # Получаем статистику
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active).count()

        total_products = db.query(Product).count()
        active_products = db.query(Product).filter(Product.is_active).count()

        total_categories = db.query(Category).count()
        active_categories = (
            db.query(Category).filter(Category.is_active).count()
        )

        total_orders = db.query(Order).count()
        pending_orders = (
            db.query(Order).filter(Order.status == "pending").count()
        )
        delivered_orders = (
            db.query(Order).filter(Order.status == "delivered").count()
        )

        total_admins = db.query(AdminUser).count()
        active_admins = db.query(AdminUser).filter(AdminUser.is_active).count()

        stats_text = (
            f"📊 **Статистика системы**\n\n"
            f"👥 **Пользователи:**\n"
            f"• Всего: {total_users}\n"
            f"• Активных: {active_users}\n\n"
            f"📦 **Товары:**\n"
            f"• Всего: {total_products}\n"
            f"• Активных: {active_products}\n\n"
            f"📁 **Категории:**\n"
            f"• Всего: {total_categories}\n"
            f"• Активных: {active_categories}\n\n"
            f"🛒 **Заказы:**\n"
            f"• Всего: {total_orders}\n"
            f"• В ожидании: {pending_orders}\n"
            f"• Доставленных: {delivered_orders}\n\n"
            f"👨‍💼 **Администраторы:**\n"
            f"• Всего: {total_admins}\n"
            f"• Активных: {active_admins}\n\n"
            f"🕒 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        # Создаем клавиатуру с кнопкой возврата
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Обновить", callback_data="admin_stats"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад в админку", callback_data="admin_main"
                    )
                ],
            ]
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            stats_text, reply_markup=keyboard, parse_mode="Markdown"
        )
        await callback.answer()


@router.callback_query(F.data == "admin_main")
async def admin_main_callback(callback: CallbackQuery, admin=None, **kwargs):
    """Главное меню администратора"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    welcome_text = (
        f"👋 Добро пожаловать, {admin.get('full_name', 'Администратор')}!\n\n"
        f"🔐 Роль: {admin.get('role', 'Неизвестно')}\n"
        f"📅 Последний вход: "
        f"{admin.get('last_login', 'Неизвестно')}\n\n"
        f"Выберите действие:"
    )

    if not callback.message or isinstance(
            callback.message, InaccessibleMessage):
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return

    assert isinstance(callback.message, Message)

    await callback.message.edit_text(
        welcome_text, reply_markup=get_admin_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_orders")
async def admin_orders_callback(callback: CallbackQuery):
    """Обработчик кнопки управления заказами в админ-панели"""
    admin = await get_admin_info(callback.from_user.id)
    if not admin:
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    if not check_admin_permission(admin, "manage_orders"):
        await callback.answer("❌ У вас нет прав для управления заказами", show_alert=True)
        return

    logger.info("admin_orders_requested", admin_id=admin.get("id"))

    # Получаем статистику заказов
    statistics = order_service.get_order_statistics()

    # Формируем сообщение со статистикой
    stats_text = "📊 **Статистика заказов:**\n\n"
    stats_text += f"📋 **Всего заказов:** {statistics.get('total_orders', 0)}\n"
    stats_text += f"💰 **Общая сумма:** {
        statistics.get(
            'total_amount', 0):.2f}₽\n"
    stats_text += f"💳 **Средний чек:** {
        statistics.get(
            'average_order_value',
            0):.2f}₽\n\n"

    # Статистика по статусам
    status_breakdown = statistics.get("status_breakdown", {})
    status_emojis = {
        "pending": "⏳",
        "confirmed": "✅",
        "processing": "🔄",
        "shipped": "🚚",
        "delivered": "📦",
        "cancelled": "❌",
    }

    stats_text += "📊 **По статусам:**\n"
    for status, count in status_breakdown.items():
        emoji = status_emojis.get(status, "❓")
        stats_text += f"{emoji} {status}: {count}\n"

    stats_text += "\nВыберите фильтр для просмотра заказов:"

    if callback.message and not isinstance(
            callback.message, InaccessibleMessage):
        assert isinstance(callback.message, Message)

        try:
            await callback.message.edit_text(
                stats_text,
                reply_markup=get_admin_orders_filter_keyboard(),
                parse_mode="Markdown",
            )
        except Exception as edit_error:
            # Игнорируем ошибку, если сообщение не изменилось
            if "message is not modified" not in str(edit_error):
                raise

    await callback.answer("✅ Статистика обновлена!")


@router.callback_query(F.data == "admin_products")
async def admin_products_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Меню управления товарами"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.message or isinstance(
            callback.message, InaccessibleMessage):
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return

    assert isinstance(callback.message, Message)

    await callback.message.edit_text(
        "📦 **Управление товарами**\n\nВыберите действие:",
        reply_markup=get_products_management_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_categories")
async def admin_categories_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Меню управления категориями"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.message or isinstance(
            callback.message, InaccessibleMessage):
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return

    assert isinstance(callback.message, Message)

    await callback.message.edit_text(
        "📋 **Управление категориями**\n\nВыберите действие:",
        reply_markup=get_categories_management_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_list_products")
async def admin_list_products_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Список товаров"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    with get_db() as db:
        products = db.query(Product).filter(Product.is_active).all()

        if not products:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                "📦 **Список товаров**\n\nТовары не найдены.",
                reply_markup=get_products_management_keyboard(),
                parse_mode="Markdown",
            )
        else:
            # Используем пагинацию с 10 товарами на странице

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"📦 **Список товаров**\n\nНайдено товаров: {len(products)}\nСтраница 1 из {((len(products) - 1) // 10) + 1}",
                reply_markup=get_product_list_keyboard(
                    products, page=0, per_page=10, action="view"
                ),
                parse_mode="Markdown",
            )

    await callback.answer()


@router.callback_query(F.data.startswith("admin_products_page_"))
async def admin_products_page_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Обработка пагинации списка товаров"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    page = int(callback.data.replace("admin_products_page_", ""))

    with get_db() as db:
        products = db.query(Product).filter(Product.is_active).all()

        if not products:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                "📦 **Список товаров**\n\nТовары не найдены.",
                reply_markup=get_products_management_keyboard(),
                parse_mode="Markdown",
            )
        else:
            total_pages = ((len(products) - 1) // 10) + 1
            current_page = page + 1

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"📦 **Список товаров**\n\nНайдено товаров: {len(products)}\nСтраница {current_page} из {total_pages}",
                reply_markup=get_product_list_keyboard(
                    products, page=page, per_page=10, action="view"
                ),
                parse_mode="Markdown",
            )

    await callback.answer()


@router.callback_query(F.data == "admin_edit_category")
async def admin_edit_category_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Меню редактирования категорий - показывает все категории с пагинацией"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    with get_db() as db:
        categories = db.query(
            Category
        ).all()  # Все категории (активные и неактивные)

        if not categories:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                "📝 **Редактирование категорий**\n\nКатегории не найдены.",
                reply_markup=get_categories_management_keyboard(),
                parse_mode="Markdown",
            )
        else:
            # Используем пагинацию с 10 категориями на странице
            total_pages = ((len(categories) - 1) // 10) + 1
            current_page = 1

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"📝 **Редактирование категорий**\n\nНайдено категорий: {len(categories)}\nСтраница {current_page} из {total_pages}",
                reply_markup=get_category_list_keyboard_with_pagination(
                    categories, page=0, per_page=10, action="edit"
                ),
                parse_mode="Markdown",
            )
    await callback.answer()


@router.callback_query(F.data == "admin_delete_category")
async def admin_delete_category_menu_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Меню удаления категорий - показывает только активные категории с пагинацией"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    with get_db() as db:
        categories = (
            db.query(Category).filter(Category.is_active).all()
        )  # Только активные

        if not categories:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                "🗑️ **Удаление категорий**\n\nНет активных категорий для удаления.",
                reply_markup=get_categories_management_keyboard(),
                parse_mode="Markdown",
            )
        else:
            # Используем пагинацию с 10 категориями на странице
            total_pages = ((len(categories) - 1) // 10) + 1
            current_page = 1

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"🗑️ **Удаление категорий**\n\nНайдено активных категорий: {len(categories)}\nСтраница {current_page} из {total_pages}",
                reply_markup=get_category_list_keyboard_with_pagination(
                    categories, page=0, per_page=10, action="delete"
                ),
                parse_mode="Markdown",
            )
    await callback.answer()


@router.callback_query(F.data == "admin_activate_category")
async def admin_activate_category_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Меню активации категорий - показывает только неактивные категории с пагинацией"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    with get_db() as db:
        categories = (
            db.query(Category).filter(~Category.is_active).all()
        )  # Только неактивные

        if not categories:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                "🔄 **Активация категорий**\n\nНет неактивных категорий для активации.",
                reply_markup=get_categories_management_keyboard(),
                parse_mode="Markdown",
            )
        else:
            # Используем пагинацию с 10 категориями на странице
            total_pages = ((len(categories) - 1) // 10) + 1
            current_page = 1

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"🔄 **Активация категорий**\n\nНайдено неактивных категорий: {len(categories)}\nСтраница {current_page} из {total_pages}",
                reply_markup=get_category_list_keyboard_with_pagination(
                    categories, page=0, per_page=10, action="activate"
                ),
                parse_mode="Markdown",
            )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_category_page_"))
async def admin_category_page_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Обработчик пагинации для категорий"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    # Парсим callback_data: admin_category_page_{action}_{page}
    parts = callback.data.split("_")
    action = parts[3]  # edit, delete, activate
    page = int(parts[4])

    with get_db() as db:
        if action == "edit":
            categories = db.query(Category).all()  # Все категории
            title = "📝 **Редактирование категорий**"
        elif action == "delete":
            categories = (
                db.query(Category).filter(Category.is_active).all()
            )  # Только активные
            title = "🗑️ **Удаление категорий**"
        elif action == "activate":
            categories = (
                db.query(Category).filter(~Category.is_active).all()
            )  # Только неактивные
            title = "🔄 **Активация категорий**"
        else:
            await callback.answer("❌ Неизвестное действие!")
            return

        if not categories:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"{title}\n\nКатегории не найдены.",
                reply_markup=get_categories_management_keyboard(),
                parse_mode="Markdown",
            )
        else:
            total_pages = ((len(categories) - 1) // 10) + 1
            current_page = page + 1

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"{title}\n\nНайдено категорий: {len(categories)}\nСтраница {current_page} из {total_pages}",
                reply_markup=get_category_list_keyboard_with_pagination(
                    categories, page=page, per_page=10, action=action
                ),
                parse_mode="Markdown",
            )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_view_photo_product_"))
async def admin_view_photo_product_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Просмотр товара из управления фотографиями"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    product_id = int(callback.data.replace("admin_view_photo_product_", ""))

    with get_db() as db:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            await callback.answer("❌ Товар не найден!")
            return

        product_text = (
            f"📦 **{product.name}**\n\n"
            f"📝 Описание: {product.description or 'Не указано'}\n"
            f"💰 Цена: {product.price}₽\n"
            f"📏 Единица: {product.unit}\n"
            f"📋 Категория: {product.category.name}\n"
            f"🟢 Статус: {'Активен' if product.is_active else 'Неактивен'}\n"
            f"📦 Доступность: {'Доступен' if product.is_available else 'Недоступен'}"
        )

        # Если у товара есть фотография, отправляем её
        if product.image_url:
            try:

                if not callback.message or isinstance(
                        callback.message, InaccessibleMessage):
                    await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                    return

                assert isinstance(callback.message, Message)

                await callback.message.answer_photo(
                    photo=product.image_url,
                    caption=product_text,
                    parse_mode="Markdown",
                    reply_markup=get_product_actions_keyboard(
                        product.id, product.is_active, "photo_management"
                    ),
                )
            except Exception as e:
                logger.error(
                    "photo_send_error",
                    admin_id=admin.get("id"),
                    product_id=product.id,
                    error=str(e),
                )
                # Если не удалось отправить фото, отправляем только текст

                if not callback.message or isinstance(
                        callback.message, InaccessibleMessage):
                    await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                    return

                assert isinstance(callback.message, Message)

                await callback.message.answer(
                    product_text + "\n\n❌ Ошибка при загрузке фотографии",
                    reply_markup=get_product_actions_keyboard(
                        product.id, product.is_active, "photo_management"
                    ),
                    parse_mode="Markdown",
                )
        else:
            # Если фотографии нет, отправляем только текст

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                product_text,
                reply_markup=get_product_actions_keyboard(
                    product.id, product.is_active, "photo_management"
                ),
                parse_mode="Markdown",
            )

    await callback.answer()


@router.callback_query(F.data.startswith("admin_view_product_"))
async def admin_view_product_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Просмотр товара"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    product_id = int(callback.data.replace("admin_view_product_", ""))

    with get_db() as db:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            await callback.answer("❌ Товар не найден!")
            return

        product_text = (
            f"📦 **{product.name}**\n\n"
            f"📝 Описание: {product.description or 'Не указано'}\n"
            f"💰 Цена: {product.price}₽\n"
            f"📏 Единица: {product.unit}\n"
            f"📋 Категория: {product.category.name}\n"
            f"🟢 Статус: {'Активен' if product.is_active else 'Неактивен'}\n"
            f"📦 Доступность: {'Доступен' if product.is_available else 'Недоступен'}"
        )

        # Если у товара есть фотография, отправляем её
        if product.image_url:
            try:

                if not callback.message or isinstance(
                        callback.message, InaccessibleMessage):
                    await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                    return

                assert isinstance(callback.message, Message)

                await callback.message.answer_photo(
                    photo=product.image_url,
                    caption=product_text,
                    parse_mode="Markdown",
                    reply_markup=get_product_actions_keyboard(
                        product.id, product.is_active, "general"
                    ),
                )
            except Exception as e:
                logger.error(
                    "photo_send_error",
                    admin_id=admin.get("id"),
                    product_id=product.id,
                    error=str(e),
                )
                # Если не удалось отправить фото, отправляем только текст

                if not callback.message or isinstance(
                        callback.message, InaccessibleMessage):
                    await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                    return

                assert isinstance(callback.message, Message)

                await callback.message.edit_text(
                    product_text + "\n\n❌ Ошибка при загрузке фотографии",
                    reply_markup=get_product_actions_keyboard(
                        product.id, product.is_active, "general"
                    ),
                    parse_mode="Markdown",
                )
        else:
            # Если фотографии нет, отправляем только текст

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                product_text,
                reply_markup=get_product_actions_keyboard(
                    product.id, product.is_active, "general"
                ),
                parse_mode="Markdown",
            )

    await callback.answer()


@router.callback_query(F.data.startswith("admin_view_category_"))
async def admin_view_category_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Просмотр категории"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    category_id = int(callback.data.replace("admin_view_category_", ""))

    with get_db() as db:
        category = (
            db.query(Category).filter(Category.id == category_id).first()
        )

        if not category:
            await callback.answer("❌ Категория не найдена!")
            return

        products_count = (
            db.query(Product)
            .filter(Product.category_id == category.id)
            .count()
        )

        category_text = (
            f"📋 **{category.name}**\n\n"
            f"📝 Описание: {category.description or 'Не указано'}\n"
            f"🟢 Статус: {'Активна' if category.is_active else 'Неактивна'}\n"
            f"📦 Товаров в категории: {products_count}"
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            category_text,
            reply_markup=get_category_actions_keyboard(category.id),
            parse_mode="Markdown",
        )

    await callback.answer()


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_callback(
    callback: CallbackQuery, state: FSMContext, admin=None, **kwargs
):
    """Начало добавления товара"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    await state.set_state(AddProductStates.waiting_for_name)

    if not callback.message or isinstance(
            callback.message, InaccessibleMessage):
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return

    assert isinstance(callback.message, Message)

    await callback.message.edit_text(
        "📦 **Добавление товара**\n\nВведите название товара:",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(AddProductStates.waiting_for_name)
async def process_product_name(
    message: Message, state: FSMContext, admin=None, **kwargs
):
    """Обработка названия товара"""
    if not admin:
        await message.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await message.answer("❌ Недостаточно прав!")
        return

    await state.update_data(name=message.text)
    await state.set_state(AddProductStates.waiting_for_description)

    await message.answer(
        "📝 Введите описание товара:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard("admin_products"),
    )


@router.message(AddProductStates.waiting_for_description)
async def process_product_description(
    message: Message, state: FSMContext, admin=None, **kwargs
):
    """Обработка описания товара"""
    if not admin:
        await message.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await message.answer("❌ Недостаточно прав!")
        return

    await state.update_data(description=message.text)
    await state.set_state(AddProductStates.waiting_for_price)

    await message.answer(
        "💰 Введите цену товара (только число):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard("admin_products"),
    )


@router.message(AddProductStates.waiting_for_price)
async def process_product_price(
    message: Message, state: FSMContext, admin=None, **kwargs
):
    """Обработка цены товара"""
    if not admin:
        await message.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await message.answer("❌ Недостаточно прав!")
        return

    try:
        if not message.text:
            await message.answer(
                "❌ Неверный формат цены! Введите положительное число:",
                reply_markup=get_cancel_keyboard("admin_products"),
            )
            return
        price = Decimal(message.text.replace(",", "."))
        if price <= 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Неверный формат цены! Введите положительное число:",
            reply_markup=get_cancel_keyboard("admin_products"),
        )
        return

    await state.update_data(price=price)
    await state.set_state(AddProductStates.waiting_for_unit)

    await message.answer(
        "📏 Введите единицу измерения (кг, шт, упак и т.д.):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard("admin_products"),
    )


@router.message(AddProductStates.waiting_for_unit)
async def process_product_unit(
    message: Message, state: FSMContext, admin=None, **kwargs
):
    """Обработка единицы измерения товара"""
    if not admin:
        await message.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await message.answer("❌ Недостаточно прав!")
        return

    await state.update_data(unit=message.text)
    await state.set_state(AddProductStates.waiting_for_category)

    # Показываем список категорий
    with get_db() as db:
        categories = db.query(Category).filter(Category.is_active).all()

        if not categories:
            await message.answer(
                "❌ Нет активных категорий! Сначала создайте категорию.",
                reply_markup=get_back_to_products_keyboard(),
            )
            await state.clear()
            return

        categories_text = "📋 **Выберите категорию:**\n\n"
        keyboard_buttons = []

        for i, category in enumerate(categories, 1):
            categories_text += f"{i}. {category.name}\n"
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text=category.name,
                        callback_data=f"select_category_{category.id}",
                    )
                ]
            )

        # Добавляем кнопку отмены
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data="admin_products"
                )
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await message.answer(
            categories_text, reply_markup=keyboard, parse_mode="Markdown"
        )


@router.callback_query(F.data.startswith("select_category_"))
async def process_product_category(
    callback: CallbackQuery, state: FSMContext, admin=None, **kwargs
):
    """Обработка выбора категории для товара"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    category_id = int(callback.data.replace("select_category_", ""))

    # Получаем все данные из состояния
    product_data = await state.get_data()
    await state.clear()

    # Проверяем, что все данные есть
    required_fields = ["name", "description", "price", "unit"]
    for field in required_fields:
        if field not in product_data:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(f"❌ Отсутствует поле: {field}")
            await callback.answer("❌ Ошибка: неполные данные")
            return

    # Создаем товар
    with get_db() as db:
        category = (
            db.query(Category).filter(Category.id == category_id).first()
        )

        if not category:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text("❌ Категория не найдена!")
            await callback.answer("❌ Ошибка: категория не найдена")
            return

        product = Product(
            name=product_data["name"],
            description=product_data["description"],
            price=product_data["price"],
            unit=product_data["unit"],
            category_id=category_id,
            is_active=True,
            is_available=True,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        logger.info(
            "product_created",
            admin_id=admin.get("id"),
            product_id=product.id,
            product_name=product.name,
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            f"✅ **Товар успешно создан!**\n\n"
            f"📦 {product.name}\n"
            f"💰 {product.price}₽\n"
            f"📋 {category.name}",
            reply_markup=get_products_management_keyboard(),
            parse_mode="Markdown",
        )
        await callback.answer("✅ Товар успешно добавлен!")


@router.callback_query(F.data == "admin_add_category")
async def admin_add_category_callback(
    callback: CallbackQuery, state: FSMContext, admin=None, **kwargs
):
    """Начало добавления категории"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    await state.set_state(AddCategoryStates.waiting_for_name)

    if not callback.message or isinstance(
            callback.message, InaccessibleMessage):
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return

    assert isinstance(callback.message, Message)

    await callback.message.answer(
        "📋 **Добавление категории**\n\nВведите название категории:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard("admin_categories"),
    )
    await callback.answer()


@router.message(AddCategoryStates.waiting_for_name)
async def process_category_name(
    message: Message, state: FSMContext, admin=None, **kwargs
):
    """Обработка названия категории"""
    if not admin:
        await message.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await message.answer("❌ Недостаточно прав!")
        return

    await state.update_data(name=message.text)
    await state.set_state(AddCategoryStates.waiting_for_description)

    await message.answer(
        "📝 Введите описание категории:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard("admin_categories"),
    )


@router.message(AddCategoryStates.waiting_for_description)
async def process_category_description(
    message: Message, state: FSMContext, admin=None, **kwargs
):
    """Обработка описания категории"""
    if not admin:
        await message.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await message.answer("❌ Недостаточно прав!")
        return

    category_data = await state.get_data()
    await state.clear()

    # Создаем категорию
    with get_db() as db:
        category = Category(
            name=category_data["name"],
            description=message.text,
            is_active=True,
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        logger.info(
            "category_created",
            admin_id=admin.get("id"),
            category_id=category.id,
            category_name=category.name,
        )

        await message.answer(
            f"✅ **Категория успешно создана!**\n\n"
            f"📋 {category.name}\n"
            f"📝 {category.description}",
            reply_markup=get_categories_management_keyboard(),
            parse_mode="Markdown",
        )


@router.callback_query(F.data == "admin_edit_product")
async def admin_edit_product_menu_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Меню редактирования товаров - показывает список товаров"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    with get_db() as db:
        products = db.query(
            Product
        ).all()  # Все товары (активные и неактивные)

        if not products:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                "📝 **Редактирование товаров**\n\nТовары не найдены.",
                reply_markup=get_products_management_keyboard(),
                parse_mode="Markdown",
            )
        else:
            # Используем пагинацию с 10 товарами на странице
            total_pages = ((len(products) - 1) // 10) + 1
            current_page = 1

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"📝 **Редактирование товаров**\n\nНайдено товаров: {len(products)}\nСтраница {current_page} из {total_pages}",
                reply_markup=get_product_list_keyboard_with_pagination(
                    products, page=0, per_page=10, action="edit"
                ),
                parse_mode="Markdown",
            )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_product_"))
async def admin_edit_product_callback(
    callback: CallbackQuery, state: FSMContext, admin=None, **kwargs
):
    """Начало редактирования товара"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    product_id = int(callback.data.replace("admin_edit_product_", ""))

    with get_db() as db:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            await callback.answer("❌ Товар не найден!")
            return

        # Сохраняем ID товара и текущие значения в состоянии
        await state.update_data(
            product_id=product_id,
            current_name=product.name,
            current_description=product.description,
            current_price=product.price,
            current_unit=product.unit,
        )
        await state.set_state(EditProductStates.waiting_for_name)

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.answer(
            f"✏️ **Редактирование товара: {product.name}**\n\n"
            f"Текущее название: {product.name}\n"
            f"Введите новое название товара:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard("admin_products"),
        )

    await callback.answer()


@router.message(EditProductStates.waiting_for_name)
async def process_edit_product_name(
    message: Message, state: FSMContext, admin=None, **kwargs
):
    """Обработка нового названия товара"""
    if not admin:
        await message.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await message.answer("❌ Недостаточно прав!")
        return

    await state.update_data(name=message.text)
    await state.set_state(EditProductStates.waiting_for_description)

    # Получаем данные товара из состояния для показа текущего описания
    product_data = await state.get_data()
    current_description = product_data.get("current_description", "не указано")

    await message.answer(
        f"📝 **Введите новое описание товара**\n\n"
        f"Текущее описание: {current_description}\n"
        f"Введите новое описание товара:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard("admin_products"),
    )


@router.message(EditProductStates.waiting_for_description)
async def process_edit_product_description(
    message: Message, state: FSMContext, admin=None, **kwargs
):
    """Обработка нового описания товара"""
    if not admin:
        await message.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await message.answer("❌ Недостаточно прав!")
        return

    await state.update_data(description=message.text)
    await state.set_state(EditProductStates.waiting_for_price)

    # Получаем данные товара из состояния для показа текущей цены
    product_data = await state.get_data()
    current_price = product_data.get("current_price", "не указана")

    await message.answer(
        f"💰 **Введите новую цену товара**\n\n"
        f"Текущая цена: {current_price}₽\n"
        f"Введите новую цену (только число):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard("admin_products"),
    )


@router.message(EditProductStates.waiting_for_price)
async def process_edit_product_price(
    message: Message, state: FSMContext, admin=None, **kwargs
):
    """Обработка новой цены товара"""
    if not admin:
        await message.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await message.answer("❌ Недостаточно прав!")
        return

    try:
        if not message.text:
            await message.answer(
                "❌ Неверный формат цены! Введите положительное число:",
                reply_markup=get_cancel_keyboard("admin_products"),
            )
            return
        price = Decimal(message.text.replace(",", "."))
        if price <= 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Неверный формат цены! Введите положительное число:",
            reply_markup=get_cancel_keyboard("admin_products"),
        )
        return

    await state.update_data(price=price)
    await state.set_state(EditProductStates.waiting_for_unit)

    # Получаем данные товара из состояния для показа текущей единицы измерения
    product_data = await state.get_data()
    current_unit = product_data.get("current_unit", "не указана")

    await message.answer(
        f"📏 **Введите новую единицу измерения**\n\n"
        f"Текущая единица: {current_unit}\n"
        f"Введите новую единицу измерения (кг, шт, упак и т.д.):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard("admin_products"),
    )


@router.message(EditProductStates.waiting_for_unit)
async def process_edit_product_unit(
    message: Message, state: FSMContext, admin=None, **kwargs
):
    """Обработка новой единицы измерения товара"""
    if not admin:
        await message.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await message.answer("❌ Недостаточно прав!")
        return

    await state.update_data(unit=message.text)
    await state.set_state(EditProductStates.waiting_for_category)

    # Показываем список категорий
    with get_db() as db:
        categories = db.query(Category).filter(Category.is_active).all()

        if not categories:
            await message.answer(
                "❌ Нет активных категорий!",
                reply_markup=get_back_to_products_keyboard(),
            )
            await state.clear()
            return

        categories_text = "📋 **Выберите новую категорию:**\n\n"
        keyboard_buttons = []

        for i, category in enumerate(categories, 1):
            categories_text += f"{i}. {category.name}\n"
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text=category.name,
                        callback_data=f"edit_select_category_{category.id}",
                    )
                ]
            )

        # Добавляем кнопку отмены
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data="admin_products"
                )
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await message.answer(
            categories_text, reply_markup=keyboard, parse_mode="Markdown"
        )


@router.callback_query(F.data.startswith("edit_select_category_"))
async def process_edit_product_category(
    callback: CallbackQuery, state: FSMContext, admin=None, **kwargs
):
    """Обработка выбора новой категории для товара"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    category_id = int(callback.data.replace("edit_select_category_", ""))

    # Получаем все данные из состояния
    product_data = await state.get_data()
    await state.clear()

    # Обновляем товар
    with get_db() as db:
        product = (
            db.query(Product)
            .filter(Product.id == product_data["product_id"])
            .first()
        )

        if not product:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text("❌ Товар не найден!")
            return

        category = (
            db.query(Category).filter(Category.id == category_id).first()
        )

        if not category:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text("❌ Категория не найдена!")
            return

        # Обновляем поля товара
        product.name = product_data["name"]
        product.description = product_data["description"]
        product.price = product_data["price"]
        product.unit = product_data["unit"]
        product.category_id = category_id

        db.commit()

        logger.info(
            "product_updated",
            admin_id=admin.get("id"),
            product_id=product.id,
            product_name=product.name,
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            f"✅ **Товар успешно обновлен!**\n\n"
            f"📦 {product.name}\n"
            f"💰 {product.price}₽\n"
            f"📋 {category.name}",
            reply_markup=get_products_management_keyboard(),
            parse_mode="Markdown",
        )
        await callback.answer("✅ Товар успешно обновлен!")


@router.callback_query(F.data == "admin_delete_product")
async def admin_delete_product_menu_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Меню удаления товаров - показывает список товаров"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    with get_db() as db:
        products = (
            db.query(Product).filter(Product.is_active).all()
        )  # Только активные

        if not products:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                "🗑️ **Удаление товаров**\n\nНет активных товаров для удаления.",
                reply_markup=get_products_management_keyboard(),
                parse_mode="Markdown",
            )
        else:
            # Используем пагинацию с 10 товарами на странице
            total_pages = ((len(products) - 1) // 10) + 1
            current_page = 1

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"🗑️ **Удаление товаров**\n\nНайдено активных товаров: {len(products)}\nСтраница {current_page} из {total_pages}",
                reply_markup=get_product_list_keyboard_with_pagination(
                    products, page=0, per_page=10, action="delete"
                ),
                parse_mode="Markdown",
            )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delete_product_"))
async def admin_delete_product_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Удаление товара"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    product_id = int(callback.data.replace("admin_delete_product_", ""))

    with get_db() as db:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            await callback.answer("❌ Товар не найден!")
            return

        product_name = product.name

        # Мягкое удаление - помечаем как неактивный
        product.is_active = False
        product.is_available = False
        db.commit()

        logger.info(
            "product_deleted",
            admin_id=admin.get("id"),
            product_id=product.id,
            product_name=product_name,
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.answer(
            f"✅ **Товар '{product_name}' успешно удален!**\n\n"
            f"Товар помечен как неактивный и недоступный для заказа.",
            reply_markup=get_product_actions_keyboard(
                product.id, product.is_active, "general"
            ),
            parse_mode="Markdown",
        )
        await callback.answer("✅ Товар успешно удален!")


@router.callback_query(F.data.startswith("admin_delete_category_"))
async def admin_delete_category_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Удаление категории"""
    logger.info(
        "delete_category_callback_called",
        admin_id=admin.get("id") if admin else None,
        callback_data=callback.data,
        user_id=callback.from_user.id,
    )

    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    category_id = int(callback.data.replace("admin_delete_category_", ""))

    with get_db() as db:
        category = (
            db.query(Category).filter(Category.id == category_id).first()
        )

        if not category:
            await callback.answer("❌ Категория не найдена!")
            return

        # Проверяем, есть ли товары в категории
        products_count = (
            db.query(Product)
            .filter(Product.category_id == category_id, Product.is_active)
            .count()
        )

        if products_count > 0:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"❌ **Нельзя удалить категорию!**\n\n"
                f"В категории '{category.name}' есть {products_count} активных товаров.\n"
                f"Сначала удалите или переместите все товары из этой категории.",
                reply_markup=get_categories_management_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer()
            return

        category_name = category.name

        # Мягкое удаление - помечаем как неактивную
        category.is_active = False
        db.commit()

        logger.info(
            "category_deleted",
            admin_id=admin.get("id"),
            category_id=category.id,
            category_name=category_name,
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.answer(
            f"✅ **Категория '{category_name}' успешно удалена!**\n\n"
            f"Категория помечена как неактивная.",
            reply_markup=get_categories_management_keyboard(),
            parse_mode="Markdown",
        )

    await callback.answer()


@router.callback_query(F.data.startswith("admin_activate_category_"))
async def admin_activate_category_specific_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Активация конкретной категории"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    category_id = int(callback.data.replace("admin_activate_category_", ""))

    with get_db() as db:
        category = (
            db.query(Category).filter(Category.id == category_id).first()
        )

        if not category:
            await callback.answer("❌ Категория не найдена!")
            return

        if category.is_active:
            await callback.answer("❌ Категория уже активна!")
            return

        category_name = category.name

        # Активируем категорию
        category.is_active = True
        db.commit()

        logger.info(
            "category_activated",
            admin_id=admin.get("id"),
            category_id=category.id,
            category_name=category_name,
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.answer(
            f"✅ **Категория '{category_name}' успешно активирована!**\n\n"
            f"Категория теперь доступна для использования.",
            reply_markup=get_categories_management_keyboard(),
            parse_mode="Markdown",
        )

    await callback.answer()


@router.callback_query(F.data == "admin_inactive_products")
async def admin_inactive_products_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Список неактивных товаров"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    with get_db() as db:
        inactive_products = db.query(Product).filter(~Product.is_active).all()

        if not inactive_products:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                "🗂️ **Неактивные товары**\n\n" "❌ Нет неактивных товаров.",
                reply_markup=get_products_management_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer()
            return

        products_text = "🗂️ **Неактивные товары**\n\n"
        products_text += (
            f"Найдено неактивных товаров: {len(inactive_products)}\n\n"
        )
        products_text += "Выберите товар для восстановления:\n\n"

        keyboard = []
        for product in inactive_products:
            products_text += f"📦 **{product.name}**\n"
            products_text += f"💰 {product.price}₽ за {product.unit}\n"
            products_text += f"📋 {product.category.name}\n\n"

            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"🔄 Восстановить {product.name[:20]}...",
                        callback_data=f"admin_restore_product_{product.id}",
                    )
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🔙 К управлению товарами",
                    callback_data="admin_products",
                )
            ]
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            products_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown",
        )
        await callback.answer()


@router.callback_query(F.data.startswith("admin_restore_product_"))
async def admin_restore_product_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Восстановить неактивный товар"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    product_id = int(callback.data.replace("admin_restore_product_", ""))

    with get_db() as db:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            await callback.answer("❌ Товар не найден!")
            return

        if product.is_active:
            await callback.answer("❌ Товар уже активен!")
            return

        # Восстанавливаем товар
        product.is_active = True
        product.is_available = True
        db.commit()

        logger.info(
            "product_restored",
            admin_id=admin.get("id"),
            product_id=product.id,
            product_name=product.name,
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.answer(
            f"✅ **Товар восстановлен!**\n\n"
            f"📦 **{product.name}**\n"
            f"💰 {product.price}₽ за {product.unit}\n"
            f"📋 {product.category.name}\n\n"
            f"Товар снова доступен в каталоге.",
            reply_markup=get_product_actions_keyboard(
                product.id, product.is_active, "general"
            ),
            parse_mode="Markdown",
        )
        await callback.answer("✅ Товар успешно восстановлен!")


@router.callback_query(F.data == "admin_activate_product")
async def admin_activate_product_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Меню активации товаров - показывает только неактивные товары с пагинацией"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    with get_db() as db:
        products = (
            db.query(Product).filter(~Product.is_active).all()
        )  # Только неактивные

        if not products:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                "🔄 **Активация товаров**\n\nНет неактивных товаров для активации.",
                reply_markup=get_products_management_keyboard(),
                parse_mode="Markdown",
            )
        else:
            # Используем пагинацию с 10 товарами на странице
            total_pages = ((len(products) - 1) // 10) + 1
            current_page = 1

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"🔄 **Активация товаров**\n\nНайдено неактивных товаров: {len(products)}\nСтраница {current_page} из {total_pages}",
                reply_markup=get_product_list_keyboard_with_pagination(
                    products, page=0, per_page=10, action="activate"
                ),
                parse_mode="Markdown",
            )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_product_page_"))
async def admin_product_page_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Обработчик пагинации для товаров"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    # Парсим callback_data: admin_product_page_{action}_{page}
    parts = callback.data.split("_")
    action = parts[3]  # edit, delete, activate
    page = int(parts[4])

    with get_db() as db:
        if action == "edit":
            products = db.query(Product).all()  # Все товары
            title = "📝 **Редактирование товаров**"
        elif action == "delete":
            products = (
                db.query(Product).filter(Product.is_active).all()
            )  # Только активные
            title = "🗑️ **Удаление товаров**"
        elif action == "activate":
            products = (
                db.query(Product).filter(~Product.is_active).all()
            )  # Только неактивные
            title = "🔄 **Активация товаров**"
        else:
            await callback.answer("❌ Неизвестное действие!")
            return

        if not products:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"{title}\n\nТовары не найдены.",
                reply_markup=get_products_management_keyboard(),
                parse_mode="Markdown",
            )
        else:
            total_pages = ((len(products) - 1) // 10) + 1
            current_page = page + 1

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                f"{title}\n\nНайдено товаров: {len(products)}\nСтраница {current_page} из {total_pages}",
                reply_markup=get_product_list_keyboard_with_pagination(
                    products, page=page, per_page=10, action=action
                ),
                parse_mode="Markdown",
            )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_activate_product_"))
async def admin_activate_product_specific_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Активация конкретного товара"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    product_id = int(callback.data.replace("admin_activate_product_", ""))

    with get_db() as db:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            await callback.answer("❌ Товар не найден!")
            return

        if product.is_active:
            await callback.answer("❌ Товар уже активен!")
            return

        product_name = product.name

        # Активируем товар
        product.is_active = True
        product.is_available = True
        db.commit()

        logger.info(
            "product_activated",
            admin_id=admin.get("id"),
            product_id=product.id,
            product_name=product_name,
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.answer(
            f"✅ **Товар '{product_name}' успешно активирован!**\n\n"
            f"Товар теперь доступен в каталоге.",
            reply_markup=get_products_management_keyboard(),
            parse_mode="Markdown",
        )

    await callback.answer()


@router.callback_query(F.data == "admin_manage_photos")
async def admin_manage_photos_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Меню управления фотографиями товаров"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.message or isinstance(
            callback.message, InaccessibleMessage):
        await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
        return

    assert isinstance(callback.message, Message)

    await callback.message.answer(
        "📸 **Управление фотографиями товаров**\n\n" "Выберите действие:",
        reply_markup=get_photo_management_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_photo")
async def admin_add_photo_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Начать процесс добавления фотографии к товару"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    with get_db() as db:
        products = db.query(Product).filter(Product.is_active).all()

        if not products:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                "📸 **Добавление фотографии к товару**\n\n"
                "❌ Нет активных товаров для добавления фотографий.",
                reply_markup=get_photo_management_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer()
            return

        # Используем новую клавиатуру с пагинацией
        total_pages = ((len(products) - 1) // 10) + 1
        current_page = 1

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            f"📸 **Добавление фотографии к товару**\n\n"
            f"Найдено товаров: {len(products)}\n"
            f"Страница {current_page} из {total_pages}\n\n"
            f"Выберите товар для добавления фотографии:",
            reply_markup=get_products_for_photo_keyboard(
                products, page=0, per_page=10, action="add_photo"
            ),
            parse_mode="Markdown",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_photo_page_"))
async def admin_photo_page_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Обработчик пагинации для списка товаров в управлении фотографиями"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    # Парсим callback_data: admin_photo_page_{action}_{page}
    # Например: "admin_photo_page_add_photo_1"
    callback_data = callback.data
    prefix = "admin_photo_page_"

    if not callback_data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    if not callback_data.startswith(prefix):
        await callback.answer("❌ Неизвестный формат!")
        return

    # Убираем префикс и разбиваем оставшуюся часть
    remaining = callback_data[len(prefix):]  # "add_photo_1"
    parts = remaining.split("_")

    # Последняя часть - это номер страницы
    page = int(parts[-1])

    # Все остальные части - это действие
    action = "_".join(parts[:-1])  # "add_photo"

    with get_db() as db:
        if action == "add_photo":
            products = db.query(Product).filter(Product.is_active).all()
            title = "📸 **Добавление фотографии к товару**"
        elif action == "delete_photo":
            products = (
                db.query(Product)
                .filter(Product.is_active, Product.image_url.isnot(None))
                .all()
            )
            title = "🗑️ **Удаление фотографии товара**"
        elif action == "view_photos":
            products = (
                db.query(Product).filter(Product.image_url.isnot(None)).all()
            )
            title = "📋 **Просмотр товаров с фотографиями**"
        else:
            await callback.answer("❌ Неизвестное действие!")
            return

        if not products:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                f"{title}\n\n❌ Нет товаров для данного действия.",
                reply_markup=get_photo_management_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer()
            return

        # Используем новую клавиатуру с пагинацией
        total_pages = ((len(products) - 1) // 10) + 1
        current_page = page + 1

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            f"{title}\n\n"
            f"Найдено товаров: {len(products)}\n"
            f"Страница {current_page} из {total_pages}\n\n"
            f"Выберите товар:",
            reply_markup=get_products_for_photo_keyboard(
                products, page=page, per_page=10, action=action
            ),
            parse_mode="Markdown",
        )
        await callback.answer()


@router.callback_query(F.data == "admin_view_products_with_photos")
async def admin_view_products_with_photos_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Просмотр товаров с фотографиями"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    with get_db() as db:
        products = (
            db.query(Product).filter(Product.image_url.isnot(None)).all()
        )

        if not products:

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                "📋 **Просмотр товаров с фотографиями**\n\n"
                "❌ Нет товаров с фотографиями.",
                reply_markup=get_photo_management_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer()
            return

        # Используем новую клавиатуру с пагинацией
        total_pages = ((len(products) - 1) // 10) + 1
        current_page = 1

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            f"📋 **Просмотр товаров с фотографиями**\n\n"
            f"Найдено товаров с фото: {len(products)}\n"
            f"Страница {current_page} из {total_pages}\n\n"
            f"Выберите товар для просмотра:",
            reply_markup=get_products_for_photo_keyboard(
                products, page=0, per_page=10, action="view_photos"
            ),
            parse_mode="Markdown",
        )
        await callback.answer()


@router.callback_query(F.data.startswith("admin_add_photo_to_"))
async def admin_add_photo_to_product_callback(
    callback: CallbackQuery, state: FSMContext, admin=None, **kwargs
):
    """Начать загрузку фотографии для конкретного товара"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    product_id = int(callback.data.replace("admin_add_photo_to_", ""))

    with get_db() as db:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            await callback.answer("❌ Товар не найден!")
            return

        # Сохраняем ID товара в FSM
        await state.set_state(PhotoManagementStates.waiting_for_photo_upload)

        # Сохраняем данные товара в FSM
        await state.update_data(
            product_id=product_id,
            product_name=product.name,
            current_photo=product.image_url,
        )

        photo_text = f"📸 **Добавление фотографии к товару**\n\n"
        photo_text += f"📦 **{product.name}**\n"
        photo_text += f"💰 {product.price}₽ за {product.unit}\n"
        photo_text += f"📋 {product.category.name}\n\n"

        if product.image_url:
            photo_text += f"📸 **Текущее фото:** {product.image_url}\n\n"
        else:
            photo_text += "📷 **Текущее фото:** Нет\n\n"

        photo_text += "📤 **Отправьте фотографию товара**\n"
        photo_text += "Поддерживаемые форматы: JPG, PNG, GIF\n"
        photo_text += "Максимальный размер: 20 МБ\n\n"
        photo_text += "💡 **Совет:** Отправьте качественное фото товара для лучшего представления в каталоге"

        keyboard = [
            [
                InlineKeyboardButton(
                    text="❌ Отмена", callback_data="admin_manage_photos"
                )
            ]
        ]

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            photo_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown",
        )
        await callback.answer()


@router.message(PhotoManagementStates.waiting_for_photo_upload, F.photo)
async def process_photo_upload(
    message: Message, state: FSMContext, admin=None, **kwargs
):
    """Обработка загруженной фотографии"""
    if not admin:
        await message.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await message.answer("❌ Недостаточно прав!")
        return

    # Получаем данные из FSM
    data = await state.get_data()
    product_id = data.get("product_id")

    if not product_id:
        await message.answer(
            "❌ Ошибка: данные товара не найдены!",
            reply_markup=get_back_to_products_keyboard(),
        )
        return

    try:
        # Получаем информацию о фотографии
        if not message.photo:
            await message.answer(
                "❌ Ошибка: фотография не найдена!",
                reply_markup=get_back_to_products_keyboard(),
            )
            return
        photo = message.photo[-1]  # Берем фото наибольшего размера
        file_id = photo.file_id

        # Получаем информацию о файле
        bot = message.bot
        if not bot:
            await message.answer(
                "❌ Ошибка: бот недоступен!",
                reply_markup=get_back_to_products_keyboard(),
            )
            return
        await bot.get_file(file_id)

        # Сохраняем file_id как URL (Telegram хранит файлы 24 часа)
        # В реальном проекте лучше сохранять файл на сервер
        photo_url = file_id

        with get_db() as db:
            product = (
                db.query(Product).filter(Product.id == product_id).first()
            )

            if not product:
                await message.answer(
                    "❌ Товар не найден!",
                    reply_markup=get_back_to_products_keyboard(),
                )
                return

            # Обновляем фотографию товара
            product.image_url = photo_url
            db.commit()

            logger.info(
                "product_photo_uploaded",
                admin_id=admin.get("id"),
                product_id=product.id,
                product_name=product.name,
                photo_file_id=file_id,
            )

            await message.answer(
                f"✅ **Фотография успешно добавлена!**\n\n"
                f"📦 **{product.name}**\n"
                f"📸 Фотография сохранена\n\n"
                f"Товар теперь отображается с фотографией в каталоге.",
                reply_markup=get_photo_management_keyboard(),
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(
            "photo_upload_error",
            admin_id=admin.get("id"),
            product_id=product_id,
            error=str(e),
        )
        await message.answer(
            "❌ **Ошибка при загрузке фотографии!**\n\n"
            "Попробуйте еще раз или обратитесь к администратору.",
            reply_markup=get_photo_management_keyboard(),
            parse_mode="Markdown",
        )

    # Сбрасываем состояние FSM
    await state.clear()


@router.message(PhotoManagementStates.waiting_for_photo_upload)
async def process_invalid_photo_upload(
    message: Message, state: FSMContext, admin=None, **kwargs
):
    """Обработка некорректного сообщения при загрузке фотографии"""
    await message.answer(
        "❌ **Некорректный формат!**\n\n"
        "Пожалуйста, отправьте фотографию (JPG, PNG, GIF).\n"
        "Максимальный размер: 20 МБ",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Отмена", callback_data="admin_manage_photos"
                    )
                ]
            ]
        ),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("admin_toggle_category_"))
async def admin_toggle_category_callback(
    callback: CallbackQuery, admin=None, **kwargs
):
    """Переключение статуса категории (активна/неактивна)"""
    if not admin:
        await callback.answer("❌ У вас нет прав администратора!")
        return

    # Проверяем права доступа
    if not check_admin_permission(admin, "manage_catalog"):
        await callback.answer("❌ Недостаточно прав!")
        return

    if not callback.data:
        await callback.answer("❌ Ошибка: нет данных", show_alert=True)
        return
    category_id = int(callback.data.replace("admin_toggle_category_", ""))

    with get_db() as db:
        category = (
            db.query(Category).filter(Category.id == category_id).first()
        )

        if not category:
            await callback.answer("❌ Категория не найдена!")
            return

        # Переключаем статус
        category.is_active = not category.is_active

        # Если категория становится неактивной, делаем неактивными все товары в
        # ней
        if not category.is_active:
            products = (
                db.query(Product)
                .filter(Product.category_id == category_id)
                .all()
            )
            for product in products:
                product.is_active = False
                product.is_available = False

        db.commit()

        status_text = "активна" if category.is_active else "неактивна"

        logger.info(
            "category_status_toggled",
            admin_id=admin.get("id"),
            category_id=category.id,
            category_name=category.name,
            new_status=status_text,
        )

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            f"✅ **Статус категории изменен!**\n\n"
            f"📋 {category.name}\n"
            f"🟢 Статус: {status_text}",
            reply_markup=get_category_actions_keyboard(category.id),
            parse_mode="Markdown",
        )

    await callback.answer()


# ==================== УПРАВЛЕНИЕ ЗАКАЗАМИ ====================


@router.message(Command("admin_orders"))
async def admin_orders(message: Message):
    """Показать заказы для администратора"""
    if not message.from_user:
        await message.answer("❌ Ошибка: пользователь не найден")
        return
    admin = await get_admin_info(message.from_user.id)
    if not admin:
        await message.answer("❌ У вас нет прав администратора")
        return

    if not check_admin_permission(admin, "manage_orders"):
        await message.answer("❌ У вас нет прав для управления заказами")
        return

    logger.info("admin_orders_requested", admin_id=admin.get("id"))

    # Получаем статистику заказов
    statistics = order_service.get_order_statistics()

    # Формируем сообщение со статистикой
    stats_text = "📊 **Статистика заказов:**\n\n"
    stats_text += f"📋 **Всего заказов:** {statistics.get('total_orders', 0)}\n"
    stats_text += f"💰 **Общая сумма:** {
        statistics.get(
            'total_amount', 0):.2f}₽\n"
    stats_text += f"💳 **Средний чек:** {
        statistics.get(
            'average_order_value',
            0):.2f}₽\n\n"

    # Статистика по статусам
    status_breakdown = statistics.get("status_breakdown", {})
    status_emojis = {
        "pending": "⏳",
        "confirmed": "✅",
        "processing": "🔄",
        "shipped": "🚚",
        "delivered": "📦",
        "cancelled": "❌",
    }

    stats_text += "📊 **По статусам:**\n"
    for status, count in status_breakdown.items():
        emoji = status_emojis.get(status, "❓")
        stats_text += f"{emoji} {status}: {count}\n"

    stats_text += "\nВыберите фильтр для просмотра заказов:"

    await message.answer(
        stats_text,
        reply_markup=get_admin_orders_filter_keyboard(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("admin_orders_filter_"))
async def admin_orders_filter(callback: CallbackQuery):
    """Фильтрация заказов в админ-панели"""
    admin = await get_admin_info(callback.from_user.id)
    if not admin or not check_admin_permission(admin, "manage_orders"):
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    try:
        if not callback.data:
            await callback.answer("❌ Ошибка: нет данных", show_alert=True)
            return

        # Парсим callback_data: admin_orders_filter_{filter_type}_{page}
        parts = callback.data.split("_")
        filter_type = parts[3]  # pending, confirmed, all, etc.
        page = int(parts[4]) if len(parts) > 4 else 0  # номер страницы

        per_page = 10  # заказов на странице
        offset = page * per_page

        if filter_type == "all":
            # Получаем все заказы с пагинацией
            with get_db() as db:
                from sqlalchemy.orm import joinedload

                # Получаем общее количество заказов
                total_count = db.query(Order).count()

                # Получаем заказы для текущей страницы
                orders_orm = (
                    db.query(Order) .options(
                        joinedload(
                            Order.order_items), joinedload(
                            Order.user)) .order_by(
                        Order.id.desc()) .limit(per_page) .offset(offset) .all())

                # Преобразуем в словари
                orders = []
                for order in orders_orm:
                    orders.append({
                        "id": order.id,
                        "order_number": order.order_number,
                        "status": order.status,
                        "payment_status": order.payment_status,
                        "payment_method": order.payment_method,
                        "total_amount": order.total_amount,
                        "user": {
                            "first_name": order.user.first_name,
                            "last_name": order.user.last_name,
                        },
                        "items": [
                            {
                                "product_name": item.product_name,
                                "quantity": item.quantity,
                                "total_price": item.total_price,
                            }
                            for item in order.order_items
                        ],
                    })
            filter_name = "Все заказы"
        else:
            # Получаем заказы по статусу с пагинацией
            from ..database import OrderStatus
            status = OrderStatus(filter_type)

            # Получаем общее количество заказов по статусу
            with get_db() as db:
                total_count = db.query(Order).filter(
                    Order.status == status).count()

            # Получаем заказы для текущей страницы
            orders = order_service.get_orders_by_status(
                status, limit=per_page, offset=offset)
            filter_name = {
                "pending": "Ожидают подтверждения",
                "confirmed": "Подтверждены",
                "processing": "В обработке",
                "shipped": "Отправлены",
                "delivered": "Доставлены",
                "cancelled": "Отменены",
            }.get(filter_type, filter_type)

        if not orders:
            if callback.message and not isinstance(
                    callback.message, InaccessibleMessage):
                assert isinstance(callback.message, Message)

                try:
                    await callback.message.edit_text(
                        f"📋 **{filter_name}**\n\n"
                        "Заказы не найдены.",
                        reply_markup=get_admin_orders_filter_keyboard(),
                        parse_mode="Markdown",
                    )
                except Exception as edit_error:
                    # Игнорируем ошибку, если сообщение не изменилось
                    if "message is not modified" not in str(edit_error):
                        raise
            await callback.answer("✅ Список обновлен!")
            return

        # Вычисляем информацию о пагинации
        total_pages = (total_count + per_page -
                       1) // per_page  # округление вверх
        current_page = page + 1  # для отображения (начинаем с 1, а не с 0)

        # Формируем список заказов
        orders_text = f"📋 **{filter_name}**\n\n"

        if total_count > per_page:
            orders_text += f"📄 Страница {current_page} из {total_pages} (всего заказов: {total_count})\n\n"

        for order in orders:  # Показываем все заказы с текущей страницы
            status_value = order["status"].value if hasattr(
                order["status"], "value") else order["status"]
            status_emoji = {
                "pending": "⏳",
                "confirmed": "✅",
                "processing": "🔄",
                "shipped": "🚚",
                "delivered": "📦",
                "cancelled": "❌",
            }.get(status_value, "❓")

            user_last_name = order["user"].get("last_name", "") or ""

            orders_text += (
                f"{status_emoji} **{order['order_number']}**\n"
                f"   👤 {order['user']['first_name']} {user_last_name}\n"
                f"   💳 {order['total_amount']:.2f}₽\n"
                f"   📅 Заказ #{order['id']}\n\n"
            )

        orders_text += "Нажмите на заказ для управления:"

        # Создаем клавиатуру с заказами
        keyboard_buttons = []
        for order in orders:
            status_value = order["status"].value if hasattr(
                order["status"], "value") else order["status"]
            status_emoji = {
                "pending": "⏳",
                "confirmed": "✅",
                "processing": "🔄",
                "shipped": "🚚",
                "delivered": "📦",
                "cancelled": "❌",
            }.get(status_value, "❓")

            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{status_emoji} {order['order_number']} - {order['total_amount']:.2f}₽",
                    callback_data=f"admin_order_details_{order['id']}",
                )
            ])

        # Добавляем кнопки пагинации (если нужно)
        if total_pages > 1:
            pagination_row = []

            # Кнопка "Назад"
            if page > 0:
                pagination_row.append(
                    InlineKeyboardButton(
                        text="◀️ Назад",
                        callback_data=f"admin_orders_filter_{filter_type}_{
                            page - 1}",
                    ))

            # Индикатор страницы
            pagination_row.append(
                InlineKeyboardButton(
                    text=f"📄 {current_page}/{total_pages}",
                    callback_data="noop",  # неактивная кнопка
                )
            )

            # Кнопка "Далее"
            if page < total_pages - 1:
                pagination_row.append(
                    InlineKeyboardButton(
                        text="Далее ▶️",
                        callback_data=f"admin_orders_filter_{filter_type}_{
                            page + 1}",
                    ))

            keyboard_buttons.append(pagination_row)

        # Добавляем кнопки навигации
        keyboard_buttons.extend([
            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data=f"admin_orders_filter_{filter_type}_{page}",
                ),
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin_orders",
                ),
            ],
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        if callback.message and not isinstance(
                callback.message, InaccessibleMessage):
            assert isinstance(callback.message, Message)

            try:
                await callback.message.edit_text(
                    orders_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
            except Exception as edit_error:
                # Игнорируем ошибку, если сообщение не изменилось
                if "message is not modified" not in str(edit_error):
                    raise

        await callback.answer("✅ Список обновлен!")

        logger.info(
            "admin_orders_filtered",
            admin_id=admin.get("id"),
            filter_type=filter_type,
            orders_count=len(orders),
        )

    except Exception as e:
        logger.error(
            "admin_orders_filter_error",
            admin_id=admin.get("id"),
            error=str(e),
            callback_data=callback.data,
        )
        await callback.answer("Ошибка при загрузке заказов", show_alert=True)


@router.callback_query(F.data.startswith("admin_order_details_"))
async def admin_order_details(callback: CallbackQuery):
    """Детали заказа для администратора"""
    admin = await get_admin_info(callback.from_user.id)
    if not admin or not check_admin_permission(admin, "manage_orders"):
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    try:
        if not callback.data:
            await callback.answer("❌ Ошибка: нет данных", show_alert=True)
            return
        order_id = int(callback.data.split("_")[3])

        # Получаем заказ (уже в виде словаря с данными)
        with get_db() as db:
            from sqlalchemy.orm import joinedload

            order_orm = (
                db.query(Order)
                .options(joinedload(Order.order_items), joinedload(Order.user))
                .filter(Order.id == order_id)
                .first()
            )

            if not order_orm:
                await callback.answer("Заказ не найден", show_alert=True)
                return

            # Преобразуем в словарь
            order = {
                "id": order_orm.id,
                "order_number": order_orm.order_number,
                "status": order_orm.status,
                "payment_status": order_orm.payment_status,
                "payment_method": order_orm.payment_method,
                "total_amount": order_orm.total_amount,
                "subtotal": order_orm.subtotal,
                "delivery_cost": order_orm.delivery_cost,
                "delivery_address": order_orm.delivery_address,
                "delivery_phone": order_orm.delivery_phone,
                "delivery_notes": order_orm.delivery_notes,
                "user": {
                    "first_name": order_orm.user.first_name,
                    "last_name": order_orm.user.last_name,
                },
                "items": [
                    {
                        "product_name": item.product_name,
                        "product_unit": item.product_unit,
                        "product_price": item.product_price,
                        "quantity": item.quantity,
                        "total_price": item.total_price,
                    }
                    for item in order_orm.order_items
                ],
            }

        # Формируем сообщение с деталями
        status_value = order["status"].value if hasattr(
            order["status"], "value") else order["status"]
        status_text = {
            "pending": "⏳ Ожидает подтверждения",
            "confirmed": "✅ Подтвержден",
            "processing": "🔄 В обработке",
            "shipped": "🚚 Отправлен",
            "delivered": "📦 Доставлен",
            "cancelled": "❌ Отменен",
        }.get(status_value, "❓ Неизвестный статус")

        payment_value = order["payment_method"].value if hasattr(
            order["payment_method"], "value") else order["payment_method"]
        payment_text = {
            "cash": "💵 Наличные при получении",
            "transfer": "💳 Перевод на карту",
        }.get(payment_value, "❓ Неизвестный способ")

        user_last_name = order["user"].get("last_name", "") or ""

        details_text = (
            f"📋 **Заказ {order['order_number']}**\n\n"
            f"👤 **Клиент:** {order['user']['first_name']} {user_last_name}\n"
            f"📞 **Телефон:** {order['delivery_phone']}\n"
            f"📍 **Адрес:** {order['delivery_address']}\n"
            f"📅 **Заказ:** #{order['id']}\n"
            f"📊 **Статус:** {status_text}\n"
            f"💳 **Оплата:** {payment_text}\n"
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
                callback.message, InaccessibleMessage):
            assert isinstance(callback.message, Message)

            try:
                await callback.message.edit_text(
                    details_text,
                    reply_markup=get_admin_order_management_keyboard(order["id"]),
                    parse_mode="Markdown",
                )
            except Exception as edit_error:
                # Игнорируем ошибку, если сообщение не изменилось
                if "message is not modified" not in str(edit_error):
                    raise

        # Показываем уведомление в зависимости от того, это обновление или
        # просмотр
        is_refresh = getattr(callback, "_is_refresh", False)
        if is_refresh:
            await callback.answer("✅ Информация обновлена!")
        else:
            await callback.answer()

        logger.info(
            "admin_order_details_shown",
            admin_id=admin.get("id"),
            order_id=order_id,
            order_number=order["order_number"],
        )

    except Exception as e:
        logger.error(
            "admin_order_details_error",
            admin_id=admin.get("id"),
            error=str(e),
            callback_data=callback.data,
        )
        await callback.answer("Ошибка при загрузке заказа", show_alert=True)


@router.callback_query(F.data.startswith("admin_confirm_order_"))
async def admin_confirm_order(callback: CallbackQuery):
    """Подтверждение заказа администратором"""
    admin = await get_admin_info(callback.from_user.id)
    if not admin or not check_admin_permission(admin, "manage_orders"):
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    try:
        if not callback.data:
            await callback.answer("❌ Ошибка: нет данных", show_alert=True)
            return
        order_id = int(callback.data.split("_")[3])

        from ..database import OrderStatus
        success = order_service.update_order_status(
            order_id, OrderStatus.CONFIRMED
        )

        if success:
            await callback.answer("✅ Заказ подтвержден!")
            # Обновляем сообщение
            await admin_order_details(callback)
        else:
            await callback.answer("❌ Ошибка при подтверждении", show_alert=True)

        logger.info(
            "admin_order_confirmed",
            admin_id=admin.get("id"),
            order_id=order_id,
        )

    except Exception as e:
        logger.error(
            "admin_confirm_order_error",
            admin_id=admin.get("id"),
            error=str(e),
            callback_data=callback.data,
        )
        await callback.answer("Ошибка при подтверждении", show_alert=True)


@router.callback_query(F.data.startswith("admin_processing_order_"))
async def admin_processing_order(callback: CallbackQuery):
    """Перевод заказа в обработку"""
    admin = await get_admin_info(callback.from_user.id)
    if not admin or not check_admin_permission(admin, "manage_orders"):
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    try:
        if not callback.data:
            await callback.answer("❌ Ошибка: нет данных", show_alert=True)
            return
        order_id = int(callback.data.split("_")[3])

        from ..database import OrderStatus
        success = order_service.update_order_status(
            order_id, OrderStatus.PROCESSING
        )

        if success:
            await callback.answer("✅ Заказ переведен в обработку!")
            await admin_order_details(callback)
        else:
            await callback.answer("❌ Ошибка при обновлении", show_alert=True)

        logger.info(
            "admin_order_processing",
            admin_id=admin.get("id"),
            order_id=order_id,
        )

    except Exception as e:
        logger.error(
            "admin_processing_order_error",
            admin_id=admin.get("id"),
            error=str(e),
            callback_data=callback.data,
        )
        await callback.answer("Ошибка при обновлении", show_alert=True)


@router.callback_query(F.data.startswith("admin_shipped_order_"))
async def admin_shipped_order(callback: CallbackQuery):
    """Отметка заказа как отправленного"""
    admin = await get_admin_info(callback.from_user.id)
    if not admin or not check_admin_permission(admin, "manage_orders"):
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    try:
        if not callback.data:
            await callback.answer("❌ Ошибка: нет данных", show_alert=True)
            return
        order_id = int(callback.data.split("_")[3])

        from ..database import OrderStatus
        success = order_service.update_order_status(
            order_id, OrderStatus.SHIPPED
        )

        if success:
            await callback.answer("✅ Заказ отмечен как отправленный!")
            await admin_order_details(callback)
        else:
            await callback.answer("❌ Ошибка при обновлении", show_alert=True)

        logger.info(
            "admin_order_shipped",
            admin_id=admin.get("id"),
            order_id=order_id,
        )

    except Exception as e:
        logger.error(
            "admin_shipped_order_error",
            admin_id=admin.get("id"),
            error=str(e),
            callback_data=callback.data,
        )
        await callback.answer("Ошибка при обновлении", show_alert=True)


@router.callback_query(F.data.startswith("admin_delivered_order_"))
async def admin_delivered_order(callback: CallbackQuery):
    """Отметка заказа как доставленного"""
    admin = await get_admin_info(callback.from_user.id)
    if not admin or not check_admin_permission(admin, "manage_orders"):
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    try:
        if not callback.data:
            await callback.answer("❌ Ошибка: нет данных", show_alert=True)
            return
        order_id = int(callback.data.split("_")[3])

        from ..database import OrderStatus
        success = order_service.update_order_status(
            order_id, OrderStatus.DELIVERED
        )

        if success:
            await callback.answer("✅ Заказ отмечен как доставленный!")
            await admin_order_details(callback)
        else:
            await callback.answer("❌ Ошибка при обновлении", show_alert=True)

        logger.info(
            "admin_order_delivered",
            admin_id=admin.get("id"),
            order_id=order_id,
        )

    except Exception as e:
        logger.error(
            "admin_delivered_order_error",
            admin_id=admin.get("id"),
            error=str(e),
            callback_data=callback.data,
        )
        await callback.answer("Ошибка при обновлении", show_alert=True)


@router.callback_query(F.data.startswith("admin_cancel_order_"))
async def admin_cancel_order(callback: CallbackQuery):
    """Отмена заказа администратором"""
    admin = await get_admin_info(callback.from_user.id)
    if not admin or not check_admin_permission(admin, "manage_orders"):
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    try:
        if not callback.data:
            await callback.answer("❌ Ошибка: нет данных", show_alert=True)
            return
        order_id = int(callback.data.split("_")[3])

        from ..database import OrderStatus
        success = order_service.update_order_status(
            order_id, OrderStatus.CANCELLED
        )

        if success:
            await callback.answer("✅ Заказ отменен!")
            await admin_order_details(callback)
        else:
            await callback.answer("❌ Ошибка при отмене", show_alert=True)

        logger.info(
            "admin_order_cancelled",
            admin_id=admin.get("id"),
            order_id=order_id,
        )

    except Exception as e:
        logger.error(
            "admin_cancel_order_error",
            admin_id=admin.get("id"),
            error=str(e),
            callback_data=callback.data,
        )
        await callback.answer("Ошибка при отмене", show_alert=True)


@router.callback_query(F.data.startswith("admin_refresh_order_"))
async def admin_refresh_order(callback: CallbackQuery):
    """Обновление информации о заказе"""
    # Добавляем флаг, что это обновление
    if callback.data:
        original_data = callback.data
        # Заменяем admin_refresh_order_ на admin_order_details_
        callback.data = original_data.replace(
            "admin_refresh_order_", "admin_order_details_")
        # Сохраняем флаг, что это refresh
        callback._is_refresh = True  # type: ignore

    await admin_order_details(callback)
    # callback.answer() уже вызван внутри admin_order_details


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    """Обработчик для неактивных кнопок (индикаторов)"""
    await callback.answer()


# Настройки платежа
class PaymentSettingsStates(StatesGroup):
    """Состояния для редактирования настроек платежа"""

    waiting_for_bank = State()
    waiting_for_card = State()
    waiting_for_recipient = State()
    waiting_for_info = State()


@router.callback_query(F.data == "admin_payment_settings")
async def admin_payment_settings(callback: CallbackQuery):
    """Показать настройки платежа"""
    admin = await get_admin_info(callback.from_user.id)
    if not admin or not check_admin_permission(admin, "manage_settings"):
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    try:
        from ..services.payment_settings_service import PaymentSettingsService

        service = PaymentSettingsService()
        settings = service.get_active_settings()

        if not settings:
            settings_text = (
                "💳 **Настройки оплаты**\n\n"
                "⚠️ Настройки не найдены.\n\n"
                "Создайте настройки по умолчанию."
            )
        else:
            settings_text = (
                "💳 **Текущие настройки оплаты:**\n\n"
                f"🏦 **Банк:** {settings['bank_name']}\n"
                f"💳 **Номер карты:** {settings['card_number']}\n"
                f"👤 **Получатель:** {settings['recipient_name']}\n\n"
                f"📝 **Дополнительная информация:**\n"
                f"{settings['additional_info']}\n\n"
                "Выберите, что хотите изменить:"
            )

        from ..keyboards.admin import get_payment_settings_keyboard

        if callback.message and not isinstance(
            callback.message, InaccessibleMessage
        ):

            if not callback.message or isinstance(
                    callback.message, InaccessibleMessage):
                await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                settings_text,
                reply_markup=get_payment_settings_keyboard(),
                parse_mode="Markdown",
            )

        await callback.answer()

        logger.info("payment_settings_shown", admin_id=admin.get("id"))

    except Exception as e:
        logger.error(
            "payment_settings_error", admin_id=admin.get("id"), error=str(e)
        )
        await callback.answer("Ошибка при загрузке настроек", show_alert=True)


@router.callback_query(F.data == "cancel_payment_edit")
async def cancel_payment_edit(callback: CallbackQuery, state: FSMContext):
    """Отмена редактирования настроек платежа"""
    await state.clear()
    await admin_payment_settings(callback)


@router.callback_query(F.data == "admin_edit_bank")
async def admin_edit_bank(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование банка"""
    admin = await get_admin_info(callback.from_user.id)
    if not admin or not check_admin_permission(admin, "manage_settings"):
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    await state.set_state(PaymentSettingsStates.waiting_for_bank)

    from ..keyboards.admin import get_cancel_edit_keyboard

    if callback.message and not isinstance(
            callback.message, InaccessibleMessage):

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            "🏦 **Изменение банка**\n\n"
            "Отправьте название банка:",
            reply_markup=get_cancel_edit_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()


@router.message(PaymentSettingsStates.waiting_for_bank)
async def process_bank_update(message: Message, state: FSMContext):
    """Обработка нового названия банка"""
    if not message.text:
        from ..keyboards.admin import get_cancel_edit_keyboard
        await message.answer(
            "❌ Название банка не может быть пустым.",
            reply_markup=get_cancel_edit_keyboard(),
        )
        return
    bank_name = message.text.strip()

    if not bank_name or len(bank_name) > 255:
        from ..keyboards.admin import get_cancel_edit_keyboard
        await message.answer(
            "❌ Название банка должно быть от 1 до 255 символов.",
            reply_markup=get_cancel_edit_keyboard(),
        )
        return

    from ..services.payment_settings_service import PaymentSettingsService

    service = PaymentSettingsService()
    settings = service.get_active_settings()

    if settings and service.update_settings(
            settings["id"], bank_name=bank_name):
        from ..keyboards.admin import get_back_to_payment_settings_keyboard

        await message.answer(
            f"✅ Название банка обновлено: **{bank_name}**",
            reply_markup=get_back_to_payment_settings_keyboard(),
            parse_mode="Markdown",
        )
        await state.clear()
    else:
        from ..keyboards.admin import get_back_to_payment_settings_keyboard
        await message.answer(
            "❌ Ошибка при обновлении",
            reply_markup=get_back_to_payment_settings_keyboard(),
        )


@router.callback_query(F.data == "admin_edit_card")
async def admin_edit_card(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование номера карты"""
    admin = await get_admin_info(callback.from_user.id)
    if not admin or not check_admin_permission(admin, "manage_settings"):
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    await state.set_state(PaymentSettingsStates.waiting_for_card)

    from ..keyboards.admin import get_cancel_edit_keyboard

    if callback.message and not isinstance(
            callback.message, InaccessibleMessage):

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            "💳 **Изменение номера карты**\n\n"
            "Отправьте номер карты (формат: 1234 5678 9012 3456):",
            reply_markup=get_cancel_edit_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()


@router.message(PaymentSettingsStates.waiting_for_card)
async def process_card_update(message: Message, state: FSMContext):
    """Обработка нового номера карты"""
    if not message.text:
        from ..keyboards.admin import get_cancel_edit_keyboard
        await message.answer(
            "❌ Номер карты не может быть пустым.",
            reply_markup=get_cancel_edit_keyboard(),
        )
        return
    card_number = message.text.strip()

    if not card_number or len(card_number) > 19:
        from ..keyboards.admin import get_cancel_edit_keyboard
        await message.answer(
            "❌ Номер карты должен быть от 1 до 19 символов.",
            reply_markup=get_cancel_edit_keyboard(),
        )
        return

    from ..services.payment_settings_service import PaymentSettingsService

    service = PaymentSettingsService()
    settings = service.get_active_settings()

    if settings and service.update_settings(
        settings["id"], card_number=card_number
    ):
        from ..keyboards.admin import get_back_to_payment_settings_keyboard

        await message.answer(
            f"✅ Номер карты обновлен: **{card_number}**",
            reply_markup=get_back_to_payment_settings_keyboard(),
            parse_mode="Markdown",
        )
        await state.clear()
    else:
        from ..keyboards.admin import get_back_to_payment_settings_keyboard
        await message.answer(
            "❌ Ошибка при обновлении",
            reply_markup=get_back_to_payment_settings_keyboard(),
        )


@router.callback_query(F.data == "admin_edit_recipient")
async def admin_edit_recipient(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование получателя"""
    admin = await get_admin_info(callback.from_user.id)
    if not admin or not check_admin_permission(admin, "manage_settings"):
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    await state.set_state(PaymentSettingsStates.waiting_for_recipient)

    from ..keyboards.admin import get_cancel_edit_keyboard

    if callback.message and not isinstance(
            callback.message, InaccessibleMessage):

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            "👤 **Изменение получателя**\n\n"
            "Отправьте имя получателя:",
            reply_markup=get_cancel_edit_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()


@router.message(PaymentSettingsStates.waiting_for_recipient)
async def process_recipient_update(message: Message, state: FSMContext):
    """Обработка нового получателя"""
    if not message.text:
        from ..keyboards.admin import get_cancel_edit_keyboard
        await message.answer(
            "❌ Имя получателя не может быть пустым.",
            reply_markup=get_cancel_edit_keyboard(),
        )
        return
    recipient_name = message.text.strip()

    if not recipient_name or len(recipient_name) > 255:
        from ..keyboards.admin import get_cancel_edit_keyboard
        await message.answer(
            "❌ Имя получателя должно быть от 1 до 255 символов.",
            reply_markup=get_cancel_edit_keyboard(),
        )
        return

    from ..services.payment_settings_service import PaymentSettingsService

    service = PaymentSettingsService()
    settings = service.get_active_settings()

    if settings and service.update_settings(
        settings["id"], recipient_name=recipient_name
    ):
        from ..keyboards.admin import get_back_to_payment_settings_keyboard

        await message.answer(
            f"✅ Имя получателя обновлено: **{recipient_name}**",
            reply_markup=get_back_to_payment_settings_keyboard(),
            parse_mode="Markdown",
        )
        await state.clear()
    else:
        from ..keyboards.admin import get_back_to_payment_settings_keyboard
        await message.answer(
            "❌ Ошибка при обновлении",
            reply_markup=get_back_to_payment_settings_keyboard(),
        )


@router.callback_query(F.data == "admin_edit_info")
async def admin_edit_info(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование дополнительной информации"""
    admin = await get_admin_info(callback.from_user.id)
    if not admin or not check_admin_permission(admin, "manage_settings"):
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    await state.set_state(PaymentSettingsStates.waiting_for_info)

    from ..keyboards.admin import get_cancel_edit_keyboard

    if callback.message and not isinstance(
            callback.message, InaccessibleMessage):

        if not callback.message or isinstance(
                callback.message, InaccessibleMessage):
            await callback.answer("❌ Ошибка обработки запроса", show_alert=True)
            return

        assert isinstance(callback.message, Message)

        await callback.message.edit_text(
            "📝 **Изменение дополнительной информации**\n\n"
            "Отправьте текст дополнительной информации:",
            reply_markup=get_cancel_edit_keyboard(),
            parse_mode="Markdown",
        )
    await callback.answer()


@router.message(PaymentSettingsStates.waiting_for_info)
async def process_info_update(message: Message, state: FSMContext):
    """Обработка новой дополнительной информации"""
    if not message.text:
        from ..keyboards.admin import get_cancel_edit_keyboard
        await message.answer(
            "❌ Текст не может быть пустым.",
            reply_markup=get_cancel_edit_keyboard(),
        )
        return
    additional_info = message.text.strip()

    if not additional_info:
        from ..keyboards.admin import get_cancel_edit_keyboard
        await message.answer(
            "❌ Текст не может быть пустым.",
            reply_markup=get_cancel_edit_keyboard(),
        )
        return

    from ..services.payment_settings_service import PaymentSettingsService

    service = PaymentSettingsService()
    settings = service.get_active_settings()

    if settings and service.update_settings(
        settings["id"], additional_info=additional_info
    ):
        from ..keyboards.admin import get_back_to_payment_settings_keyboard

        await message.answer(
            "✅ Дополнительная информация обновлена!",
            reply_markup=get_back_to_payment_settings_keyboard(),
            parse_mode="Markdown",
        )
        await state.clear()
    else:
        from ..keyboards.admin import get_back_to_payment_settings_keyboard
        await message.answer(
            "❌ Ошибка при обновлении",
            reply_markup=get_back_to_payment_settings_keyboard(),
        )
