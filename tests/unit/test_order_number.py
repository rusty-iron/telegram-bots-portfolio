"""
Unit тесты для генератора номеров заказов
"""

from datetime import datetime
from unittest.mock import Mock, patch

from meatbot.app.utils.order_number import (
    generate_order_number,
    get_order_date_from_number,
    validate_order_number,
)


class TestOrderNumberGenerator:
    """Тесты для генератора номеров заказов"""

    @patch("meatbot.app.utils.order_number.get_db")
    def test_generate_order_number_first_order(self, mock_get_db):
        """Тест генерации номера для первого заказа за день"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Нет заказов за сегодня
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None)

        # Мокаем текущую дату
        with patch("meatbot.app.utils.order_number.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20251021"

            result = generate_order_number()

        # Проверяем результат
        assert result == "ORD-20251021-0001"

    @patch("meatbot.app.utils.order_number.get_db")
    def test_generate_order_number_existing_orders(self, mock_get_db):
        """Тест генерации номера при наличии заказов за день"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Мокаем последний заказ
        mock_last_order = Mock()
        mock_last_order.order_number = "ORD-20251021-0005"
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            mock_last_order)

        # Мокаем текущую дату
        with patch("meatbot.app.utils.order_number.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20251021"

            result = generate_order_number()

        # Проверяем результат
        assert result == "ORD-20251021-0006"

    @patch("meatbot.app.utils.order_number.get_db")
    def test_generate_order_number_invalid_last_order(self, mock_get_db):
        """Тест генерации номера при некорректном номере последнего заказа"""
        # Мокаем базу данных
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Мокаем заказ с некорректным номером
        mock_last_order = Mock()
        mock_last_order.order_number = "INVALID-ORDER-NUMBER"
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            mock_last_order)

        # Мокаем текущую дату
        with patch("meatbot.app.utils.order_number.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20251021"

            result = generate_order_number()

        # Проверяем результат (должен начать с 1)
        assert result == "ORD-20251021-0001"

    def test_validate_order_number_valid(self):
        """Тест валидации корректных номеров заказов"""
        valid_numbers = [
            "ORD-20251021-0001",
            "ORD-20241231-9999",
            "ORD-20240101-0001",
        ]

        for order_number in valid_numbers:
            result = validate_order_number(order_number)
            assert result is True

    def test_validate_order_number_invalid_format(self):
        """Тест валидации неверных форматов номеров заказов"""
        invalid_numbers = [
            "ORD-20251021",  # Неполный номер
            "ORD-20251021-0001-EXTRA",  # Лишние части
            "INVALID-20251021-0001",  # Неверный префикс
            "ORD-2025102-0001",  # Неверная дата (7 цифр)
            "ORD-20251021-001",  # Неверный номер (3 цифры)
            "ORD-20251021-00001",  # Неверный номер (5 цифр)
            "ORD-20251321-0001",  # Неверная дата (13 месяц)
            "ORD-20251032-0001",  # Неверная дата (32 день)
            "",  # Пустая строка
            None,  # None
        ]

        for order_number in invalid_numbers:
            result = validate_order_number(order_number)
            assert result is False

    def test_validate_order_number_invalid_date(self):
        """Тест валидации номеров с неверными датами"""
        invalid_dates = [
            "ORD-20250230-0001",  # 30 февраля
            "ORD-20250431-0001",  # 31 апреля
            "ORD-20250631-0001",  # 31 июня
            "ORD-20250931-0001",  # 31 сентября
            "ORD-20251131-0001",  # 31 ноября
        ]

        for order_number in invalid_dates:
            result = validate_order_number(order_number)
            assert result is False

    def test_get_order_date_from_number_valid(self):
        """Тест извлечения даты из корректного номера заказа"""
        test_cases = [
            ("ORD-20251021-0001", datetime(2025, 10, 21)),
            ("ORD-20241231-9999", datetime(2024, 12, 31)),
            ("ORD-20240101-0001", datetime(2024, 1, 1)),
        ]

        for order_number, expected_date in test_cases:
            result = get_order_date_from_number(order_number)
            assert result == expected_date

    def test_get_order_date_from_number_invalid(self):
        """Тест извлечения даты из неверного номера заказа"""
        invalid_numbers = [
            "ORD-20251021",  # Неполный номер
            "INVALID-20251021-0001",  # Неверный префикс
            "ORD-20251321-0001",  # Неверная дата
            "",  # Пустая строка
            None,  # None
        ]

        for order_number in invalid_numbers:
            result = get_order_date_from_number(order_number)
            assert result is None

    def test_order_number_format_consistency(self):
        """Тест консистентности формата номеров заказов"""
        # Генерируем несколько номеров и проверяем их формат
        with patch("meatbot.app.utils.order_number.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

            with patch("meatbot.app.utils.order_number.datetime") as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "20251021"

                for i in range(1, 6):
                    # Мокаем предыдущий заказ
                    if i > 1:
                        mock_last_order = Mock()
                        mock_last_order.order_number = f"ORD-20251021-{
                            i - 1:04d}"
                        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_last_order
                    else:
                        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

                    result = generate_order_number()

                    # Проверяем формат
                    assert result.startswith("ORD-20251021-")
                    assert len(result) == 17  # ORD-YYYYMMDD-NNNN
                    assert result.endswith(f"{i:04d}")

                    # Проверяем валидность
                    assert validate_order_number(result) is True
