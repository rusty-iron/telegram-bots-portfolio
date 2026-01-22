"""
Модуль валидации пользовательского ввода.

Содержит функции проверки имени, телефона и email.
"""

import re
from typing import Tuple


def validate_name(name: str) -> Tuple[bool, str]:
    """
    Проверяет корректность имени.

    Args:
        name: Введённое пользователем имя.

    Returns:
        Tuple[bool, str]: (успех, сообщение об ошибке или пустая строка).
    """
    name = name.strip()

    if len(name) < 2:
        return False, "Имя слишком короткое. Минимум 2 символа."

    if len(name) > 50:
        return False, "Имя слишком длинное. Максимум 50 символов."

    # Проверяем, что имя содержит только буквы, пробелы и дефисы
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$", name):
        return False, "Имя может содержать только буквы, пробелы и дефисы."

    return True, ""


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Проверяет корректность номера телефона.

    Допустимые форматы:
    - +7XXXXXXXXXX (российский)
    - 8XXXXXXXXXX (российский без +)
    - +XXXXXXXXXXX (международный)

    Args:
        phone: Введённый номер телефона.

    Returns:
        Tuple[bool, str]: (успех, сообщение об ошибке или пустая строка).
    """
    # Удаляем пробелы, скобки и дефисы
    cleaned = re.sub(r"[\s\(\)\-]", "", phone)

    # Паттерн для международного формата
    international_pattern = r"^\+[1-9]\d{6,14}$"

    # Паттерн для российского формата с 8
    russian_pattern = r"^8\d{10}$"

    if re.match(international_pattern, cleaned):
        return True, ""

    if re.match(russian_pattern, cleaned):
        return True, ""

    return False, (
        "Некорректный формат телефона.\n"
        "Примеры правильного формата:\n"
        "• +79991234567\n"
        "• 89991234567\n"
        "• +1234567890"
    )


def normalize_phone(phone: str) -> str:
    """
    Нормализует номер телефона к единому формату.

    Args:
        phone: Исходный номер телефона.

    Returns:
        str: Нормализованный номер.
    """
    cleaned = re.sub(r"[\s\(\)\-]", "", phone)

    # Если начинается с 8, заменяем на +7
    if cleaned.startswith("8") and len(cleaned) == 11:
        cleaned = "+7" + cleaned[1:]

    # Если нет +, добавляем
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    return cleaned


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Проверяет корректность email адреса.

    Args:
        email: Введённый email.

    Returns:
        Tuple[bool, str]: (успех, сообщение об ошибке или пустая строка).
    """
    email = email.strip().lower()

    # RFC 5322 упрощённый паттерн
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        return False, (
            "Некорректный формат email.\n"
            "Пример: example@mail.com"
        )

    return True, ""


def validate_message(message: str) -> Tuple[bool, str]:
    """
    Проверяет корректность сообщения.

    Args:
        message: Текст сообщения.

    Returns:
        Tuple[bool, str]: (успех, сообщение об ошибке или пустая строка).
    """
    if len(message) > 500:
        return False, f"Сообщение слишком длинное ({len(message)}/500 символов)."

    return True, ""
