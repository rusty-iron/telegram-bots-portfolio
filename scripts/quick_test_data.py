#!/usr/bin/env python3
"""
Быстрый скрипт для добавления минимальных тестовых данных
"""
import os
import sys

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main():
    try:
        from meatbot.app.database import Category, Product, get_db

        print("Добавляем минимальные тестовые данные...")

        with get_db() as db:
            # Проверяем, есть ли уже категории
            existing_categories = db.query(Category).count()
            if existing_categories > 0:
                print(f"В базе уже есть {existing_categories} категорий")
                return

            # Создаем одну категорию
            category = Category(
                name="Говядина",
                description="Свежая говядина высшего качества",
                is_active=True,
            )
            db.add(category)
            db.commit()
            db.refresh(category)

            # Создаем один товар
            product = Product(
                name="Говяжья вырезка",
                description="Нежная говяжья вырезка",
                price=1200,
                stock_quantity=10,
                category_id=category.id,
                is_active=True,
            )
            db.add(product)
            db.commit()

            print("✅ Тестовые данные добавлены успешно!")
            print(f"Добавлена категория: {category.name}")
            print(f"Добавлен товар: {product.name}")

    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        print("Убедитесь, что все зависимости установлены")
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
