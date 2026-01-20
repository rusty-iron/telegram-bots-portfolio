"""
Unit тесты для ValidationService
"""

from decimal import Decimal

import pytest

from meatbot.app.utils.validation import (
    DataValidator,
    DecimalValidator,
    EmailValidator,
    IntegerValidator,
    PhoneValidator,
    StringValidator,
    ValidationError,
    ValidationSchemas,
    validate_input,
)


class TestStringValidator:
    """Тесты для StringValidator"""

    def test_valid_string(self):
        """Тест валидации корректной строки"""
        validator = StringValidator(min_length=1, max_length=10)
        result = validator.validate("test")
        assert result == "test"

    def test_string_too_short(self):
        """Тест валидации слишком короткой строки"""
        validator = StringValidator(min_length=5, max_length=10)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("test")
        assert "Minimum length is 5" in str(exc_info.value)

    def test_string_too_long(self):
        """Тест валидации слишком длинной строки"""
        validator = StringValidator(min_length=1, max_length=3)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("test")
        assert "Maximum length is 3" in str(exc_info.value)

    def test_string_with_pattern(self):
        """Тест валидации строки с паттерном"""
        validator = StringValidator(pattern=r"^[a-z]+$")
        result = validator.validate("test")
        assert result == "test"

    def test_string_pattern_mismatch(self):
        """Тест валидации строки с несоответствующим паттерном"""
        validator = StringValidator(pattern=r"^[a-z]+$")
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("Test123")
        assert "does not match required pattern" in str(exc_info.value)

    def test_required_string_none(self):
        """Тест валидации обязательной строки с None"""
        validator = StringValidator(required=True)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(None)
        assert "Field is required" in str(exc_info.value)

    def test_optional_string_none(self):
        """Тест валидации необязательной строки с None"""
        validator = StringValidator(required=False)
        result = validator.validate(None)
        assert result == ""

    def test_string_trimming(self):
        """Тест обрезки пробелов в строке"""
        validator = StringValidator(trim=True)
        result = validator.validate("  test  ")
        assert result == "test"


class TestIntegerValidator:
    """Тесты для IntegerValidator"""

    def test_valid_integer(self):
        """Тест валидации корректного целого числа"""
        validator = IntegerValidator(min_value=1, max_value=10)
        result = validator.validate(5)
        assert result == 5

    def test_integer_from_string(self):
        """Тест валидации целого числа из строки"""
        validator = IntegerValidator()
        result = validator.validate("123")
        assert result == 123

    def test_integer_too_small(self):
        """Тест валидации слишком маленького числа"""
        validator = IntegerValidator(min_value=5)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(3)
        assert "Minimum value is 5" in str(exc_info.value)

    def test_integer_too_large(self):
        """Тест валидации слишком большого числа"""
        validator = IntegerValidator(max_value=5)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(10)
        assert "Maximum value is 5" in str(exc_info.value)

    def test_invalid_integer(self):
        """Тест валидации некорректного целого числа"""
        validator = IntegerValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("not_a_number")
        assert "Invalid integer value" in str(exc_info.value)

    def test_required_integer_none(self):
        """Тест валидации обязательного целого числа с None"""
        validator = IntegerValidator(required=True)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(None)
        assert "Field is required" in str(exc_info.value)


class TestDecimalValidator:
    """Тесты для DecimalValidator"""

    def test_valid_decimal(self):
        """Тест валидации корректного десятичного числа"""
        validator = DecimalValidator(
            min_value=Decimal("0"), max_value=Decimal("100")
        )
        result = validator.validate(Decimal("50.5"))
        assert result == Decimal("50.50")

    def test_decimal_from_string(self):
        """Тест валидации десятичного числа из строки"""
        validator = DecimalValidator()
        result = validator.validate("123.45")
        assert result == Decimal("123.45")

    def test_decimal_from_float(self):
        """Тест валидации десятичного числа из float"""
        validator = DecimalValidator()
        result = validator.validate(123.45)
        assert result == Decimal("123.45")

    def test_decimal_too_small(self):
        """Тест валидации слишком маленького десятичного числа"""
        validator = DecimalValidator(min_value=Decimal("10"))
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(Decimal("5"))
        assert "Minimum value is 10" in str(exc_info.value)

    def test_decimal_too_large(self):
        """Тест валидации слишком большого десятичного числа"""
        validator = DecimalValidator(max_value=Decimal("100"))
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(Decimal("150"))
        assert "Maximum value is 100" in str(exc_info.value)

    def test_invalid_decimal(self):
        """Тест валидации некорректного десятичного числа"""
        validator = DecimalValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("not_a_number")
        assert "Invalid decimal value" in str(exc_info.value)


class TestEmailValidator:
    """Тесты для EmailValidator"""

    def test_valid_email(self):
        """Тест валидации корректного email"""
        validator = EmailValidator()
        result = validator.validate("test@example.com")
        assert result == "test@example.com"

    def test_email_lowercase(self):
        """Тест приведения email к нижнему регистру"""
        validator = EmailValidator()
        result = validator.validate("TEST@EXAMPLE.COM")
        assert result == "test@example.com"

    def test_invalid_email(self):
        """Тест валидации некорректного email"""
        validator = EmailValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("invalid_email")
        assert "Invalid email format" in str(exc_info.value)

    def test_required_email_none(self):
        """Тест валидации обязательного email с None"""
        validator = EmailValidator(required=True)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(None)
        assert "Email is required" in str(exc_info.value)


class TestPhoneValidator:
    """Тесты для PhoneValidator"""

    def test_valid_phone(self):
        """Тест валидации корректного телефона"""
        validator = PhoneValidator()
        result = validator.validate("+1234567890")
        assert result == "+1234567890"

    def test_phone_cleaning(self):
        """Тест очистки телефона от лишних символов"""
        validator = PhoneValidator()
        result = validator.validate("+1 (234) 567-890")
        assert result == "+1234567890"

    def test_invalid_phone(self):
        """Тест валидации некорректного телефона"""
        validator = PhoneValidator()
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("123")
        assert "Invalid phone number format" in str(exc_info.value)

    def test_required_phone_none(self):
        """Тест валидации обязательного телефона с None"""
        validator = PhoneValidator(required=True)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(None)
        assert "Phone number is required" in str(exc_info.value)


class TestDataValidator:
    """Тесты для DataValidator"""

    def test_valid_data(self):
        """Тест валидации корректных данных"""
        schema = {
            "name": StringValidator(min_length=1, max_length=50),
            "age": IntegerValidator(min_value=0, max_value=120),
            "email": EmailValidator(required=False),
        }
        validator = DataValidator(schema)

        data = {"name": "John Doe", "age": 30, "email": "john@example.com"}

        result = validator.validate(data)
        assert result["name"] == "John Doe"
        assert result["age"] == 30
        assert result["email"] == "john@example.com"

    def test_invalid_data(self):
        """Тест валидации некорректных данных"""
        schema = {
            "name": StringValidator(min_length=1, max_length=50),
            "age": IntegerValidator(min_value=0, max_value=120),
        }
        validator = DataValidator(schema)

        data = {
            "name": "",
            "age": 150,
        }  # Слишком короткое имя  # Слишком большой возраст

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(data)
        assert "Validation failed" in str(exc_info.value)


class TestValidationSchemas:
    """Тесты для ValidationSchemas"""

    def test_user_data_schema(self):
        """Тест схемы валидации данных пользователя"""
        schema = ValidationSchemas.user_data()
        assert isinstance(schema, DataValidator)

        valid_data = {
            "telegram_id": 123456789,
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1234567890",
        }

        result = schema.validate(valid_data)
        assert result["telegram_id"] == 123456789
        assert result["first_name"] == "Test"

    def test_product_data_schema(self):
        """Тест схемы валидации данных товара"""
        schema = ValidationSchemas.product_data()
        assert isinstance(schema, DataValidator)

        valid_data = {
            "name": "Test Product",
            "description": "Test Description",
            "price": Decimal("99.99"),
            "category_id": 1,
            "is_active": 1,
        }

        result = schema.validate(valid_data)
        assert result["name"] == "Test Product"
        assert result["price"] == Decimal("99.99")

    def test_category_data_schema(self):
        """Тест схемы валидации данных категории"""
        schema = ValidationSchemas.category_data()
        assert isinstance(schema, DataValidator)

        valid_data = {
            "name": "Test Category",
            "description": "Test Description",
            "is_active": 1,
        }

        result = schema.validate(valid_data)
        assert result["name"] == "Test Category"

    def test_order_data_schema(self):
        """Тест схемы валидации данных заказа"""
        schema = ValidationSchemas.order_data()
        assert isinstance(schema, DataValidator)

        valid_data = {
            "user_id": 123,
            "total_amount": Decimal("99.99"),
            "status": "pending",
            "notes": "Test order",
        }

        result = schema.validate(valid_data)
        assert result["user_id"] == 123
        assert result["status"] == "pending"

    def test_cart_item_data_schema(self):
        """Тест схемы валидации данных элемента корзины"""
        schema = ValidationSchemas.cart_item_data()
        assert isinstance(schema, DataValidator)

        valid_data = {"product_id": 1, "quantity": 2, "notes": "Test notes"}

        result = schema.validate(valid_data)
        assert result["product_id"] == 1
        assert result["quantity"] == 2


class TestValidateInput:
    """Тесты для функции validate_input"""

    def test_validate_user_input(self):
        """Тест валидации входных данных пользователя"""
        data = {
            "telegram_id": 123456789,
            "first_name": "Test",
            "last_name": "User",
        }

        result = validate_input(data, "user")
        assert result["telegram_id"] == 123456789
        assert result["first_name"] == "Test"

    def test_validate_product_input(self):
        """Тест валидации входных данных товара"""
        data = {"name": "Test Product", "price": "99.99", "category_id": 1}

        result = validate_input(data, "product")
        assert result["name"] == "Test Product"
        assert result["price"] == Decimal("99.99")

    def test_validate_unknown_schema(self):
        """Тест валидации с неизвестной схемой"""
        data = {"test": "value"}

        with pytest.raises(ValidationError) as exc_info:
            validate_input(data, "unknown")
        assert "Unknown schema type" in str(exc_info.value)
