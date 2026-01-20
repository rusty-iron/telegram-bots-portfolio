"""
Утилиты для генерации номеров заказов
"""

from datetime import datetime
from typing import Optional

from ..database import Order, get_db


def generate_order_number() -> str:
    """
    Генерирует уникальный номер заказа в формате ORD-YYYYMMDD-NNNN

    Формат:
    - ORD - префикс
    - YYYYMMDD - дата создания
    - NNNN - порядковый номер за день (0001, 0002, ...)

    Returns:
        str: Уникальный номер заказа
    """
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"ORD-{today}"

    with get_db() as db:
        # Находим последний заказ за сегодня
        last_order = (
            db.query(Order)
            .filter(Order.order_number.like(f"{prefix}%"))
            .order_by(Order.order_number.desc())
            .first()
        )

        if last_order:
            # Извлекаем номер из последнего заказа
            try:
                last_number = int(last_order.order_number.split("-")[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                # Если не удалось распарсить, начинаем с 1
                next_number = 1
        else:
            # Первый заказ за сегодня
            next_number = 1

    return f"{prefix}-{next_number:04d}"


def validate_order_number(order_number: str) -> bool:
    """
    Проверяет корректность формата номера заказа

    Args:
        order_number: Номер заказа для проверки

    Returns:
        bool: True если формат корректный, False иначе
    """
    if not order_number:
        return False

    parts = order_number.split("-")
    if len(parts) != 3:
        return False

    prefix, date_part, number_part = parts

    # Проверяем префикс
    if prefix != "ORD":
        return False

    # Проверяем дату (должна быть 8 цифр)
    if len(date_part) != 8 or not date_part.isdigit():
        return False

    # Проверяем номер (должен быть 4 цифры)
    if len(number_part) != 4 or not number_part.isdigit():
        return False

    # Проверяем, что дата корректная
    try:
        datetime.strptime(date_part, "%Y%m%d")
    except ValueError:
        return False

    return True


def get_order_date_from_number(order_number: str) -> Optional[datetime]:
    """
    Извлекает дату создания заказа из номера заказа

    Args:
        order_number: Номер заказа

    Returns:
        datetime: Дата создания заказа или None если номер некорректный
    """
    if not validate_order_number(order_number):
        return None

    try:
        date_part = order_number.split("-")[1]
        return datetime.strptime(date_part, "%Y%m%d")
    except (ValueError, IndexError):
        return None
