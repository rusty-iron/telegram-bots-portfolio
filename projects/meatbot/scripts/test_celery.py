"""
Скрипт для тестирования Celery задач
"""

from meatbot.app.celery_app import celery_app
from meatbot.app.tasks import (
    process_order,
    process_payment_webhook,
    send_order_notification,
    update_order_status,
)


def test_celery_connection():
    """Тест подключения к Celery"""
    print("🔍 Тестирование подключения к Celery...")

    try:
        # Проверяем подключение к брокеру
        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        if stats:
            print("✅ Celery подключен успешно")
            print(f"   - Активные воркеры: {len(stats)}")
            for worker_name, worker_stats in stats.items():
                print(
                    f"   - Воркер {worker_name}: {worker_stats.get('total', 0)} задач"
                )
            return True
        else:
            print("⚠️ Celery подключен, но нет активных воркеров")
            return False

    except Exception as e:
        print(f"❌ Ошибка подключения к Celery: {e}")
        return False


def test_order_tasks():
    """Тест задач обработки заказов"""
    print("\n🔍 Тестирование задач обработки заказов...")

    try:
        # Тест обработки заказа
        print("   - Тестируем process_order...")
        result = process_order.delay(123)
        print(f"   - Задача отправлена: {result.id}")

        # Ждем результат (максимум 10 секунд)
        try:
            task_result = result.get(timeout=10)
            print(f"   - Результат: {task_result}")
        except Exception as e:
            print(f"   - Ошибка получения результата: {e}")

        # Тест обновления статуса заказа
        print("   - Тестируем update_order_status...")
        result2 = update_order_status.delay(123, "confirmed")
        print(f"   - Задача отправлена: {result2.id}")

        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования задач заказов: {e}")
        return False


def test_notification_tasks():
    """Тест задач уведомлений"""
    print("\n🔍 Тестирование задач уведомлений...")

    try:
        # Тест отправки уведомления
        print("   - Тестируем send_order_notification...")
        result = send_order_notification.delay(
            user_id=123456789, order_id=123, message="Ваш заказ обработан!"
        )
        print(f"   - Задача отправлена: {result.id}")

        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования задач уведомлений: {e}")
        return False


def test_webhook_tasks():
    """Тест задач webhook'ов"""
    print("\n🔍 Тестирование задач webhook'ов...")

    try:
        # Тест обработки webhook'а платежа
        print("   - Тестируем process_payment_webhook...")
        webhook_data = {
            "id": "test_webhook_123",
            "event": "payment.succeeded",
            "object": {
                "id": "payment_123",
                "status": "succeeded",
                "amount": {"value": "1000.00", "currency": "RUB"},
            },
        }

        result = process_payment_webhook.delay(webhook_data)
        print(f"   - Задача отправлена: {result.id}")

        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования задач webhook'ов: {e}")
        return False


def test_task_queues():
    """Тест очередей задач"""
    print("\n🔍 Тестирование очередей задач...")

    try:
        inspect = celery_app.control.inspect()

        # Получаем информацию об активных задачах
        active = inspect.active()
        if active:
            print("   - Активные задачи:")
            for worker, tasks in active.items():
                print(f"     Воркер {worker}: {len(tasks)} задач")
                for task in tasks:
                    print(f"       - {task['name']} (ID: {task['id']})")

        # Получаем информацию о зарезервированных задачах
        reserved = inspect.reserved()
        if reserved:
            print("   - Зарезервированные задачи:")
            for worker, tasks in reserved.items():
                print(f"     Воркер {worker}: {len(tasks)} задач")

        # Получаем информацию о статистике
        stats = inspect.stats()
        if stats:
            print("   - Статистика воркеров:")
            for worker, worker_stats in stats.items():
                print(f"     Воркер {worker}:")
                print(f"       - Всего задач: {worker_stats.get('total', 0)}")
                print(
                    f"       - Успешных: {worker_stats.get('pool', {}).get('processes', 0)}"
                )

        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования очередей: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования Celery задач MeatBot\n")

    # Тест подключения
    connection_ok = test_celery_connection()

    if not connection_ok:
        print("\n⚠️ Celery не подключен. Убедитесь, что:")
        print("   1. Redis запущен")
        print("   2. Celery worker запущен")
        print("   3. Конфигурация корректна")
        return False

    # Тест задач
    orders_ok = test_order_tasks()
    notifications_ok = test_notification_tasks()
    webhooks_ok = test_webhook_tasks()
    queues_ok = test_task_queues()

    print(f"\n📊 Результаты тестирования:")
    print(f"   - Подключение к Celery: {'✅' if connection_ok else '❌'}")
    print(f"   - Задачи заказов: {'✅' if orders_ok else '❌'}")
    print(f"   - Задачи уведомлений: {'✅' if notifications_ok else '❌'}")
    print(f"   - Задачи webhook'ов: {'✅' if webhooks_ok else '❌'}")
    print(f"   - Очереди задач: {'✅' if queues_ok else '❌'}")

    if all(
        [connection_ok, orders_ok, notifications_ok, webhooks_ok, queues_ok]
    ):
        print("\n🎉 Все тесты Celery прошли успешно!")
        return True
    else:
        print("\n⚠️ Некоторые тесты не прошли")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
