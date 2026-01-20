"""
Unit тесты для OrderService
"""

from decimal import Decimal
from unittest.mock import Mock, patch

from meatbot.app.database import OrderStatus, PaymentStatus
from meatbot.app.services.order_service import OrderService


class TestOrderService:
    """Тесты для OrderService"""

    def setup_method(self):
        """Настройка для каждого теста"""
        self.order_service = OrderService()

    @patch("meatbot.app.services.order_service.get_db")
    def test_create_order_from_cart_success(self, mock_get_db):
        """Тест успешного создания заказа из корзины"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Мокаем пользователя
        mock_user = Mock()
        mock_user.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_user
        )

        # Мокаем товары в корзине
        mock_cart_item = Mock()
        mock_cart_item.price_at_add = Decimal("100.00")
        mock_cart_item.quantity = 2
        mock_cart_item.product.is_available = True
        mock_cart_item.product.name = "Тестовый товар"
        mock_cart_item.product.unit = "кг"

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_cart_item
        ]

        # Мокаем создание заказа
        mock_order = Mock()
        mock_order.id = 1
        mock_order.order_number = "ORD-20251021-0001"
        mock_order.formatted_total_amount = "200.00 ₽"
        mock_db.add.return_value = None
        mock_db.flush.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Данные для заказа
        delivery_data = {
            "phone": "+79123456789",
            "address": "Тестовый адрес 123",
            "notes": "Тестовые комментарии",
        }

        # Вызываем метод
        with patch(
            "meatbot.app.services.order_service.generate_order_number",
            return_value="ORD-20251021-0001",
        ):
            result = self.order_service.create_order_from_cart(
                user_id=1, delivery_data=delivery_data, payment_method="cash"
            )

        # Проверяем результат
        assert result is not None
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @patch("meatbot.app.services.order_service.get_db")
    def test_create_order_from_cart_empty_cart(self, mock_get_db):
        """Тест создания заказа с пустой корзиной"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Мокаем пользователя
        mock_user = Mock()
        mock_user.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_user
        )

        # Пустая корзина
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # Данные для заказа
        delivery_data = {
            "phone": "+79123456789",
            "address": "Тестовый адрес 123",
            "notes": "",
        }

        # Вызываем метод
        result = self.order_service.create_order_from_cart(
            user_id=1, delivery_data=delivery_data, payment_method="cash"
        )

        # Проверяем результат
        assert result is None

    @patch("meatbot.app.services.order_service.get_db")
    def test_create_order_from_cart_user_not_found(self, mock_get_db):
        """Тест создания заказа для несуществующего пользователя"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Пользователь не найден
        mock_db.query.return_value.filter.return_value.first.return_value = (
            None
        )

        # Данные для заказа
        delivery_data = {
            "phone": "+79123456789",
            "address": "Тестовый адрес 123",
            "notes": "",
        }

        # Вызываем метод
        result = self.order_service.create_order_from_cart(
            user_id=999, delivery_data=delivery_data, payment_method="cash"
        )

        # Проверяем результат
        assert result is None

    @patch("meatbot.app.services.order_service.get_db")
    def test_get_user_order_success(self, mock_get_db):
        """Тест успешного получения заказа пользователя"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Мокаем заказ
        mock_order = Mock()
        mock_order.id = 1
        mock_order.user_id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_order
        )

        # Вызываем метод
        result = self.order_service.get_user_order(user_id=1, order_id=1)

        # Проверяем результат
        assert result is not None
        assert result.id == 1

    @patch("meatbot.app.services.order_service.get_db")
    def test_get_user_order_not_found(self, mock_get_db):
        """Тест получения несуществующего заказа"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Заказ не найден
        mock_db.query.return_value.filter.return_value.first.return_value = (
            None
        )

        # Вызываем метод
        result = self.order_service.get_user_order(user_id=1, order_id=999)

        # Проверяем результат
        assert result is None

    @patch("meatbot.app.services.order_service.get_db")
    def test_get_user_orders_success(self, mock_get_db):
        """Тест успешного получения списка заказов пользователя"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Мокаем заказы
        mock_order1 = Mock()
        mock_order1.id = 1
        mock_order2 = Mock()
        mock_order2.id = 2
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_order1,
            mock_order2,
        ]

        # Вызываем метод
        result = self.order_service.get_user_orders(
            user_id=1, limit=10, offset=0
        )

        # Проверяем результат
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2

    @patch("meatbot.app.services.order_service.get_db")
    def test_cancel_order_success(self, mock_get_db):
        """Тест успешной отмены заказа"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Мокаем заказ
        mock_order = Mock()
        mock_order.id = 1
        mock_order.user_id = 1
        mock_order.status = OrderStatus.PENDING
        mock_order.order_number = "ORD-20251021-0001"
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_order
        )

        # Вызываем метод
        result = self.order_service.cancel_order(user_id=1, order_id=1)

        # Проверяем результат
        assert result is True
        assert mock_order.status == OrderStatus.CANCELLED
        assert mock_order.payment_status == PaymentStatus.REFUNDED
        mock_db.commit.assert_called()

    @patch("meatbot.app.services.order_service.get_db")
    def test_cancel_order_not_found(self, mock_get_db):
        """Тест отмены несуществующего заказа"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Заказ не найден
        mock_db.query.return_value.filter.return_value.first.return_value = (
            None
        )

        # Вызываем метод
        result = self.order_service.cancel_order(user_id=1, order_id=999)

        # Проверяем результат
        assert result is False

    @patch("meatbot.app.services.order_service.get_db")
    def test_cancel_order_already_delivered(self, mock_get_db):
        """Тест отмены уже доставленного заказа"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Мокаем заказ с статусом DELIVERED
        mock_order = Mock()
        mock_order.id = 1
        mock_order.user_id = 1
        mock_order.status = OrderStatus.DELIVERED
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_order
        )

        # Вызываем метод
        result = self.order_service.cancel_order(user_id=1, order_id=1)

        # Проверяем результат
        assert result is False

    @patch("meatbot.app.services.order_service.get_db")
    def test_get_order_details_success(self, mock_get_db):
        """Тест успешного получения деталей заказа"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Мокаем заказ
        mock_order = Mock()
        mock_order.id = 1
        mock_order.formatted_total_amount = "200.00 ₽"
        mock_order.formatted_subtotal = "200.00 ₽"
        mock_order.formatted_delivery_cost = "0.00 ₽"

        # Мокаем элементы заказа
        mock_order_item = Mock()
        mock_order_item.product_name = "Тестовый товар"
        mock_order_item.quantity = 2
        mock_order_item.product_price = Decimal("100.00")
        mock_order_item.total_price = Decimal("200.00")

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_order_item
        ]

        # Вызываем метод
        result = self.order_service.get_order_details(mock_order)

        # Проверяем результат
        assert result is not None
        assert "order" in result
        assert "items" in result
        assert "items_count" in result
        assert result["items_count"] == 1

    @patch("meatbot.app.services.order_service.get_db")
    def test_update_order_status_success(self, mock_get_db):
        """Тест успешного обновления статуса заказа"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Мокаем заказ
        mock_order = Mock()
        mock_order.id = 1
        mock_order.status = OrderStatus.PENDING
        mock_order.order_number = "ORD-20251021-0001"
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_order
        )

        # Вызываем метод
        result = self.order_service.update_order_status(
            order_id=1, new_status=OrderStatus.CONFIRMED
        )

        # Проверяем результат
        assert result is True
        assert mock_order.status == OrderStatus.CONFIRMED
        mock_db.commit.assert_called()

    @patch("meatbot.app.services.order_service.get_db")
    def test_get_order_statistics_success(self, mock_get_db):
        """Тест успешного получения статистики заказов"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Мокаем результаты запросов
        mock_db.query.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.filter.return_value.all.return_value = [
            (Decimal("100.00"),),
            (Decimal("200.00"),),
            (Decimal("150.00"),),
        ]

        # Вызываем метод
        result = self.order_service.get_order_statistics()

        # Проверяем результат
        assert result is not None
        assert "total_orders" in result
        assert "status_breakdown" in result
        assert "total_amount" in result
        assert "average_order_value" in result
        assert result["total_orders"] == 10
        assert result["total_amount"] == 450.0
        assert result["average_order_value"] == 45.0
