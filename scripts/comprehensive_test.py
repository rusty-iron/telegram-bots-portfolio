#!/usr/bin/env python3
"""
Комплексный тест функциональности MeatBot
"""

import asyncio

import structlog
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from meatbot.app.config import settings
from meatbot.app.database import AdminUser, Category, Product, get_db
from meatbot.app.handlers import (
    admin_router,
    cart_router,
    catalog_router,
    commands_router,
    start_router,
)
from meatbot.app.middlewares.admin import AdminMiddleware

logger = structlog.get_logger()


async def test_database_connection():
    """Тест подключения к базе данных"""
    print("🧪 Тестирование подключения к базе данных...")

    try:
        with get_db() as db:
            # Проверяем категории
            categories = db.query(Category).filter(Category.is_active).all()
            print(f"✅ Категории: {len(categories)}")
            for cat in categories:
                print(f"   - {cat.name}")

            # Проверяем товары
            products = db.query(Product).filter(Product.is_active).all()
            print(f"✅ Товары: {len(products)}")
            for prod in products[:3]:
                print(f"   - {prod.name} ({prod.price}₽)")

            # Проверяем администраторов
            admins = db.query(AdminUser).filter(AdminUser.is_active).all()
            print(f"✅ Администраторы: {len(admins)}")
            for admin in admins:
                print(f"   - {admin.full_name} ({admin.role})")

    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")


async def test_handlers_registration():
    """Тест регистрации обработчиков"""
    print("\n🧪 Тестирование регистрации обработчиков...")

    try:
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

        # Проверяем обработчики каталога
        catalog_handlers = [
            h for h in dp.callback_query.handlers if hasattr(h, "callback")
        ]
        catalog_handler_names = [h.callback.__name__ for h in catalog_handlers]

        expected_handlers = [
            "catalog_callback",
            "show_category_products",
            "show_product_details",
            "back_to_catalog",
        ]

        print("✅ Обработчики каталога:")
        for handler_name in expected_handlers:
            if handler_name in catalog_handler_names:
                print(f"   ✅ {handler_name}")
            else:
                print(f"   ❌ {handler_name} - НЕ НАЙДЕН")

        # Проверяем обработчики команд
        command_handlers = [
            h for h in dp.message.handlers if hasattr(h, "callback")
        ]
        command_handler_names = [h.callback.__name__ for h in command_handlers]

        expected_commands = ["start_command", "help_command", "about_command"]

        print("✅ Обработчики команд:")
        for handler_name in expected_commands:
            if handler_name in command_handler_names:
                print(f"   ✅ {handler_name}")
            else:
                print(f"   ❌ {handler_name} - НЕ НАЙДЕН")

        await bot.session.close()

    except Exception as e:
        print(f"❌ Ошибка тестирования обработчиков: {e}")


async def test_admin_permissions():
    """Тест системы прав администратора"""
    print("\n🧪 Тестирование системы прав администратора...")

    try:
        with get_db() as db:
            admin = db.query(AdminUser).filter(AdminUser.is_active).first()
            if not admin:
                print("❌ Администратор не найден")
                return

            print(f"✅ Администратор найден: {admin.full_name} ({admin.role})")

            # Тестируем права
            permissions_to_test = [
                "manage_catalog",
                "manage_orders",
                "manage_users",
                "manage_admins",
                "view_statistics",
                "manage_promotions",
            ]

            print("✅ Проверка прав:")
            for permission in permissions_to_test:
                has_permission = admin.has_permission(permission)
                status = "✅" if has_permission else "❌"
                print(f"   {status} {permission}")

    except Exception as e:
        print(f"❌ Ошибка тестирования прав: {e}")


async def test_catalog_functionality():
    """Тест функциональности каталога"""
    print("\n🧪 Тестирование функциональности каталога...")

    try:
        with get_db() as db:
            # Проверяем категории
            categories = db.query(Category).filter(Category.is_active).all()
            if not categories:
                print("❌ Категории не найдены")
                return

            print(f"✅ Найдено категорий: {len(categories)}")

            # Проверяем товары в каждой категории
            for category in categories:
                products = (
                    db.query(Product)
                    .filter(
                        Product.category_id == category.id, Product.is_active
                    )
                    .all()
                )
                print(f"   📁 {category.name}: {len(products)} товаров")

                # Показываем первые 2 товара
                for product in products[:2]:
                    print(f"      🥩 {product.name} - {product.price}₽")

    except Exception as e:
        print(f"❌ Ошибка тестирования каталога: {e}")


async def test_health_endpoints():
    """Тест health endpoints"""
    print("\n🧪 Тестирование health endpoints...")

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            # Тест live endpoint
            async with session.get(
                "http://localhost:8000/health/live"
            ) as response:
                if response.status == 200:
                    print("✅ Health live endpoint работает")
                else:
                    print(f"❌ Health live endpoint: {response.status}")

            # Тест ready endpoint
            async with session.get(
                "http://localhost:8000/health/ready"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Health ready endpoint работает")
                    print(f"   Статус: {data.get('status')}")
                    checks = data.get("checks", {})
                    print(f"   БД: {'✅' if checks.get('db') else '❌'}")
                    print(f"   Redis: {'✅' if checks.get('redis') else '❌'}")
                else:
                    print(f"❌ Health ready endpoint: {response.status}")

    except Exception as e:
        print(f"❌ Ошибка тестирования health endpoints: {e}")


async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск комплексного тестирования MeatBot...")
    print("=" * 50)

    await test_database_connection()
    await test_handlers_registration()
    await test_admin_permissions()
    await test_catalog_functionality()
    await test_health_endpoints()

    print("\n" + "=" * 50)
    print("✅ Комплексное тестирование завершено!")
    print("\n📋 Следующие шаги:")
    print("1. Протестируйте бота в Telegram:")
    print("   - Отправьте /start")
    print("   - Нажмите '🛒 Каталог товаров'")
    print("   - Выберите категорию и товар")
    print("2. Протестируйте админ панель:")
    print("   - Отправьте /admin")
    print("   - Нажмите '📦 Управление товарами'")
    print("   - Проверьте все функции")


if __name__ == "__main__":
    asyncio.run(main())
