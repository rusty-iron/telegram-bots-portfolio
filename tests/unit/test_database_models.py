"""
Тест для проверки работы моделей базы данных
"""

from decimal import Decimal

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


def test_user_model():
    """Тест модели User"""
    user = User(
        id=123456789,
        username="testuser",
        first_name="Тест",
        last_name="Пользователь",
        phone="+7900123456",
        language_code="ru",
    )

    assert user.id == 123456789
    assert user.username == "testuser"
    assert user.full_name == "Тест Пользователь"
    assert user.display_name == "@testuser"
    assert user.is_active is True
    assert user.is_blocked is False


def test_category_model():
    """Тест модели Category"""
    category = Category(name="Мясо", description="Свежее мясо", sort_order=1)

    assert category.name == "Мясо"
    assert category.description == "Свежее мясо"
    assert category.sort_order == 1
    assert category.is_active is True


def test_product_model():
    """Тест модели Product"""
    product = Product(
        name="Говядина",
        description="Свежая говядина",
        price=Decimal("500.00"),
        unit="кг",
        category_id=1,
    )

    assert product.name == "Говядина"
    assert product.price == Decimal("500.00")
    assert product.formatted_price == "500.00 ₽"
    assert product.display_name == "Говядина (кг)"
    assert product.is_active is True
    assert product.is_available is True


def test_cart_item_model():
    """Тест модели CartItem"""
    cart_item = CartItem(
        user_id=123456789,
        product_id=1,
        quantity=2,
        price_at_add=Decimal("500.00"),
    )

    assert cart_item.user_id == 123456789
    assert cart_item.product_id == 1
    assert cart_item.quantity == 2
    assert cart_item.total_price == Decimal("1000.00")
    assert cart_item.formatted_total_price == "1000.00 ₽"


def test_order_model():
    """Тест модели Order"""
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

    assert order.order_number == "ORD-001"
    assert order.status == OrderStatus.PENDING
    assert order.payment_status == PaymentStatus.PENDING
    assert order.payment_method == PaymentMethod.CARD
    assert order.total_amount == Decimal("1200.00")
    assert order.formatted_total_amount == "1200.00 ₽"


def test_order_item_model():
    """Тест модели OrderItem"""
    order_item = OrderItem(
        order_id=1,
        product_id=1,
        product_name="Говядина",
        product_unit="кг",
        product_price=Decimal("500.00"),
        quantity=2,
        total_price=Decimal("1000.00"),
    )

    assert order_item.order_id == 1
    assert order_item.product_id == 1
    assert order_item.product_name == "Говядина"
    assert order_item.quantity == 2
    assert order_item.total_price == Decimal("1000.00")
    assert order_item.formatted_total_price == "1000.00 ₽"


def test_enum_values():
    """Тест значений enum"""
    assert OrderStatus.PENDING == "pending"
    assert PaymentStatus.PAID == "paid"
    assert PaymentMethod.CARD == "card"
