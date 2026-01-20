"""
Unit тесты для валидации данных заказов
"""

import pytest

from meatbot.app.utils.validation import (
    ValidationError,
    sanitize_text,
    validate_address,
    validate_delivery_notes,
    validate_payment_method,
    validate_phone_number,
)


class TestOrderValidation:
    """Тесты для валидации данных заказов"""

    def test_validate_phone_number_success(self):
        """Тест успешной валидации номера телефона"""
        # Тестируем различные форматы
        test_cases = [
            "+79123456789",
            "89123456789",
            "79123456789",
            "+7 (912) 345-67-89",
            "8 (912) 345-67-89",
            "7 (912) 345-67-89",
        ]

        for phone in test_cases:
            result = validate_phone_number(phone)
            assert result == "+79123456789"

    def test_validate_phone_number_invalid_formats(self):
        """Тест валидации неверных форматов номера телефона"""
        invalid_phones = [
            "123",
            "123456789",
            "12345678901",
            "abc123456789",
            "",
            None,
            "+1234567890",  # Не российский номер
        ]

        for phone in invalid_phones:
            with pytest.raises(ValidationError):
                validate_phone_number(phone)

    def test_validate_phone_number_empty(self):
        """Тест валидации пустого номера телефона"""
        with pytest.raises(ValidationError) as exc_info:
            validate_phone_number("")

        assert "Номер телефона обязателен" in str(exc_info.value)

    def test_validate_address_success(self):
        """Тест успешной валидации адреса"""
        valid_addresses = [
            "ул. Тестовая, д. 123, кв. 45",
            "г. Москва, ул. Ленина, д. 1",
            "Санкт-Петербург, Невский проспект, д. 28",
            "Московская область, г. Подольск, ул. Советская, д. 15, кв. 7",
        ]

        for address in valid_addresses:
            result = validate_address(address)
            assert result == address.strip()

    def test_validate_address_too_short(self):
        """Тест валидации слишком короткого адреса"""
        short_addresses = [
            "ул. Тест",
            "д. 1",
            "Москва",
            "123",
        ]

        for address in short_addresses:
            with pytest.raises(ValidationError) as exc_info:
                validate_address(address)

            assert "Адрес слишком короткий" in str(exc_info.value)

    def test_validate_address_too_long(self):
        """Тест валидации слишком длинного адреса"""
        long_address = "у" * 501  # 501 символ

        with pytest.raises(ValidationError) as exc_info:
            validate_address(long_address)

        assert "Адрес слишком длинный" in str(exc_info.value)

    def test_validate_address_suspicious_content(self):
        """Тест валидации адреса с подозрительным содержимым"""
        suspicious_addresses = [
            "ул. Тестовая <script>alert('xss')</script>",
            "д. 123 javascript:alert('xss')",
            "кв. 45 onload=alert('xss')",
            "г. Москва data:text/html,<script>alert('xss')</script>",
        ]

        for address in suspicious_addresses:
            with pytest.raises(ValidationError) as exc_info:
                validate_address(address)

            assert "недопустимые символы" in str(exc_info.value)

    def test_validate_address_empty(self):
        """Тест валидации пустого адреса"""
        with pytest.raises(ValidationError) as exc_info:
            validate_address("")

        assert "Адрес доставки обязателен" in str(exc_info.value)

    def test_validate_delivery_notes_success(self):
        """Тест успешной валидации комментариев к доставке"""
        valid_notes = [
            "Код домофона: 1234",
            "Оставить у соседей",
            "Позвонить за 10 минут до доставки",
            "Вход со двора",
            "",  # Пустые комментарии разрешены
        ]

        for notes in valid_notes:
            result = validate_delivery_notes(notes)
            assert result == notes.strip()

    def test_validate_delivery_notes_too_long(self):
        """Тест валидации слишком длинных комментариев"""
        long_notes = "к" * 201  # 201 символ

        with pytest.raises(ValidationError) as exc_info:
            validate_delivery_notes(long_notes)

        assert "слишком длинные" in str(exc_info.value)

    def test_validate_delivery_notes_suspicious_content(self):
        """Тест валидации комментариев с подозрительным содержимым"""
        suspicious_notes = [
            "Код домофона <script>alert('xss')</script>",
            "Позвонить javascript:alert('xss')",
            "Оставить onload=alert('xss')",
        ]

        for notes in suspicious_notes:
            with pytest.raises(ValidationError) as exc_info:
                validate_delivery_notes(notes)

            assert "недопустимые символы" in str(exc_info.value)

    def test_validate_payment_method_success(self):
        """Тест успешной валидации способа оплаты"""
        valid_methods = ["cash", "transfer"]

        for method in valid_methods:
            result = validate_payment_method(method)
            assert result == method

    def test_validate_payment_method_invalid(self):
        """Тест валидации неверного способа оплаты"""
        invalid_methods = [
            "card",
            "paypal",
            "bitcoin",
            "invalid",
            "",
            None,
        ]

        for method in invalid_methods:
            with pytest.raises(ValidationError) as exc_info:
                validate_payment_method(method)

            assert "Неверный способ оплаты" in str(exc_info.value)

    def test_sanitize_text_success(self):
        """Тест успешной очистки текста"""
        test_cases = [
            ("<script>alert('xss')</script>", "alert('xss')"),
            ("<b>Жирный текст</b>", "Жирный текст"),
            ('Текст с "кавычками"', "Текст с кавычками"),
            ("Текст с < и > символами", "Текст с  и  символами"),
            ("Текст   с   лишними   пробелами", "Текст с лишними пробелами"),
            ("", ""),
            (None, ""),
        ]

        for input_text, expected in test_cases:
            result = sanitize_text(input_text)
            assert result == expected

    def test_sanitize_text_complex(self):
        """Тест очистки сложного текста"""
        input_text = "<script>alert('xss')</script>Текст с \"кавычками\" и <b>тегами</b>   и   пробелами"
        expected = "alert('xss')Текст с кавычками и тегами и пробелами"

        result = sanitize_text(input_text)
        assert result == expected

    def test_validation_error_message(self):
        """Тест сообщений об ошибках валидации"""
        # Тест с кастомным сообщением
        try:
            validate_phone_number("")
        except ValidationError as e:
            assert e.message == "Номер телефона обязателен"
            assert e.field is None

        # Тест с полем
        try:
            validate_address("")
        except ValidationError as e:
            assert e.message == "Адрес доставки обязателен"
            assert e.field is None
