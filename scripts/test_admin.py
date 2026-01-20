#!/usr/bin/env python3
"""
Скрипт для тестирования админской панели
"""
import os
import sys

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from meatbot.app.database import (
        AdminRole,
        AdminUser,
        Category,
        Product,
        get_db,
    )

    def test_admin_panel():
        """Тестирование админской панели"""
        print("🧪 Тестирование админской панели...")

        with get_db() as db:
            # Проверяем администраторов
            admins = db.query(AdminUser).all()
            print(f"\n👥 Найдено администраторов: {len(admins)}")

            for admin in admins:
                print(
                    f"   - {admin.full_name} (ID: {admin.telegram_id}, Роль: {admin.role.value})"
                )

            # Проверяем категории
            categories = db.query(Category).all()
            print(f"\n📋 Найдено категорий: {len(categories)}")

            for category in categories:
                products_count = (
                    db.query(Product)
                    .filter(Product.category_id == category.id)
                    .count()
                )
                print(
                    f"   - {category.name} (Товаров: {products_count}, Активна: {category.is_active})"
                )

            # Проверяем товары
            products = db.query(Product).all()
            print(f"\n📦 Найдено товаров: {len(products)}")

            active_products = (
                db.query(Product).filter(Product.is_active).count()
            )
            available_products = (
                db.query(Product).filter(Product.is_available).count()
            )

            print(f"   - Активных: {active_products}")
            print(f"   - Доступных: {available_products}")

            # Показываем примеры товаров
            for product in products[:3]:  # Показываем первые 3 товара
                print(
                    f"   - {product.name} ({product.price}₽, Категория: {product.category.name})"
                )

            if len(products) > 3:
                print(f"   ... и еще {len(products) - 3} товаров")

        print("\n✅ Тестирование завершено!")

    def create_test_admin():
        """Создать тестового администратора"""
        print("\n🔧 Создание тестового администратора...")

        with get_db() as db:
            # Проверяем, есть ли уже тестовый админ
            test_admin = (
                db.query(AdminUser)
                .filter(AdminUser.telegram_id == 123456789)
                .first()
            )

            if test_admin:
                print("❌ Тестовый администратор уже существует!")
                return

            # Создаем тестового администратора
            admin = AdminUser(
                telegram_id=123456789,
                username="test_admin",
                first_name="Test",
                last_name="Admin",
                role=AdminRole.SUPER_ADMIN,
                is_active=True,
            )

            db.add(admin)
            db.commit()
            db.refresh(admin)

            print(f"✅ Тестовый администратор создан!")
            print(f"   Telegram ID: {admin.telegram_id}")
            print(f"   Username: @{admin.username}")
            print(f"   Роль: {admin.role.value}")
            print(f"\n💡 Для тестирования используйте команду /admin в боте")

    if __name__ == "__main__":
        test_admin_panel()
        create_test_admin()

except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что все зависимости установлены")
except Exception as e:
    print(f"Ошибка: {e}")
