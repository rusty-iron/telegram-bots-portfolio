#!/usr/bin/env python3
"""
Скрипт для проверки базы данных
"""
import os
import sys

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from meatbot.app.database import Category, Product, get_db

    def check_database():
        """Проверить содержимое базы данных"""
        print("Проверяем базу данных...")

        try:
            with get_db() as db:
                # Проверяем категории
                categories = db.query(Category).all()
                print(f"Найдено категорий: {len(categories)}")

                for cat in categories:
                    print(
                        f"  - {cat.name} (ID: {cat.id}, активна: {cat.is_active})"
                    )

                # Проверяем товары
                products = db.query(Product).all()
                print(f"\nНайдено товаров: {len(products)}")

                for prod in products:
                    print(
                        f"  - {
                            prod.name} (ID: {
                            prod.id}, цена: {
                            prod.price}₽, активен: {
                            prod.is_active})")

        except Exception as e:
            print(f"Ошибка при обращении к базе данных: {e}")

    if __name__ == "__main__":
        check_database()

except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что все зависимости установлены")
except Exception as e:
    print(f"Ошибка: {e}")
