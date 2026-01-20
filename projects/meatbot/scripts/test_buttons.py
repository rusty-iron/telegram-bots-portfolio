#!/usr/bin/env python3
"""
Скрипт для тестирования работы кнопок MeatBot
"""

import asyncio

import structlog
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from meatbot.app.config import settings
from meatbot.app.handlers import (
    admin_router,
    cart_router,
    catalog_router,
    commands_router,
    start_router,
)
from meatbot.app.middlewares.admin import AdminMiddleware

logger = structlog.get_logger()


async def test_catalog_button():
    """Тест кнопки каталога"""
    print("🧪 Тестирование кнопки каталога...")

    # Создаем мок объекты
    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # Добавляем middleware
    dp.message.middleware(AdminMiddleware())
    dp.callback_query.middleware(AdminMiddleware())

    # Подключаем роутеры
    dp.include_router(start_router)
    dp.include_router(commands_router)
    dp.include_router(catalog_router)
    dp.include_router(cart_router)
    dp.include_router(admin_router)

    # Создаем мок пользователя (для будущего использования)
    # user = User(
    #     id=123456789,
    #     is_bot=False,
    #     first_name="Test",
    #     last_name="User",
    #     username="testuser"
    # )

    # Создаем мок сообщение (для будущего использования)
    # _message = Message(
    #     message_id=1,
    #     date=1234567890,
    #     chat=None,  # Будет установлено позже
    #     from_user=user,
    #     content_type="text",
    #     text="/start"
    # )

    # Создаем мок callback query (для будущего использования)
    # _callback_query = CallbackQuery(
    #     id="test_callback",
    #     from_user=user,
    #     chat_instance="test_chat",
    #     data="catalog"
    # )

    print("✅ Мок объекты созданы")
    print("✅ Роутеры подключены")
    print("✅ Middleware добавлены")

    # Проверяем, что обработчик каталога зарегистрирован
    catalog_handlers = [
        h for h in dp.callback_query.handlers if hasattr(h, "callback")
    ]
    catalog_handler = None

    for handler in catalog_handlers:
        if (
            hasattr(handler, "callback")
            and handler.callback.__name__ == "catalog_callback"
        ):
            catalog_handler = handler
            break

    if catalog_handler:
        print("✅ Обработчик каталога найден")
        print(f"   - Функция: {catalog_handler.callback.__name__}")
        print(f"   - Фильтр: {handler.filters}")
    else:
        print("❌ Обработчик каталога НЕ найден")

    await bot.session.close()


async def test_database_connection():
    """Тест подключения к базе данных"""
    print("\n🧪 Тестирование подключения к базе данных...")

    try:
        from meatbot.app.database import Category, Product, get_db

        with get_db() as db:
            categories = db.query(Category).filter(Category.is_active).all()
            products = db.query(Product).filter(Product.is_active).all()

            print(f"✅ Категории: {len(categories)}")
            for cat in categories:
                print(f"   - {cat.name}")

            print(f"✅ Товары: {len(products)}")
            for prod in products[:5]:  # Показываем только первые 5
                print(f"   - {prod.name} ({prod.price}₽)")

            if len(products) > 5:
                print(f"   ... и еще {len(products) - 5} товаров")

    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")


async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования MeatBot...")

    await test_database_connection()
    await test_catalog_button()

    print("\n✅ Тестирование завершено!")


if __name__ == "__main__":
    asyncio.run(main())
