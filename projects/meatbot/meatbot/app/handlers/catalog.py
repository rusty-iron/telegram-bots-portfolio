"""
Handler для работы с каталогом товаров
"""

import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ..database import Category, Product, get_db
from ..keyboards.catalog import get_catalog_products_keyboard

router = Router()
logger = structlog.get_logger()


@router.message(Command("catalog"))
async def show_catalog(message: Message):
    """Показать каталог категорий"""
    try:
        from_user = message.from_user
        user_id = from_user.id if from_user is not None else None
        logger.info("catalog_command_requested", user_id=user_id)

        with get_db() as db:
            categories = db.query(Category).filter(Category.is_active).all()

            if not categories:
                await message.answer(
                    "📦 Каталог пока пуст. Скоро здесь появятся товары!"
                )
                logger.info("catalog_empty", user_id=user_id)
                return

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"📁 {cat.name}",
                            callback_data=f"category_{cat.id}",
                        )
                    ]
                    for cat in categories
                ]
                + [
                    [
                        InlineKeyboardButton(
                            text="🔙 Назад в меню",
                            callback_data="back_to_menu",
                        )
                    ]
                ]
            )

            await message.answer(
                "🛒 **Каталог товаров**\n\n" "Выберите категорию:",
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            logger.info(
                "catalog_shown",
                user_id=user_id,
                categories_count=len(categories),
            )

    except Exception as e:
        logger.error("catalog_command_error", user_id=user_id, error=str(e))
        await message.answer(
            "❌ Произошла ошибка при загрузке каталога. Попробуйте позже."
        )


@router.callback_query(lambda c: c.data == "catalog")
async def catalog_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Каталог товаров'"""
    try:
        await callback.answer()
        from_user = callback.from_user
        user_id = from_user.id if from_user is not None else None
        logger.info("catalog_callback_requested", user_id=user_id)

        # Получаем категории из базы данных и сразу извлекаем нужные данные
        with get_db() as db:
            categories = db.query(Category).filter(Category.is_active).all()

            if not categories:
                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

                assert isinstance(callback.message, Message)

                await callback.message.edit_text(
                    "🛒 **Каталог товаров**\n\n"
                    "К сожалению, категории временно недоступны.",
                    parse_mode="Markdown",
                )
                logger.info("catalog_empty_callback", user_id=user_id)
                return

            # Создаем кнопки с категориями, извлекая данные внутри сессии
            keyboard_buttons = []
            for category in categories:
                keyboard_buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"📁 {category.name}",
                            callback_data=f"category_{category.id}",
                        )
                    ]
                )

            # Добавляем кнопку "Назад"
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text="🔙 Назад в меню", callback_data="back_to_menu"
                    )
                ]
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

            if not callback.message or isinstance(
                callback.message, InaccessibleMessage
            ):
                await callback.answer(
                    "❌ Ошибка обработки запроса", show_alert=True
                )
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                "🛒 **Каталог товаров**\n\n" "Выберите категорию:",
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
            logger.info(
                "catalog_callback_shown",
                user_id=user_id,
                categories_count=len(categories),
            )

    except Exception as e:
        logger.error(
            "catalog_callback_error",
            user_id=user_id,
            error=str(e),
        )
        await callback.answer(
            "Произошла ошибка при загрузке каталога", show_alert=True
        )


@router.callback_query(F.data.startswith("category_"))
async def show_category_products(callback: CallbackQuery):
    """Показать товары в категории"""
    try:
        await callback.answer()
        if not callback.data:
            await callback.answer(
                "❌ Ошибка обработки запроса", show_alert=True
            )
            return
        category_id = int(callback.data.split("_")[1])
        from_user = callback.from_user
        user_id = from_user.id if from_user is not None else None
        logger.info(
            "category_products_requested",
            user_id=user_id,
            category_id=category_id,
        )

        with get_db() as db:
            category = (
                db.query(Category).filter(Category.id == category_id).first()
            )
            if not category:
                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

                assert isinstance(callback.message, Message)

                await callback.message.edit_text("❌ Категория не найдена")
                logger.warning(
                    "category_not_found",
                    user_id=user_id,
                    category_id=category_id,
                )
                return

            products = (
                db.query(Product)
                .filter(Product.category_id == category_id, Product.is_active)
                .all()
            )

            if not products:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Назад к каталогу",
                                callback_data="catalog",
                            )
                        ]
                    ]
                )

                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

                assert isinstance(callback.message, Message)

                await callback.message.edit_text(
                    f"📁 **{category.name}**\n\n"
                    "В этой категории пока нет товаров.",
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
                logger.info(
                    "category_empty",
                    user_id=user_id,
                    category_id=category_id,
                    category_name=category.name,
                )
                return

            # Используем пагинацию с 10 товарами на странице
            total_pages = ((len(products) - 1) // 10) + 1

            if not callback.message or isinstance(
                callback.message, InaccessibleMessage
            ):
                await callback.answer(
                    "❌ Ошибка обработки запроса", show_alert=True
                )
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                f"📁 **{category.name}**\n\n"
                f"Найдено товаров: {len(products)}\n"
                f"Страница 1 из {total_pages}\n\n"
                f"Выберите товар:",
                reply_markup=get_catalog_products_keyboard(
                    products, category_id, page=0, per_page=10
                ),
                parse_mode="Markdown",
            )
            logger.info(
                "category_products_shown",
                user_id=user_id,
                category_id=category_id,
                products_count=len(products),
            )

    except Exception as e:
        logger.error(
            "category_products_error",
            user_id=user_id,
            error=str(e),
        )
        await callback.answer(
            "Произошла ошибка при загрузке товаров", show_alert=True
        )


@router.callback_query(
    lambda c: c.data.startswith("category_") and "_page_" in c.data
)
async def show_category_products_page(callback: CallbackQuery):
    """Показать товары в категории с пагинацией"""
    try:
        await callback.answer()

        # Парсим callback_data: category_{category_id}_page_{page}
        if not callback.data:
            await callback.answer(
                "❌ Ошибка обработки запроса", show_alert=True
            )
            return
        parts = callback.data.split("_")
        category_id = int(parts[1])
        page = int(parts[3])

        from_user = callback.from_user
        user_id = from_user.id if from_user is not None else None
        logger.info(
            "category_products_page_requested",
            user_id=user_id,
            category_id=category_id,
            page=page,
        )

        with get_db() as db:
            category = (
                db.query(Category).filter(Category.id == category_id).first()
            )
            if not category:
                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

                assert isinstance(callback.message, Message)

                await callback.message.edit_text("❌ Категория не найдена")
                logger.warning(
                    "category_not_found",
                    user_id=user_id,
                    category_id=category_id,
                )
                return

            products = (
                db.query(Product)
                .filter(Product.category_id == category_id, Product.is_active)
                .all()
            )

            if not products:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Назад к каталогу",
                                callback_data="catalog",
                            )
                        ]
                    ]
                )

                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

                assert isinstance(callback.message, Message)

                await callback.message.edit_text(
                    f"📁 **{category.name}**\n\n"
                    "В этой категории пока нет товаров.",
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
                return

            # Используем пагинацию с 10 товарами на странице
            total_pages = ((len(products) - 1) // 10) + 1
            current_page = page + 1

            if not callback.message or isinstance(
                callback.message, InaccessibleMessage
            ):
                await callback.answer(
                    "❌ Ошибка обработки запроса", show_alert=True
                )
                return

            assert isinstance(callback.message, Message)

            await callback.message.edit_text(
                f"📁 **{category.name}**\n\n"
                f"Найдено товаров: {len(products)}\n"
                f"Страница {current_page} из {total_pages}\n\n"
                f"Выберите товар:",
                reply_markup=get_catalog_products_keyboard(
                    products, category_id, page=page, per_page=10
                ),
                parse_mode="Markdown",
            )
            logger.info(
                "category_products_page_shown",
                user_id=user_id,
                category_id=category_id,
                page=page,
                products_count=len(products),
            )

    except Exception as e:
        logger.error(
            "category_products_page_error",
            user_id=user_id,
            error=str(e),
        )
        await callback.answer(
            "Произошла ошибка при загрузке товаров", show_alert=True
        )


@router.callback_query(F.data.startswith("product_"))
async def show_product_details(callback: CallbackQuery):
    """Показать детали товара"""
    try:
        await callback.answer()
        if not callback.data:
            await callback.answer(
                "❌ Ошибка обработки запроса", show_alert=True
            )
            return
        product_id = int(callback.data.split("_")[1])
        from_user = callback.from_user
        user_id = from_user.id if from_user is not None else None
        logger.info(
            "product_details_requested",
            user_id=user_id,
            product_id=product_id,
        )

        with get_db() as db:
            product = (
                db.query(Product).filter(Product.id == product_id).first()
            )
            if not product:
                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

                assert isinstance(callback.message, Message)

                await callback.message.edit_text("❌ Товар не найден")
                logger.warning(
                    "product_not_found",
                    user_id=user_id,
                    product_id=product_id,
                )
                return

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🛒 Добавить в корзину",
                            callback_data=f"add_to_cart_{product_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 Назад к категориям",
                            callback_data="catalog",
                        )
                    ],
                ]
            )

            # Формируем текст товара
            product_text = (
                f"🥩 **{product.name}**\n\n"
                f"💰 Цена: {product.price}₽ за {product.unit}\n"
                f"📝 Описание: {product.description}\n"
                f"📦 В наличии: {'Да' if product.is_available else 'Нет'}"
            )

            # Если есть фотография, отправляем её с текстом
            if product.image_url:
                try:
                    # Удаляем старое сообщение и отправляем новое с фото
                    if not callback.message or isinstance(
                        callback.message, InaccessibleMessage
                    ):
                        await callback.answer(
                            "❌ Ошибка обработки запроса", show_alert=True
                        )
                        return

                    assert isinstance(callback.message, Message)
                    await callback.message.delete()

                    await callback.message.answer_photo(
                        photo=product.image_url,
                        caption=product_text,
                        reply_markup=keyboard,
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    logger.error(
                        "product_photo_error",
                        user_id=user_id,
                        product_id=product_id,
                        error=str(e),
                    )
                    # Если фотография не загрузилась, отправляем только текст

                    if not callback.message or isinstance(
                        callback.message, InaccessibleMessage
                    ):
                        await callback.answer(
                            "❌ Ошибка обработки запроса", show_alert=True
                        )
                        return

                    assert isinstance(callback.message, Message)

                    await callback.message.edit_text(
                        product_text + "\n\n❌ Ошибка при загрузке фотографии",
                        reply_markup=keyboard,
                        parse_mode="Markdown",
                    )
            else:
                # Если фотографии нет, отправляем только текст

                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

                assert isinstance(callback.message, Message)

                await callback.message.edit_text(
                    product_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
            logger.info(
                "product_details_shown",
                user_id=user_id,
                product_id=product_id,
                product_name=product.name,
            )

    except Exception as e:
        logger.error(
            "product_details_error",
            user_id=user_id,
            error=str(e),
        )
        await callback.answer(
            "Произошла ошибка при загрузке товара", show_alert=True
        )


@router.callback_query(lambda c: c.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    """Вернуться к каталогу"""
    try:
        await callback.answer()
        user_id = (
            callback.from_user.id
            if getattr(callback, "from_user", None)
            else None
        )
        logger.info("back_to_catalog_requested", user_id=user_id)

        with get_db() as db:
            categories = db.query(Category).filter(Category.is_active).all()

            if not categories:
                if not callback.message or isinstance(
                    callback.message, InaccessibleMessage
                ):
                    await callback.answer(
                        "❌ Ошибка обработки запроса", show_alert=True
                    )
                    return

                assert isinstance(callback.message, Message)

                await callback.message.answer(
                    "🛒 **Каталог товаров**\n\n"
                    "К сожалению, категории временно недоступны.",
                    parse_mode="Markdown",
                )
                logger.info("back_to_catalog_empty", user_id=user_id)
                return

            keyboard_buttons = []
            for category in categories:
                keyboard_buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"📁 {category.name}",
                            callback_data=f"category_{category.id}",
                        )
                    ]
                )

            # Добавляем кнопку "Назад в меню"
            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text="🔙 Назад в меню", callback_data="back_to_menu"
                    )
                ]
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

            if not callback.message or isinstance(
                callback.message, InaccessibleMessage
            ):
                await callback.answer(
                    "❌ Ошибка обработки запроса", show_alert=True
                )
                return

            assert isinstance(callback.message, Message)

            await callback.message.answer(
                "🛒 **Каталог товаров**\n\n" "Выберите категорию:",
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            logger.info(
                "back_to_catalog_shown",
                user_id=user_id,
                categories_count=len(categories),
            )

    except Exception as e:
        logger.error(
            "back_to_catalog_error",
            user_id=user_id,
            error=str(e),
        )
        await callback.answer(
            "Произошла ошибка при возврате к каталогу", show_alert=True
        )
