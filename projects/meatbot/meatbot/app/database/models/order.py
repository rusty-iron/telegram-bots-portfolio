"""
Модели заказов
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class OrderStatus(str, Enum):
    """Статусы заказа"""

    PENDING = "pending"  # Ожидает обработки
    CONFIRMED = "confirmed"  # Подтвержден
    PROCESSING = "processing"  # В обработке
    SHIPPED = "shipped"  # Отправлен
    DELIVERED = "delivered"  # Доставлен
    CANCELLED = "cancelled"  # Отменен
    REFUNDED = "refunded"  # Возвращен


class PaymentStatus(str, Enum):
    """Статусы оплаты"""

    PENDING = "pending"  # Ожидает оплаты
    PAID = "paid"  # Оплачен
    FAILED = "failed"  # Ошибка оплаты
    REFUNDED = "refunded"  # Возвращен


class PaymentMethod(str, Enum):
    """Способы оплаты"""

    CARD = "card"  # Банковская карта
    CASH = "cash"  # Наличные при получении
    TRANSFER = "transfer"  # Перевод на карту


class Order(Base):
    """Модель заказа"""

    __tablename__ = "orders"

    # Основные поля
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="ID заказа"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID пользователя",
    )

    # Номер заказа (уникальный)
    order_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, comment="Номер заказа"
    )

    # Статусы
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
        comment="Статус заказа",
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False,
        comment="Статус оплаты",
    )

    # Способ оплаты
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(PaymentMethod), nullable=False, comment="Способ оплаты"
    )

    # Суммы
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="Сумма товаров без доставки"
    )
    delivery_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, nullable=False, comment="Стоимость доставки"
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="Общая сумма заказа"
    )

    # Данные доставки
    delivery_address: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Адрес доставки")
    delivery_phone: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Телефон для доставки"
    )
    delivery_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Заметки к доставке"
    )

    # Временные метки
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата подтверждения заказа",
    )
    shipped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Дата отправки заказа"
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Дата доставки заказа"
    )

    # Дополнительная информация
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Заметки к заказу")

    # Связи с другими моделями
    user = relationship("User", back_populates="orders")
    order_items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Order(id={
            self.id}, number={
            self.order_number}, status={
            self.status}, total={
                self.total_amount})>"

    @property
    def formatted_total_amount(self) -> str:
        """Форматированная общая сумма"""
        return f"{self.total_amount:.2f} ₽"

    @property
    def formatted_subtotal(self) -> str:
        """Форматированная сумма товаров"""
        return f"{self.subtotal:.2f} ₽"

    @property
    def formatted_delivery_cost(self) -> str:
        """Форматированная стоимость доставки"""
        return f"{self.delivery_cost:.2f} ₽"


class OrderItem(Base):
    """Модель позиции в заказе"""

    __tablename__ = "order_items"

    # Основные поля
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="ID позиции заказа",
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID заказа",
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID товара",
    )

    # Данные товара на момент заказа (snapshot)
    product_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Название товара на момент заказа"
    )
    product_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Единица измерения на момент заказа",
    )
    product_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="Цена товара на момент заказа"
    )

    # Количество и сумма
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Количество товара")
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="Общая стоимость позиции"
    )

    # Связи с другими моделями
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

    def __repr__(self) -> str:
        return f"<OrderItem(order_id={
            self.order_id}, product={
            self.product_name}, qty={
            self.quantity})>"

    @property
    def formatted_total_price(self) -> str:
        """Форматированная общая стоимость позиции"""
        return f"{self.total_price:.2f} ₽"

    @property
    def formatted_product_price(self) -> str:
        """Форматированная цена товара"""
        return f"{self.product_price:.2f} ₽"
