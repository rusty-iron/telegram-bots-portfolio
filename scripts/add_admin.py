#!/usr/bin/env python3
"""
Скрипт для добавления администратора
"""
import os
import sys

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from meatbot.app.database import AdminRole, AdminUser, get_db

    def add_admin():
        """Добавить администратора"""
        print("Добавление администратора...")

        # Запрашиваем данные
        telegram_id = input("Введите Telegram ID администратора: ")
        if not telegram_id.isdigit():
            print("❌ Telegram ID должен быть числом!")
            return

        telegram_id = int(telegram_id)

        username = input("Введите username (или оставьте пустым): ").strip()
        first_name = input("Введите имя (или оставьте пустым): ").strip()
        last_name = input("Введите фамилию (или оставьте пустым): ").strip()

        print("\nДоступные роли:")
        for role in AdminRole:
            print(f"- {role.value}: {role.name}")

        role_input = (
            input("Введите роль (по умолчанию moderator): ").strip().lower()
        )

        if role_input == "super_admin":
            role = AdminRole.SUPER_ADMIN
        elif role_input == "admin":
            role = AdminRole.ADMIN
        else:
            role = AdminRole.MODERATOR

        with get_db() as db:
            # Проверяем, есть ли уже такой администратор
            existing = (
                db.query(AdminUser)
                .filter(AdminUser.telegram_id == telegram_id)
                .first()
            )

            if existing:
                print(
                    f"❌ Администратор с Telegram ID {telegram_id} уже существует!"
                )
                return

            # Создаем администратора
            admin = AdminUser(
                telegram_id=telegram_id,
                username=username if username else None,
                first_name=first_name if first_name else None,
                last_name=last_name if last_name else None,
                role=role,
                is_active=True,
            )

            db.add(admin)
            db.commit()
            db.refresh(admin)

            print(f"✅ Администратор успешно создан!")
            print(f"   ID: {admin.id}")
            print(f"   Telegram ID: {admin.telegram_id}")
            print(f"   Имя: {admin.full_name}")
            print(f"   Роль: {admin.role.value}")
            print(f"   Username: {admin.username or 'Не указан'}")

    if __name__ == "__main__":
        add_admin()

except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что все зависимости установлены")
except Exception as e:
    print(f"Ошибка: {e}")
