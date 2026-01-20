"""
Валидация для админ-панели
"""

import re

from .validation import ValidationError, sanitize_text


def validate_product_name(name: str) -> str:
    """
    Валидирует название товара

    Args:
        name: Название товара

    Returns:
        str: Очищенное название

    Raises:
        ValidationError: Если название некорректное
    """
    if not name:
        raise ValidationError("Название товара обязательно")

    # Очищаем и санитизируем
    cleaned = sanitize_text(name.strip())

    # Проверяем длину
    if len(cleaned) < 2:
        raise ValidationError(
            "Название товара слишком короткое (минимум 2 символа)"
        )

    if len(cleaned) > 255:
        raise ValidationError(
            "Название товара слишком длинное (максимум 255 символов)"
        )

    # Проверяем на подозрительные паттерны
    suspicious_patterns = [
        r"<script",
        r"javascript:",
        r"on\w+\s*=",
        r"data:",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            raise ValidationError("Название содержит недопустимые символы")

    return cleaned


def validate_product_description(description: str) -> str:
    """
    Валидирует описание товара

    Args:
        description: Описание товара

    Returns:
        str: Очищенное описание

    Raises:
        ValidationError: Если описание некорректное
    """
    if not description:
        return ""

    # Очищаем и санитизируем
    cleaned = sanitize_text(description.strip())

    # Проверяем длину
    if len(cleaned) > 1000:
        raise ValidationError(
            "Описание товара слишком длинное (максимум 1000 символов)"
        )

    # Проверяем на подозрительные паттерны
    suspicious_patterns = [
        r"<script",
        r"javascript:",
        r"on\w+\s*=",
        r"data:",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            raise ValidationError("Описание содержит недопустимые символы")

    return cleaned


def validate_category_name(name: str) -> str:
    """
    Валидирует название категории

    Args:
        name: Название категории

    Returns:
        str: Очищенное название

    Raises:
        ValidationError: Если название некорректное
    """
    if not name:
        raise ValidationError("Название категории обязательно")

    # Очищаем и санитизируем
    cleaned = sanitize_text(name.strip())

    # Проверяем длину
    if len(cleaned) < 2:
        raise ValidationError(
            "Название категории слишком короткое (минимум 2 символа)"
        )

    if len(cleaned) > 255:
        raise ValidationError(
            "Название категории слишком длинное (максимум 255 символов)"
        )

    # Проверяем на подозрительные паттерны
    suspicious_patterns = [
        r"<script",
        r"javascript:",
        r"on\w+\s*=",
        r"data:",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            raise ValidationError("Название содержит недопустимые символы")

    return cleaned


def validate_category_description(description: str) -> str:
    """
    Валидирует описание категории

    Args:
        description: Описание категории

    Returns:
        str: Очищенное описание

    Raises:
        ValidationError: Если описание некорректное
    """
    if not description:
        return ""

    # Очищаем и санитизируем
    cleaned = sanitize_text(description.strip())

    # Проверяем длину
    if len(cleaned) > 500:
        raise ValidationError(
            "Описание категории слишком длинное (максимум 500 символов)"
        )

    # Проверяем на подозрительные паттерны
    suspicious_patterns = [
        r"<script",
        r"javascript:",
        r"on\w+\s*=",
        r"data:",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            raise ValidationError("Описание содержит недопустимые символы")

    return cleaned


def validate_unit(unit: str) -> str:
    """
    Валидирует единицу измерения

    Args:
        unit: Единица измерения

    Returns:
        str: Очищенная единица

    Raises:
        ValidationError: Если единица некорректная
    """
    if not unit:
        raise ValidationError("Единица измерения обязательна")

    # Очищаем
    cleaned = unit.strip()

    # Проверяем длину
    if len(cleaned) < 1:
        raise ValidationError("Единица измерения слишком короткая")

    if len(cleaned) > 20:
        raise ValidationError(
            "Единица измерения слишком длинная (максимум 20 символов)"
        )

    # Проверяем, что это простой текст (буквы и точки)
    if not re.match(r"^[а-яА-ЯёЁa-zA-Z.]+$", cleaned):
        raise ValidationError(
            "Единица измерения должна содержать только буквы"
        )

    return cleaned
