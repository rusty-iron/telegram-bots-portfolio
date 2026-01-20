"""
Модели пользователей системы
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class User(Base):
    """Модель пользователя Telegram"""

    __tablename__ = "users"

    # Основные поля
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        comment="Telegram User ID")
    username: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Telegram username"
    )
    first_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Имя пользователя")
    last_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Фамилия пользователя"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Номер телефона"
    )
    delivery_address: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Сохраненный адрес доставки"
    )
    delivery_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Сохраненные комментарии к доставке"
    )
    language_code: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="Код языка пользователя"
    )

    # Статусные поля
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Активен ли пользователь",
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Заблокирован ли пользователь",
    )

    # Дополнительная информация
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Заметки о пользователе"
    )

    # Связи с другими моделями
    cart_items = relationship(
        "CartItem",
        back_populates="user",
        cascade="all, delete-orphan")
    orders = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={
            self.id}, username={
            self.username}, name={
            self.first_name})>"

    @property
    def full_name(self) -> str:
        """Полное имя пользователя"""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def display_name(self) -> str:
        """Отображаемое имя пользователя"""
        if self.username:
            return f"@{self.username}"
        return self.full_name
