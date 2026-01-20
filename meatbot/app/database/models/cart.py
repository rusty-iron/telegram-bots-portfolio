"""
Модели корзины покупок
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class CartItem(Base):
    """Модель товара в корзине"""

    __tablename__ = "cart_items"

    # Основные поля
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="ID записи корзины",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID пользователя",
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID товара",
    )

    # Количество и цена
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="Количество товара"
    )
    price_at_add: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Цена товара на момент добавления в корзину",
    )

    # Дополнительные параметры
    notes: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Заметки к товару в корзине"
    )

    # Связи с другими моделями
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

    # Уникальность: один товар на пользователя
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "product_id",
            name="uq_cart_user_product"),
    )

    def __repr__(self) -> str:
        return (
            f"<CartItem(user_id={
                self.user_id}, product_id={
                self.product_id}, qty={
                self.quantity})>")

    @property
    def total_price(self) -> Decimal:
        """Общая стоимость позиции в корзине"""
        return self.price_at_add * self.quantity

    @property
    def formatted_total_price(self) -> str:
        """Форматированная общая стоимость"""
        return f"{self.total_price:.2f} ₽"

    @property
    def formatted_price_at_add(self) -> str:
        """Форматированная цена на момент добавления"""
        return f"{self.price_at_add:.2f} ₽"
