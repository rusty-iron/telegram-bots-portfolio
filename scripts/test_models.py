"""
Скрипт для тестирования подключения к базе данных и моделей
"""

from decimal import Decimal

from meatbot.app.config import settings
from meatbot.app.database import (
    CartItem,
    Category,
    Order,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    Product,
    User,
)
from meatbot.app.utils.db import create_sync_engine


def test_database_connection():
    """Тест подключения к базе данных"""
    print("🔍 Тестирование подключения к базе данных...")

    engine = create_sync_engine(settings.database_url)

    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1 as test")
            test_value = result.fetchone()[0]
            print(f"✅ Подключение к БД успешно: {test_value}")
            return True
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False


def test_models_creation():
    """Тест создания моделей"""
    print("\n🔍 Тестирование создания моделей...")

    try:
        # Создаем тестовые объекты
        user = User(
            id=123456789,
            username="testuser",
            first_name="Тест",
            last_name="Пользователь",
            phone="+7900123456",
            language_code="ru",
        )

        category = Category(
            name="Мясо", description="Свежее мясо", sort_order=1
        )

        product = Product(
            name="Говядина",
            description="Свежая говядина",
            price=Decimal("500.00"),
            unit="кг",
            category_id=1,
        )

        cart_item = CartItem(
            user_id=123456789,
            product_id=1,
            quantity=2,
            price_at_add=Decimal("500.00"),
        )

        order = Order(
            user_id=123456789,
            order_number="ORD-001",
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            payment_method=PaymentMethod.CARD,
            subtotal=Decimal("1000.00"),
            delivery_cost=Decimal("200.00"),
            total_amount=Decimal("1200.00"),
            delivery_address="ул. Тестовая, д. 1",
            delivery_phone="+7900123456",
        )

        order_item = OrderItem(
            order_id=1,
            product_id=1,
            product_name="Говядина",
            product_unit="кг",
            product_price=Decimal("500.00"),
            quantity=2,
            total_price=Decimal("1000.00"),
        )

        print("✅ Все модели созданы успешно")
        print(f"   - User: {user}")
        print(f"   - Category: {category}")
        print(f"   - Product: {product}")
        print(f"   - CartItem: {cart_item}")
        print(f"   - Order: {order}")
        print(f"   - OrderItem: {order_item}")

        return True

    except Exception as e:
        print(f"❌ Ошибка создания моделей: {e}")
        return False


def test_model_properties():
    """Тест свойств моделей"""
    print("\n🔍 Тестирование свойств моделей...")

    try:
        user = User(
            id=123456789,
            username="testuser",
            first_name="Тест",
            last_name="Пользователь",
        )

        product = Product(
            name="Говядина", price=Decimal("500.00"), unit="кг", category_id=1
        )

        cart_item = CartItem(
            user_id=123456789,
            product_id=1,
            quantity=2,
            price_at_add=Decimal("500.00"),
        )

        # Тестируем свойства
        assert user.full_name == "Тест Пользователь"
        assert user.display_name == "@testuser"
        assert product.formatted_price == "500.00 ₽"
        assert product.display_name == "Говядина (кг)"
        assert cart_item.total_price == Decimal("1000.00")
        assert cart_item.formatted_total_price == "1000.00 ₽"

        print("✅ Все свойства моделей работают корректно")
        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования свойств: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования моделей базы данных MeatBot\n")

    # Тест подключения к БД
    db_ok = test_database_connection()

    # Тест создания моделей
    models_ok = test_models_creation()

    # Тест свойств моделей
    properties_ok = test_model_properties()

    print(f"\n📊 Результаты тестирования:")
    print(f"   - Подключение к БД: {'✅' if db_ok else '❌'}")
    print(f"   - Создание моделей: {'✅' if models_ok else '❌'}")
    print(f"   - Свойства моделей: {'✅' if properties_ok else '❌'}")

    if all([db_ok, models_ok, properties_ok]):
        print("\n🎉 Все тесты прошли успешно!")
        return True
    else:
        print("\n⚠️ Некоторые тесты не прошли")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
