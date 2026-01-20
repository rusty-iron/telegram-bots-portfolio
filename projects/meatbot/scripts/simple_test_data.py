#!/usr/bin/env python3
"""
Простой скрипт для добавления тестовых данных
"""
import os
import sys

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from meatbot.app.database import Category, Product, get_db

    def add_simple_test_data():
        """Добавить простые тестовые данные"""
        print("Добавляем тестовые данные...")

        with get_db() as db:
            # Проверяем, есть ли уже категории
            existing_categories = db.query(Category).count()
            if existing_categories > 0:
                print(f"В базе уже есть {existing_categories} категорий")
                return

            # Создаем категории
            categories_data = [
                {
                    "name": "Говядина",
                    "description": "Свежая говядина высшего качества",
                    "is_active": True,
                },
                {
                    "name": "Свинина",
                    "description": "Отборная свинина",
                    "is_active": True,
                },
                {
                    "name": "Курица",
                    "description": "Свежая курица",
                    "is_active": True,
                },
            ]

            categories = []
            for cat_data in categories_data:
                category = Category(**cat_data)
                db.add(category)
                categories.append(category)

            db.commit()

            # Обновляем ID категорий после коммита
            for category in categories:
                db.refresh(category)

            # Создаем товары
            products_data = [
                # Говядина
                {
                    "name": "Говяжья вырезка",
                    "description": "Нежная говяжья вырезка",
                    "price": 1200,
                    "stock_quantity": 10,
                    "category_id": categories[0].id,
                    "is_active": True,
                },
                {
                    "name": "Говяжий фарш",
                    "description": "Свежий говяжий фарш",
                    "price": 800,
                    "stock_quantity": 15,
                    "category_id": categories[0].id,
                    "is_active": True,
                },
                # Свинина
                {
                    "name": "Свиная корейка",
                    "description": "Сочная свиная корейка",
                    "price": 900,
                    "stock_quantity": 12,
                    "category_id": categories[1].id,
                    "is_active": True,
                },
                {
                    "name": "Свиной фарш",
                    "description": "Свежий свиной фарш",
                    "price": 600,
                    "stock_quantity": 20,
                    "category_id": categories[1].id,
                    "is_active": True,
                },
                # Курица
                {
                    "name": "Целая курица",
                    "description": "Свежая целая курица",
                    "price": 400,
                    "stock_quantity": 25,
                    "category_id": categories[2].id,
                    "is_active": True,
                },
                {
                    "name": "Куриные грудки",
                    "description": "Куриные грудки без кости",
                    "price": 500,
                    "stock_quantity": 20,
                    "category_id": categories[2].id,
                    "is_active": True,
                },
            ]

            for prod_data in products_data:
                product = Product(**prod_data)
                db.add(product)

            db.commit()
            print("✅ Тестовые данные добавлены успешно!")
            print(
                f"Добавлено {len(categories)} категорий "
                f"и {len(products_data)} товаров"
            )

    if __name__ == "__main__":
        add_simple_test_data()

except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что все зависимости установлены")
except Exception as e:
    print(f"Ошибка: {e}")
