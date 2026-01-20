"""
Утилиты для валидации пользовательского ввода
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


class ValidationError(Exception):
    """Исключение для ошибок валидации"""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class Validator:
    """Базовый класс для валидаторов"""

    def validate(self, value: Any) -> Any:
        """Валидирует значение и возвращает очищенное значение"""
        raise NotImplementedError


class StringValidator(Validator):
    """Валидатор для строк"""

    def __init__(
        self,
        min_length: int = 0,
        max_length: int = 255,
        pattern: Optional[str] = None,
        required: bool = True,
        trim: bool = True,
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.required = required
        self.trim = trim

    def validate(self, value: Any) -> str:
        """Валидирует строковое значение"""
        if value is None:
            if self.required:
                raise ValidationError("Field is required")
            return ""

        # Преобразуем в строку
        if not isinstance(value, str):
            value = str(value)

        # Обрезаем пробелы
        if self.trim:
            value = value.strip()

        # Проверяем длину
        if len(value) < self.min_length:
            raise ValidationError(f"Minimum length is {self.min_length}")

        if len(value) > self.max_length:
            raise ValidationError(f"Maximum length is {self.max_length}")

        # Проверяем паттерн
        if self.pattern and not re.match(self.pattern, value):
            raise ValidationError("Value does not match required pattern")

        return value


class IntegerValidator(Validator):
    """Валидатор для целых чисел"""

    def __init__(
        self,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        required: bool = True,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.required = required

    def validate(self, value: Any) -> int:
        """Валидирует целочисленное значение"""
        if value is None:
            if self.required:
                raise ValidationError("Field is required")
            return 0

        try:
            # Преобразуем в целое число
            if isinstance(value, str):
                value = int(value)
            elif not isinstance(value, int):
                value = int(value)
        except (ValueError, TypeError):
            raise ValidationError("Invalid integer value")

        # Проверяем диапазон
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(f"Minimum value is {self.min_value}")

        if self.max_value is not None and value > self.max_value:
            raise ValidationError(f"Maximum value is {self.max_value}")

        return value


class DecimalValidator(Validator):
    """Валидатор для десятичных чисел"""

    def __init__(
        self,
        min_value: Optional[Decimal] = None,
        max_value: Optional[Decimal] = None,
        decimal_places: int = 2,
        required: bool = True,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.decimal_places = decimal_places
        self.required = required

    def validate(self, value: Any) -> Decimal:
        """Валидирует десятичное значение"""
        if value is None:
            if self.required:
                raise ValidationError("Field is required")
            return Decimal("0")

        try:
            # Преобразуем в Decimal
            if isinstance(value, str):
                value = Decimal(value)
            elif isinstance(value, (int, float)):
                value = Decimal(str(value))
            elif not isinstance(value, Decimal):
                value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            raise ValidationError("Invalid decimal value")

        # Проверяем диапазон
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(f"Minimum value is {self.min_value}")

        if self.max_value is not None and value > self.max_value:
            raise ValidationError(f"Maximum value is {self.max_value}")

        # Округляем до нужного количества знаков
        return value.quantize(Decimal("0.01"))


class EmailValidator(Validator):
    """Валидатор для email адресов"""

    def __init__(self, required: bool = True):
        self.required = required
        self.pattern = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def validate(self, value: Any) -> str:
        """Валидирует email адрес"""
        if value is None:
            if self.required:
                raise ValidationError("Email is required")
            return ""

        if not isinstance(value, str):
            value = str(value)

        value = value.strip().lower()

        if not self.pattern.match(value):
            raise ValidationError("Invalid email format")

        return value


class PhoneValidator(Validator):
    """Валидатор для телефонных номеров"""

    def __init__(self, required: bool = True):
        self.required = required
        self.pattern = re.compile(r"^\+?[1-9]\d{1,14}$")

    def validate(self, value: Any) -> str:
        """Валидирует телефонный номер"""
        if value is None:
            if self.required:
                raise ValidationError("Phone number is required")
            return ""

        if not isinstance(value, str):
            value = str(value)

        # Удаляем все символы кроме цифр и +
        cleaned = re.sub(r"[^\d+]", "", value)

        if not self.pattern.match(cleaned):
            raise ValidationError("Invalid phone number format")

        return cleaned


class FileValidator(Validator):
    """Валидатор для файлов"""

    def __init__(
        self,
        allowed_extensions: Optional[List[str]] = None,
        max_size: int = 5 * 1024 * 1024,
        required: bool = True,
    ):  # 5MB
        self.allowed_extensions = allowed_extensions or [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        ]
        self.max_size = max_size
        self.required = required

    def validate(self, value: Any) -> Any:
        """Валидирует файл"""
        if value is None:
            if self.required:
                raise ValidationError("File is required")
            return None

        # Проверяем размер файла
        if hasattr(value, "size") and value.size > self.max_size:
            raise ValidationError(
                f"File size exceeds maximum of {
                    self.max_size} bytes")

        # Проверяем расширение файла
        if hasattr(value, "filename"):
            filename = value.filename.lower()
            if not any(filename.endswith(ext)
                       for ext in self.allowed_extensions):
                raise ValidationError(
                    f"File type not allowed. Allowed types: {
                        ', '.join(
                            self.allowed_extensions)}")

        return value


class DataValidator:
    """Валидатор для сложных структур данных"""

    def __init__(self, schema: Dict[str, Validator]):
        self.schema = schema

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидирует словарь данных"""
        validated_data = {}
        errors = {}

        for field, validator in self.schema.items():
            try:
                value = data.get(field)
                validated_data[field] = validator.validate(value)
            except ValidationError as e:
                errors[field] = e.message
                logger.warning(
                    "validation_error",
                    field=field,
                    error=e.message)

        if errors:
            raise ValidationError(f"Validation failed: {errors}")

        return validated_data


# Предопределенные схемы валидации
class ValidationSchemas:
    """Предопределенные схемы валидации"""

    @staticmethod
    def user_data() -> DataValidator:
        """Схема валидации данных пользователя"""
        return DataValidator(
            {
                "telegram_id": IntegerValidator(min_value=1, required=True),
                "username": StringValidator(min_length=1, max_length=255, required=False),
                "first_name": StringValidator(min_length=1, max_length=255, required=True),
                "last_name": StringValidator(min_length=1, max_length=255, required=False),
                "phone": PhoneValidator(required=False),
            }
        )

    @staticmethod
    def product_data() -> DataValidator:
        """Схема валидации данных товара"""
        return DataValidator(
            {
                "name": StringValidator(
                    min_length=1, max_length=255, required=True), "description": StringValidator(
                    min_length=0, max_length=1000, required=False), "price": DecimalValidator(
                    min_value=Decimal("0"), required=True), "category_id": IntegerValidator(
                        min_value=1, required=True), "is_active": IntegerValidator(
                            min_value=0, max_value=1, required=False), })

    @staticmethod
    def category_data() -> DataValidator:
        """Схема валидации данных категории"""
        return DataValidator(
            {
                "name": StringValidator(
                    min_length=1, max_length=255, required=True), "description": StringValidator(
                    min_length=0, max_length=500, required=False), "is_active": IntegerValidator(
                    min_value=0, max_value=1, required=False), })

    @staticmethod
    def order_data() -> DataValidator:
        """Схема валидации данных заказа"""
        return DataValidator(
            {
                "user_id": IntegerValidator(
                    min_value=1,
                    required=True),
                "total_amount": DecimalValidator(
                    min_value=Decimal("0"),
                    required=True),
                "status": StringValidator(
                    pattern=r"^(pending|confirmed|processing|ready|delivered|cancelled)$",
                    required=True,
                ),
                "notes": StringValidator(
                    min_length=0,
                    max_length=500,
                    required=False),
            })

    @staticmethod
    def cart_item_data() -> DataValidator:
        """Схема валидации данных элемента корзины"""
        return DataValidator(
            {
                "product_id": IntegerValidator(
                    min_value=1, required=True), "quantity": IntegerValidator(
                    min_value=1, max_value=99, required=True), "notes": StringValidator(
                    min_length=0, max_length=200, required=False), })


def validate_input(data: Dict[str, Any], schema_type: str) -> Dict[str, Any]:
    """Удобная функция для валидации входных данных"""
    try:
        if schema_type == "user":
            validator = ValidationSchemas.user_data()
        elif schema_type == "product":
            validator = ValidationSchemas.product_data()
        elif schema_type == "category":
            validator = ValidationSchemas.category_data()
        elif schema_type == "order":
            validator = ValidationSchemas.order_data()
        elif schema_type == "cart_item":
            validator = ValidationSchemas.cart_item_data()
        else:
            raise ValidationError(f"Unknown schema type: {schema_type}")

        return validator.validate(data)

    except ValidationError as e:
        logger.error(
            "input_validation_failed",
            schema_type=schema_type,
            error=str(e))
        raise e


# Специальные валидаторы для заказов
def validate_phone_number(phone: str) -> str:
    """
    Валидирует российский номер телефона

    Args:
        phone: Номер телефона для валидации

    Returns:
        str: Очищенный номер телефона

    Raises:
        ValidationError: Если номер некорректный
    """
    if not phone:
        raise ValidationError("Номер телефона обязателен")

    # Удаляем все символы кроме цифр и +
    cleaned = re.sub(r"[^\d+]", "", phone.strip())

    # Проверяем различные форматы российских номеров
    patterns = [
        r"^\+7\d{10}$",  # +7XXXXXXXXXX
        r"^8\d{10}$",  # 8XXXXXXXXXX
        r"^7\d{10}$",  # 7XXXXXXXXXX
    ]

    for pattern in patterns:
        if re.match(pattern, cleaned):
            # Нормализуем к формату +7XXXXXXXXXX
            if cleaned.startswith("8"):
                cleaned = "+7" + cleaned[1:]
            elif cleaned.startswith("7"):
                cleaned = "+" + cleaned
            elif not cleaned.startswith("+"):
                cleaned = "+" + cleaned

            return cleaned

    raise ValidationError(
        "Неверный формат номера телефона. "
        "Используйте формат: +7XXXXXXXXXX или 8XXXXXXXXXX")


def validate_address(address: str, user_id: Optional[int] = None) -> str:
    """
    Валидирует адрес доставки

    Args:
        address: Адрес для валидации
        user_id: ID пользователя (для мониторинга)

    Returns:
        str: Очищенный адрес

    Raises:
        ValidationError: Если адрес некорректный
    """
    if not address:
        raise ValidationError("Адрес доставки обязателен")

    # Очищаем адрес
    cleaned = address.strip()

    # Проверяем минимальную длину
    if len(cleaned) < 10:
        if user_id:
            from ..services.security_monitor import security_monitor

            security_monitor.log_validation_error(
                user_id=user_id,
                field_name="address",
                error_message="Address too short",
                input_value=cleaned,
            )
        raise ValidationError("Адрес слишком короткий. Укажите полный адрес")

    # Проверяем максимальную длину
    if len(cleaned) > 500:
        raise ValidationError("Адрес слишком длинный")

    # Проверяем на подозрительные символы
    suspicious_patterns = [
        (r"<script", "XSS/Script injection"),
        (r"javascript:", "JavaScript injection"),
        (r"on\w+\s*=", "Event handler injection"),
        (r"data:", "Data URI injection"),
        (r";select", "SQL injection"),
        (r"union.*select", "SQL injection"),
        (r"drop\s+table", "SQL injection"),
    ]

    for pattern, attack_type in suspicious_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            if user_id:
                from ..services.security_monitor import security_monitor

                security_monitor.log_injection_attempt(
                    user_id=user_id,
                    input_text=cleaned,
                    detected_pattern=attack_type,
                    field_name="address",
                )
            raise ValidationError("Адрес содержит недопустимые символы")

    return cleaned


def validate_delivery_notes(notes: str) -> str:
    """
    Валидирует комментарии к доставке

    Args:
        notes: Комментарии для валидации

    Returns:
        str: Очищенные комментарии
    """
    if not notes:
        return ""

    # Очищаем комментарии
    cleaned = notes.strip()

    # Проверяем максимальную длину
    if len(cleaned) > 200:
        raise ValidationError(
            "Комментарии слишком длинные (максимум 200 символов)")

    # Проверяем на подозрительные символы
    suspicious_patterns = [
        r"<script",
        r"javascript:",
        r"on\w+\s*=",
        r"data:",
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            raise ValidationError("Комментарии содержат недопустимые символы")

    return cleaned


def sanitize_text(text: str) -> str:
    """
    Очищает текст от потенциально опасных символов

    Args:
        text: Текст для очистки

    Returns:
        str: Очищенный текст
    """
    if not text:
        return ""

    # Удаляем HTML теги
    text = re.sub(r"<[^>]+>", "", text)

    # Удаляем потенциально опасные символы
    text = re.sub(r"[<>\"'&]", "", text)

    # Удаляем лишние пробелы
    text = re.sub(r"\s+", " ", text).strip()

    return text


def validate_payment_method(payment_method: str) -> str:
    """
    Валидирует способ оплаты

    Args:
        payment_method: Способ оплаты для валидации

    Returns:
        str: Валидный способ оплаты

    Raises:
        ValidationError: Если способ оплаты некорректный
    """
    valid_methods = ["cash", "transfer"]

    if payment_method not in valid_methods:
        raise ValidationError(
            f"Неверный способ оплаты. Доступные варианты: {
                ', '.join(valid_methods)}")

    return payment_method
