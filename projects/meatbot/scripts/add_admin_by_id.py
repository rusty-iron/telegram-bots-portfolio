#!/usr/bin/env python3
"""
Скрипт для добавления администратора по ID
"""
import os
import sys

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from meatbot.app.database import AdminRole, AdminUser, get_db

    def add_admin_by_id(
        telegram_id: int, role: AdminRole = AdminRole.MODERATOR
    ):
        """Добавить администратора по Telegram ID"""
        print(f"Добавление администратора с Telegram ID: {telegram_id}")

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
                print(f"   ID: {existing.id}")
                print(f"   Имя: {existing.full_name}")
                print(f"   Роль: {existing.role.value}")
                print(f"   Username: {existing.username or 'Не указан'}")
                return False

            # Создаем администратора
            admin = AdminUser(
                telegram_id=telegram_id,
                username=None,
                first_name=None,
                last_name=None,
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
            return True

    if __name__ == "__main__":
        if len(sys.argv) < 2:
            print(
                "Использование: python add_admin_by_id.py <telegram_id> [role]"
            )
            print("Роли: super_admin, admin, moderator (по умолчанию)")
            sys.exit(1)

        try:
            telegram_id = int(sys.argv[1])
        except ValueError:
            print("❌ Telegram ID должен быть числом!")
            sys.exit(1)

        role = AdminRole.MODERATOR
        if len(sys.argv) > 2:
            role_input = sys.argv[2].lower()
            if role_input == "super_admin":
                role = AdminRole.SUPER_ADMIN
            elif role_input == "admin":
                role = AdminRole.ADMIN
            elif role_input == "moderator":
                role = AdminRole.MODERATOR
            else:
                print(f"❌ Неизвестная роль: {role_input}")
                print("Доступные роли: super_admin, admin, moderator")
                sys.exit(1)

        add_admin_by_id(telegram_id, role)

except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что все зависимости установлены")
except Exception as e:
    print(f"Ошибка: {e}")
